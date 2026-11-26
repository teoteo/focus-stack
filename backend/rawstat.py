"""Livelli di un'immagine con fs-rawstat (tools/rawstat: LibRaw 0.22.3, la stessa di Focus Fusion).

I valori sono percentuali fra il nero e la saturazione del sensore (RAW, lineari) oppure, per JPEG/PNG,
stime linearizzate dalla curva sRGB ("linear": False). Vedi tools/rawstat/rawstat.cpp.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

from .i18n import tr

APP_ROOT = Path(__file__).resolve().parent.parent
# nell'app compilata: Contents/Resources/app/bin; in sviluppo: build/rawstat (python3 tools/rawstat/build.py)
CANDIDATES = (APP_ROOT / "bin" / "fs-rawstat", APP_ROOT / "build" / "rawstat" / "fs-rawstat")


class RawStatError(Exception):
    pass


def tool_path() -> Path | None:
    return next((p for p in CANDIDATES if p.is_file() and os.access(p, os.X_OK)), None)


async def measure(path: str | Path, timeout_s: float = 60) -> dict:
    """Statistiche di un file (vedi rawstat.cpp). Solleva RawStatError se non si può misurare."""
    exe = tool_path()
    if exe is None:
        raise RawStatError(tr("Strumento di misura fs-rawstat mancante: python3 tools/rawstat/build.py"))
    proc = await asyncio.create_subprocess_exec(str(exe), str(path), stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout_s)
    except asyncio.TimeoutError as exc:
        proc.kill()
        raise RawStatError(tr("Misura troppo lenta: {name}", name=Path(path).name)) from exc
    try:
        data = json.loads(out.decode("utf-8", "replace").strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise RawStatError(tr("Misura non riuscita: {name}", name=Path(path).name)) from exc
    if data.get("error"):
        raise RawStatError(tr("Misura non riuscita ({name}): {err}", name=Path(path).name, err=data["error"]))
    return data


async def ptc(flats: list, darks: list, timeout_s: float = 120) -> dict:
    """Analisi del sensore da due flat e due dark con le stesse impostazioni (fs-rawstat --ptc, vedi rawstat.cpp):
    guadagno, rumore di lettura, pieno pozzetto, gamma dinamica."""
    exe = tool_path()
    if exe is None:
        raise RawStatError(tr("Strumento di misura fs-rawstat mancante: python3 tools/rawstat/build.py"))
    if len(flats) < 2 or len(darks) < 2:
        raise RawStatError(tr("Servono due flat e due dark"))
    proc = await asyncio.create_subprocess_exec(str(exe), "--ptc", *[str(f) for f in (*flats[:2], *darks[:2])],
                                                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout_s)
    except asyncio.TimeoutError as exc:
        proc.kill()
        raise RawStatError(tr("Misura troppo lenta: {name}", name=Path(flats[0]).name)) from exc
    try:
        data = json.loads(out.decode("utf-8", "replace").strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise RawStatError(tr("Misura non riuscita: {name}", name=Path(flats[0]).name)) from exc
    if data.get("error"):
        raise RawStatError(tr("Misura non riuscita ({name}): {err}", name=Path(flats[0]).name, err=data["error"]))
    return data


async def focus(path: str | Path, roi, source: str = "auto", timeout_s: float = 30) -> dict:
    """Nitidezza di un'area (frazioni x0, y0, x1, y1 dell'immagine vista): {"focus", "mean", "source", "roi_px",
    "image"}. source: auto (anteprima incorporata nei RAW, o il RAW a metà risoluzione se l'area è troppo piccola
    nell'anteprima), preview, raw. Vedi rawstat.cpp, focus_file."""
    exe = tool_path()
    if exe is None:
        raise RawStatError(tr("Strumento di misura fs-rawstat mancante: python3 tools/rawstat/build.py"))
    args = [str(exe), "--focus", *(f"{float(v):.6f}" for v in roi)]
    if source != "auto":
        args += ["--source", source]
    proc = await asyncio.create_subprocess_exec(*args, str(path), stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE)
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout_s)
    except asyncio.TimeoutError as exc:
        proc.kill()
        raise RawStatError(tr("Misura troppo lenta: {name}", name=Path(path).name)) from exc
    try:
        data = json.loads(out.decode("utf-8", "replace").strip().splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise RawStatError(tr("Misura non riuscita: {name}", name=Path(path).name)) from exc
    if data.get("error"):
        raise RawStatError(tr("Misura non riuscita ({name}): {err}", name=Path(path).name, err=data["error"]))
    return data


RAW_EXT = (".nef", ".nrw", ".cr2", ".cr3", ".crw", ".arw", ".srf", ".sr2", ".raf", ".orf", ".rw2", ".dng",
           ".pef", ".srw", ".3fr", ".iiq", ".x3f", ".erf", ".mef", ".mos", ".kdc", ".rwl")


def pick_file(files: list[str]) -> str | None:
    """Il file da misurare: il RAW se c'è (dati lineari del sensore), altrimenti il primo."""
    return next((f for f in files if f.lower().endswith(RAW_EXT)), files[0] if files else None)


def level(stats: dict, stat: str) -> float:
    """Livello usato per l'esposizione: "mean" = media del canale più chiaro (flat), "highlights" = 99,5°
    percentile del canale più chiaro (light: le luci non devono bruciare)."""
    key = "p99_5" if stat == "highlights" else "mean"
    vals = [c[key] for c in (stats.get("channels") or {}).values() if c]
    if not vals:
        raise RawStatError(tr("Misura vuota"))
    return max(vals)


def summary(stats: dict) -> dict:
    """Valori essenziali da salvare per ogni fotogramma."""
    ch = stats.get("channels") or {}
    out = {"mean_pct": {k: round(v["mean"], 3) for k, v in ch.items() if v},
           "p99_5_pct": round(level(stats, "highlights"), 3),
           "burnt_pct": (stats.get("all") or {}).get("burnt_pct"),
           "linear": stats.get("linear")}
    if stats.get("center_mean") is not None:
        out["center_mean_pct"] = round(stats["center_mean"], 3)
    return out
