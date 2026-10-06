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
    "sequence": {
        "start": 0,
        "end": 1000,
        "step": 50,
        "settle_ms": 1500,
        "post_shot_ms": 500,
        "backlash": 0,
        "return_to_start": True,
        "capture_mode": "download",
        "session_name": "stack",
    },
    "presets": {},
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
    return data


def save(data: dict) -> None:
    with _lock:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        tmp = CONFIG_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(CONFIG_FILE)
