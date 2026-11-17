"""Controllo fotocamera Sony / Nikon / Canon tramite libgphoto2 (python-gphoto2) + simulatore.

Una sessione PTP persistente viene tenuta aperta su un unico thread dedicato
(libgphoto2 non è thread-safe). macOS (ptpcamerad / mscamerad-xpc) tende a
reclamare la fotocamera appena collegata: i processi vengono terminati prima
di aprire la sessione.
"""
from __future__ import annotations

import asyncio
import os
import re
import struct
import subprocess
import time
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .i18n import tr

try:
    import gphoto2 as gp
except ImportError:  # pragma: no cover
    gp = None

GPHOTO_AVAILABLE = gp is not None

# Chiave logica -> chiavi gphoto2 candidate (la prima esistente sulla fotocamera vince)
SONY_SETTLE_S = 2.5   # eventi da leggere dopo ogni scatto Sony prima del successivo (vedi _capture_blocking)

SETTING_KEYS: dict[str, list[str]] = {
    "shutterspeed": ["shutterspeed"],
    "iso": ["iso"],
    "aperture": ["f-number", "aperture"],
    "imageformat": ["imageformat", "imagequality"],
    "capturetarget": ["capturetarget"],
}

MACOS_CAMERA_DAEMONS = ["ptpcamerad", "mscamerad-xpc", "PTPCamera"]


class CameraError(Exception):
    pass


def release_from_macos() -> None:
    for name in MACOS_CAMERA_DAEMONS:
        subprocess.run(["killall", "-9", name], capture_output=True)


