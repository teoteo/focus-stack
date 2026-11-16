"""Frame di calibrazione (dark, flat, dark dei flat) ed esposizione automatica.

Libreria condivisa: <cartella di salvataggio delle pile>/_calibrazione/<tipo>_<data-ora>/, con i fotogrammi e
calibration.json (formato "focus-stack-calibration" 1, vedi docs/calibration-json.md). Le pile non copiano i
fotogrammi: il loro sequence.json indica in "calibration" i set adatti (percorsi relativi), scelti all'avvio
della sequenza in base a fotocamera, ISO, tempo di posa e profilo ottico.

- dark: tappo sull'obiettivo, stessi ISO e tempo dei light (rumore termico, pixel caldi, livello del nero);
- flat: campo illuminato in modo uniforme, stessa ottica e diaframma dei light (vignettatura, polvere); il
  tempo si trova da solo per arrivare al livello obiettivo;
- dark dei flat (flat_dark): tappo, stessi ISO e tempo dei flat.
I bias non servono: i dark alla stessa esposizione dei light li comprendono già (Focus Fusion non li usa).

Esposizione automatica: scatti di prova, misura con fs-rawstat (valori lineari dei RAW), nuovo tempo = tempo ×
obiettivo / misura, scelto fra quelli che la fotocamera offre; al massimo MAX_ITER tentativi.
"""
from __future__ import annotations

import asyncio
import json
import math
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from . import rawstat
from .i18n import tr
from .sequence import now_iso, write_atomic
from .summary import num


def pct(v: float) -> str:
    """Percentuale con un decimale e il separatore della lingua (35,1)."""
    return num(round(v, 1), 1)

LIBRARY_DIR = "_calibrazione"
FORMAT = "focus-stack-calibration"
VERSION = 1
KINDS = ("dark", "flat", "flat_dark")
FOLDER = {"dark": "dark", "flat": "flat", "flat_dark": "flat-dark"}
MAX_ITER = 7
TOLERANCE = 0.08          # ±8 % del livello obiettivo
MAX_FRAMES = 100
MIN_PAUSE_S = 1.0         # pausa minima dopo ogni scatto: la fotocamera deve finire di scrivere il RAW
CAPTURE_RETRIES = 2       # nuovi tentativi dopo uno scatto fallito (attese 3 s e 6 s), come nella sequenza


def library_root(output_root: str) -> Path:
    return Path(output_root).expanduser() / LIBRARY_DIR


