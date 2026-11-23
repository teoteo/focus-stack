"""Server locale: API REST + WebSocket di stato + interfaccia web (PWA) per Safari."""
from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import settings as store
from . import flasher
from . import i18n
from .i18n import tr
from .optics import manifest_optics
from . import calibration, desktop, rawstat, remote
from .autofocus import AFParams, AutofocusRunner, computed_defaults, expected_width
from .camera import GPHOTO_AVAILABLE, CameraError, GPhotoCamera, SimulatedCamera
from .focuser import FocuserError, LimitError, MyFocuserPro2, SimulatedFocuser, list_serial_ports
from .sequence import SequenceParams, SequenceRunner
from .updater import AppUpdater, app_version, bundled_firmware

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
CACHE_DIR = Path.home() / "Library" / "Caches" / "MyFocuserStack"
BROWSER_FORMATS = (".jpg", ".jpeg", ".png", ".webp", ".gif")
PREVIEW_PX = 1200
CODE_DIRS = (Path(__file__).resolve().parent, WEB_DIR)


def code_signature() -> float:
    """Data di modifica più recente del codice: serve a capire se il server va riavviato."""
    return max(p.stat().st_mtime for d in CODE_DIRS for p in d.iterdir()
               if p.suffix in (".py", ".js", ".html", ".css"))


BOOT_SIGNATURE = code_signature()
BOOT_ID = f"{time.time():.6f}"


class App:
    def __init__(self):
        self.cfg = store.load()
        i18n.set_language(i18n.resolve(self.cfg.get("language")))
        self.focuser: MyFocuserPro2 | None = None
        self.camera: GPhotoCamera | None = None
        self.log_lines: deque[str] = deque(maxlen=500)
        self.temp_history: deque[tuple[float, float]] = deque(maxlen=720)  # 2 h a 10 s
        self.shots: list[dict] = []          # galleria della sessione (prova + sequenze)
        self.next_shot_id = 0                # gli id non si riusano dopo "Svuota" (l'elenco riparte vuoto)
        self.shots_rev = 0                   # cambia a ogni scatto aggiunto e a ogni "Svuota"
        self.shot_group = 0                  # gruppo corrente della striscia del visualizzatore (vedi new_shot_group)
        self.shot_group_family = ""          # sequence | calibration | test
        self.alarm: str = ""                  # avviso fine corsa / movimento non comandato
        self.alarm_kind: str = ""             # "limits" = posizione fuori dai fine corsa (il testo è tradotto)
        self.code_stale = False               # il codice su disco è più recente del server in esecuzione
        self.updater = AppUpdater(self.log)
        # aggiornamento del firmware in corso: fase e avanzamento per la pagina
        self.fw = {"busy": False, "phase": "", "progress": 0.0, "error": ""}
        # movimento continuo (pulsante della pagina tenuto premuto): verso (-1/+1, 0 = nessuno) e
        # scadenza: la pagina la rinnova di continuo, se smette il motore viene fermato
        self.hold_dir = 0
        self.hold_deadline = 0.0
        # dopo uno STOP le conferme del pulsante vengono rifiutate finché non lo si preme di nuovo
        self.hold_blocked = False
        self.hold_lock = asyncio.Lock()   # un solo tratto alla volta anche se le conferme si accavallano
        # una connessione alla volta: due richieste insieme (due finestre, due clic) aprivano due volte la
        # stessa porta seriale e le risposte si mescolavano (letta "posizione 1")
        self.focuser_lock = asyncio.Lock()
        self.camera_lock = asyncio.Lock()
        # live view: pagine collegate allo stream e ultimo errore (es. fotocamera senza live view)
        self.live_clients = 0
        self.live_stop_rev = 0               # cresce a ogni «Ferma live»: tutte le finestre chiudono la loro live
        # scatto di prova con il live view acceso: le finestre lo chiudono per mostrare lo scatto e lo riaprono
        # al primo movimento del focheggiatore (posizione diversa da pos)
        self.live_park = {"rev": 0, "pos": None}
        self.live_error = ""
        self.runner = SequenceRunner(lambda: self.focuser if self.focuser and self.focuser.connected else None,
                                     lambda: self.camera if self.camera and self.camera.connected else None,
                                     self.log, self.add_sequence_shot)
        # frame di calibrazione ed esposizione automatica (libreria in <output_root>/_calibrazione)
        self.calib = calibration.CalibrationRunner(
            lambda: self.camera if self.camera and self.camera.connected else None,
            lambda: self.focuser if self.focuser and self.focuser.connected else None,
            self.log, self.add_calibration_shot, Path(store.CONFIG_DIR) / "test-shots")
        # pagina di sola lettura sulla rete locale (avanzamento da smartphone)
        self.remote = remote.RemoteServer(self.remote_status, self.remote_preview, CACHE_DIR)
        # autofocus su un punto (visualizzatore): scatti o fotogrammi del live view, vedi autofocus.py
        self.af = AutofocusRunner(lambda: self.focuser if self.focuser and self.focuser.connected else None,
                                  self.af_grab, self.log, self.af_learn)

    def log(self, msg: str) -> None:
        self.log_lines.append(f"{time.strftime('%H:%M:%S')}  {msg}")

    # ---------- calibrazione / limiti ----------
    def um_per_step(self) -> float:
        mech = self.cfg["mechanics"]
        if mech.get("mode") == "computed":
            micro = (self.focuser.motor.get("step_mode") if self.focuser else None) or 1
            denom = mech["motor_steps_per_rev"] * micro * mech["gear_ratio"]
            return mech["um_per_knob_rev"] / denom if denom else 0.0
        return float(self.cfg.get("um_per_step") or 0)

    def apply_limits(self) -> None:
        if self.focuser:
            self.focuser.limit_min = int(self.cfg.get("limit_min") or 0)
            lm = self.cfg.get("limit_max")
            self.focuser.limit_max = int(lm) if lm is not None else None

    # ---------- galleria ----------
    @staticmethod
    def _shot_family(kind: str) -> str:
        return {"sequence": "sequence", "calibration": "calibration"}.get(kind, "test")

    def new_shot_group(self, family: str) -> None:
        """Nuovo gruppo nella striscia del visualizzatore (avvio di una sequenza o di una calibrazione)."""
        self.shot_group += 1
        self.shot_group_family = family
        self.shots_rev += 1

    def add_shot(self, files: list[str], kind: str, position: int | None, temperature: float | None,
                 index: int | None = None, repeat: int | None = None) -> None:
        if not files:
            return
        family = self._shot_family(kind)
        if family != self.shot_group_family:   # es. uno scatto di prova dopo una pila: la striscia ricomincia
            self.new_shot_group(family)
        # file per il browser: preferisce il JPEG se la fotocamera salva RAW+JPEG
        display = next((f for f in files if f.lower().endswith(BROWSER_FORMATS)), files[0])
        # chiave unica per scatto: dopo un riavvio gli id ripartono da 0, la chiave no
        # (evita che il browser mostri dalla cache un'immagine di una sessione precedente)
        try:
            mtime = Path(display).stat().st_mtime_ns
        except OSError:
            mtime = 0
        key = hashlib.sha1(f"{BOOT_ID}:{display}:{mtime}".encode()).hexdigest()[:16]
        self.shots.append({"id": self.next_shot_id, "key": key, "kind": kind, "file": display, "files": files,
                           "name": Path(display).name, "position": position, "temperature": temperature,
                           "index": index, "repeat": repeat, "time": time.strftime("%H:%M:%S"),
                           "group": self.shot_group})
        self.next_shot_id += 1
        self.shots_rev += 1
        asyncio.get_running_loop().create_task(warm_cache(display))

    def get_shot(self, shot_id: int) -> dict | None:
        """Scatto per id: gli id sono consecutivi dal primo dell'elenco (dopo "Svuota" non ripartono da 0)."""
        if not self.shots:
            return None
        i = shot_id - self.shots[0]["id"]
        return self.shots[i] if 0 <= i < len(self.shots) else None

    def clear_shots(self) -> int:
        """Toglie tutti gli scatti dal visualizzatore; i file restano dove sono."""
        n = len(self.shots)
        self.shots = []
        self.shots_rev += 1
        return n

    def add_sequence_shot(self, record: dict) -> None:
        self.add_shot(record["files"], "sequence", record["position"], record["temperature"], record["index"],
                      record.get("repeat") if record.get("repeats", 1) > 1 else None)

    def add_calibration_shot(self, files: list[str], kind: str) -> None:
        f = self.focuser if self.focuser and self.focuser.connected else None
        self.add_shot(files, kind, f.position if f else None, f.temperature if f else None)

    def busy(self) -> bool:
        """Sequenza, calibrazione o autofocus in corso: la fotocamera è occupata."""
        return self.runner.busy or self.calib.busy or self.af.busy

    def live_paused(self) -> bool:
        """Live view in pausa: durante la calibrazione, durante l'autofocus con gli scatti veri e durante la
        sequenza, tranne mentre la slitta raggiunge il primo piano (si può guardare il ritorno all'inizio)."""
        return (self.calib.busy or (self.af.busy and self.af.status.source == "shot")
                or (self.runner.busy and not self.runner.status.live_ok))

    # ---------- autofocus ----------
    def af_profile(self) -> str:
        return self.cfg["sequence"].get("optics_profile") or ""

    def af_view(self) -> dict:
        """Impostazioni dell'autofocus con i valori calcolati (quelli usati quando un campo è vuoto)."""
        a = self.cfg["autofocus"]
        f = self.focuser if self.focuser and self.focuser.connected else None
        lo, hi = f.bounds() if f else (int(self.cfg.get("limit_min") or 0), self.cfg.get("limit_max"))
        travel = hi - lo if hi is not None else None
        width, source = expected_width(self.cfg, self.um_per_step(), self.af_profile(), travel)
        calc = computed_defaults(width, travel, int(self.cfg["sequence"].get("backlash") or 0))
        calc["settle_ms"] = int(self.cfg["sequence"].get("settle_ms") or 0)
        used = {k: (a.get(k) if a.get(k) is not None else v) for k, v in calc.items()}
        return {"width": width, "width_source": source, "um_per_step": self.um_per_step(), "computed": calc,
                "used": used, "profile": self.af_profile()}

    def af_learn(self, profile: str, width: float) -> None:
        """Larghezza del picco misurata da un autofocus riuscito: media con quella già salvata per il profilo."""
        widths = self.cfg["autofocus"].setdefault("widths", {})
        old = widths.get(profile or "")
        widths[profile or ""] = round((old + width) / 2 if old else width, 1)
        store.save(self.cfg)
        self.log(tr("Autofocus: larghezza del picco {w} passi, salvata per i prossimi autofocus", w=round(width)))

    async def af_grab(self, source: str, position: int) -> str:
        """Immagine da misurare a questa posizione: uno scatto vero (nel visualizzatore come prova) oppure un
        fotogramma del live view letto dopo l'attesa anti-vibrazione."""
        cam = self.camera if self.camera and self.camera.connected else None
        if cam is None:
            raise RuntimeError(tr("Fotocamera non connessa"))
        if source == "live":
            ready = time.monotonic()
            seq = 0
            for _ in range(60):
                frame = await next_live_frame(cam, seq)
                seq = frame["seq"]
                if frame["t"] >= ready:   # fotogramma cominciato a leggere dopo che la slitta si è fermata
                    break
            data = frame["data"]
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            out = CACHE_DIR / ("af-live.png" if data[:4] == b"\x89PNG" else "af-live.jpg")
            out.write_bytes(data)
            return str(out)
        test_dir = Path(store.CONFIG_DIR) / "test-shots"
        test_dir.mkdir(parents=True, exist_ok=True)
        for old in sorted(test_dir.glob("af_*"), key=lambda q: q.stat().st_mtime)[:-80]:
            old.unlink(missing_ok=True)
        seq = self.cfg["sequence"]
        base = test_dir / f"af_{time.strftime('%H%M%S')}_{int(time.time() * 1000) % 1000:03d}"
        files: list[str] = []
        for attempt in range(2):
            try:
                files = await cam.capture(mode="download", dest_base=base, bulb_s=seq.get("bulb_s") or 0,
                                          mirror_s=(seq.get("mirror_delay_ms") or 0) / 1000)
                break
            except Exception as exc:  # noqa: BLE001
                if attempt:
                    raise RuntimeError(tr("La fotocamera non ha scattato ({exc})", exc=exc)) from exc
                self.log(tr("Scatto non riuscito ({exc}): nuovo tentativo fra {s} s ({a} di {n})", exc=exc, s=3, a=1, n=1))
                await asyncio.sleep(3)
        if not files:
            raise RuntimeError(tr("La fotocamera non ha restituito il file: imposta la destinazione sul computer o RAM"))
        f = self.focuser
        self.add_shot(files, "autofocus", position, f.temperature if f and f.connected else None)
        await asyncio.sleep(max(0.3, (seq.get("post_shot_ms") or 0) / 1000))
        # il JPEG della fotocamera se c'è (piena risoluzione), altrimenti il RAW (con la sua anteprima)
        return next((x for x in files if x.lower().endswith((".jpg", ".jpeg"))), rawstat.pick_file(files) or files[0])

    def manifest_context(self, profile: str | None = None) -> dict:
        """Dati per il manifesto sequence.json (vedi sequence.build_manifest)."""
        f, cam = self.focuser, self.camera
        ctx: dict = {
            "software": f"Focus Stack {app_version()}",
            "um_per_step": round(self.um_per_step(), 6),
            "um_per_step_source": "computed_from_mechanics" if self.cfg["mechanics"].get("mode") == "computed"
            else "entered",
            # z positivo verso l'obiettivo: con "decreasing" i passi crescenti allontanano l'obiettivo
            # dal campione, quindi il piano di fuoco sale
            "z_sign": 1 if self.cfg.get("toward_specimen", "decreasing") == "decreasing" else -1,
        }
        if f:
            ctx["rail_model"] = "Simulator" if f.simulated else \
                {"ardufocus": "Ardufocus", "myfp2": "myFocuserPro2"}.get(f.board, f.board)
            fw = " ".join(str(x) for x in (f.firmware, f"build {f.fs_build}" if f.fs_build else None) if x)
            ctx["firmware"] = fw or None
            ctx["microstep"] = (f.motor or {}).get("step_mode")
        if cam:
            info = {"model": cam.model or None}
            for key in ("iso", "shutterspeed", "aperture", "imageformat"):
                cur = (cam.settings.get(key) or {}).get("current")
                if cur:
                    info[key] = cur
            ctx["camera"] = {k: v for k, v in info.items() if v is not None}
        # Profilo di ottica/filtro scelto nella sequenza; nessun profilo = nessun filtro.
        name = (self.cfg["sequence"].get("optics_profile") or "") if profile is None else profile
        o = (self.cfg.get("optics_profiles") or {}).get(name) if name else None
        if o is None:
            ctx["filter"] = None
            return ctx
        ctx["optics_profile"] = name
        optics = manifest_optics(o)
        if optics:
            ctx["optics"] = optics
        mode = o.get("filter_mode", "unknown")
        if mode == "none":
            ctx["filter"] = None
        elif mode == "filter":
            fl = o.get("filter") or {}
            data = {"name": fl.get("name") or None, "type": fl.get("type") or None}
            if fl.get("type") == "bandpass":
                data.update(center_nm=fl.get("center_nm"), bandwidth_nm=fl.get("bandwidth_nm"))
            elif fl.get("type") in ("longpass", "shortpass"):
                data["edge_nm"] = fl.get("edge_nm")
            ctx["filter"] = {k: v for k, v in data.items() if v not in (None, "")}
        il = o.get("illumination") or {}
        illum = {k: v for k, v in (("type", il.get("type")), ("level_percent", il.get("level_percent")),
                                   ("color_temp_k", il.get("color_temp_k")))
                 if v not in (None, "")}
        if illum:
            ctx["illumination"] = illum
        if o.get("notes"):
            ctx["notes"] = o["notes"]
        return ctx

    def state(self) -> dict:
        st = self.runner.status
        last = self.shots[-1] if self.shots else None
        return {
            "focuser": self.focuser.describe() if self.focuser else {"connected": False},
            "camera": {**self.camera.describe(), "live_error": self.live_error} if self.camera
            else {"connected": False},
            "gphoto": GPHOTO_AVAILABLE,
            "sequence": {**st.__dict__, "files": st.files[-3:], "file_count": len(st.files)},
            "calibration": {**self.calib.status.__dict__, "busy": self.calib.busy,
                            "tool": rawstat.tool_path() is not None},
            "autofocus": {**self.af.status.__dict__, "busy": self.af.busy, **self.af_view()},
            "settings": self.cfg,
            "um_per_step": self.um_per_step(),
            "alarm": self.alarm,
            "temp_history": [t for _, t in list(self.temp_history)[-180:]],
            "last_shot": last,
            "shot_count": len(self.shots),
            "shots_rev": self.shots_rev,
            "live_stop_rev": self.live_stop_rev,
            "live_park": self.live_park,
            "shot_group": self.shot_group,
            "log": list(self.log_lines)[-200:],
            "boot_signature": BOOT_SIGNATURE,
            "language": i18n.current(),
            "code_stale": self.code_stale,
            "app": self.updater.describe(),
            "firmware_update": self.firmware_update_state(),
            "remote": self.remote.describe(),
        }

    def remote_status(self) -> dict:
        """Dati per la pagina di sola lettura: avanzamento e ultimo scatto, niente impostazioni."""
        st = self.runner.status
        last = self.shots[-1] if self.shots else None
        label = None
        if last:   # posizione nella sequenza (da 1), con lo scatto nella posizione se sono più di uno
            label = str(last["index"]) if last.get("index") is not None else last.get("name")
            if last.get("index") is not None and last.get("repeat"):
                label += f" · {last['repeat']}"
        return {"state": st.state, "index": st.index, "total": st.total, "eta_s": st.eta_s,
                "message": st.message,
                "name": self.cfg["sequence"].get("session_name") or (Path(st.folder).name if st.folder else ""),
                "last": {"key": last["key"], "time": last["time"], "label": label} if last else None}

    async def remote_preview(self, size: str = "preview") -> Path | None:
        """Ultimo scatto per la pagina remota: "preview" (quella già pronta per l'interfaccia) o "full" (per lo zoom)."""
        if not self.shots:
            return None
        try:
            return await render_image(self.shots[-1]["file"], size)
        except HTTPException:
            return None

    async def remote_apply(self) -> None:
        """Avvia o ferma la pagina remota secondo le impostazioni."""
        r = self.cfg["remote"]
        if r.get("enabled"):
            if not r.get("token"):
                r["token"] = remote.new_token()
                store.save(self.cfg)
            await self.remote.start(int(r.get("port") or remote.DEFAULT_PORT), r["token"])
            self.log(tr("Avanzamento da smartphone attivo: {url}", url=self.remote.url() or f"porta {self.remote.port}"))
        else:
            await self.remote.stop()

    def firmware_update_state(self) -> dict:
        f = self.focuser
        real = bool(f and f.connected and not f.simulated)
        fw = bundled_firmware(f.board if real else "myfp2")
        installed = f.fs_build if real else None
        return {**self.fw, "bundled": fw["build"] if fw else None,
                "installed": installed,
                # firmware originale (nessuna build) o build più vecchia di quella inclusa nell'app
                "available": bool(fw and real and (installed is None or installed < fw["build"]))}


