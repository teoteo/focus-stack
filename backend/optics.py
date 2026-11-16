"""Ottica dei profili: ingrandimento sul sensore per microscopio e per macro fotografica.

Microscopio: obiettivo × cambio intermedio (Optovar) × adattatore / oculare di proiezione.

Macro (lente sottile, stime): l'obiettivo fotografico di focale f è a fuoco a un rapporto di
riproduzione m0 (0 = all'infinito, 1 = 1:1).
- Tubi di prolunga lunghi e mm allungano il tiraggio: m1 = m0 + e / f.
- Lenti addizionali (close-up) davanti all'obiettivo, potenze in diottrie che si sommano (P = ΣD / 1000
  per mm): con l'obiettivo a fuoco su una distanza u = f (1 + m1) / m1 la lente rende l'oggetto più
  vicino e l'ingrandimento diventa m = m1 + P · f · (1 + m1). Con m1 = 0 (infinito) è il noto m = f · D / 1000.
- Diaframma impostato N: diaframma effettivo N (1 + m1) (pupilla d'uscita = d'entrata) e apertura
  numerica equivalente lato soggetto NA = m / (2 N (1 + m1)), la stessa grandezza dei microscopi, usata
  per la profondità di campo.
"""
from __future__ import annotations


def _f(v) -> float | None:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return None
    return x if x > 0 else None


def lens_name(maker: str | None, model: str | None) -> str:
    """Marca + modello, senza ripetere la marca quando il modello la contiene già (Lensfun: «Nikon AF-S …»)."""
    maker, model = (maker or "").strip(), (model or "").strip()
    if maker and model.lower().startswith(maker.lower()):
        return model
    return " ".join(x for x in (maker, model) if x)


def macro_numbers(o: dict) -> dict:
    """Valori calcolati di un profilo macro: magnification, lens_side_magnification, effective_f_number, na.
    Mancano le chiavi che non si possono calcolare."""
    mc = o.get("macro") or {}
    lens = mc.get("lens") or {}
    focal = _f(lens.get("focal_mm"))
    m0 = mc.get("lens_magnification")
    m0 = float(m0) if isinstance(m0, (int, float)) and m0 >= 0 else None
    ext = _f(mc.get("extension_mm")) or 0.0
    power = sum(_f(c.get("diopters")) or 0.0 for c in (mc.get("closeup") or []) if isinstance(c, dict))
    out: dict = {}
    if m0 is None and not (ext or power):
        return out
    if (ext or power) and not focal:
        return out            # tubi e lenti addizionali dipendono dalla focale
    fl = focal or 0.0
    m1 = (m0 or 0.0) + (ext / fl if ext else 0.0)
    m = m1 + (power / 1000.0) * fl * (1 + m1) if power else m1
    if m <= 0:
        return out
    out["magnification"] = round(m, 4)
    out["lens_side_magnification"] = round(m1, 4)
    n = _f(mc.get("f_number"))
    if n:
        out["effective_f_number"] = round(n * (1 + m1), 2)
        out["na"] = round(m / (2 * n * (1 + m1)), 5)
    return out


def total_magnification(o: dict) -> float | None:
    """Ingrandimento sul sensore del profilo (microscopio o macro)."""
    if o.get("kind") == "macro":
        return macro_numbers(o).get("magnification")
    obj = o.get("objective_magnification")
    if not obj:
        return None
    total = float(obj)
    for key in ("intermediate", "relay"):
        total *= float((o.get(key) or {}).get("factor") or 1)
    return round(total, 4)


def manifest_optics(o: dict) -> dict:
    """Chiave "optics" del manifesto per un profilo (solo i valori indicati o calcolabili)."""
    optics: dict = {}
    total = total_magnification(o)
    if o.get("kind") == "macro":
        mc = o.get("macro") or {}
        lens = mc.get("lens") or {}
        optics["kind"] = "macro"
        name = lens_name(lens.get("maker"), lens.get("model"))
        data = {k: v for k, v in (("name", name), ("focal_length_mm", _f(lens.get("focal_mm"))),
                                   ("max_aperture", _f(lens.get("max_aperture"))),
                                   ("source", lens.get("source") or None)) if v}
        if data:
            optics["lens"] = data
        if isinstance(mc.get("lens_magnification"), (int, float)):
            optics["lens_magnification"] = mc["lens_magnification"]
        if _f(mc.get("extension_mm")):
            optics["extension_mm"] = _f(mc["extension_mm"])
        closeup = [{k: v for k, v in (("name", (c.get("name") or "").strip()), ("diopters", _f(c.get("diopters")))) if v}
                   for c in (mc.get("closeup") or []) if isinstance(c, dict) and _f(c.get("diopters"))]
        if closeup:
            optics["closeup_lenses"] = closeup
        if _f(mc.get("f_number")):
            optics["f_number"] = _f(mc["f_number"])
        calc = macro_numbers(o)
        if total:
            optics["magnification"] = total
            optics["magnification_source"] = "estimated_thin_lens"
        if calc.get("effective_f_number"):
            optics["effective_f_number"] = calc["effective_f_number"]
        if calc.get("na"):
            optics["na"] = calc["na"]
            optics["na_source"] = "f_number_and_magnification"
    else:
        optics["kind"] = "microscope"
        if o.get("objective"):
            optics["objective"] = o["objective"]
        if o.get("objective_magnification"):
            optics["objective_magnification"] = o["objective_magnification"]
        for key in ("intermediate", "relay"):   # solo se indicati: assenti = non si sa (o nessuno)
            part = o.get(key) or {}
            data = {k: v for k, v in (("name", part.get("name")), ("magnification", part.get("factor"))) if v}
            if data:
                optics[key] = data
        if total:
            optics["magnification"] = total
        if o.get("na"):
            optics["na"] = o["na"]
        if o.get("immersion"):
            optics["immersion"] = o["immersion"]
    if o.get("sensor_pixel_um"):
        optics["sensor_pixel_um"] = o["sensor_pixel_um"]
    if o.get("pixel_size_um"):
        optics["pixel_size_um"] = o["pixel_size_um"]
        optics["pixel_size_source"] = "calibrated"
    elif o.get("sensor_pixel_um") and total:
        optics["pixel_size_um"] = round(o["sensor_pixel_um"] / total, 5)
        optics["pixel_size_source"] = "sensor_pixel / magnification"
    return optics