class GPhotoCamera:
    simulated = False

    def __init__(self, model: str = "", port: str = ""):
        self.model = model    # nome mostrato (dopo il collegamento quello che dichiara la fotocamera, es. "ILCE-6400")
        # nome del driver libgphoto2 (es. "Sony ILCE-6400 (PC Control)"): serve per riaprire la stessa fotocamera.
        # Va tenuto a parte: con il nome breve lookup_model falliva e il ricollegamento dava "[-105] Unknown model".
        self.driver = model
        self.port = port
        self._cam = None
        self._ctx = None
        self._exec = ThreadPoolExecutor(max_workers=1, thread_name_prefix="gphoto2")
        self._keys: dict[str, str] = {}
        self.settings: dict[str, dict] = {}
        self.busy = False
        self.last_file: str | None = None
        # Ritardo dopo il sollevamento dello specchio (reflex):
        # "nikon" = ritardo di esposizione della fotocamera, "canon" = blocco specchio (due pressioni)
        self.mirror_method: str | None = None
        self._mirror_original: str | None = None   # valore Nikon prima che l'app lo cambiasse
        self._mirror_warned = False
        self.live = False   # live view attivo (fotogrammi letti con capture_preview)
        self.log = lambda _msg: None

    @property
    def connected(self) -> bool:
        return self._cam is not None

    @property
    def is_sony(self) -> bool:
        # il nome dichiarato dalla fotocamera può non contenere la marca ("ILCE-6400"); quello del driver sì
        return "sony" in f"{self.driver or ''} {self.model or ''}".lower()

    async def _run(self, fn, *args):
        return await asyncio.get_running_loop().run_in_executor(self._exec, fn, *args)

    # ---------- rilevamento ----------
    @staticmethod
    def _detect_blocking() -> list[dict]:
        if not GPHOTO_AVAILABLE:
            raise CameraError(tr("python-gphoto2 non installato (pip install gphoto2)"))
        release_from_macos()
        time.sleep(0.3)
        cams = gp.check_result(gp.gp_camera_autodetect())
        return [{"model": name, "port": addr} for name, addr in cams]

    @classmethod
    async def detect(cls) -> list[dict]:
        return await asyncio.to_thread(cls._detect_blocking)

    # ---------- connessione ----------
    def _connect_blocking(self) -> None:
        if not GPHOTO_AVAILABLE:
            raise CameraError(tr("python-gphoto2 non installato (pip install gphoto2)"))
        last_err = None
        for attempt in range(4):
            release_from_macos()
            time.sleep(0.4 + attempt * 0.4)
            cam = gp.Camera()
            try:
                port = self.port
                if self.driver and not port:
                    # ricollegamento dopo che la fotocamera è sparita dall'USB: la porta può avere un numero nuovo e
                    # la si ritrova dal nome del driver (con il driver impostato e senza porta init() fallisce: [-5])
                    found = [addr for name, addr in gp.check_result(gp.gp_camera_autodetect()) if name == self.driver]
                    port = found[0] if found else ""
                if port:
                    port_list = gp.PortInfoList()
                    port_list.load()
                    cam.set_port_info(port_list[port_list.lookup_path(port)])
                if self.driver and port:
                    abilities = gp.CameraAbilitiesList()
                    abilities.load()
                    try:
                        cam.set_abilities(abilities[abilities.lookup_model(self.driver)])
                    except gp.GPhoto2Error:
                        pass   # nome sconosciuto: libgphoto2 riconosce la fotocamera da sé
                cam.init()
                self._cam = cam
                self.port = port or self.port
                break
            except gp.GPhoto2Error as exc:
                last_err = exc
        else:
            raise CameraError(tr(
                "Impossibile aprire la fotocamera ({err}). Chiudi Foto, Anteprima, Acquisizione Immagine "
                "e i software del produttore; per Sony imposta USB 'PC Remote'.", err=last_err))
        try:
            self.driver = str(self._cam.get_abilities().model or "").strip() or self.driver
        except gp.GPhoto2Error:
            pass
        try:
            summary = str(self._cam.get_summary())
            for line in summary.splitlines():
                if line.lower().startswith("model:"):
                    self.model = line.split(":", 1)[1].strip()
                    break
        except gp.GPhoto2Error:
            pass
        if not self.model:   # alcune fotocamere (es. Sony) non mettono "Model:" nel riepilogo
            try:
                self.model = str(self._cam.get_abilities().model or "").strip()
            except gp.GPhoto2Error:
                pass
        self._resolve_keys()
        self._read_settings_blocking()
        if self._has("exposuredelaymode"):
            self.mirror_method = "nikon"
        elif self._has("eosremoterelease"):
            self.mirror_method = "canon"

    def _resolve_keys(self) -> None:
        self._keys = {}
        for logical, candidates in SETTING_KEYS.items():
            for key in candidates:
                try:
                    self._cam.get_single_config(key)
                    self._keys[logical] = key
                    break
                except gp.GPhoto2Error:
                    continue

    def _has(self, key: str) -> bool:
        try:
            self._cam.get_single_config(key)
            return True
        except gp.GPhoto2Error:
            return False

    def _read_settings_blocking(self) -> dict:
        out = {}
        for logical, key in self._keys.items():
            try:
                w = self._cam.get_single_config(key)
                choices = [w.get_choice(i) for i in range(w.count_choices())] \
                    if w.get_type() in (gp.GP_WIDGET_RADIO, gp.GP_WIDGET_MENU) else []
                out[logical] = {"key": key, "current": str(w.get_value()), "choices": choices,
                                "readonly": bool(w.get_readonly())}
            except gp.GPhoto2Error:
                continue
        self.settings = out
        return out

    def _set_blocking(self, logical: str, value: str) -> dict:
        key = self._keys.get(logical)
        if not key:
            raise CameraError(tr("Impostazione '{name}' non supportata da questa fotocamera", name=logical))
        # Sony: il valore viene raggiunto "a scatti" e la fotocamera ignora il comando finché sta scrivendo
        # l'ultimo RAW sulla scheda; si rilegge e, se non ha preso il valore, si riprova (fino a ~6 s)
        out = {}
        for attempt in range(6):
            w = self._cam.get_single_config(key)
            w.set_value(value)
            self._cam.set_single_config(key, w)
            time.sleep(0.2 + 0.4 * attempt)
            out = self._read_settings_blocking()
            if str((out.get(logical) or {}).get("current")) == str(value):
                break
        return out

    def _disconnect_blocking(self) -> None:
        if self._cam is not None:
            self._end_preview_blocking()
            try:
                self._nikon_delay_blocking(0)
            except gp.GPhoto2Error:
                pass
            try:
                self._cam.exit()
            except gp.GPhoto2Error:
                pass
            self._cam = None

    async def connect(self) -> None:
        await self._run(self._connect_blocking)

    async def disconnect(self) -> None:
        await self._run(self._disconnect_blocking)

    async def reconnect(self) -> None:
        """Nuova sessione PTP con la stessa fotocamera, dopo che è sparita dall'USB (stop del Mac, batteria,
        cavo). La vecchia sessione si chiude senza badare agli errori: il dispositivo può non esserci più.
        Se la porta era fissata e dopo il ricollegamento ha un numero nuovo, si ritenta in automatico."""
        try:
            await self.disconnect()
        except Exception:  # noqa: BLE001  (sessione già morta)
            pass
        self._cam = None
        self.live = False
        try:
            await self.connect()
        except CameraError:
            if not self.port:
                raise
            self.port = ""
            await self.connect()

    async def read_settings(self) -> dict:
        self._require()
        return await self._run(self._read_settings_blocking)

    async def set_setting(self, logical: str, value: str) -> dict:
        self._require()
        return await self._run(self._set_blocking, logical, value)

    def _require(self) -> None:
        if not self.connected:
            raise CameraError(tr("Fotocamera non connessa"))

    # ---------- live view ----------
    def _preview_blocking(self) -> bytes:
        """Un fotogramma del live view (JPEG). Il primo accende il live view della fotocamera."""
        self._require()
        try:
            cam_file = self._cam.capture_preview()
        except gp.GPhoto2Error as exc:
            raise CameraError(tr("Live view non disponibile su questa fotocamera ({exc})", exc=exc)) from exc
        self.live = True
        return bytes(memoryview(cam_file.get_data_and_size()))

    def _end_preview_blocking(self) -> None:
        """Spegne il live view (Canon/Nikon: abbassa lo specchio). Sony non ha il comando."""
        if not self.live or self._cam is None:
            return
        self.live = False
        for key in ("viewfinder", "eosviewfinder"):
            if self._has(key):
                try:
                    self._set_raw(key, 0)
                except gp.GPhoto2Error:
                    pass
                return

    async def preview(self) -> bytes:
        return await self._run(self._preview_blocking)

    async def end_preview(self) -> None:
        await self._run(self._end_preview_blocking)

    # ---------- scatto ----------
    def _drain_events(self, timeout_ms: int, want_files: bool, deadline: float) -> list:
        """Legge gli eventi della fotocamera; restituisce i file aggiunti."""
        files = []
        while time.monotonic() < deadline:
            ev_type, data = self._cam.wait_for_event(timeout_ms)
            if ev_type == gp.GP_EVENT_FILE_ADDED:
                files.append((data.folder, data.name))
            elif ev_type == gp.GP_EVENT_CAPTURE_COMPLETE and not want_files:
                break
            elif ev_type == gp.GP_EVENT_TIMEOUT:
                if files or not want_files:
                    break
        return files

    # ---------- specchio ----------
    def _set_raw(self, key: str, value) -> None:
        w = self._cam.get_single_config(key)
        w.set_value(value)
        self._cam.set_single_config(key, w)

    def _nikon_delay_blocking(self, delay_s: float) -> None:
        """Imposta il ritardo di esposizione Nikon più vicino (per eccesso) a delay_s.
        Con delay_s = 0 rimette il valore che c'era prima che l'app lo cambiasse."""
        if self.mirror_method != "nikon":
            return
        w = self._cam.get_single_config("exposuredelaymode")
        current = str(w.get_value())
        if delay_s <= 0:
            if self._mirror_original is not None and current != self._mirror_original:
                self._set_raw("exposuredelaymode", self._mirror_original)
                self.log(tr("Ritardo di esposizione della fotocamera riportato a {value}", value=self._mirror_original))
            self._mirror_original = None
            return
        choices = [w.get_choice(i) for i in range(w.count_choices())]
        timed = []
        for c in choices:
            m = re.search(r"\d+(?:[.,]\d+)?", c)
            if m and float(m.group().replace(",", ".")) > 0:
                timed.append((float(m.group().replace(",", ".")), c))
        if timed:
            timed.sort()
            choice = next((c for t, c in timed if t >= delay_s - 0.01), timed[-1][1])
        else:  # modelli con solo On/Off: ritardo fisso deciso dalla fotocamera
            choice = next((c for c in choices if c.lower() in ("on", "1")), None)
        if choice is None:
            raise CameraError(tr("Ritardo di esposizione non riconosciuto (valori: {values})", values=", ".join(choices)))
        if choice != current:
            if self._mirror_original is None:
                self._mirror_original = current
            self._set_raw("exposuredelaymode", choice)
            self.log(tr("Ritardo di esposizione della fotocamera: {choice} (richiesti {delay} s)", choice=choice, delay=f"{delay_s:g}"))

    def _canon_mirror_up_blocking(self, delay_s: float) -> list | None:
        """Prima pressione: con il blocco specchio attivo solleva lo specchio, poi attende.
        Se invece la fotocamera scatta subito (blocco specchio spento) restituisce i file."""
        for value in ("Press Full", "Release Full"):
            self._set_raw("eosremoterelease", value)
        files, shot = [], False
        end = time.monotonic() + delay_s
        while (left := end - time.monotonic()) > 0:
            ev_type, data = self._cam.wait_for_event(max(1, int(left * 1000)))
            if ev_type == gp.GP_EVENT_FILE_ADDED:
                files.append((data.folder, data.name))
            elif ev_type == gp.GP_EVENT_CAPTURE_COMPLETE:
                shot = True
        if files or shot:
            if not self._mirror_warned:
                self._mirror_warned = True
                self.log(tr("Attenzione: la fotocamera ha scattato senza ritardo. Attiva il blocco dello "
                            "specchio nel menu della fotocamera (funzioni personalizzate)"))
            return files
        return None

    def _ensure_bulb(self) -> None:
        ss = self.settings.get("shutterspeed")
        if ss:
            bulb = next((c for c in ss["choices"] if c.lower() == "bulb"), None)
            if bulb and ss["current"] != bulb:
                self._set_blocking("shutterspeed", bulb)

    def _bulb_blocking(self, seconds: float) -> None:
        if self._has("eosremoterelease"):
            key, press, release = "eosremoterelease", "Press Full", "Release Full"
        elif self._has("bulb"):
            key, press, release = "bulb", 1, 0
        else:
            raise CameraError(tr("Questa fotocamera non supporta la posa B da remoto"))
        for value in (press, release):
            w = self._cam.get_single_config(key)
            w.set_value(value)
            self._cam.set_single_config(key, w)
            if value == press:
                time.sleep(seconds)

    def _capture_blocking(self, mode: str, dest_base: str | None, bulb_s: float, timeout_s: float,
                          mirror_s: float = 0) -> list[str]:
        self._require()
        deadline = time.monotonic() + timeout_s
        if self.is_sony:
            # Sony: senza una lettura delle proprietà dopo lo scatto precedente, la fotocamera (via libgphoto2)
            # crede di avere ancora un'immagine in memoria e lo scatto successivo va in timeout ([-1] dopo ~30 s).
            # Rileggere le impostazioni aggiorna lo stato; costa una frazione di secondo.
            try:
                self._read_settings_blocking()
            except gp.GPhoto2Error:
                pass
        self._nikon_delay_blocking(mirror_s)
        canon_mlu = mirror_s > 0 and self.mirror_method == "canon"
        if bulb_s > 0:
            self._ensure_bulb()
        early = self._canon_mirror_up_blocking(mirror_s) if canon_mlu else None
        if early is not None:  # scattato alla prima pressione: niente seconda pressione
            if mode == "trigger":
                return []
            new_files = early + [f for f in self._drain_events(500, not early, deadline) if f not in early]
        elif bulb_s > 0:
            self._bulb_blocking(bulb_s)
            new_files = self._drain_events(1000, True, deadline)
        elif canon_mlu:  # specchio già sollevato: la seconda pressione scatta
            for value in ("Press Full", "Release Full"):
                self._set_raw("eosremoterelease", value)
            if mode == "trigger":
                self._drain_events(500, False, deadline)
                return []
            new_files = self._drain_events(1000, True, deadline)
        elif mode == "trigger":
            self._cam.trigger_capture()
            self._drain_events(500, False, deadline)
            return []
        else:
            path = self._cam.capture(gp.GP_CAPTURE_IMAGE)
            new_files = [(path.folder, path.name)]
            # RAW+JPEG: il secondo file arriva come evento
            new_files += [f for f in self._drain_events(150, False, time.monotonic() + 2) if f not in new_files]

        if not new_files:
            raise CameraError(tr("La fotocamera non ha segnalato nessun file"))
        saved = []
        if mode == "download" and dest_base:
            for folder, name in new_files:
                ext = os.path.splitext(name)[1] or ".jpg"
                target = f"{dest_base}{ext}"
                cam_file = self._cam.file_get(folder, name, gp.GP_FILE_TYPE_NORMAL)
                cam_file.save(target)
                saved.append(target)
            if saved:
                self.last_file = saved[0]
        if self.is_sony:
            # Sony (provato su ILCE-6400 in PC Remote): dopo lo scatto la fotocamera manda ancora eventi per ~2 s
            # (oggetto rimosso dalla memoria, stati). Se lo scatto successivo parte prima che siano stati letti,
            # la fotocamera non scatta e libgphoto2 va in timeout dopo 35 s ([-1]). Leggerli qui per 2,5 s lo evita.
            end = time.monotonic() + SONY_SETTLE_S
            while time.monotonic() < end:
                try:
                    self._cam.wait_for_event(200)
                except gp.GPhoto2Error:
                    break
        return saved

    async def capture(self, mode: str = "download", dest_base: Path | None = None,
                      bulb_s: float = 0, timeout_s: float = 60, mirror_s: float = 0) -> list[str]:
        self._require()
        self.busy = True
        try:
            return await self._run(self._capture_blocking, mode, str(dest_base) if dest_base else None,
                                   bulb_s, timeout_s + bulb_s + mirror_s, mirror_s)
        finally:
            self.busy = False

    def describe(self) -> dict:
        return {"connected": self.connected, "simulated": self.simulated, "model": self.model,
                "port": self.port, "busy": self.busy, "settings": self.settings,
                "last_file": self.last_file, "mirror_method": self.mirror_method, "live": self.live}


