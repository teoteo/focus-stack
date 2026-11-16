#!/usr/bin/env python3
"""Builds web/data/lenses-lensfun.json from the Lensfun lens database.

The Lensfun database (https://github.com/lensfun/lensfun, folder data/db) is licensed under
Creative Commons Attribution-Share Alike 3.0 (CC BY-SA 3.0). The JSON written here is a derived
database: it keeps the same licence and the attribution in its "license" and "source" keys, and is
distributed as a separate file (the app's code stays MIT).

Only interchangeable lenses are kept (compact cameras and action cams have a fixed lens). For each
lens: maker, model, mounts, focal range (mm), fastest f-number, crop factor of the calibration, and
"macro" when the name says so. Lensfun has no reproduction ratio: when the model name states it
(«1-5x», «2:1», «1:1» on a macro lens) it goes into "mag", otherwise the user types it.

Usage: python3 tools/lensfun_import.py <lensfun checkout>/data/db
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "web" / "data" / "lenses-lensfun.json"
SKIP_FILES = ("compact-", "actioncams")

FOCAL_RE = re.compile(r"(\d+(?:\.\d+)?)(?:\s*-\s*(\d+(?:\.\d+)?))?\s*mm", re.I)
# f/2.8, F2.8, f2.8-4, 1:2.8 (but not Leica's «1:2/50», which is f-number/focal)
APERTURE_RE = re.compile(r"(?:\b[fF]/?|(?<=mm)F)\s?(\d+(?:\.\d+)?)|\b1:(\d+(?:\.\d+)?)(?!\s*/)(?=[\s-]|$)")
LEICA_RE = re.compile(r"\b1:(\d+(?:\.\d+)?)/(\d+(?:\.\d+)?)")
# «1-5x» (Canon MP-E 65 mm); a bare «1.4x» is usually a teleconverter, not the reproduction ratio
MAG_X_RE = re.compile(r"\b\d+(?:\.\d+)?\s*-\s*(\d+(?:\.\d+)?)\s*x\b", re.I)
MAG_X_MACRO_RE = re.compile(r"\b(\d(?:\.\d)?)\s*x\s+(?:ultra|macro|super)", re.I)   # Laowa «2X Ultra-Macro»
MACRO_RE = re.compile(r"(?<![a-z])(macro|micro|makro)(?![a-z])")   # not «Summicron»
MAG_RATIO_RE = re.compile(r"\b(\d(?:\.\d)?):1\b")
MAG_AFTER_MACRO_RE = re.compile(r"\bmacro\s+1:(\d(?:\.\d)?)\b(?!\s*/)", re.I)   # «Macro 1:2» = 0.5×


def num(v: str | None) -> float | None:
    try:
        return float(v) if v is not None else None
    except ValueError:
        return None


def clean(x: float | None) -> float | int | None:
    if x is None:
        return None
    return int(x) if abs(x - round(x)) < 1e-9 else round(x, 2)


def parse_lens(el: ET.Element) -> dict | None:
    maker = (el.findtext("maker") or "").strip()
    model = next((m.text.strip() for m in el.findall("model") if not m.get("lang") and m.text), "")
    if not maker or not model:
        return None
    mounts = [m.text.strip() for m in el.findall("mount") if m.text]
    crop = num(el.findtext("cropfactor"))
    focal = el.find("focal")
    fmin = num(focal.get("min") or focal.get("value")) if focal is not None else None
    fmax = num(focal.get("max")) if focal is not None else None
    ap = el.find("aperture")
    amin = num(ap.get("min")) if ap is not None else None
    leica = LEICA_RE.search(model)
    if fmin is None:
        m = FOCAL_RE.search(model)
        if m:
            fmin, fmax = num(m.group(1)), num(m.group(2))
        elif leica:
            fmin = num(leica.group(2))
    # the f-number in the name is the lens's own; <aperture> belongs to a calibration
    if leica:
        amin = num(leica.group(1))
    else:
        m = APERTURE_RE.search(model)
        if m:
            amin = num(m.group(1) or m.group(2))
    if fmin is None:
        return None
    lens: dict = {"maker": maker, "model": model, "mounts": mounts, "focal": [clean(fmin), clean(fmax or fmin)]}
    if amin:
        lens["f"] = clean(amin)
    if crop:
        lens["crop"] = clean(crop)
    low = model.lower()
    if MACRO_RE.search(low):
        lens["macro"] = True
        m = MAG_X_RE.search(model)
        r = MAG_RATIO_RE.search(model)
        if not m:
            m = MAG_X_MACRO_RE.search(model)
        top = num(m.group(1)) if m else None
        if top and top <= 10:
            lens["mag"] = clean(top)
        elif r and not leica:
            lens["mag"] = clean(num(r.group(1)))
        # only when the name gives the f-number in another form (Pentax «Macro 1:4» is f/4)
        elif (h := MAG_AFTER_MACRO_RE.search(model)) and num(h.group(1)) and re.search(r"\b[fF]/?\d", model):
            lens["mag"] = clean(1 / num(h.group(1)))
    return lens


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    db = Path(sys.argv[1])
    lenses: dict[tuple, dict] = {}
    for xml in sorted(db.glob("*.xml")):
        if xml.name.startswith(SKIP_FILES):
            continue
        root = ET.parse(xml).getroot()
        for el in root.iter("lens"):
            lens = parse_lens(el)
            if not lens:
                continue
            key = (lens["maker"].lower(), lens["model"].lower())
            if key in lenses:   # the same lens calibrated for more mounts or crop factors
                for mt in lens["mounts"]:
                    if mt not in lenses[key]["mounts"]:
                        lenses[key]["mounts"].append(mt)
                continue
            lenses[key] = lens
    try:
        rev = subprocess.run(["git", "-C", str(db), "log", "-1", "--format=%H %cs"], capture_output=True,
                             text=True, check=True).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        rev = ["", ""]
    items = sorted(lenses.values(), key=lambda x: (x["maker"].lower(), x["model"].lower()))
    data = {
        "source": "Lensfun lens database, https://github.com/lensfun/lensfun (data/db)",
        "source_commit": rev[0], "source_date": rev[1] if len(rev) > 1 else "",
        "license": "CC BY-SA 3.0 (https://creativecommons.org/licenses/by-sa/3.0/)",
        "attribution": "Lens data © the Lensfun contributors, derived from the Lensfun database "
                       "(maker, model, mounts, focal length, f-number, crop factor; name parsing by Focus Stack).",
        "count": len(items),
        "lenses": items,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"{len(items)} lenses → {OUT} ({OUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