app_state = App()


# ---------------- conversione immagini per la visualizzazione ----------------
_render_locks: dict[str, asyncio.Lock] = {}


async def render_image(src: str, size: str) -> Path:
    """Restituisce un file visualizzabile dal browser: l'originale se è già JPEG/PNG,
    altrimenti una conversione (anche da RAW) con `sips` di macOS, in cache."""
    path = Path(src)
    if not path.exists():
        raise HTTPException(404, tr("File non trovato"))
    if path.suffix.lower() in BROWSER_FORMATS:
        # sips -Z ingrandirebbe le immagini piccole: l'anteprima serve solo se l'originale è grande
        if size == "full" or max(await image_size(path)) <= PREVIEW_PX:
            return path
    key = hashlib.sha1(f"{path}:{path.stat().st_mtime_ns}:{size}".encode()).hexdigest()[:20]
    out = CACHE_DIR / f"{key}.jpg"
    lock = _render_locks.setdefault(key, asyncio.Lock())
    async with lock:
        if not out.exists():
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            args = ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92"]
            if size == "preview" and max(await image_size(path)) > PREVIEW_PX:
                args += ["-Z", str(PREVIEW_PX)]
            tmp = out.with_suffix(".part.jpg")
            proc = await asyncio.create_subprocess_exec(*args, str(path), "--out", str(tmp),
                                                        stdout=asyncio.subprocess.DEVNULL,
                                                        stderr=asyncio.subprocess.DEVNULL)
            await proc.wait()
            if proc.returncode != 0 or not tmp.exists():
                raise HTTPException(415, tr("Impossibile convertire {name}", name=path.name))
            tmp.replace(out)
    _render_locks.pop(key, None)
    return out


