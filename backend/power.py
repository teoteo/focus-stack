"""Tiene sveglio il Mac durante una pila o una serie di calibrazione.

Con le impostazioni di risparmio energia macOS manda il sistema in stop qualche minuto dopo l'ultimo tocco
di tastiera o trackpad, anche se un programma sta lavorando: l'USB viene sospesa, la fotocamera sparisce e
la sequenza si ferma (successo il 2026-11-17 allo scatto 102 di 191). `caffeinate -i -s` tiene la stessa
richiesta di un lettore video: lo schermo può spegnersi, il sistema resta sveglio. `-w <pid>` lo lega al
server, quindi non sopravvive a Focus Stack nemmeno se il server si chiude male.

Chiudere il coperchio di un portatile senza monitor esterno lo manda comunque in stop: non si può evitare.
"""
from __future__ import annotations

import os
import subprocess
import threading

_lock = threading.Lock()
_holders = 0
_proc: subprocess.Popen | None = None


def hold() -> str:
    """Inizia a tenere sveglio il Mac (conteggiato: ogni hold() vuole un release()). Restituisce "" o l'errore."""
    global _holders, _proc
    with _lock:
        _holders += 1
        if _proc is not None and _proc.poll() is None:
            return ""
        try:
            _proc = subprocess.Popen(["/usr/bin/caffeinate", "-i", "-s", "-w", str(os.getpid())],
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return ""
        except OSError as exc:
            _proc = None
            return str(exc)


def release() -> None:
    """Chiude un hold(); il Mac può tornare in stop quando nessuno lo tiene più sveglio."""
    global _holders, _proc
    with _lock:
        _holders = max(0, _holders - 1)
        if _holders or _proc is None:
            return
        proc, _proc = _proc, None
    try:
        proc.terminate()
        proc.wait(timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        try:
            proc.kill()
        except OSError:
            pass


def holding() -> bool:
    return _proc is not None and _proc.poll() is None
