"""Riepilogo leggibile della pila (sequence.txt), generato dal manifesto sequence.json."""
from __future__ import annotations

from datetime import datetime

from . import i18n
from .i18n import tr

# etichette tradotte (funzioni: la lingua può cambiare mentre il server è acceso)
def immersion_labels() -> dict:
    return {"air": tr("Aria (a secco)"), "water": tr("Acqua"), "oil": tr("Olio"), "glycerol": tr("Glicerina"),
            "silicone": tr("Silicone")}


def filter_labels() -> dict:
    return {"bandpass": tr("Passa banda"), "longpass": tr("Long pass"), "shortpass": tr("Short pass"),
            "neutral_density": tr("Neutro (ND)"), "polarizer": tr("Polarizzatore"), "other": tr("Altro")}


def capture_labels() -> dict:
    return {"download": tr("Scarica sul Mac"), "card": tr("Solo sulla scheda"), "trigger": tr("Solo trigger (veloce)")}


def num(value, decimals: int | None = None) -> str:
    """Numero con la virgola decimale (punto in inglese); senza decimali inutili se decimals è None."""
    if value is None:
        return "—"
    if decimals is None:
        text = f"{value:.4f}".rstrip("0").rstrip(".") if isinstance(value, float) else str(value)
    else:
        text = f"{value:.{decimals}f}"
    return text if i18n.current() == "en" else text.replace(".", ",")


def um2(value) -> str:
    """Lunghezza in µm con al massimo 2 decimali (36,2499 → 36,25; 10,00 → 10)."""
    return "—" if value is None else num(float(f"{value:.2f}"))


def when(iso: str | None) -> str:
    if not iso:
        return "—"
    dt = datetime.fromisoformat(iso)
    fmt = {"en": "%Y-%m-%d %H:%M:%S", "de": "%d.%m.%Y %H:%M:%S"}.get(i18n.current(), "%d/%m/%Y %H:%M:%S")
    return dt.strftime(fmt)


def duration(a: str | None, b: str | None) -> str:
    if not a or not b:
        return "—"
    s = int((datetime.fromisoformat(b) - datetime.fromisoformat(a)).total_seconds())
    h, m, sec = s // 3600, s % 3600 // 60, s % 60
    return f"{h} h {m:02d} min" if h else (f"{m} min {sec:02d} s" if m else f"{sec} s")