def shutter_seconds(value: str) -> float | None:
    """Tempo di posa di gphoto2 in secondi: "1/60", "30", "2.5", "0,3", "1/8000s", "0.0005s"; None per bulb e simili."""
    v = str(value).strip().lower().rstrip('s"').strip().replace(",", ".")
    if "65535" in v:          # Sony: valore non disponibile (es. subito dopo la connessione)
        return None
    m = re.fullmatch(r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", v)
    if m:
        den = float(m.group(2))
        return float(m.group(1)) / den if den else None
    try:
        x = float(v)
    except ValueError:
        return None
    return x if x > 0 else None


def shutter_choices(cam) -> list[tuple[float, str]]:
    sh = (cam.settings or {}).get("shutterspeed") or {}
    out = [(s, c) for c in sh.get("choices") or [] if (s := shutter_seconds(c))]
    return sorted(set(out))


def camera_info(cam) -> dict:
    info = {"model": cam.model or None}
    for key in ("iso", "shutterspeed", "aperture", "imageformat"):
        cur = ((cam.settings or {}).get(key) or {}).get("current")
        if cur:
            info[key] = cur
    return info


@dataclass
class CalibStatus:
    state: str = "idle"            # idle, exposing, running, stopping, done, error
    kind: str | None = None
    index: int = 0
    total: int = 0
    message: str = ""
    folder: str | None = None
    shutter: str | None = None
    level_pct: float | None = None
    target_pct: float | None = None
    exposure: dict | None = None   # ultimo risultato dell'esposizione automatica
    history: list = field(default_factory=list)   # tentativi dell'esposizione automatica


class CalibrationRunner:
    def __init__(self, camera_getter: Callable, focuser_getter: Callable, log: Callable[[str], None],
                 on_shot: Callable[[list[str], str], None], test_dir: Path):
        self._camera = camera_getter
        self._focuser = focuser_getter
        self._log = log
        self._on_shot = on_shot
        self._test_dir = test_dir
        self.pause_s = 0.0        # «Pausa dopo lo scatto» della sequenza (si usa almeno MIN_PAUSE_S)
        self.status = CalibStatus()
        self._task: asyncio.Task | None = None
        self._stop = False

    @property
    def busy(self) -> bool:
        return self._task is not None and not self._task.done()

    def _temperature(self):
        f = self._focuser()
        return getattr(f, "temperature", None) if f else None

    async def _capture(self, cam, dest_base: Path, bulb_s: float = 0, mirror_s: float = 0) -> list[str]:
        """Scatto con nuovi tentativi (la fotocamera può non rispondere mentre scrive sulla scheda), poi la pausa."""
        files: list[str] = []
        for attempt in range(CAPTURE_RETRIES + 1):
            try:
                files = await cam.capture(mode="download", dest_base=dest_base, bulb_s=bulb_s, mirror_s=mirror_s)
                break
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                if self._stop:
                    raise
                if attempt == CAPTURE_RETRIES:
                    raise RuntimeError(tr(
                        "La fotocamera non ha scattato dopo {n} tentativi ({exc}). Controlla: obiettivo in messa a "
                        "fuoco manuale (MF), «Pausa dopo lo scatto» abbastanza lunga perché la fotocamera finisca di "
                        "scrivere sulla scheda (con i RAW almeno 1–2 s), batteria e scheda.", n=attempt + 1, exc=exc)) from exc
                wait = 3 * (attempt + 1)
                self._log(tr("Scatto non riuscito ({exc}): nuovo tentativo fra {s} s ({a} di {n})",
                             exc=exc, s=wait, a=attempt + 1, n=CAPTURE_RETRIES))
                await asyncio.sleep(wait)
        await asyncio.sleep(max(MIN_PAUSE_S, self.pause_s))
        return files

    async def _set_shutter(self, cam, value: str) -> None:
        """Imposta il tempo e controlla che la fotocamera l'abbia preso (Sony a volte lo ignora)."""
        await cam.set_setting("shutterspeed", value)
        got = ((cam.settings or {}).get("shutterspeed") or {}).get("current")
        if got != value:
            self._log(tr("La fotocamera non ha accettato il tempo {s} (è ancora {got})", s=value, got=got))

    # ---------------- esposizione automatica ----------------
    async def _test_shot(self, cam, mirror_s: float) -> dict:
        self._test_dir.mkdir(parents=True, exist_ok=True)
        for p in sorted(self._test_dir.glob("expo_*"), key=lambda p: p.stat().st_mtime)[:-12]:
            p.unlink(missing_ok=True)
        files = await self._capture(cam, self._test_dir / f"expo_{time.strftime('%H%M%S')}_{int(time.time() * 1000) % 1000:03d}",
                                    mirror_s=mirror_s)
        f = rawstat.pick_file(files)
        if not f:
            raise RuntimeError(tr("La fotocamera non ha restituito il file: imposta la destinazione sul computer o RAM"))
        self._on_shot(files, "exposure")
        return await rawstat.measure(f)

    async def auto_expose(self, cam, target_pct: float, stat: str, mirror_s: float = 0) -> dict:
        """Porta il livello misurato (stat: "mean" o "highlights") vicino a target_pct cambiando solo il tempo."""
        choices = shutter_choices(cam)
        if not choices:
            raise RuntimeError(tr("La fotocamera non permette di scegliere il tempo di posa da qui"))
        cur: str = str(((cam.settings or {}).get("shutterspeed") or {}).get("current") or "")
        t = shutter_seconds(cur) if cur else None
        if t is None:   # bulb o valore sconosciuto: parte da 1/60 o dal più vicino
            t, cur = min(choices, key=lambda c: abs(math.log(c[0] / (1 / 60))))
            await self._set_shutter(cam, cur)
        tried: dict[str, float] = {}
        best = None
        self.status.history = []
        for _ in range(MAX_ITER):
            if self._stop:
                raise asyncio.CancelledError
            self.status.shutter = cur
            self.status.message = tr("Esposizione: prova a {s}", s=cur)
            stats = await self._test_shot(cam, mirror_s)
            # il tempo vero è quello dell'EXIF: se la fotocamera non ha preso il valore chiesto il conto resta giusto
            exif_t = stats.get("shutter_s")
            if exif_t and exif_t > 0 and abs(math.log(exif_t / t)) > 0.15:
                real = min(choices, key=lambda c: abs(math.log(c[0] / exif_t)))
                self._log(tr("La fotocamera ha scattato a {got} invece di {s}", got=real[1], s=cur))
                t, cur = real
            lv = rawstat.level(stats, stat)
            burnt = (stats.get("all") or {}).get("burnt_pct") or 0
            tried[cur] = lv
            self.status.level_pct = round(lv, 2)
            self.status.history.append({"shutter": cur, "level_pct": round(lv, 2), "burnt_pct": burnt})
            self._log(tr("Esposizione {s}: livello {v} % (obiettivo {t} %)", s=cur, v=pct(lv), t=num(target_pct)))
            err = abs(lv / target_pct - 1) if target_pct else 1
            # il migliore: prima i tentativi senza luci bruciate, poi il più vicino all'obiettivo
            clipped = lv >= 99.5 or burnt > 1
            if best is None or (clipped, err) < (best[4], best[0]):
                best = (err, cur, lv, stats, clipped)
            if err <= TOLERANCE and lv < 99.5:
                break
            # nuovo tempo: proporzionale (valori lineari); se bruciato o quasi nero, salti decisi
            if clipped:
                want = t / 2
            elif lv < 0.3:
                want = t * 16
            else:
                want = t * target_pct / lv
            nt, nc = min(choices, key=lambda c: abs(math.log(c[0] / want)))
            if nc == cur or nc in tried:
                # già provato: un tempo intermedio non ancora provato fra quello attuale e quello voluto
                lo_t, hi_t = sorted((t, nt))
                between = [c for c in choices if lo_t < c[0] < hi_t and c[1] not in tried]
                if not between:
                    break      # nessun tempo migliore disponibile
                nt, nc = min(between, key=lambda c: abs(math.log(c[0] / want)))
            await self._set_shutter(cam, nc)
            t, cur = nt, nc
        assert best is not None
        err, cur_best, lv, stats, _clipped = best
        if cur_best != ((cam.settings or {}).get("shutterspeed") or {}).get("current"):
            await self._set_shutter(cam, cur_best)
        result = {"shutter": cur_best, "level_pct": round(lv, 2), "target_pct": target_pct, "stat": stat,
                  "within_tolerance": err <= TOLERANCE, "linear": stats.get("linear"), "attempts": len(self.status.history)}
        self.status.exposure = result
        self.status.shutter = cur_best
        return result

    def start_exposure(self, target_pct: float, stat: str, mirror_s: float) -> None:
        """Esposizione automatica dei light (nessun fotogramma salvato nella libreria)."""
        cam = self._ready()
        self.status = CalibStatus(state="exposing", target_pct=target_pct, message=tr("Esposizione automatica…"))
        self._task = asyncio.create_task(self._run_exposure(cam, target_pct, stat, mirror_s))

    async def _run_exposure(self, cam, target_pct: float, stat: str, mirror_s: float) -> None:
        try:
            r = await self.auto_expose(cam, target_pct, stat, mirror_s)
            self.status.state = "done"
            self.status.message = (tr("Tempo impostato: {s} (livello {v} %)", s=r["shutter"], v=pct(r["level_pct"]))
                                   if r["within_tolerance"] else
                                   tr("Tempo più vicino: {s} (livello {v} %, obiettivo {t} %)", s=r["shutter"],
                                      v=pct(r["level_pct"]), t=num(target_pct)))
            self._log(self.status.message)
        except asyncio.CancelledError:
            self.status.state = "idle"
            self.status.message = tr("Esposizione automatica interrotta")
        except Exception as exc:  # noqa: BLE001
            self.status.state = "error"
            self.status.message = str(exc)
            self._log(tr("ERRORE esposizione automatica: {exc}", exc=exc))
        finally:
            self._scene(cam, None)

    # ---------------- acquisizione dei set ----------------
    def _ready(self):
        if self.busy:
            raise RuntimeError(tr("Calibrazione già in corso"))
        cam = self._camera()
        if cam is None:
            raise RuntimeError(tr("Fotocamera non connessa"))
        self._stop = False
        return cam

    def start(self, kind: str, count: int, output_root: str, *, target_pct: float = 50, flat_set: dict | None = None,
              optics_profile: str = "", optics: dict | None = None, illumination: dict | None = None,
              bulb_s: float = 0, mirror_s: float = 0, software: str = "") -> None:
        if kind not in KINDS:
            raise ValueError(tr("Tipo di calibrazione non valido"))
        if not 1 <= count <= MAX_FRAMES:
            raise ValueError(tr("Fotogrammi: da 1 a {n}", n=MAX_FRAMES))
        if kind == "flat_dark" and not flat_set:
            raise ValueError(tr("Prima scatta i flat: i dark dei flat usano il loro tempo di posa"))
        cam = self._ready()
        self.status = CalibStatus(state="running", kind=kind, total=count, target_pct=target_pct if kind == "flat" else None,
                                  message=tr("Preparazione…"))
        self._task = asyncio.create_task(self._run(cam, kind, count, output_root, target_pct, flat_set, optics_profile,
                                                   optics, illumination, bulb_s, mirror_s, software))

    async def stop(self) -> None:
        task = self._task
        if task is not None and not task.done():
            self._stop = True
            self.status.state = "stopping"
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):  # noqa: BLE001
                pass

    def _scene(self, cam, scene: str | None) -> None:
        """Simulatore: tappo (dark) o campo uniforme (flat). Le fotocamere vere non hanno questo attributo."""
        if getattr(cam, "simulated", False):
            cam.scene = scene

    async def _run(self, cam, kind, count, output_root, target_pct, flat_set, optics_profile, optics, illumination,
                   bulb_s, mirror_s, software) -> None:
        root = library_root(output_root)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        folder = root / f"{FOLDER[kind]}_{stamp}"
        n = 2
        while folder.exists():
            folder = root / f"{FOLDER[kind]}_{stamp}-{n}"
            n += 1
        meta: dict = {"format": FORMAT, "version": VERSION, "software": software, "type": kind, "state": "running",
                      "created": now_iso(), "updated": None, "frames": []}
        try:
            self._scene(cam, "flat" if kind == "flat" else "dark")
            if kind == "flat_dark":
                fc = flat_set.get("camera") or {}
                for key in ("iso", "shutterspeed"):
                    if fc.get(key) and ((cam.settings or {}).get(key) or {}).get("current") != fc[key]:
                        if key == "shutterspeed":
                            await self._set_shutter(cam, fc[key])
                        else:
                            await cam.set_setting(key, fc[key])
                meta["flat_set"] = flat_set.get("name")
            if kind == "flat":
                self.status.state = "exposing"
                expo = await self.auto_expose(cam, target_pct, "mean", mirror_s)
                meta["exposure"] = expo
                if not expo["within_tolerance"]:
                    self._log(tr("Flat: livello {v} % invece di {t} %: nessun tempo di posa più adatto",
                                 v=pct(expo["level_pct"]), t=num(target_pct)))
                self.status.state = "running"
            meta["camera"] = camera_info(cam)
            # dark: la posa B dei light vale anche per i dark; flat e dark dei flat usano il tempo di posa
            use_bulb = bulb_s if kind == "dark" else 0
            if use_bulb:
                meta["bulb_s"] = use_bulb
            if kind == "flat":
                meta["optics_profile"] = optics_profile or None
                if optics:
                    meta["optics"] = optics
                if illumination:
                    meta["illumination"] = illumination
            folder.mkdir(parents=True, exist_ok=True)
            self.status.folder = str(folder)
            self._log(tr("Calibrazione {kind}: {n} fotogrammi in {path}", kind=kind, n=count, path=folder))
            temps = []
            for i in range(count):
                if self._stop:
                    raise asyncio.CancelledError
                self.status.index = i
                self.status.message = tr("Fotogramma {i} di {n}", i=i + 1, n=count)
                files = await self._capture(cam, folder / f"{FOLDER[kind]}_{i + 1:04d}", bulb_s=use_bulb, mirror_s=mirror_s)
                temp = self._temperature()
                if temp is not None:
                    temps.append(temp)
                frame = {"index": i, "time": now_iso(), "files": [Path(f).name for f in files], "temperature_c": temp}
                f = rawstat.pick_file(files)
                if f:
                    try:
                        st = await rawstat.measure(f)
                        frame["stats"] = rawstat.summary(st)
                        self.status.level_pct = round(rawstat.level(st, "mean"), 2)
                    except rawstat.RawStatError as exc:
                        frame["stats_error"] = str(exc)
                meta["frames"].append({k: v for k, v in frame.items() if v is not None})
                self._on_shot(files, "calibration")
                self.status.index = i + 1
                if temps:
                    meta["temperature_c"] = {"min": min(temps), "max": max(temps), "mean": round(sum(temps) / len(temps), 2)}
                levels = [fr["stats"]["mean_pct"] for fr in meta["frames"] if fr.get("stats")]
                if levels:
                    meta["mean_level_pct"] = {k: round(sum(l[k] for l in levels) / len(levels), 3) for k in levels[0]}
                meta["updated"] = now_iso()
                write_atomic(folder / "calibration.json", meta)
            meta["state"] = "completed"
            self.status.state = "done"
            self.status.message = tr("Calibrazione completata: {n} fotogrammi", n=count)
            self._log(self.status.message)
        except asyncio.CancelledError:
            meta["state"] = "interrupted"
            self.status.state = "idle"
            self.status.message = tr("Calibrazione interrotta")
            self._log(self.status.message)
        except Exception as exc:  # noqa: BLE001
            meta["state"] = "error"
            meta["error"] = str(exc)
            self.status.state = "error"
            self.status.message = str(exc)
            self._log(tr("ERRORE calibrazione: {exc}", exc=exc))
        finally:
            self._scene(cam, None)
            if folder.exists():
                meta["finished"] = meta["updated"] = now_iso()
                try:
                    write_atomic(folder / "calibration.json", meta)
                except OSError:
                    pass


