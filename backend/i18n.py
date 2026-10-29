"""Lingua dell'interfaccia e dei messaggi del server.

Le chiavi sono i testi italiani, con segnaposto {nome}; le traduzioni stanno in
web/lang/<lingua>-*.json ({chiave italiana: traduzione}), condivise con la pagina. L'italiano
non ha file: la chiave è già il testo. "auto" segue la lingua di macOS.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

SUPPORTED = ("it", "en", "fr", "de", "es")
FALLBACK = "en"
LANG_DIR = Path(__file__).resolve().parent.parent / "web" / "lang"

_current = "it"
_cache: dict[str, tuple[tuple, dict]] = {}


def system_language() -> str:
    """Prima lingua preferita di macOS (Impostazioni › Generali › Lingua e zona), se supportata."""
    try:
        out = subprocess.run(["defaults", "read", "-g", "AppleLanguages"], capture_output=True,
                             text=True, timeout=2).stdout
        # formato: ( "it-IT", "en-IT" )
        first = next((ln.strip().strip('",') for ln in out.splitlines() if ln.strip().strip('",()')), "")
        code = first[:2].lower()
        return code if code in SUPPORTED else FALLBACK
    except Exception:  # noqa: BLE001
        return FALLBACK


def resolve(setting: str | None) -> str:
    return setting if setting in SUPPORTED else system_language()


def set_language(code: str) -> None:
    global _current
    _current = code if code in SUPPORTED else FALLBACK


def current() -> str:
    return _current


def strings(code: str) -> dict:
    """Tutte le traduzioni di una lingua (file web/lang/<code>-*.json uniti), rilette se cambiano."""
    if code == "it":
        return {}
    files = sorted(LANG_DIR.glob(f"{code}-*.json"))
    sig = tuple((p.name, p.stat().st_mtime_ns) for p in files)
    cached = _cache.get(code)
    if cached and cached[0] == sig:
        return cached[1]
    merged: dict = {}
    for p in files:
        try:
            merged.update(json.loads(p.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            pass
    _cache[code] = (sig, merged)
    return merged


def tr(key: str, **kw) -> str:
    """Testo nella lingua corrente; i segnaposto {nome} si riempiono con gli argomenti."""
    text = strings(_current).get(key, key)
    if kw:
        try:
            return text.format_map(kw)
        except (KeyError, ValueError, IndexError):
            return key.format_map(kw)
    return text