def render(m: dict) -> str:
    rail, seq, cam = m.get("rail", {}), m.get("sequence", {}), m.get("camera", {})
    frames = m.get("frames", [])
    shots = sum(len(f.get("exposures", [])) for f in frames)
    out: list[str] = []
    add = out.append

    def section(title: str) -> None:
        add("")
        add(title)
        add("-" * len(title))

    state = str(m.get("state") or "")
    states = {"running": tr("in corso"), "completed": tr("completata"), "interrupted": tr("interrotta"),
              "error": tr("errore")}
    add(f"{m.get('software', '')} · {tr('stato')}: {states.get(state, state)}")
    add(f"{tr('Inizio')}: {when(m.get('started'))}")
    if m.get("finished"):
        add(f"{tr('Fine')}: {when(m.get('finished'))} ({tr('durata')} {duration(m.get('started'), m.get('finished'))})")

    # ---- sequenza
    section(tr("SEQUENZA"))
    um = rail.get("um_per_step")
    k = seq.get("shots_per_position", 1)
    add(tr("Posizioni: {n} · scatti per posizione: {k} · scatti eseguiti: {done} su {tot}",
           n=seq.get("positions"), k=k, done=shots, tot=(seq.get("positions") or 0) * k))
    line = tr("Da {start} a {end} passi, passo {step} passi",
              start=seq.get("start_steps"), end=seq.get("end_steps"), step=seq.get("step_steps"))
    if um:
        line += " " + tr("= {step} µm · escursione {span} µm", step=um2(seq.get("step_um")), span=um2(seq.get("span_um")))
    add(line)
    if rail.get("approach"):
        add(tr("Verso del movimento: {dir}", dir=tr("verso l'obiettivo") if rail["approach"] == "toward_objective"
                                                else tr("allontanandosi dall'obiettivo")))
    if rail.get("backlash_overshoot_steps"):
        add(tr("Compensazione del gioco: {n} passi", n=rail["backlash_overshoot_steps"]))
    add(tr("Attesa dopo il movimento: {a} ms · pausa dopo lo scatto: {b} ms",
           a=rail.get("settle_ms"), b=rail.get("post_shot_ms")))
    if seq.get("mirror_delay_ms"):
        add(tr("Ritardo specchio: {ms} ms", ms=seq["mirror_delay_ms"]))
    if seq.get("bulb_s"):
        add(tr("Posa B: {s} s", s=num(seq["bulb_s"])))
    mode = str(seq.get("capture_mode") or "")
    add(tr("Modalità di scatto: {mode}", mode=capture_labels().get(mode, mode)))
    temps = [f["temperature_c"] for f in frames if f.get("temperature_c") is not None]
    if temps:
        lo, hi = num(min(temps), 1), num(max(temps), 1)
        add(tr("Temperatura: {lo}–{hi} °C", lo=lo, hi=hi) if lo != hi else tr("Temperatura: {t} °C", t=lo))
    add(tr("Asse z: 0 = primo fotogramma, valori positivi verso l'obiettivo"))

    # ---- focheggiatore
    section(tr("FOCHEGGIATORE"))
    add(" · ".join(x for x in (rail.get("model"), rail.get("firmware") and f"firmware {rail['firmware']}") if x))
    if um:
        src = tr("calcolata dalla meccanica") if rail.get("um_per_step_source") == "computed_from_mechanics" \
            else tr("inserita a mano")
        line = tr("Scala: {um} µm/passo ({src})", um=num(um), src=src)
        if rail.get("microstep"):
            line += f" · microstep {rail['microstep']}"
        add(line)
    else:
        add(tr("Scala µm/passo non configurata: posizioni solo in passi"))

    # ---- fotocamera
    section(tr("FOTOCAMERA"))
    if cam.get("model"):
        add(cam["model"])
    parts = [f"{label} {cam[key]}" for key, label in (("iso", "ISO"), ("shutterspeed", tr("Tempo di posa")),
                                                         ("aperture", tr("Diaframma")), ("imageformat", tr("Formato")))
             if cam.get(key)]
    if parts:
        add(" · ".join(parts))

    # ---- ottica
    section(tr("OTTICA"))
    optics = m.get("optics", {})
    if m.get("optics_profile"):
        add(tr("Profilo: {name}", name=m["optics_profile"]))
    else:
        add(tr("Nessun profilo ottico"))
    if optics.get("objective"):
        add(f"{tr('Obiettivo')}: {optics['objective']}")
    parts = []
    if optics.get("magnification"):
        parts.append(f"{tr('Ingrandimento sul sensore')} {num(optics['magnification'])}×")
    if optics.get("na"):
        parts.append(f"NA {num(optics['na'])}")
    if optics.get("immersion"):
        parts.append(f"{tr('Immersione')}: {immersion_labels().get(optics['immersion'], optics['immersion'])}")
    if parts:
        add(" · ".join(parts))
    if optics.get("pixel_size_um"):
        how = tr("misurato") if optics.get("pixel_size_source") == "calibrated" else \
            tr("pixel del sensore {px} µm ÷ ingrandimento", px=num(optics.get("sensor_pixel_um")))
        add(tr("Pixel sul campione: {v} µm ({how})", v=num(optics["pixel_size_um"]), how=how))
    if "filter" not in m:
        add(f"{tr('Filtro')}: {tr('non indicato')}")
    elif m["filter"] is None:
        add(f"{tr('Filtro')}: {tr('nessuno')}")
    else:
        f = m["filter"]
        ftype = str(f.get("type") or "")
        desc = [x for x in (f.get("name"), filter_labels().get(ftype, ftype)) if x]
        if f.get("center_nm"):
            desc.append(f"{num(f['center_nm'])}" + (f"/{num(f['bandwidth_nm'])}" if f.get("bandwidth_nm") else "") + " nm")
        if f.get("edge_nm"):
            desc.append(tr("taglio {nm} nm", nm=num(f["edge_nm"])))
        add(f"{tr('Filtro')}: " + ", ".join(desc))
    il = m.get("illumination", {})
    if il:
        add(f"{tr('Illuminazione')}: " + " · ".join(x for x in (il.get("type"), il.get("level_percent") is not None
                                                             and f"{num(il['level_percent'])} %") if x))
    if m.get("notes"):
        add(f"{tr('Note')}: {m['notes']}")

    # ---- file
    section(tr("FILE"))
    names = [n for f in frames for e in f.get("exposures", []) for n in e.get("files", [])]
    if names:
        add(names[0] if len(names) == 1 else f"{names[0]} … {names[-1]}  ({tr('{n} file', n=len(names))})")
    elif shots:
        add(tr("Le immagini sono sulla scheda della fotocamera, nell'ordine di scatto"))
    add(tr("Dati completi per il software di fusione: sequence.json"))
    return "\n".join(out) + "\n"