# ---------------- libreria ----------------
def list_library(output_root: str) -> list[dict]:
    """Set di calibrazione nella libreria, dal più recente."""
    root = library_root(output_root)
    out = []
    if not root.is_dir():
        return out
    for meta_file in root.glob("*/calibration.json"):
        try:
            m = json.loads(meta_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if m.get("format") != FORMAT:
            continue
        frames = m.get("frames") or []
        out.append({"name": meta_file.parent.name, "path": str(meta_file.parent), "type": m.get("type"),
                    "state": m.get("state"), "created": m.get("created"), "camera": m.get("camera") or {},
                    "bulb_s": m.get("bulb_s"), "optics_profile": m.get("optics_profile"), "frames": len(frames),
                    "mean_level_pct": m.get("mean_level_pct"), "temperature_c": m.get("temperature_c"),
                    "flat_set": m.get("flat_set"), "exposure": m.get("exposure")})
    out.sort(key=lambda x: x.get("created") or "", reverse=True)
    return out


def _usable(s: dict) -> bool:
    return s.get("state") == "completed" and s.get("frames", 0) > 0


def match(library: list[dict], camera: dict | None, optics_profile: str, bulb_s: float = 0) -> dict:
    """I set più recenti adatti a una pila: dark con stessa fotocamera, ISO e tempo (o posa B); flat con stessa
    fotocamera e profilo ottico (stesso diaframma se noto); dark dei flat con ISO e tempo di quei flat."""
    cam = camera or {}
    model = cam.get("model")
    same_cam = [s for s in library if _usable(s) and (s["camera"].get("model") == model)]
    out: dict = {}

    def entry(s: dict) -> dict:
        e = {"set": s["name"], "path": f"../{LIBRARY_DIR}/{s['name']}", "frames": s["frames"], "created": s["created"]}
        for k in ("iso", "shutterspeed", "aperture"):
            if s["camera"].get(k):
                e[k] = s["camera"][k]
        if s.get("bulb_s"):
            e["bulb_s"] = s["bulb_s"]
        if s.get("temperature_c"):
            e["temperature_c"] = s["temperature_c"]
        if s.get("optics_profile"):
            e["optics_profile"] = s["optics_profile"]
        return e

    darks = [s for s in same_cam if s["type"] == "dark" and s["camera"].get("iso") == cam.get("iso")
             and ((s.get("bulb_s") or 0) == (bulb_s or 0)) and (bulb_s or s["camera"].get("shutterspeed") == cam.get("shutterspeed"))]
    if darks:
        out["darks"] = entry(darks[0])
    flats = [s for s in same_cam if s["type"] == "flat" and (s.get("optics_profile") or "") == (optics_profile or "")]
    same_ap = [s for s in flats if cam.get("aperture") and s["camera"].get("aperture") == cam.get("aperture")]
    flat = (same_ap or flats or [None])[0]
    if flat:
        out["flats"] = entry(flat)
        fd = [s for s in same_cam if s["type"] == "flat_dark" and s["camera"].get("iso") == flat["camera"].get("iso")
              and s["camera"].get("shutterspeed") == flat["camera"].get("shutterspeed")]
        if fd:
            out["flat_darks"] = entry(fd[0])
    return out


def delete_set(output_root: str, name: str) -> Path:
    """Sposta nel Cestino la cartella di un set della libreria (recuperabile dal Finder). Solo cartelle dirette
    di _calibrazione che contengono un calibration.json di Focus Stack."""
    import os
    import shutil
    import subprocess
    root = library_root(output_root).resolve()
    folder = (root / name).resolve()
    if "/" in name or folder.parent != root or not (folder / "calibration.json").is_file():
        raise ValueError(tr("Set di calibrazione non trovato: {name}", name=name))
    trash = Path.home() / ".Trash"
    target = trash / name
    n = 2
    while target.exists():
        target = trash / f"{name} {n}"
        n += 1
    try:
        os.rename(folder, target)            # stesso disco: istantaneo
    except OSError:
        try:
            shutil.move(str(folder), str(target))
        except OSError:
            # Cestino non raggiungibile da qui (o altro disco): lo sposta il Finder
            r = subprocess.run(["osascript", "-e", f'tell application "Finder" to delete (POSIX file "{folder}" as alias)'],
                               capture_output=True, text=True)
            if r.returncode != 0:
                raise RuntimeError(tr("Impossibile spostare nel Cestino {name}: {err}", name=name, err=r.stderr.strip()))
            target = trash / name
    return target


def latest_flat(library: list[dict], model: str | None) -> dict | None:
    return next((s for s in library if _usable(s) and s["type"] == "flat" and s["camera"].get("model") == model), None)
