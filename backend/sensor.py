"""Analisi del sensore: curva di trasferimento dei fotoni da coppie di flat e di dark, ISO per ISO.

Procedura guidata (Calibrazione › Sensore):
1. flat: per ogni ISO scelto l'app imposta l'ISO, trova il tempo per arrivare al livello obiettivo (50 %) e
   scatta `frames` flat (2 bastano);
2. tappo: aspetta che l'utente metta il tappo sull'obiettivo (pulsante «Ho messo il tappo»);
3. dark: stessi ISO e tempi dei flat, `frames` dark ciascuno;
4. analisi: fs-rawstat --ptc su due flat e due dark per ISO → guadagno (e-/ADU), rumore di lettura (e-),
   pieno pozzetto (e-), gamma dinamica (stop).

I fotogrammi stanno in <cartella delle pile>/_calibrazione/_sensore/<modello>_<data-ora>/ (fuori dalla libreria
dei set: non vengono mai scelti per una pila); il risultato è il profilo del sensore
_calibrazione/_sensore/<modello>.json (formato "focus-stack-sensor" 1), che leggono il riepilogo, il manifesto
delle pile (sequence.json, valori dell'ISO della pila) e Focus Fusion.

Valori non affidabili: sopra un certo ISO molte fotocamere filtrano il rumore già nel RAW, e il rumore misurato
scende sotto quello degli ISO più bassi (fisicamente non torna); quegli ISO, i flat bruciati e i dark con il
nero spostato sono segnati "reliable": false e restano fuori dalle raccomandazioni.
"""
from __future__ import annotations

import asyncio
import json
import math
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from . import power, rawstat
from .calibration import camera_info, library_root
from .i18n import tr
from .sequence import now_iso, write_atomic

SENSOR_DIR = "_sensore"
FORMAT = "focus-stack-sensor"
VERSION = 1
DEFAULT_FRAMES = 2
TARGET_PCT = 50.0
FULL_STOPS = [100 * 2 ** k for k in range(-2, 13)]    # 25, 50, 100, 200 … 409600


def sensor_root(output_root: str) -> Path:
    return library_root(output_root) / SENSOR_DIR


MAKERS = ("Sony", "Canon", "Nikon", "Fujifilm", "FUJIFILM", "Olympus", "OM System", "OM Digital", "Panasonic", "Pentax",
          "Ricoh", "Leica", "Sigma", "Hasselblad")


def camera_key(model: str | None) -> str:
    """Nome della fotocamera senza marca né modalità: gphoto2 dice a volte «ILCE-6400», a volte
    «Sony ILCE-6400 (PC Control)» per la stessa fotocamera; il profilo deve essere lo stesso."""
    m = re.sub(r"\s*\([^)]*\)\s*$", "", (model or "").strip())
    for mk in MAKERS:
        if m.lower().startswith(mk.lower() + " ") and re.search(r"\d", m[len(mk):]):
            m = m[len(mk):].strip()
            break
    return m or "fotocamera"