async def image_size(path: Path) -> tuple[int, int]:
    proc = await asyncio.create_subprocess_exec("sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path),
                                                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    out, _ = await proc.communicate()
    vals = [int(line.split(":")[1]) for line in out.decode().splitlines() if "pixel" in line]
    return (vals[0], vals[1]) if len(vals) == 2 else (0, 0)


async def warm_cache(src: str) -> None:
    """Prepara anteprima e piena risoluzione appena arriva un nuovo scatto."""
    for size in ("preview", "full"):
        try:
            await render_image(src, size)
        except HTTPException:
            return


# ---------------- ciclo di lettura + watchdog fine corsa ----------------
async def poll_loop():
    tick = 0
    last_pos: int | None = None
    while True:
        f = app_state.focuser
        # Durante la sequenza è il runner stesso a interrogare il motore.
        if f and f.connected and not app_state.runner.busy:
            try:
                await f.poll(with_temp=(tick % 20 == 0))
                watchdog(f, last_pos)
                hold_watchdog(f)
                last_pos = f.position
            except Exception as exc:  # noqa: BLE001
                if f.connected and f is app_state.focuser:   # non durante una disconnessione
                    app_state.log(tr("Errore lettura focheggiatore: {exc}", exc=exc))
                    await asyncio.sleep(2)
        else:
            # scollegato o sequenza in corso: la posizione letta prima non vale più come riferimento (a fine
            # sequenza la slitta è altrove e il confronto la scambiava per un movimento dai pulsanti)
            last_pos = None
        if tick % 10 == 0:
            try:
                app_state.code_stale = code_signature() > BOOT_SIGNATURE + 1
            except OSError:
                pass
        if f and f.connected and f.temperature is not None and tick % 20 == 0:
            app_state.temp_history.append((time.time(), f.temperature))
        tick += 1
        await asyncio.sleep(0.2 if f and f.moving else 0.5)


def watchdog(f: MyFocuserPro2, last_pos: int | None) -> None:
    lo, hi = f.bounds()
    outside = f.position < lo or (hi is not None and f.position > hi)
    if outside:
        if f.moving:
            asyncio.get_running_loop().create_task(f.halt())
            msg = tr("Posizione {pos} fuori dai fine corsa ({lo} – {hi}): motore fermato", pos=f.position, lo=lo, hi=hi)
        else:
            msg = tr("Posizione {pos} fuori dai fine corsa ({lo} – {hi})", pos=f.position, lo=lo, hi=hi)
        if app_state.alarm != msg:
            app_state.alarm, app_state.alarm_kind = msg, "limits"
            app_state.log("⚠ " + msg)
    elif app_state.alarm_kind == "limits":
        app_state.alarm, app_state.alarm_kind = "", ""
    # Movimento non comandato dall'app: pulsanti fisici del focheggiatore
    if last_pos is not None and f.position != last_pos and not f.commanded:
        if "manual" not in _once:
            _once.add("manual")
            app_state.log(tr("Movimento dai pulsanti del focheggiatore (da {pos})", pos=last_pos))
    elif last_pos is not None and f.position == last_pos:
        _once.discard("manual")


_once: set[str] = set()

HOLD_TIMEOUT = 1.0  # s senza conferma dalla pagina prima di fermare il movimento continuo
HOLD_CHUNK_DEFAULT = 500   # passi per tratto del movimento continuo (vedi focuser_hold)
HOLD_CHUNK_RANGE = (10, 100_000)


def hold_watchdog(f: MyFocuserPro2) -> None:
    if not app_state.hold_dir:
        return
    # fra un tratto e l'altro il motore è fermo: il movimento continuo resta attivo finché arrivano conferme
    if time.monotonic() > app_state.hold_deadline:
        app_state.hold_dir = 0
        if f.moving:
            asyncio.get_running_loop().create_task(f.halt())
            app_state.log(tr("Movimento continuo fermato: la pagina non risponde"))


async def update_check_loop():
    """Controlla le nuove versioni su GitHub all'avvio e poi ogni CHECK_INTERVAL."""
    while True:
        if app_state.updater.due():
            await asyncio.to_thread(app_state.updater.check_blocking)
            u = app_state.updater.describe()
            if u["available"]:
                app_state.log(tr("È disponibile Focus Stack {latest} (installata {version})",
                                 latest=u["latest"], version=u["version"]))
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(poll_loop())
    update_task = asyncio.create_task(update_check_loop())
    app_state.log(tr("Server avviato (Focus Stack {version})", version=app_state.updater.describe()["version"]))
    async def remote_on_boot() -> None:
        # in background: al riavvio la porta può restare occupata qualche secondo dal server vecchio
        try:
            await app_state.remote_apply()
        except RuntimeError as exc:
            app_state.log(tr("Errore: {exc}", exc=exc))

    remote_task = asyncio.create_task(remote_on_boot()) if app_state.cfg["remote"].get("enabled") else None
    connect_task = asyncio.create_task(connect_on_boot())
    yield
    connect_task.cancel()
    if remote_task:
        remote_task.cancel()
    await app_state.remote.stop()
    task.cancel()
    update_task.cancel()
    if app_state.focuser:
        await app_state.focuser.disconnect()
    if app_state.camera:
        await app_state.camera.disconnect()


async def connect_on_boot() -> None:
    """All'apertura ricollega il focheggiatore e la fotocamera usati l'ultima volta, se sono collegati al Mac.

    Collegarsi non muove il motore: aprire la porta riavvia la scheda, che riprende posizione e impostazioni dalla
    EEPROM (come con «Connetti»). La porta seriale si apre solo se è lo stesso adattatore USB dell'ultima volta
    (hwid): un altro dispositivo con lo stesso nome di porta non riceve niente. La fotocamera si riconosce dal
    nome del driver; se non c'è o è spenta non succede nulla. Una richiesta della pagina nel frattempo (Connetti)
    passa dagli stessi lock e la seconda diventa un no-op.
    """
    cfg = app_state.cfg
    await asyncio.sleep(1.5)   # dopo un riavvio il processo vecchio libera porte seriali e USB
    port, hwid = cfg.get("focuser_port"), cfg.get("focuser_hwid")
    if port and not (app_state.focuser and app_state.focuser.connected):
        found = next((p for p in list_serial_ports() if p["device"] == port), None)
        if found and (not hwid or not found["hwid"] or found["hwid"] == hwid):
            try:
                async with app_state.focuser_lock:
                    await _focuser_connect(FocuserConnect(port=port, baud=cfg.get("focuser_baud", 9600)))
            except Exception as exc:  # noqa: BLE001
                app_state.log(tr("Collegamento automatico del focheggiatore non riuscito: {exc}", exc=exc))
    driver = cfg.get("camera_driver")
    if driver and GPHOTO_AVAILABLE and not (app_state.camera and app_state.camera.connected):
        try:
            cam = next((c for c in await GPhotoCamera.detect() if c["model"] == driver), None)
            if cam:
                async with app_state.camera_lock:
                    await _camera_connect(CameraConnect(model=cam["model"], port=cam["port"]))
        except Exception as exc:  # noqa: BLE001
            app_state.log(tr("Collegamento automatico della fotocamera non riuscito: {exc}", exc=exc))


api = FastAPI(title="Focus Stack", lifespan=lifespan)

ALLOWED_HOSTS = {"localhost", "127.0.0.1", "[::1]"}


@api.middleware("http")
async def local_only(request, call_next):
    """Il server comanda hardware reale: accetta solo richieste dalla propria interfaccia.
    - Host deve essere localhost (blocca il DNS rebinding);
    - i POST devono avere l'intestazione X-FocusStack: un sito esterno non può aggiungerla
      senza un preflight CORS, che questo server non autorizza."""
    host = (request.headers.get("host") or "").rsplit(":", 1)[0]
    if host not in ALLOWED_HOSTS:
        return Response(tr("Host non consentito"), status_code=403)
    if request.method == "POST" and request.headers.get("x-focusstack") != "1":
        return Response(tr("Richiesta non consentita"), status_code=403)
    response = await call_next(request)
    # pagine e script dell'interfaccia: senza questa intestazione Safari può riusare la copia vecchia
    # dopo un aggiornamento (era successo con il visualizzatore). Con no-cache ricontrolla sempre (ETag).
    if not request.url.path.startswith("/api") and "cache-control" not in response.headers:
        response.headers["Cache-Control"] = "no-cache"
    return response


@api.post("/api/shutdown")
async def shutdown():
    """Spegne il server (pulsante ⏻ dell'interfaccia, oppure run.py per sostituire un'istanza
    avviata con codice vecchio). Prima ferma sequenza e motore; le connessioni a focheggiatore
    e fotocamera vengono chiuse dal lifespan."""
    import os
    import signal
    await app_state.calib.stop()
    if app_state.runner.busy:
        await app_state.runner.stop()
    elif app_state.focuser and app_state.focuser.connected:
        try:
            await app_state.focuser.halt()
        except Exception:  # noqa: BLE001
            pass
    app_state.log(tr("Spegnimento del server…"))
    # il ritardo lascia il tempo di inviare la risposta alla pagina
    asyncio.get_running_loop().call_later(0.5, os.kill, os.getpid(), signal.SIGINT)
    return {"ok": True, "pid": os.getpid()}   # run.py aspetta che questo processo esca (porte seriali libere)


def guard(fn):
    """Converte gli errori di dominio in risposte HTTP leggibili dalla UI."""
    @functools.wraps(fn)
    async def wrapper(*a, **kw):
        try:
            return await fn(*a, **kw)
        except HTTPException:
            raise
        except (FocuserError, CameraError, RuntimeError, ValueError, OSError) as exc:
            app_state.log(tr("Errore: {exc}", exc=exc))
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:  # errori gphoto2 e simili
            app_state.log(tr("Errore: {exc}", exc=exc))
            raise HTTPException(500, str(exc)) from exc
    return wrapper


def need_focuser() -> MyFocuserPro2:
    if not app_state.focuser or not app_state.focuser.connected:
        raise HTTPException(400, tr("Focheggiatore non connesso"))
    return app_state.focuser


def need_camera() -> GPhotoCamera:
    if not app_state.camera or not app_state.camera.connected:
        raise HTTPException(400, tr("Fotocamera non connessa"))
    return app_state.camera


def not_running():
    if app_state.runner.busy:
        raise HTTPException(409, tr("Sequenza in corso"))
    if app_state.calib.busy:
        raise HTTPException(409, tr("Calibrazione in corso"))
    if app_state.af.busy:
        raise HTTPException(409, tr("Autofocus in corso"))


# ---------------- stato ----------------
@api.get("/api/state")
async def get_state():
    return app_state.state()


@api.websocket("/ws")
async def ws_state(ws: WebSocket):
    """Stato ogni 250 ms verso la pagina; dalla pagina arrivano i comandi del tieni premuto.

    Il tieni premuto passa da qui e non da fetch: Safari tiene al massimo 6 connessioni verso l'app e con il
    live view aperto in due finestre le richieste potevano restare in coda più di un secondo (motore che partiva
    in ritardo, fermato dalla sorveglianza o rilascio in ritardo). La WebSocket è già aperta e non fa coda.
    """
    await ws.accept()
    # comandi solo dalle pagine dell'app: un sito qualsiasi aperto nel browser può aprire una WebSocket verso
    # localhost, ma con la sua Origin (per HTTP la stessa protezione la dà l'intestazione X-FocusStack)
    trusted = ws.headers.get("origin") == f"http://{ws.headers.get('host', '')}"
    send_lock = asyncio.Lock()
    tasks: set[asyncio.Task] = set()

    async def send(obj) -> None:
        async with send_lock:
            await ws.send_text(json.dumps(obj))

    async def command(msg: dict) -> None:
        reply = {"reply": msg.get("id")}
        try:
            if not trusted:
                raise HTTPException(403, "origin")
            if msg.get("type") != "hold":
                raise ValueError(tr("Valore non valido"))
            reply.update(await focuser_hold(Hold(direction=int(msg.get("direction", 0)), start=bool(msg.get("start")))))
        except HTTPException as exc:
            reply["error"] = str(exc.detail)
        except Exception as exc:  # noqa: BLE001  (messaggio non valido)
            reply["error"] = str(exc)
        try:
            await send(reply)
        except (WebSocketDisconnect, RuntimeError):
            pass

    async def receive() -> None:
        while True:
            try:
                msg = json.loads(await ws.receive_text())
            except ValueError:
                continue
            # un task per comando: una conferma che aspetta il motore non deve trattenere le successive
            task = asyncio.create_task(command(msg if isinstance(msg, dict) else {}))
            tasks.add(task)
            task.add_done_callback(tasks.discard)

    rx = asyncio.create_task(receive())
    try:
        while not rx.done():
            await send(app_state.state())
            await asyncio.sleep(0.25)
    except (WebSocketDisconnect, RuntimeError):
        pass
    finally:
        rx.cancel()


# ---------------- focheggiatore ----------------
class FocuserConnect(BaseModel):
    port: str = ""
    baud: int = 9600
    simulate: bool = False


class Position(BaseModel):
    position: int


class Delta(BaseModel):
    delta: int


class MotorSetting(BaseModel):
    name: str
    value: int | bool


@api.get("/api/ports")
async def ports():
    return list_serial_ports()


@api.post("/api/focuser/connect")
@guard
async def focuser_connect(body: FocuserConnect):
    not_running()
    async with app_state.focuser_lock:
        return await _focuser_connect(body)


async def _focuser_connect(body: FocuserConnect):
    old = app_state.focuser
    if old and old.connected and not body.simulate and not old.simulated and old.port == body.port:
        return old.describe()   # già collegato a questa porta (richiesta doppia): niente seconda apertura
    if app_state.focuser:
        await app_state.focuser.disconnect()
    if body.simulate:
        f = SimulatedFocuser()
    else:
        if not body.port:
            raise ValueError(tr("Seleziona una porta seriale"))
        f = MyFocuserPro2(body.port, body.baud)
    app_state.log(tr("Connessione focheggiatore {port}…", port=tr("simulatore") if f.simulated else f.port))
    await f.connect()
    app_state.focuser = f
    app_state.apply_limits()
    if not body.simulate:
        app_state.cfg["focuser_port"] = body.port
        app_state.cfg["focuser_baud"] = body.baud
        app_state.cfg["focuser_hwid"] = next((p["hwid"] for p in list_serial_ports() if p["device"] == body.port), "")
        store.save(app_state.cfg)
    probe = f"{f.temperature:.1f} °C" if f.temperature is not None else tr("sonda assente")
    app_state.log(tr("Focheggiatore connesso (firmware {firmware}, max {max} passi, {probe})",
                     firmware=f.firmware, max=f.max_step, probe=probe))
    lo, hi = f.bounds()
    if f.position < lo or (hi is not None and f.position > hi):
        app_state.log(tr("⚠ La posizione attuale {pos} è fuori dai fine corsa impostati", pos=f.position))
    return f.describe()


@api.post("/api/focuser/disconnect")
@guard
async def focuser_disconnect():
    not_running()
    if app_state.focuser:
        await app_state.focuser.disconnect()
        app_state.focuser = None
        app_state.alarm, app_state.alarm_kind = "", ""
        app_state.log(tr("Focheggiatore disconnesso"))
    return {"ok": True}


async def run_firmware_update(port: str, baud: int, hex_path: Path, build: int, manual_reset: bool) -> None:
    fw = app_state.fw

    def progress(phase: str, frac: float) -> None:
        fw["phase"], fw["progress"] = phase, frac

    try:
        await asyncio.to_thread(flasher.flash, port, hex_path, progress, manual_reset)
        app_state.log(tr("Firmware aggiornato (build {build})", build=build))
    except Exception as exc:  # noqa: BLE001
        fw["error"] = str(exc)
        app_state.log(tr("⚠ Aggiornamento firmware non riuscito: {exc}", exc=exc))
    # ricollega in ogni caso: se la scrittura è fallita il bootloader resta e il vecchio
    # firmware (o nessuno) risponde; l'errore è comunque mostrato nella pagina
    fw["phase"] = tr("Ricollegamento")
    try:
        f = MyFocuserPro2(port, baud)
        await f.connect()
        app_state.focuser = f
        app_state.apply_limits()
        app_state.log(tr("Focheggiatore ricollegato (firmware {firmware}, build {build})", firmware=f.firmware, build=f.fs_build))
    except Exception as exc:  # noqa: BLE001
        app_state.log(tr("Focheggiatore non ricollegato: {exc}", exc=exc))
    fw["busy"] = False
    fw["phase"] = ""


@api.post("/api/firmware/update")
@guard
async def firmware_update():
    not_running()
    if app_state.fw["busy"]:
        raise ValueError(tr("Aggiornamento del firmware già in corso"))
    f = need_focuser()
    if f.simulated:
        raise ValueError(tr("Il simulatore non ha firmware da aggiornare"))
    fw = bundled_firmware(f.board)
    if not fw:
        raise ValueError(tr("Questa copia dell'app non contiene il firmware per questa scheda"))
    if f.moving:
        raise ValueError(tr("Attendi che il motore sia fermo"))
    port, baud = f.port, f.baud
    app_state.fw.update(busy=True, phase=tr("Preparazione"), progress=0.0, error="")
    app_state.log(tr("Aggiornamento firmware alla build {build} su {port}…", build=fw["build"], port=port))
    await f.disconnect()
    app_state.focuser = None
    # l'Ardufocus ha un condensatore che impedisce il riavvio da USB: serve il tasto reset
    manual = f.board == "ardufocus"
    asyncio.get_running_loop().create_task(run_firmware_update(port, baud, fw["hex"], fw["build"], manual))
    return {"ok": True}


# ---------------- aggiornamenti dell'app ----------------
@api.post("/api/app/check")
@guard
async def app_check():
    await asyncio.to_thread(app_state.updater.check_blocking)
    return app_state.updater.describe()


@api.post("/api/app/update")
@guard
async def app_update():
    not_running()
    if app_state.fw["busy"]:
        raise ValueError(tr("Attendi la fine dell'aggiornamento del firmware"))
    await asyncio.to_thread(app_state.updater.install_blocking)
    return {"ok": True}


@api.post("/api/focuser/move")
@guard
async def focuser_move(body: Position):
    not_running()
    f = need_focuser()
    await f.move_to(body.position)
    return {"ok": True}


@api.post("/api/focuser/jog")
@guard
async def focuser_jog(body: Delta):
    not_running()
    f = need_focuser()
    await f.poll()
    target, clamped = f.jog_target(body.delta)
    await f.move_to(target)
    return {"ok": True, "target": target, "clamped": clamped}


class Hold(BaseModel):
    direction: int  # -1 / +1 = muovi e continua; 0 = fermati
    start: bool = False   # True = pulsante appena premuto, False = conferma "ancora premuto"


def hold_target(f: MyFocuserPro2, direction: int) -> int:
    """Meta del movimento continuo: un tratto (hold_chunk_steps) oltre la posizione attuale, entro i fine corsa."""
    lo, hi = f.bounds()
    chunk = int(app_state.cfg.get("hold_chunk_steps") or HOLD_CHUNK_DEFAULT)
    target = f.position + direction * chunk
    return max(lo, target) if direction < 0 else (min(hi, target) if hi is not None else target)


@api.post("/api/focuser/hold")
@guard
async def focuser_hold(body: Hold):
    """Movimento continuo mentre un pulsante della pagina è tenuto premuto.

    Il motore riceve un TRATTO alla volta (hold_chunk_steps passi, Configurazione › Comandi manuali) e solo
    una conferma fresca della pagina (ogni 250 ms) fa partire il tratto successivo: se la comunicazione si
    interrompe (pagina, rete, server bloccato, cavo del focheggiatore) il motore percorre al massimo il
    tratto in corso. Se la pagina smette di confermare, hold_watchdog lo ferma anche prima.
    Con il firmware build 5 ogni conferma sposta la meta del movimento in corso un tratto più avanti
    (extend_to): niente soste fra un tratto e l'altro, e al massimo un tratto oltre l'ultima conferma.
    Dopo uno STOP o il rilascio le conferme vengono rifiutate finché il pulsante non viene premuto di nuovo
    (start=True): una conferma in ritardo o una pagina che ha perso il rilascio non fanno ripartire il motore.
    """
    f = need_focuser()
    if body.direction == 0:
        # rilascio: una conferma ancora in viaggio non deve far ripartire il motore (serve start=True)
        app_state.hold_blocked = True
        if app_state.hold_dir:
            app_state.hold_dir = 0
            await f.halt()
        return {"ok": True}
    not_running()
    if body.direction not in (-1, 1):
        raise ValueError(tr("Verso non valido"))
    if body.start:
        app_state.hold_blocked = False
    elif app_state.hold_blocked:
        return {"ok": False, "stopped": True}   # fermato con STOP: la pagina smette di confermare
    app_state.hold_deadline = time.monotonic() + HOLD_TIMEOUT
    if app_state.hold_dir == body.direction and f.moving:
        if f.extendable and not app_state.hold_lock.locked():
            # firmware build 5: la meta resta un tratto più avanti dell'ultima conferma, il motore non si ferma
            target = hold_target(f, body.direction)
            if (target - f.position) * body.direction > 0:
                await f.extend_to(target)
        return {"ok": True}   # tratto in corso
    if app_state.hold_lock.locked():
        return {"ok": True}   # il tratto successivo lo sta già preparando un'altra conferma
    async with app_state.hold_lock:
        await f.poll()
        if f.moving:
            if app_state.hold_dir == body.direction:
                return {"ok": True}
            await f.wait_idle(timeout=5)   # il firmware ignora un nuovo target mentre si muove (sta rallentando)
        if app_state.hold_blocked and not body.start:
            return {"ok": False, "stopped": True}
        f.check_direction(body.direction)
        target = hold_target(f, body.direction)
        # mai nel verso opposto a quello chiesto (succedeva con la posizione già oltre un fine corsa)
        if (target - f.position) * body.direction <= 0:
            app_state.hold_dir = 0
            raise LimitError(tr("Fine corsa raggiunto"))
        app_state.hold_dir = body.direction
        app_state.hold_deadline = time.monotonic() + HOLD_TIMEOUT
        # firmware build 4+: il tratto è anche sorvegliato dal firmware (si ferma se il Mac tace per 1,5 s)
        await f.move_to(target, supervised=True)
    return {"ok": True, "target": target}


@api.post("/api/focuser/halt")
@guard
async def focuser_halt():
    app_state.hold_dir = 0
    app_state.hold_blocked = True   # una pagina che conferma ancora il pulsante non deve far ripartire il motore
    await app_state.calib.stop()   # STOP ferma tutto, anche gli scatti di calibrazione
    if app_state.runner.busy:
        await app_state.runner.stop()
    elif app_state.focuser and app_state.focuser.connected:
        await app_state.focuser.halt()
    return {"ok": True}


@api.post("/api/focuser/sync")
@guard
async def focuser_sync(body: Position):
    not_running()
    await need_focuser().sync(body.position)
    app_state.log(tr("Posizione sincronizzata a {pos}: verifica i fine corsa!", pos=body.position))
    return {"ok": True}


@api.post("/api/focuser/maxstep")
@guard
async def focuser_maxstep(body: Position):
    not_running()
    f = need_focuser()
    await f.set_max_step(body.position)
    if f.max_step != body.position:
        app_state.log(tr("⚠ Il firmware ha mantenuto max = {max} (richiesto {requested})", max=f.max_step, requested=body.position))
    else:
        app_state.log(tr("Max passi del firmware impostato a {max}", max=f.max_step))
    return f.describe()


@api.post("/api/focuser/motor")
@guard
async def focuser_motor(body: MotorSetting):
    not_running()
    f = need_focuser()
    motor = await f.set_motor(body.name, body.value)
    app_state.log(tr("Motore: {name} = {value}", name=body.name, value=motor.get(body.name)))
    return motor


@api.post("/api/focuser/motor/reload")
@guard
async def focuser_motor_reload():
    not_running()
    return await need_focuser().read_motor()


@api.post("/api/focuser/sim-button")
@guard
async def focuser_sim_button(body: Delta):
    """Solo simulatore: riproduce la pressione dei pulsanti fisici (per provare il watchdog)."""
    f = need_focuser()
    if not isinstance(f, SimulatedFocuser):
        raise ValueError(tr("Disponibile solo con il simulatore"))
    f.simulate_button(body.delta)
    return {"ok": True}


class SimCameraLost(BaseModel):
    lost: str = ""     # "" = funziona, "session" = sessione morta, "unplugged" = sparita


@api.post("/api/camera/sim-lost")
@guard
async def camera_sim_lost(body: SimCameraLost):
    """Solo simulatore: fa sparire la fotocamera (per provare pausa e ricollegamento della sequenza)."""
    cam = app_state.camera
    if not isinstance(cam, SimulatedCamera):
        raise ValueError(tr("Disponibile solo con il simulatore"))
    if body.lost not in ("", "session", "unplugged"):
        raise ValueError("lost: '', 'session' o 'unplugged'")
    cam.lost = body.lost
    return {"ok": True}


# ---------------- fine corsa / meccanica ----------------
class LimitsBody(BaseModel):
    limit_min: int
    limit_max: int | None = None
    toward_specimen: str | None = None


class MechanicsBody(BaseModel):
    mode: str
    motor_steps_per_rev: int = 200
    gear_ratio: float = 1.0
    um_per_knob_rev: float = 100.0
    um_per_step: float | None = None


@api.post("/api/limits")
@guard
async def set_limits(body: LimitsBody):
    if body.limit_min < 0:
        raise ValueError(tr("Il fine corsa inferiore non può essere negativo"))
    if body.limit_max is not None and body.limit_max <= body.limit_min:
        raise ValueError(tr("Il fine corsa superiore deve essere maggiore di quello inferiore"))
    f = app_state.focuser
    if f and f.max_step and body.limit_max and body.limit_max > f.max_step:
        raise ValueError(tr("Il fine corsa superiore supera il max del firmware ({max}): aumenta prima il max del firmware",
                            max=f.max_step))
    app_state.cfg["limit_min"] = body.limit_min
    app_state.cfg["limit_max"] = body.limit_max
    if body.toward_specimen in ("increasing", "decreasing"):
        app_state.cfg["toward_specimen"] = body.toward_specimen
    store.save(app_state.cfg)
    app_state.apply_limits()
    app_state.log(tr("Fine corsa: {lo} – {hi}", lo=body.limit_min,
                     hi=body.limit_max if body.limit_max is not None else tr("max firmware")))
    return {"ok": True}


@api.post("/api/limits/zero-here")
@guard
async def zero_here():
    """Rende la posizione attuale lo zero: da qui in giù neanche i pulsanti fisici possono scendere."""
    not_running()
    f = need_focuser()
    await f.poll()
    shift = f.position
    await f.sync(0)
    lm = app_state.cfg.get("limit_max")
    app_state.cfg["limit_min"] = 0
    if lm is not None:
        app_state.cfg["limit_max"] = max(1, lm - shift)
    seq = app_state.cfg["sequence"]
    seq["start"], seq["end"] = max(0, seq["start"] - shift), max(0, seq["end"] - shift)
    store.save(app_state.cfg)
    app_state.apply_limits()
    app_state.log(tr("Zero impostato sulla posizione {shift}: limiti e sequenza traslati di −{shift}", shift=shift))
    return {"ok": True}


@api.post("/api/mechanics")
@guard
async def set_mechanics(body: MechanicsBody):
    if body.mode not in ("manual", "computed"):
        raise ValueError(tr("Modalità non valida"))
    if body.motor_steps_per_rev <= 0 or body.gear_ratio <= 0 or body.um_per_knob_rev <= 0:
        raise ValueError(tr("I valori meccanici devono essere positivi"))
    data = body.model_dump()
    um = data.pop("um_per_step")
    app_state.cfg["mechanics"].update(data)
    if um is not None and um > 0:
        app_state.cfg["um_per_step"] = um
    store.save(app_state.cfg)
    app_state.log(tr("Meccanica aggiornata: {um} µm/passo", um=f"{app_state.um_per_step():.4f}"))
    return {"um_per_step": app_state.um_per_step()}


# ---------------- fotocamera ----------------
class CameraConnect(BaseModel):
    model: str = ""
    port: str = ""
    simulate: bool = False


class CameraSetting(BaseModel):
    name: str
    value: str


class TestShot(BaseModel):
    bulb_s: float = 0
    mirror_delay_ms: int = 0


def check_mirror_delay(ms: int) -> None:
    if not 0 <= ms <= 2500:
        raise ValueError(tr("Il ritardo dello specchio deve essere fra 0 e 2,5 secondi"))


@api.post("/api/camera/detect")
@guard
async def camera_detect():
    cams = await GPhotoCamera.detect()
    app_state.log(tr("Fotocamere rilevate: {list}", list=", ".join(c["model"] for c in cams) or tr("nessuna")))
    return cams


@api.post("/api/camera/connect")
@guard
async def camera_connect(body: CameraConnect):
    not_running()
    async with app_state.camera_lock:
        return await _camera_connect(body)


async def _camera_connect(body: CameraConnect):
    old = app_state.camera
    if (old and old.connected and not body.simulate and not old.simulated
            and body.model in ("", old.model, old.driver) and body.port in ("", old.port)):
        return old.describe()   # già collegata (richiesta doppia): niente seconda sessione PTP
    if app_state.camera:
        await app_state.camera.disconnect()
        app_state.camera = None
    cam = SimulatedCamera() if body.simulate else GPhotoCamera(body.model, body.port)
    app_state.log(tr("Connessione fotocamera {model}…",
                     model=body.model or (tr("simulata") if body.simulate else tr("automatica"))))
    await cam.connect()
    cam.log = app_state.log
    if isinstance(cam, SimulatedCamera):
        cam.focus_position = lambda: (app_state.focuser.position
                                      if app_state.focuser and app_state.focuser.connected else None)
    app_state.camera = cam
    if not cam.simulated and cam.driver:
        app_state.cfg["camera_driver"] = cam.driver   # per ricollegarla da sola alla prossima apertura
        store.save(app_state.cfg)
    app_state.log(tr("Fotocamera connessa: {model}", model=cam.model))
    return cam.describe()


@api.post("/api/camera/disconnect")
@guard
async def camera_disconnect():
    not_running()
    if app_state.camera:
        await app_state.camera.disconnect()
        app_state.camera = None
        app_state.log(tr("Fotocamera disconnessa"))
    return {"ok": True}


LIVE_BOUNDARY = "fsframe"
LIVE_MAX_FPS = 15
# ultimo fotogramma letto, condiviso fra le pagine collegate (finestra principale e visualizzatore):
# la fotocamera ne produce uno solo per volta, al massimo LIVE_MAX_FPS al secondo
live_lock = asyncio.Lock()
live_frame: dict | None = None


async def next_live_frame(cam: GPhotoCamera, last_seq: int) -> dict:
    """Il fotogramma più recente non ancora inviato a questo client: riusa quello appena letto
    per un'altra pagina, altrimenti ne legge uno nuovo rispettando LIVE_MAX_FPS."""
    global live_frame
    async with live_lock:
        f = live_frame if live_frame and live_frame["cam"] is cam else None
        if f:
            # appena letto per un'altra pagina: la freschezza si misura dalla fine della lettura,
            # perché una fotocamera vera (Nikon ~120 ms) impiega più di 1/LIVE_MAX_FPS per fotogramma
            if f["seq"] != last_seq and time.monotonic() - f["done"] < 0.5:
                return f
            await asyncio.sleep(max(0.0, 1 / LIVE_MAX_FPS - (time.monotonic() - f["t"])))
        t0 = time.monotonic()
        data = await cam.preview()
        live_frame = {"cam": cam, "seq": f["seq"] + 1 if f else 1, "t": t0, "done": time.monotonic(), "data": data}
        return live_frame


async def live_frames(cam: GPhotoCamera):
    """Fotogrammi del live view come multipart/x-mixed-replace (MJPEG): il browser li mostra
    in un normale <img>. Si mette in pausa durante scatti e sequenza e si spegne quando
    l'ultima pagina chiude la connessione."""
    global live_frame
    app_state.live_clients += 1
    seq = 0
    park = app_state.live_park["rev"]
    try:
        while cam.connected and app_state.camera is cam:
            if app_state.live_park["rev"] != park:
                # scatto di prova: lo stream finisce qui (le finestre mostrano lo scatto e lo riaprono al primo
                # movimento); riprendere subito il live dopo lo scatto, con la Sony, può dare errore -52
                return
            if app_state.live_paused():
                # sequenza e calibrazione scattano come senza live view (specchio, ritardi): live view spento
                if cam.live:
                    await cam.end_preview()
                await asyncio.sleep(0.3)
                continue
            if cam.busy:
                await asyncio.sleep(0.1)
                continue
            try:
                frame = await next_live_frame(cam, seq)
            except Exception as exc:  # noqa: BLE001
                app_state.live_error = str(exc)
                app_state.log(tr("Live view interrotto: {exc}", exc=exc))
                return
            app_state.live_error = ""
            seq, data = frame["seq"], frame["data"]
            mime = "image/png" if data[:4] == b"\x89PNG" else "image/jpeg"
            yield (f"--{LIVE_BOUNDARY}\r\nContent-Type: {mime}\r\nContent-Length: {len(data)}\r\n\r\n"
                   .encode() + data + b"\r\n")
    finally:
        app_state.live_clients -= 1
        if app_state.live_clients == 0:
            live_frame = None
            if cam.connected and cam.live:
                # la connessione può chiudersi con il generatore cancellato: spegne in un task a parte
                asyncio.get_running_loop().create_task(cam.end_preview())


@api.get("/api/camera/live")
async def camera_live():
    cam = need_camera()
    app_state.live_error = ""
    return StreamingResponse(live_frames(cam), media_type=f"multipart/x-mixed-replace; boundary={LIVE_BOUNDARY}",
                             headers={"Cache-Control": "no-store"})


@api.post("/api/camera/live/stop")
@guard
async def camera_live_stop():
    """«Ferma live» in una finestra: lo stato lo dice a tutte (principale e visualizzatore), che chiudono la loro."""
    app_state.live_stop_rev += 1
    return {"live_stop_rev": app_state.live_stop_rev}


@api.post("/api/camera/settings/reload")
@guard
async def camera_reload():
    not_running()
    return await need_camera().read_settings()


@api.post("/api/camera/settings")
@guard
async def camera_set(body: CameraSetting):
    not_running()
    cam = need_camera()
    settings = await cam.set_setting(body.name, body.value)
    actual = settings.get(body.name, {}).get("current")
    if body.name == "capturetarget" and actual != body.value and cam.is_sony:
        # Sony: la destinazione si sceglie solo dal menu della fotocamera, prima del controllo remoto
        app_state.log(tr("{name} = {actual} (richiesto {requested})", name=body.name, actual=actual, requested=body.value))
        raise ValueError(tr("La Sony non permette di cambiare la destinazione dal computer. Premi «Disconnetti», poi "
                            "sulla fotocamera MENU › Impostazione › Impostazioni Remote PC › Destinazione salvataggio "
                            "foto (Still Img. Save Dest.) › Solo PC, e ricollega la fotocamera."))
    app_state.log(f"{body.name} = {actual}" if actual == body.value
                  else tr("{name} = {actual} (richiesto {requested})", name=body.name, actual=actual, requested=body.value))
    return settings


@api.post("/api/camera/test")
@guard
async def camera_test(body: TestShot):
    not_running()
    check_mirror_delay(body.mirror_delay_ms)
    cam = need_camera()
    test_dir = Path(store.CONFIG_DIR) / "test-shots"
    test_dir.mkdir(parents=True, exist_ok=True)
    # tiene solo gli ultimi scatti di prova
    old = sorted(test_dir.iterdir(), key=lambda p: p.stat().st_mtime)
    for p in old[:-20]:
        p.unlink(missing_ok=True)
    app_state.log(tr("Scatto di prova…"))
    live = app_state.live_clients > 0     # qualcuno guardava il live view: dopo lo scatto lo mette da parte
    files = await cam.capture(mode="download", dest_base=test_dir / f"prova_{time.strftime('%H%M%S')}",
                              bulb_s=body.bulb_s, mirror_s=body.mirror_delay_ms / 1000)
    f = app_state.focuser
    if live:
        app_state.live_park = {"rev": app_state.live_park["rev"] + 1,
                               "pos": f.position if f and f.connected else None}
    app_state.add_shot(files, "test", f.position if f and f.connected else None,
                       f.temperature if f and f.connected else None)
    app_state.log(tr("Scatto di prova completato ({n} file)", n=len(files)))
    return {"files": files}


# ---------------- galleria / visualizzatore ----------------
@api.get("/api/shots")
async def shots():
    # group: gruppo corrente della striscia (il visualizzatore mostra solo quello; vedi new_shot_group)
    return {"items": app_state.shots[-500:], "count": len(app_state.shots), "group": app_state.shot_group}


@api.post("/api/shots/clear")
@guard
async def shots_clear():
    """Ricomincia da capo: svuota il visualizzatore e, se non c'è una sequenza in corso, riporta la
    sequenza a "pronta". La prossima sequenza crea comunque una cartella nuova con i suoi
    sequence.json e sequence.txt; i file già salvati restano dove sono."""
    n = app_state.clear_shots()
    app_state.runner.reset()
    if n:
        app_state.log(tr("Visualizzatore svuotato ({n} scatti): i file restano nella cartella", n=n))
    return {"ok": True}


@api.get("/api/shots/{shot_id}/image")
async def shot_image(shot_id: int, size: str = "full", v: str = ""):
    shot = app_state.get_shot(shot_id)
    if not shot:
        raise HTTPException(404)
    if v and v != shot["key"]:
        raise HTTPException(404, tr("Scatto di una sessione precedente"))
    if size not in ("full", "preview"):
        raise HTTPException(400)
    out = await render_image(shot["file"], size)
    # no-cache = il browser può tenere l'immagine ma deve ricontrollare (ETag) prima di riusarla
    return FileResponse(out, headers={"Cache-Control": "private, no-cache"})


@api.post("/api/shots/{shot_id}/reveal")
async def shot_reveal(shot_id: int):
    shot = app_state.get_shot(shot_id)
    if not shot:
        raise HTTPException(404)
    desktop.reveal(shot["file"])
    return {"ok": True}


# ---------------- avanzamento da smartphone (pagina di sola lettura sulla rete locale) ----------------
class RemoteBody(BaseModel):
    enabled: bool
    new_link: bool = False      # nuovo codice: il link vecchio smette di funzionare


@api.post("/api/remote")
@guard
async def remote_set(body: RemoteBody):
    r = app_state.cfg["remote"]
    r["enabled"] = body.enabled
    if body.new_link:
        r["token"] = remote.new_token()
    store.save(app_state.cfg)
    if not body.enabled:
        app_state.log(tr("Avanzamento da smartphone disattivato"))
    try:
        await app_state.remote_apply()
    except RuntimeError:
        r["enabled"] = False
        store.save(app_state.cfg)
        raise
    return app_state.remote.describe()


@api.get("/api/remote/qr.png")
async def remote_qr():
    url = app_state.remote.url() if app_state.remote.running else None
    if not url:
        raise HTTPException(404)
    out = CACHE_DIR / f"qr-{hashlib.sha1(url.encode()).hexdigest()[:16]}.png"
    if not out.exists() and not await asyncio.to_thread(remote.qr_png, url, out):
        raise HTTPException(500, tr("Impossibile creare il codice QR"))
    return FileResponse(out, media_type="image/png", headers={"Cache-Control": "no-store"})


# ---------------- sequenza ----------------
class SequenceBody(BaseModel):
    start: int
    end: int
    step: int
    settle_ms: int = 1500
    post_shot_ms: int = 500
    mirror_delay_ms: int = 0
    backlash: int = 0
    return_to_start: bool = True
    capture_mode: str = "download"
    session_name: str = "stack"
    output_root: str = ""
    bulb_s: float = 0
    shots_per_position: int = 1
    sound_on_end: bool = True
    optics_profile: str = ""      # profilo di ottica/filtro (tab Ottica); "" = nessun filtro


@api.post("/api/sequence/start")
@guard
async def sequence_start(body: SequenceBody):
    data = body.model_dump()
    if body.step < 1:
        raise ValueError(tr("Il passo deve essere almeno 1"))
    if body.capture_mode not in ("download", "card", "trigger"):
        raise ValueError(tr("Modalità di scatto non valida"))
    check_mirror_delay(body.mirror_delay_ms)
    if not 1 <= body.shots_per_position <= MAX_SHOTS_PER_POSITION:
        raise ValueError(tr("Scatti per posizione: da 1 a {max}", max=MAX_SHOTS_PER_POSITION))
    if body.optics_profile and body.optics_profile not in app_state.cfg["optics_profiles"]:
        raise ValueError(tr("Il profilo ottico «{name}» non esiste più: scegline un altro", name=body.optics_profile))
    need_focuser()
    data["output_root"] = (validate_output_root(body.output_root or app_state.cfg["output_root"])
                           if body.capture_mode == "download" else body.output_root or app_state.cfg["output_root"])
    profile = data.pop("optics_profile")
    if app_state.calib.busy:
        raise ValueError(tr("Calibrazione in corso"))
    if app_state.af.busy:
        raise ValueError(tr("Autofocus in corso"))
    ctx = app_state.manifest_context(profile)
    # set di calibrazione adatti (stessa fotocamera, ISO, tempo, profilo ottico): solo riferimenti, niente copie
    if body.capture_mode == "download":
        found = calibration.match(calibration.list_library(data["output_root"]), ctx.get("camera"), profile, body.bulb_s)
        if found:
            ctx["calibration"] = found
    app_state.runner.start(SequenceParams(**data), ctx,   # verifica anche i fine corsa
                           hold_coils=bool(app_state.cfg.get("coil_during_sequence", True)))
    app_state.new_shot_group("sequence")   # partita davvero: la striscia del visualizzatore ricomincia
    app_state.cfg["sequence"].update({k: v for k, v in data.items() if k != "output_root"},
                                     optics_profile=profile)
    app_state.cfg["output_root"] = data["output_root"]
    store.save(app_state.cfg)
    return {"ok": True}


@api.post("/api/sequence/pause")
async def sequence_pause():
    app_state.runner.pause()
    return {"ok": True}


@api.post("/api/sequence/resume")
async def sequence_resume():
    app_state.runner.resume()
    return {"ok": True}


@api.post("/api/sequence/stop")
async def sequence_stop():
    await app_state.runner.stop()
    return {"ok": True}


@api.post("/api/sequence/reset")
@guard
async def sequence_reset():
    """Nuova pila: la sequenza finita torna «pronta» (0 / N). Il visualizzatore e i file non cambiano;
    la prossima sequenza crea comunque una cartella nuova, anche con lo stesso nome."""
    if not app_state.runner.reset():
        raise ValueError(tr("Sequenza in corso"))
    return {"ok": True}


# ---------------- autofocus su un punto ----------------
class AutofocusStart(BaseModel):
    roi: list[float]                # x0, y0, x1, y1 in frazioni dell'immagine vista
    source: str | None = None       # shot | live (None = quella della Configurazione)


class AutofocusSettings(BaseModel):
    source: str = "live"
    roi_px: int = 256
    fine_step: int | None = None    # None = calcolato
    fine_points: int | None = None
    passes: int | None = None       # passate fini (1–3)
    overscan: int | None = None     # sovracorsa per il gioco (passi)
    coarse: bool = False
    coarse_range: int | None = None
    coarse_step: int | None = None  # passo della ricerca ampia (passi)
    settle_ms: int | None = None
    forget_width: bool = False      # dimentica la larghezza del picco imparata per il profilo della sequenza


AF_SOURCES = ("shot", "live")


@api.post("/api/autofocus/start")
@guard
async def autofocus_start(body: AutofocusStart):
    not_running()
    need_focuser()
    need_camera()
    if len(body.roi) != 4:
        raise ValueError(tr("Area non valida"))
    x0, y0, x1, y1 = (min(1.0, max(0.0, float(v))) for v in body.roi)
    if not (x1 > x0 and y1 > y0):
        raise ValueError(tr("Area non valida"))
    f = need_focuser()
    await f.poll()
    if f.moving:
        raise ValueError(tr("Il focheggiatore si sta muovendo: aspetta che si fermi"))
    source = body.source or app_state.cfg["autofocus"].get("source") or "live"
    if source not in AF_SOURCES:
        raise ValueError(tr("Origine non valida"))
    seq = app_state.cfg["sequence"]
    used = app_state.af_view()["used"]
    p = AFParams(roi=(x0, y0, x1, y1), source=source, fine_step=int(used["fine_step"]),
                 fine_points=int(used["fine_points"]), coarse=bool(app_state.cfg["autofocus"].get("coarse")),
                 coarse_range=int(used["coarse_range"]), coarse_step=int(used["coarse_step"]),
                 settle_ms=int(used["settle_ms"]), overscan=int(used["overscan"]), passes=int(used["passes"]),
                 direction=1 if int(seq.get("end") or 0) >= int(seq.get("start") or 0) else -1,
                 profile=app_state.af_profile())
    app_state.af.start(p)
    return {"ok": True}


@api.post("/api/autofocus/stop")
async def autofocus_stop():
    await app_state.af.stop()
    return {"ok": True}


@api.post("/api/autofocus/settings")
@guard
async def autofocus_settings(body: AutofocusSettings):
    if body.source not in AF_SOURCES:
        raise ValueError(tr("Origine non valida"))
    checks = (("fine_step", tr("Passo"), 1, 100000), ("fine_points", tr("Scatti della passata fine"), 5, 41),
              ("coarse_range", tr("Ampiezza della ricerca ampia"), 1, 1000000),
              ("coarse_step", tr("Passo della ricerca ampia"), 1, 1000000),
              ("passes", tr("Passate"), 1, 3), ("overscan", tr("Sovracorsa per il gioco"), 0, 1000000),
              ("settle_ms", tr("Attesa dopo il movimento"), 0, 30000))
    for key, label, lo, hi in checks:
        v = getattr(body, key)
        if v is not None and not lo <= v <= hi:
            raise ValueError(tr("{name}: da {lo} a {hi}", name=label, lo=lo, hi=hi))
    if not 16 <= body.roi_px <= 4000:
        raise ValueError(tr("Lato dell'area: da 16 a 4000 pixel"))
    a = app_state.cfg["autofocus"]
    a.update(body.model_dump(exclude={"forget_width"}))
    if body.forget_width:
        (a.get("widths") or {}).pop(app_state.af_profile(), None)
    store.save(app_state.cfg)
    return app_state.af_view()


# ---------------- calibrazione ed esposizione automatica ----------------
class CalibrationStart(BaseModel):
    kind: str                      # dark, flat, flat_dark
    count: int = 16
    target_pct: float = 50         # flat: livello medio del canale più chiaro (% della saturazione)


class ExposureBody(BaseModel):
    target_pct: float = 85
    stat: str = "highlights"       # "highlights" (99,5° percentile) o "mean"


def calibration_view() -> dict:
    """Libreria e set che una pila avviata ora userebbe (con le impostazioni attuali della fotocamera)."""
    root = app_state.cfg["output_root"]
    sets = calibration.list_library(root)
    cam = app_state.camera if app_state.camera and app_state.camera.connected else None
    info = calibration.camera_info(cam) if cam else None
    seq = app_state.cfg["sequence"]
    return {"root": str(calibration.library_root(root)), "sets": sets,
            "match": calibration.match(sets, info, seq.get("optics_profile") or "", seq.get("bulb_s") or 0) if info else None,
            "flat": calibration.latest_flat(sets, info.get("model")) if info else None}


@api.get("/api/calibration")
async def calibration_get():
    return calibration_view()


@api.post("/api/calibration/start")
@guard
async def calibration_start(body: CalibrationStart):
    not_running()
    if not 1 <= body.target_pct <= 95:
        raise ValueError(tr("Livello obiettivo: da 1 a 95 %"))
    root = validate_output_root(app_state.cfg["output_root"])
    cam = need_camera()
    seq = app_state.cfg["sequence"]
    flat = None
    if body.kind == "flat_dark":
        flat = calibration.latest_flat(calibration.list_library(root), cam.model)
    profile = seq.get("optics_profile") or ""
    ctx = app_state.manifest_context(profile) if body.kind == "flat" else {}
    app_state.calib.pause_s = (seq.get("post_shot_ms") or 0) / 1000
    app_state.calib.start(body.kind, body.count, root, target_pct=body.target_pct, flat_set=flat,
                          optics_profile=profile, optics=ctx.get("optics"), illumination=ctx.get("illumination"),
                          bulb_s=seq.get("bulb_s") or 0, mirror_s=(seq.get("mirror_delay_ms") or 0) / 1000,
                          software=f"Focus Stack {app_version()}")
    app_state.new_shot_group("calibration")
    app_state.cfg.setdefault("calibration", {}).update(count=body.count, **({"flat_target_pct": body.target_pct} if body.kind == "flat" else {}))
    store.save(app_state.cfg)
    return {"ok": True}


@api.post("/api/calibration/stop")
async def calibration_stop():
    await app_state.calib.stop()
    return {"ok": True}


@api.post("/api/exposure/auto")
@guard
async def exposure_auto(body: ExposureBody):
    """Esposizione dei light: una volta, prima della pila, alla posizione attuale (mai fotogramma per fotogramma)."""
    not_running()
    if body.stat not in ("highlights", "mean"):
        raise ValueError(tr("Misura non valida"))
    if not 1 <= body.target_pct <= 99:
        raise ValueError(tr("Livello obiettivo: da 1 a 99 %"))
    need_camera()
    if app_state.cfg["sequence"].get("bulb_s"):
        raise ValueError(tr("Con la posa B il tempo si imposta a mano: azzera «Posa B» per l'esposizione automatica"))
    seq = app_state.cfg["sequence"]
    app_state.calib.pause_s = (seq.get("post_shot_ms") or 0) / 1000
    app_state.calib.start_exposure(body.target_pct, body.stat, (seq.get("mirror_delay_ms") or 0) / 1000)
    app_state.cfg.setdefault("calibration", {}).update(light_target_pct=body.target_pct, light_stat=body.stat)
    store.save(app_state.cfg)
    return {"ok": True}


class CalibrationSetBody(BaseModel):
    name: str


@api.post("/api/calibration/delete")
@guard
async def calibration_delete(body: CalibrationSetBody):
    """Sposta nel Cestino un set della libreria (dark, flat, dark dei flat)."""
    not_running()
    calibration.delete_set(app_state.cfg["output_root"], body.name)
    app_state.log(tr("Set di calibrazione spostato nel Cestino: {name}", name=body.name))
    return calibration_view()


@api.post("/api/calibration/open")
async def calibration_open():
    root = calibration.library_root(app_state.cfg["output_root"])
    root.mkdir(parents=True, exist_ok=True)
    desktop.open_path(root)
    return {"ok": True}


# ---------------- impostazioni / preset ----------------
class SettingsBody(BaseModel):
    output_root: str | None = None
    jog_max: int | None = None
    jog_hold: bool | None = None
    coil_during_sequence: bool | None = None
    hold_chunk_steps: int | None = None
    language: str | None = None   # "auto" (lingua di macOS) oppure un codice di i18n.SUPPORTED


MAX_SHOTS_PER_POSITION = 32
MAX_CLOSEUP = 3
MAX_CUSTOM_LENSES = 500
IMMERSIONS = ("", "air", "water", "oil", "glycerol", "silicone")
FILTER_TYPES = ("bandpass", "longpass", "shortpass", "neutral_density", "polarizer", "other")


class FilterBody(BaseModel):
    name: str = ""
    type: str = "bandpass"
    center_nm: float | None = None
    bandwidth_nm: float | None = None
    edge_nm: float | None = None


class IlluminationBody(BaseModel):
    type: str = ""
    level_percent: float | None = None
    color_temp_k: float | None = None      # temperatura di colore in kelvin (es. 4000)


class RelayBody(BaseModel):
    """Elemento ottico fra obiettivo e sensore: nome libero e fattore d'ingrandimento (vuoto = 1)."""
    name: str = ""
    factor: float | None = None


class MacroLensBody(BaseModel):
    """Obiettivo fotografico: dal database Lensfun, dall'elenco personale o scritto a mano."""
    maker: str = ""
    model: str = ""
    focal_mm: float | None = None
    max_aperture: float | None = None    # diaframma più aperto (f/)
    source: str = ""                     # "lensfun", "custom" o "" (scritto a mano)


class CloseupBody(BaseModel):
    """Lente addizionale (close-up) davanti all'obiettivo."""
    name: str = ""
    diopters: float | None = None


class MacroBody(BaseModel):
    lens: MacroLensBody = MacroLensBody()
    lens_magnification: float | None = None   # rapporto di riproduzione dell'obiettivo da solo (0 = infinito)
    f_number: float | None = None             # diaframma impostato
    extension_mm: float | None = None         # tubi di prolunga / soffietto
    closeup: list[CloseupBody] = []


class OpticsBody(BaseModel):
    kind: str = "microscope"                  # "microscope" o "macro" (fotografica)
    macro: MacroBody = MacroBody()
    objective: str = ""
    objective_magnification: float | None = None
    intermediate: RelayBody = RelayBody()   # cambio d'ingrandimento intermedio, es. Optovar 1,6×
    relay: RelayBody = RelayBody()          # adattatore per fotocamera / oculare di proiezione
    na: float | None = None
    immersion: str = ""
    sensor_pixel_um: float | None = None
    pixel_size_um: float | None = None
    dof_overlap: float = 30
    filter_mode: str = "unknown"
    filter: FilterBody = FilterBody()
    illumination: IlluminationBody = IlluminationBody()
    notes: str = ""


class OpticsProfileBody(BaseModel):
    name: str
    optics: OpticsBody | None = None


class PresetBody(BaseModel):
    name: str
    data: dict | None = None


def validate_output_root(raw: str) -> str:
    """Normalizza la cartella di salvataggio, la crea se manca e verifica che sia scrivibile."""
    import os
    path = Path(raw.strip()).expanduser()
    if not raw.strip() or not path.is_absolute():
        raise ValueError(tr("Indica un percorso completo, per esempio ~/Pictures/FocusStack"))
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValueError(tr("Impossibile creare la cartella {path}: permesso negato o disco non disponibile", path=path)) from exc
    if not path.is_dir() or not os.access(path, os.W_OK):
        raise ValueError(tr("Non è possibile scrivere nella cartella {path}", path=path))
    return str(path)


@api.post("/api/settings")
@guard
async def save_settings(body: SettingsBody):
    if body.language is not None:
        if body.language not in ("auto", *i18n.SUPPORTED):
            raise ValueError(tr("Lingua non valida"))
        app_state.cfg["language"] = body.language
        i18n.set_language(i18n.resolve(body.language))
    if body.output_root is not None:
        app_state.cfg["output_root"] = validate_output_root(body.output_root)
        app_state.log(tr("Cartella di salvataggio: {path}", path=app_state.cfg["output_root"]))
    if body.jog_max is not None:
        if body.jog_max not in (1000, 10_000, 100_000):
            raise ValueError(tr("Ampiezza massima non valida"))
        app_state.cfg["jog_max"] = body.jog_max
    if body.jog_hold is not None:
        app_state.cfg["jog_hold"] = body.jog_hold
    if body.coil_during_sequence is not None:
        app_state.cfg["coil_during_sequence"] = body.coil_during_sequence
    if body.hold_chunk_steps is not None:
        lo, hi = HOLD_CHUNK_RANGE
        if not lo <= body.hold_chunk_steps <= hi:
            raise ValueError(tr("Tratto del movimento continuo: da {lo} a {hi} passi", lo=lo, hi=hi))
        app_state.cfg["hold_chunk_steps"] = body.hold_chunk_steps
    store.save(app_state.cfg)
    return app_state.cfg


def clean_optics(body: OpticsBody) -> dict:
    """Verifica e normalizza ottica, filtro e illuminazione (senza il nome del profilo)."""
    if body.kind not in ("microscope", "macro"):
        raise ValueError(tr("Tipo di ottica non valido"))
    mc = body.macro
    if len(mc.closeup) > MAX_CLOSEUP:
        raise ValueError(tr("Al massimo {n} lenti addizionali", n=MAX_CLOSEUP))
    for value in (mc.lens.focal_mm, mc.lens.max_aperture, mc.f_number, *(c.diopters for c in mc.closeup)):
        if value is not None and value <= 0:
            raise ValueError(tr("I valori dell'ottica devono essere positivi"))
    for value in (mc.lens_magnification, mc.extension_mm):
        if value is not None and value < 0:
            raise ValueError(tr("I valori dell'ottica devono essere positivi"))
    if body.immersion not in IMMERSIONS:
        raise ValueError(tr("Mezzo di immersione non valido"))
    if body.filter_mode not in ("unknown", "none", "filter"):
        raise ValueError(tr("Scelta del filtro non valida"))
    if body.filter.type not in FILTER_TYPES:
        raise ValueError(tr("Tipo di filtro non valido"))
    for value in (body.objective_magnification, body.intermediate.factor, body.relay.factor,
                  body.sensor_pixel_um, body.pixel_size_um, body.filter.center_nm,
                  body.filter.bandwidth_nm, body.filter.edge_nm):
        if value is not None and value <= 0:
            raise ValueError(tr("I valori dell'ottica devono essere positivi"))
    if body.na is not None and not 0 < body.na <= 1.7:
        raise ValueError(tr("Apertura numerica non valida (0–1,7)"))
    if body.illumination.color_temp_k is not None and not 1000 <= body.illumination.color_temp_k <= 20000:
        raise ValueError(tr("Temperatura di colore: da 1000 a 20000 K"))
    if body.illumination.level_percent is not None and not 0 <= body.illumination.level_percent <= 100:
        raise ValueError(tr("Livello dell'illuminazione: da 0 a 100 %"))
    data = body.model_dump()
    for key in ("objective", "immersion", "notes"):
        data[key] = data[key].strip()
    data["filter"]["name"] = data["filter"]["name"].strip()
    data["illumination"]["type"] = data["illumination"]["type"].strip()
    for key in ("intermediate", "relay"):
        data[key]["name"] = data[key]["name"].strip()
    lens = data["macro"]["lens"]
    for key in ("maker", "model", "source"):
        lens[key] = lens[key].strip()
    # lenti addizionali senza potenza = righe vuote del modulo
    data["macro"]["closeup"] = [{"name": c["name"].strip(), "diopters": c["diopters"]}
                                for c in data["macro"]["closeup"] if c["diopters"]]
    return data


@api.post("/api/optics/profiles/save")
@guard
async def save_optics_profile(body: OpticsProfileBody):
    """Crea o sovrascrive un profilo di ottica, filtro e illuminazione."""
    name = body.name.strip()
    if not name or body.optics is None:
        raise ValueError(tr("Nome e dati obbligatori"))
    app_state.cfg["optics_profiles"][name] = clean_optics(body.optics)
    store.save(app_state.cfg)
    app_state.log(tr("Profilo ottico salvato: {name}", name=name))
    return app_state.cfg["optics_profiles"]


class CustomLensBody(BaseModel):
    maker: str = ""
    model: str
    focal_mm: float | None = None
    max_aperture: float | None = None
    max_magnification: float | None = None
    mounts: list[str] = []


@api.post("/api/lenses/save")
@guard
async def save_custom_lens(body: CustomLensBody):
    """Aggiunge (o sostituisce, stesso marchio e modello) un obiettivo all'elenco personale, cercato
    insieme al database Lensfun nel tab Ottica."""
    lens = body.model_dump()
    lens["maker"], lens["model"] = lens["maker"].strip(), lens["model"].strip()
    if not lens["model"]:
        raise ValueError(tr("Indica il nome dell'obiettivo"))
    if not body.focal_mm:
        raise ValueError(tr("Indica la focale dell'obiettivo"))
    for value in (body.focal_mm, body.max_aperture, body.max_magnification):
        if value is not None and value <= 0:
            raise ValueError(tr("I valori dell'ottica devono essere positivi"))
    lens["mounts"] = [m.strip() for m in body.mounts if m.strip()]
    key = (lens["maker"].lower(), lens["model"].lower())
    lenses = [x for x in app_state.cfg["custom_lenses"] if (x.get("maker", "").lower(), x.get("model", "").lower()) != key]
    if len(lenses) >= MAX_CUSTOM_LENSES:
        raise ValueError(tr("Elenco personale pieno ({n} obiettivi)", n=MAX_CUSTOM_LENSES))
    lenses.append(lens)
    app_state.cfg["custom_lenses"] = lenses
    store.save(app_state.cfg)
    app_state.log(tr("Obiettivo aggiunto all'elenco personale: {name}", name=" ".join(x for x in (lens["maker"], lens["model"]) if x)))
    return lenses


@api.post("/api/lenses/delete")
@guard
async def delete_custom_lens(body: CustomLensBody):
    key = (body.maker.strip().lower(), body.model.strip().lower())
    app_state.cfg["custom_lenses"] = [x for x in app_state.cfg["custom_lenses"]
                                      if (x.get("maker", "").lower(), x.get("model", "").lower()) != key]
    store.save(app_state.cfg)
    return app_state.cfg["custom_lenses"]


class RenameProfileBody(BaseModel):
    name: str
    new_name: str


@api.post("/api/optics/profiles/rename")
@guard
async def rename_optics_profile(body: RenameProfileBody):
    """Rinomina un profilo: anche nella sequenza che lo usa e nei flat della libreria di calibrazione."""
    old, new = body.name, body.new_name.strip()
    profiles = app_state.cfg["optics_profiles"]
    if old not in profiles:
        raise ValueError(tr("Il profilo ottico «{name}» non esiste più: scegline un altro", name=old))
    if not new:
        raise ValueError(tr("Nome e dati obbligatori"))
    if new != old and new in profiles:
        raise ValueError(tr("Esiste già un profilo «{name}»", name=new))
    if new != old:
        # stesso ordine di prima, con il nome nuovo al posto del vecchio
        app_state.cfg["optics_profiles"] = {(new if k == old else k): v for k, v in profiles.items()}
        if app_state.cfg["sequence"].get("optics_profile") == old:
            app_state.cfg["sequence"]["optics_profile"] = new
        widths = app_state.cfg["autofocus"].get("widths") or {}
        if old in widths:   # larghezza del picco imparata dall'autofocus
            widths[new] = widths.pop(old)
        store.save(app_state.cfg)
        flats = calibration.rename_profile(app_state.cfg.get("output_root") or "", old, new)
        app_state.log(tr("Profilo ottico rinominato: «{old}» → «{new}»", old=old, new=new)
                      + (" " + tr("({n} set di calibrazione aggiornati)", n=flats) if flats else ""))
    return app_state.cfg["optics_profiles"]


@api.post("/api/optics/profiles/delete")
@guard
async def delete_optics_profile(body: OpticsProfileBody):
    app_state.cfg["optics_profiles"].pop(body.name, None)
    (app_state.cfg["autofocus"].get("widths") or {}).pop(body.name, None)
    if app_state.cfg["sequence"].get("optics_profile") == body.name:
        app_state.cfg["sequence"]["optics_profile"] = ""
    store.save(app_state.cfg)
    return app_state.cfg["optics_profiles"]


class OutputRootBody(BaseModel):
    path: str


@api.post("/api/choose-folder")
@guard
async def choose_folder():
    """Finestra "Scegli cartella" aperta dal server. Un browser non può fornire percorsi reali del
    disco a una pagina web, quindi la apre il server, che gira sullo stesso computer. Nell'app per Mac
    la finestra è nativa e il percorso arriva da /api/output-root."""
    current = Path(app_state.cfg["output_root"]).expanduser()
    start = current if current.is_dir() else Path.home()
    path = await desktop.choose_folder(start, tr("Cartella in cui salvare gli scatti"))
    if path is None:
        return {"cancelled": True}
    return set_output_root(path)


@api.post("/api/output-root")
@guard
async def output_root(body: OutputRootBody):
    """Cartella scelta dalla finestra nativa dell'app per Mac."""
    return set_output_root(body.path)


def set_output_root(path: str) -> dict:
    app_state.cfg["output_root"] = validate_output_root(path)
    store.save(app_state.cfg)
    app_state.log(tr("Cartella di salvataggio: {path}", path=app_state.cfg["output_root"]))
    return {"path": app_state.cfg["output_root"]}


@api.post("/api/presets/save")
async def preset_save(body: PresetBody):
    if not body.name.strip() or body.data is None:
        raise HTTPException(400, tr("Nome e dati obbligatori"))
    app_state.cfg["presets"][body.name.strip()] = body.data
    store.save(app_state.cfg)
    return app_state.cfg["presets"]


@api.post("/api/presets/delete")
async def preset_delete(body: PresetBody):
    app_state.cfg["presets"].pop(body.name, None)
    store.save(app_state.cfg)
    return app_state.cfg["presets"]


# ---------------- cartelle nel Finder (desktop.py) ----------------
@api.post("/api/open-folder")
async def open_folder():
    folder = app_state.runner.status.folder
    target = Path(folder) if folder and Path(folder).exists() else Path(app_state.cfg["output_root"]).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    desktop.open_path(target)
    return {"ok": True}


@api.post("/api/open-stack-folder")
async def open_stack_folder():
    """Apre nel Finder la cartella dell'ultima pila (immagini e sequence.json)."""
    folder = app_state.runner.status.folder
    if not folder or not Path(folder).exists():
        raise HTTPException(400, tr("Nessuna pila da aprire"))
    desktop.open_path(folder)
    return {"ok": True}


# ---------------- file statici (PWA) ----------------
@api.get("/lang.js")
async def lang_js():
    """Lingua effettiva e traduzioni per la pagina, caricate prima degli script dell'interfaccia."""
    code = i18n.current()
    body = (f"window.FS_LANG = {json.dumps(code)};\n"
            f"window.FS_STRINGS = {json.dumps(i18n.strings(code), ensure_ascii=False)};\n")
    return Response(body, media_type="text/javascript; charset=utf-8", headers={"Cache-Control": "no-cache"})


@api.get("/sw.js")
async def service_worker():
    return FileResponse(WEB_DIR / "sw.js", media_type="text/javascript",
                        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"})


@api.get("/manifest.webmanifest")
async def manifest():
    return Response((WEB_DIR / "manifest.webmanifest").read_text(), media_type="application/manifest+json")


api.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
