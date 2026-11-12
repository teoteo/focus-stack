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
        "optics_profile": "",      # profilo di ottica/filtro usato dalla sequenza ("" = nessun filtro)
    },
    # Profili di ottica, filtro e illuminazione (tab Ottica), scritti nel manifesto sequence.json.
    # nome -> {objective, objective_magnification, intermediate {name, factor} (cambio d'ingrandimento,
    #          es. Optovar), relay {name, factor} (adattatore / oculare di proiezione), na,
    #          immersion (air|water|oil|glycerol|silicone),
    #          sensor_pixel_um, pixel_size_um (misurato, ha la precedenza), dof_overlap,
    #          filter_mode (unknown|none|filter), filter {name, type, center_nm, bandwidth_nm, edge_nm},
    #          illumination {type, level_percent}, notes}. None/"" = non indicato.
    "optics_profiles": {},
    "presets": {},
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


def save(data: dict) -> None:
    with _lock:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(CONFIG_FILE)