def safe_name(model: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", camera_key(model)).strip("_") or "fotocamera"


def profile_path(output_root: str, model: str) -> Path:
    return sensor_root(output_root) / f"{safe_name(model)}.json"


def load_profile(output_root: str, model: str | None) -> dict | None:
    if not model:
        return None
    try:
        data = json.loads(profile_path(output_root, model).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if data.get("format") == FORMAT else None


def iso_choices(cam) -> list[int]:
    """ISO numerici che la fotocamera propone (niente Auto ISO né riduzioni del rumore multi-scatto)."""
    out = []
    for c in ((cam.settings or {}).get("iso") or {}).get("choices") or []:
        if re.fullmatch(r"\d+", str(c).strip()):
            out.append(int(c))
    return sorted(set(out))


def plan_isos(choices: list[int], iso_from: int, iso_to: int, step: str) -> list[int]:
    lo, hi = min(iso_from, iso_to), max(iso_from, iso_to)
    sel = [v for v in choices if lo <= v <= hi]
    if step == "full":
        sel = [v for v in sel if v in FULL_STOPS]
    return sel


def entry_for(profile: dict | None, iso) -> dict | None:
    """Valori del profilo per un ISO (stringa o numero); se l'ISO non è stato misurato, None."""
    try:
        want = int(str(iso).strip())
    except (TypeError, ValueError):
        return None
    for e in (profile or {}).get("iso") or []:
        if e.get("iso") == want:
            return e
    return None


def mark_reliability(rows: list[dict]) -> None:
    """Segna gli ISO con valori poco credibili (vedi il commento in testa). rows in ordine di ISO crescente."""
    ok_rn: list[float] = []
    ok_dr: list[float] = []
    filtered = False
    black_ref = rows[0].get("black") if rows else 0
    for r in rows:
        reasons = []
        if (r.get("saturated_pct") or 0) > 0.05:
            reasons.append("saturated")
        rn = r.get("read_noise_e")
        if not (r.get("gain_e_adu") or 0) > 0 or rn is None or not math.isfinite(rn):
            reasons.append("no_signal")
        rng = (r.get("white") or 0) - (black_ref or 0)
        if rng > 0 and r.get("dark_mean") is not None and abs(r["dark_mean"] - black_ref) > 0.01 * rng:
            reasons.append("black_shift")
        # rumore molto più basso degli ISO precedenti affidabili. Se la gamma dinamica sale è il secondo guadagno
        # del sensore (Sony: ISO 400, rumore da 3 a 1,2 e-), un miglioramento vero; se invece continua a scendere,
        # la fotocamera filtra il rumore già nel RAW: da lì in su nessun ISO è affidabile
        if filtered or (ok_rn and rn is not None and rn < 0.85 * min(ok_rn[-3:])
                        and (r.get("dynamic_range_stops") or 0) <= ok_dr[-1] + 0.1):
            filtered = True
            reasons.append("noise_filtered")
        r["reliable"] = not reasons
        if reasons:
            r["reasons"] = reasons
        else:
            r.pop("reasons", None)
            ok_rn.append(rn)
            ok_dr.append(r["dynamic_range_stops"])


def recommend(rows: list[dict]) -> dict:
    ok = [r for r in rows if r.get("reliable")]
    if not ok:
        return {}
    best = max(ok, key=lambda r: r["dynamic_range_stops"])
    # ISO da cui il rumore di lettura (in elettroni) non scende più: oltre, alzare l'ISO toglie solo gamma
    floor = min(r["read_noise_e"] for r in ok)
    low_noise = next(r for r in ok if r["read_noise_e"] <= floor * 1.2)
    # da evitare: un ISO più alto ha almeno la stessa gamma (quindi tempi più brevi e niente da perdere)
    avoid = [r["iso"] for r in ok if any(o["iso"] > r["iso"] and o["dynamic_range_stops"] >= r["dynamic_range_stops"] - 0.05
                                         for o in ok)]
    return {"max_dynamic_range_iso": best["iso"], "low_noise_iso": low_noise["iso"], "avoid_iso": avoid,
            "reliable_up_to_iso": max(r["iso"] for r in ok)}


def simulated_row(iso: int) -> dict:
    """Valori verosimili per il simulatore (modello di un APS-C con doppio guadagno a ISO 400)."""
    gain = 250 / iso
    rn = 3.6 - 0.6 * math.log2(iso / 100) / 1.7 if iso < 400 else max(1.25 - 0.03 * math.log2(iso / 400), 1.05)
    white, black = 15360, 512
    fw = (white - black) * gain
    return {"iso": iso, "gain_e_adu": round(gain, 4), "read_noise_e": round(rn, 3), "read_noise_adu": round(rn / gain, 3),
            "full_well_e": round(fw), "dynamic_range_stops": round(math.log2(fw / rn), 2), "flat_level_pct": 50.0,
            "black": black, "white": white, "dark_mean": black, "saturated_pct": 0.0, "simulated": True}


@dataclass
class SensorStatus:
    state: str = "idle"            # idle, flats, wait_cap, darks, analyzing, done, error, stopping
    message: str = ""
    model: str | None = None
    isos: list = field(default_factory=list)   # [{iso, phase: pending/flat/flat_done/dark/done/skipped/error, shutter, level_pct}]
    index: int = 0
    frames: int = DEFAULT_FRAMES
    folder: str | None = None


class SensorRunner:
    """Procedura guidata dell'analisi del sensore. Usa il CalibrationRunner per esposizione e scatti."""

    def __init__(self, calib, camera_getter: Callable, log: Callable[..., None]):
        self._calib = calib
        self._camera = camera_getter
        self._log = log
        self.status = SensorStatus()
        self._task: asyncio.Task | None = None
        self._cap = asyncio.Event()
        self._stop = False
        self._restore: dict = {}
        self.software = ""

    @property
    def busy(self) -> bool:
        return self._task is not None and not self._task.done()

    def start(self, output_root: str, isos: list[int], frames: int = DEFAULT_FRAMES, mirror_s: float = 0) -> None:
        if self.busy:
            raise RuntimeError(tr("Analisi del sensore già in corso"))
        if self._calib.busy:
            raise RuntimeError(tr("Calibrazione in corso"))
        cam = self._camera()
        if cam is None:
            raise RuntimeError(tr("Fotocamera non connessa"))
        if not isos:
            raise ValueError(tr("Nessun ISO nell'intervallo scelto"))
        if not 2 <= frames <= 10:
            raise ValueError(tr("Fotogrammi per ISO: da 2 a 10"))
        if not getattr(cam, "simulated", False) and rawstat.tool_path() is None:
            raise RuntimeError(tr("Strumento di misura fs-rawstat mancante: python3 tools/rawstat/build.py"))
        self._stop = False
        self._cap = asyncio.Event()
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        folder = sensor_root(output_root) / f"{safe_name(cam.model)}_{stamp}"
        self.status = SensorStatus(state="flats", model=cam.model, frames=frames, folder=str(folder),
                                   isos=[{"iso": v, "phase": "pending"} for v in isos],
                                   message=tr("Flat: diffusore illuminato davanti all'obiettivo"))
        self._restore = {k: ((cam.settings or {}).get(k) or {}).get("current") for k in ("iso", "shutterspeed")}
        self._task = asyncio.create_task(self._run(cam, output_root, folder, frames, mirror_s))

    def cap_on(self) -> None:
        if self.status.state != "wait_cap":
            raise RuntimeError(tr("L'analisi del sensore non sta aspettando il tappo"))
        self._cap.set()

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

    async def _set(self, cam, key: str, value: str) -> bool:
        await cam.set_setting(key, value)
        return ((cam.settings or {}).get(key) or {}).get("current") == value

    async def _shots(self, cam, folder: Path, prefix: str, n: int, mirror_s: float) -> list[str]:
        folder.mkdir(parents=True, exist_ok=True)
        out = []
        for i in range(n):
            if self._stop:
                raise asyncio.CancelledError
            files = await self._calib._capture(cam, folder / f"{prefix}_{i + 1:04d}", mirror_s=mirror_s)
            f = rawstat.pick_file(files) or (files[0] if files else None)
            if not f:
                raise RuntimeError(tr("La fotocamera non ha restituito il file: imposta la destinazione sul computer o RAM"))
            out.append(f)
        return out

    async def _run(self, cam, output_root: str, folder: Path, frames: int, mirror_s: float) -> None:
        st = self.status
        sim = getattr(cam, "simulated", False)
        run = {"format": FORMAT + "-run", "version": VERSION, "software": self.software, "camera": {"model": cam.model},
               "created": now_iso(), "frames_per_iso": frames, "iso": []}
        power.hold()
        try:
            folder.mkdir(parents=True, exist_ok=True)
            self._log(tr("Analisi del sensore: {n} ISO, {f} flat e {f} dark ciascuno, in {path}",
                         n=len(st.isos), f=frames, path=folder))
            # ---- 1. flat ----
            if sim:
                cam.scene = "flat"
            for i, item in enumerate(st.isos):
                st.index = i
                iso = str(item["iso"])
                if not await self._set(cam, "iso", iso):
                    item["phase"] = "skipped"
                    item["message"] = tr("la fotocamera resta a {v}", v=((cam.settings or {}).get("iso") or {}).get("current"))
                    self._log(tr("Analisi del sensore: ISO {iso} non accettato, salto", iso=iso))
                    continue
                item["phase"] = "flat"
                st.message = tr("ISO {iso}: esposizione dei flat…", iso=iso)
                expo = await self._calib.auto_expose(cam, TARGET_PCT, "mean", mirror_s)
                item["shutter"] = ((cam.settings or {}).get("shutterspeed") or {}).get("current")
                item["level_pct"] = round(expo.get("level_pct") or 0, 1)
                st.message = tr("ISO {iso}: flat a {sh}", iso=iso, sh=item["shutter"])
                item["flats"] = await self._shots(cam, folder / f"flat_iso{iso}", "flat", frames, mirror_s)
                item["phase"] = "flat_done"
            todo = [x for x in st.isos if x["phase"] == "flat_done"]
            if not todo:
                raise RuntimeError(tr("Nessun ISO accettato dalla fotocamera"))
            # ---- 2. tappo ----
            st.state = "wait_cap"
            st.message = tr("Metti il tappo sull'obiettivo, poi premi «Ho messo il tappo»")
            self._log(tr("Analisi del sensore: flat fatti, in attesa del tappo"))
            await self._cap.wait()
            # ---- 3. dark ----
            st.state = "darks"
            if sim:
                cam.scene = "dark"
            for i, item in enumerate(st.isos):
                if item["phase"] != "flat_done":
                    continue
                st.index = i
                iso = str(item["iso"])
                item["phase"] = "dark"
                st.message = tr("ISO {iso}: dark a {sh}", iso=iso, sh=item["shutter"])
                await self._set(cam, "iso", iso)
                if item.get("shutter"):
                    await self._calib._set_shutter(cam, item["shutter"])
                item["darks"] = await self._shots(cam, folder / f"dark_iso{iso}", "dark", frames, 0)
                item["phase"] = "dark_done"
            # ---- 4. analisi ----
            st.state = "analyzing"
            rows = []
            for item in st.isos:
                if item["phase"] != "dark_done":
                    continue
                st.message = tr("Analisi ISO {iso}…", iso=item["iso"])
                if sim:
                    row = simulated_row(item["iso"])
                else:
                    data = await rawstat.ptc(item["flats"][:2], item["darks"][:2])
                    row = {"iso": item["iso"], **{k: data.get(k) for k in (
                        "gain_e_adu", "read_noise_e", "read_noise_adu", "full_well_e", "dynamic_range_stops", "flat_level_pct",
                        "black", "white", "dark_mean", "saturated_pct", "samples")}}
                row["shutter"] = item.get("shutter")
                row["flat_files"] = [str(Path(f).relative_to(folder.parent)) for f in item["flats"][:2]]
                row["dark_files"] = [str(Path(f).relative_to(folder.parent)) for f in item["darks"][:2]]
                rows.append(row)
                item["phase"] = "done"
            rows.sort(key=lambda r: r["iso"])
            mark_reliability(rows)
            profile = {"format": FORMAT, "version": VERSION, "software": self.software,
                       "camera": {k: v for k, v in camera_info(cam).items() if k in ("aperture", "imageformat")}
                       | {"model": camera_key(cam.model), "gphoto_model": cam.model}, "created": now_iso(),
                       "method": "photon transfer: 2 flat + 2 dark per ISO, central crop of one green CFA channel, raw values",
                       "run": folder.name, "simulated": sim or None, "iso": rows, "recommended": recommend(rows)}
            profile = {k: v for k, v in profile.items() if v is not None}
            write_atomic(folder / "analysis.json", profile)
            write_atomic(profile_path(output_root, cam.model), profile)
            st.state = "done"
            st.message = tr("Analisi del sensore salvata: {n} ISO", n=len(rows))
            self._log(st.message)
        except asyncio.CancelledError:
            st.state = "idle"
            st.message = tr("Analisi del sensore interrotta")
            self._log(st.message)
        except Exception as exc:  # noqa: BLE001
            st.state = "error"
            st.message = str(exc)
            self._log(tr("ERRORE analisi del sensore: {exc}", exc=exc), "error")
        finally:
            power.release()
            if sim:
                cam.scene = None
            # la fotocamera torna com'era prima dell'analisi
            try:
                if self._restore.get("iso"):
                    await cam.set_setting("iso", self._restore["iso"])
                if self._restore.get("shutterspeed"):
                    await cam.set_setting("shutterspeed", self._restore["shutterspeed"])
            except Exception:  # noqa: BLE001
                pass
            run["iso"] = [{k: v for k, v in x.items() if k not in ("flats", "darks")} for x in st.isos]
            run["state"] = st.state
            run["finished"] = now_iso()
            try:
                if folder.exists():
                    write_atomic(folder / "run.json", run)
            except OSError:
                pass


def csv_text(profile: dict) -> str:
    head = "iso;shutter;gain_e_per_adu;read_noise_e;read_noise_adu;full_well_e;dynamic_range_stops;flat_level_pct;reliable"
    lines = [head]
    for r in profile.get("iso") or []:
        lines.append(";".join(str(x) for x in (r["iso"], r.get("shutter") or "", r.get("gain_e_adu"), r.get("read_noise_e"),
                                                r.get("read_noise_adu"), r.get("full_well_e"), r.get("dynamic_range_stops"),
                                                r.get("flat_level_pct"), "yes" if r.get("reliable") else "no")))
    return "\n".join(lines) + "\n"
