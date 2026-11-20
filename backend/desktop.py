"""Integrazione con il sistema: aprire cartelle, mostrare un file, scegliere una cartella.

Tutte le chiamate al sistema stanno qui, così il resto del backend non dipende da macOS.
Su macOS si usano `open` e AppleScript. Nell'app per Mac la scelta della cartella la fa la finestra
nativa (web/native.js → /api/output-root), quindi qui si arriva solo dal browser.
Le vie per Linux (xdg-open, zenity) sono pronte per un port futuro ma non sono ancora provate.
"""
from __future__ import annotations

import asyncio
import shutil
import subprocess
import sys
from pathlib import Path

from .i18n import tr

IS_MAC = sys.platform == "darwin"


def _spawn(args: list[str]) -> None:
    subprocess.Popen(args, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def open_path(path: str | Path) -> None:
    """Apre una cartella (o un file) con il programma predefinito: il Finder su macOS."""
    if IS_MAC:
        _spawn(["open", str(path)])
    elif shutil.which("xdg-open"):
        _spawn(["xdg-open", str(path)])
    else:
        raise RuntimeError(tr("Impossibile aprire {path}", path=path))


def reveal(path: str | Path) -> None:
    """Mostra un file selezionato nella sua cartella."""
    if IS_MAC:
        _spawn(["open", "-R", str(path)])
    else:
        open_path(Path(path).parent)


async def choose_folder(start: Path, prompt: str) -> str | None:
    """Finestra "Scegli cartella" aperta dal server. Restituisce il percorso, o None se l'utente annulla."""
    if IS_MAC:
        # il percorso iniziale passa come argomento (argv), non dentro il testo dello script
        args = ["osascript",
                "-e", "on run argv",
                "-e", "tell current application to activate",
                "-e", "set f to choose folder with prompt (item 2 of argv) default location (POSIX file (item 1 of argv))",
                "-e", "return POSIX path of f",
                "-e", "end run",
                str(start), prompt]
        cancelled = b"-128"
    elif shutil.which("zenity"):
        args = ["zenity", "--file-selection", "--directory", f"--title={prompt}", f"--filename={start}/"]
        cancelled = None          # zenity: codice d'uscita 1 senza messaggi
    else:
        raise RuntimeError(tr("Impossibile aprire la finestra di selezione: {err}", err="zenity"))
    proc = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    if proc.returncode != 0:
        if cancelled is None and proc.returncode == 1 and not err.strip():
            return None
        if cancelled is not None and cancelled in err:      # l'utente ha premuto Annulla
            return None
        raise RuntimeError(tr("Impossibile aprire la finestra di selezione: {err}", err=err.decode().strip()))
    return out.decode().strip().rstrip("/") or "/"