def _gain_lut(gain: float) -> bytes:
    """Tabella sRGB → sRGB che moltiplica la luce (valori lineari) per gain, come un'esposizione diversa."""
    def lin(v):
        v /= 255
        return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4

    def enc(x):
        x = min(1.0, max(0.0, x))
        return round(255 * (x * 12.92 if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055))
    return bytes(enc(lin(v) * gain) for v in range(256))


def _sim_png(path: str, n: int, gain: float = 1.0, scene: str | None = None) -> None:
    """Scrive un PNG 1800×1200 di prova: sfondo sfumato e una fascia "a fuoco" con
    scacchiera di 2 px che si sposta a ogni scatto (utile per provare zoom al 100%).
    gain = luce rispetto all'esposizione di riferimento (1/60, ISO 100, f/8).
    scene: "dark" (tappo: quasi nero, qualche pixel caldo) o "flat" (campo uniforme con vignettatura, 600×400)."""
    w, h = (600, 400) if scene in ("dark", "flat") else (1800, 1200)
    lut = _gain_lut(gain)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    rows = []
    if scene == "dark":
        for y in range(h):
            row = bytearray(b"\x02\x02\x03" * w)
            if y % 97 == 13:
                row[(y * 7 % w) * 3:(y * 7 % w) * 3 + 3] = b"\xff\xf0\xe0"   # pixel caldo
            rows.append(b"\x00" + bytes(row))
    elif scene == "flat":
        cx, cy, r2 = w / 2, h / 2, (w / 2) ** 2 + (h / 2) ** 2
        for y in range(h):
            row = bytearray()
            for x in range(w):
                v = int(150 * (1 - 0.35 * ((x - cx) ** 2 + (y - cy) ** 2) / r2))
                row += bytes((lut[v], lut[min(255, v + 12)], lut[max(0, v - 10)]))
            rows.append(b"\x00" + bytes(row))
    else:
        band_y = (n * 97) % (h - 160)
        checker = [bytes(b"\x00" + b"".join(bytes((lut[0xf0],) * 3) if ((x // 2) + k) % 2 else bytes((lut[0x20], lut[0x24], lut[0x2a]))
                                            for x in range(w))) for k in (0, 1)]
        for y in range(h):
            if band_y <= y < band_y + 160:
                rows.append(checker[(y // 2) % 2])
            else:
                g = 40 + (y * 120) // h
                rows.append(b"\x00" + bytes((lut[g], lut[g // 2 + 30], lut[160 - g // 2])) * w)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(b"".join(rows), 6)) + chunk(b"IEND", b"")
    Path(path).write_bytes(png)


SIM_FOCUS = 25000   # posizione del focheggiatore simulato in cui il live view simulato è a fuoco
SIM_DOF = 1500      # passi entro cui l'immagine resta quasi nitida


def _sim_live_png(position: int | None, t: float) -> bytes:
    """Fotogramma 600×400 del live view simulato: una scacchiera di 4 px tanto più contrastata
    quanto più il focheggiatore simulato è vicino a SIM_FOCUS, e una barra che scorre nel tempo."""
    w, h = 600, 400
    sharp = 0.0 if position is None else 2.0 ** (-((position - SIM_FOCUS) / SIM_DOF) ** 2)
    hi, lo = int(128 + 112 * sharp), int(128 - 112 * sharp)
    light, dark = bytes((hi, hi, hi)), bytes((lo, lo, lo))
    checker = [b"\x00" + b"".join(light if ((x // 4) + k) % 2 else dark for x in range(w)) for k in (0, 1)]
    bar_x = int(t * 120) % w
    bar = [row[:1 + bar_x * 3] + b"\xff\xb0\x30" * 6 + row[1 + (bar_x + 6) * 3:] for row in checker]
    rows = [(bar if y >= h - 24 else checker)[(y // 4) % 2][:1 + w * 3] for y in range(h)]

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(b"".join(rows), 1)) + chunk(b"IEND", b"")


class SimulatedCamera(GPhotoCamera):
    simulated = True

    @property
    def model(self) -> str:
        return tr("Fotocamera simulata")   # nella lingua corrente, anche dopo un cambio di lingua

    @model.setter
    def model(self, _value: str) -> None:
        pass

    def __init__(self):
        super().__init__(tr("Fotocamera simulata"), "sim")
        self.mirror_method = "sim"
        self._open = False
        self._n = 0
        self.focus_position = lambda: None   # impostata dal server: posizione del focheggiatore
        self.scene: str | None = None         # calibrazione: "dark" (tappo) o "flat" (campo uniforme)
        # prove della fotocamera persa: "session" = sessione morta, torna ricollegandosi (come dopo uno stop
        # del Mac); "unplugged" = sparita finché non la si rimette (batteria scarica, cavo staccato)
        self.lost: str = ""
        self.settings = {
            "shutterspeed": {"key": "shutterspeed", "current": "1/60",
                             "choices": ["bulb", "30", "15", "8", "4", "2", "1", "1/2", "1/4", "1/8", "1/15",
                                         "1/30", "1/60", "1/125", "1/250", "1/500", "1/1000"], "readonly": False},
            "iso": {"key": "iso", "current": "100", "choices": ["100", "200", "400", "800", "1600"], "readonly": False},
            "aperture": {"key": "f-number", "current": "f/8", "choices": ["f/4", "f/5.6", "f/8", "f/11"], "readonly": False},
            "imageformat": {"key": "imagequality", "current": "RAW", "choices": ["RAW", "JPEG Fine", "RAW+JPEG"], "readonly": False},
            "capturetarget": {"key": "capturetarget", "current": "Memory card", "choices": ["Internal RAM", "Memory card"], "readonly": False},
        }

    @property
    def connected(self) -> bool:
        return self._open

    async def connect(self) -> None:
        await asyncio.sleep(0.3)
        if self.lost == "unplugged":
            raise CameraError(tr("Impossibile aprire la fotocamera ({err}). Chiudi Foto, Anteprima, Acquisizione Immagine "
                                 "e i software del produttore; per Sony imposta USB 'PC Remote'.",
                                 err="[-52] Could not find the requested device on the USB port"))
        self.lost = ""
        self._open = True

    async def disconnect(self) -> None:
        self._open = False
        self.live = False

    def _gain(self, bulb_s: float = 0) -> float:
        """Luce raccolta rispetto a 1/60 s, ISO 100, f/8 (per provare l'esposizione automatica)."""
        from .calibration import shutter_seconds
        cur = lambda k: (self.settings.get(k) or {}).get("current") or ""
        t = bulb_s or shutter_seconds(cur("shutterspeed")) or 1 / 60
        try:
            iso = float(cur("iso"))
        except ValueError:
            iso = 100
        try:
            n = float(cur("aperture").replace("f/", ""))
        except ValueError:
            n = 8
        return t * 60 * iso / 100 * (8 / n) ** 2

    async def preview(self) -> bytes:
        self._require()
        await asyncio.sleep(0.05)
        self.live = True
        return await asyncio.to_thread(_sim_live_png, self.focus_position(), time.monotonic())

    async def end_preview(self) -> None:
        self.live = False

    async def read_settings(self) -> dict:
        return self.settings

    async def set_setting(self, logical: str, value: str) -> dict:
        if logical not in self.settings or value not in self.settings[logical]["choices"]:
            raise CameraError(tr("Valore non valido: {value}", value=value))
        self.settings[logical]["current"] = value
        return self.settings

    async def capture(self, mode: str = "download", dest_base: Path | None = None,
                      bulb_s: float = 0, timeout_s: float = 60, mirror_s: float = 0) -> list[str]:
        self._require()
        self.busy = True
        try:
            await asyncio.sleep(0.5 + bulb_s + mirror_s)
            if self.lost:
                raise CameraError("[-52] Could not find the requested device on the USB port")
            self._n += 1
            if mode == "download" and dest_base:
                target = f"{dest_base}.png"
                await asyncio.to_thread(_sim_png, target, self._n, self._gain(bulb_s), self.scene)
                self.last_file = target
                return [target]
            return []
        finally:
            self.busy = False
