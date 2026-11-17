"""Persistenza delle impostazioni (porta, calibrazione, preset di sequenza)."""
from __future__ import annotations

import json
import threading
from pathlib import Path

CONFIG_DIR = Path.home() / "Library" / "Application Support" / "MyFocuserStack"
CONFIG_FILE = CONFIG_DIR / "settings.json"

DEFAULTS: dict = {
    "focuser_port": "",
    "focuser_baud": 9600,
    "um_per_step": 1.0,
    # Fine corsa software (passi). None = usa il max del firmware.
    "limit_min": 0,
    "limit_max": None,
    # Verso in cui l'obiettivo si avvicina al campione: "decreasing" = passi decrescenti
    "toward_specimen": "decreasing",
    "mechanics": {
        "mode": "manual",          # manual = µm/passo inserito a mano, computed = calcolato
        "motor_steps_per_rev": 200,
        "gear_ratio": 1.0,         # giri motore per giro della manopola
        "um_per_knob_rev": 100.0,  # corsa della micrometrica per giro (µm)
    },
    "output_root": str(Path.home() / "Pictures" / "FocusStack"),
    # Pulsanti Allontana/Avvicina: ampiezze per decine da 1 a jog_max passi; jog_hold = tenendo
    # premuto il motore si muove senza fermarsi fino al rilascio
    "jog_max": 1000,
    "jog_hold": True,
    # movimento continuo a tratti: il motore non riceve mai più di tanti passi per comando, così anche
    # perdendo la comunicazione non va oltre (vedi focuser_hold)
    "hold_chunk_steps": 500,
    # bobine del motore accese durante la sequenza anche se il firmware le spegne a motore fermo
    # (con le bobine spente il carico può riportare indietro la slitta a ogni fermata)
    "coil_during_sequence": True,
    "sequence": {
        "start": 0,
        "end": 1000,
        "step": 50,
        "settle_ms": 1500,
        "post_shot_ms": 500,
        "mirror_delay_ms": 0,
        "backlash": 0,
        "return_to_start": True,
        "capture_mode": "download",
        "session_name": "stack",
        "shots_per_position": 1,
        "sound_on_end": True,      # suono sul Mac a fine sequenza
        "optics_profile": "",      # profilo di ottica/filtro usato dalla sequenza ("" = nessun filtro)
    },
    # Profili di ottica, filtro e illuminazione (tab Ottica), scritti nel manifesto sequence.json.
    # nome -> {objective, objective_magnification, intermediate {name, factor} (cambio d'ingrandimento,
    #          es. Optovar), relay {name, factor} (adattatore / oculare di proiezione), na,
    #          immersion (air|water|oil|glycerol|silicone),
    #          sensor_pixel_um, pixel_size_um (misurato, ha la precedenza), dof_overlap,
    #          filter_mode (unknown|none|filter), filter {name, type, center_nm, bandwidth_nm, edge_nm},
    #          illumination {type, level_percent}, notes}. None/"" = non indicato.
    #          kind (microscope|macro), macro {lens {maker, model, focal_mm, max_aperture, source},
    #          lens_magnification, f_number, extension_mm, closeup [{name, diopters}]} (vedi optics.py).
    "optics_profiles": {},
    # Obiettivi fotografici aggiunti dall'utente, cercati insieme al database Lensfun:
    # [{maker, model, focal_mm, max_aperture, max_magnification, mounts}]
    "custom_lenses": [],
    "presets": {},
    # frame di calibrazione (tab Calibrazione): ultimi valori usati
    "calibration": {"count": 16, "flat_target_pct": 50, "light_target_pct": 85, "light_stat": "highlights"},
    # pagina di sola lettura per seguire la sequenza dalla rete locale (smartphone): vedi remote.py
    "remote": {"enabled": False, "port": 8766, "token": ""},
    # lingua dell'interfaccia: "auto" = quella di macOS, oppure "it" / "en"
    "language": "auto",
}

_lock = threading.Lock()


def load() -> dict:
    data = json.loads(json.dumps(DEFAULTS))
    try:
        stored = json.loads(CONFIG_FILE.read_text())
        for k, v in stored.items():
            if isinstance(v, dict) and isinstance(data.get(k), dict):
                data[k].update(v)
            else:
                data[k] = v
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    migrate_optics_profiles(data.get("optics_profiles") or {})
    return data


def migrate_optics_profiles(profiles: dict) -> None:
    """Profili della 1.0.8: "magnification" era l'ingrandimento totale scritto a mano. Diventa quello
    dell'obiettivo con Optovar e adattatore a 1, così il totale resta uguale."""
    for p in profiles.values():
        if isinstance(p, dict) and "magnification" in p and "objective_magnification" not in p:
            p["objective_magnification"] = p.pop("magnification")
        if isinstance(p, dict):
            p.setdefault("intermediate", {"name": "", "factor": None})
            p.setdefault("relay", {"name": "", "factor": None})
            p.setdefault("kind", "microscope")   # profili fino alla 1.0.11: solo microscopio


def save(data: dict) -> None:
    with _lock:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(CONFIG_FILE)
