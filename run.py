"""Avvia il server locale e apre l'interfaccia in Safari."""
import argparse
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request

import uvicorn

parser = argparse.ArgumentParser(description="Focus Stack – server locale")
parser.add_argument("--port", type=int, default=8765)
parser.add_argument("--no-browser", action="store_true")
args = parser.parse_args()
URL = f"http://localhost:{args.port}/"


def port_busy() -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", args.port)) == 0


def stop_previous_instance() -> None:
    """Se Focus Stack è già in esecuzione (magari con codice vecchio) lo chiude, così riparte aggiornato."""
    if not port_busy():
        return
    print("Focus Stack è già in esecuzione: lo riavvio con la versione aggiornata…")
    pid = None
    try:
        req = urllib.request.Request(URL + "api/shutdown", data=b"{}", method="POST",
                                     headers={"X-FocusStack": "1", "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            pid = json.loads(resp.read() or b"{}").get("pid")
    except (OSError, ValueError):
        pass
    for _ in range(50):
        if not port_busy():
            break
        time.sleep(0.2)
    else:
        sys.exit(f"La porta {args.port} è occupata da un altro programma (o da una versione vecchia di Focus Stack).\n"
                 "Chiudi le altre finestre del Terminale di Focus Stack e riprova.")
    # La porta d'ascolto si libera subito, ma il processo vecchio chiude focheggiatore e fotocamera solo alla fine:
    # finché non è uscito la porta seriale è ancora sua (il nuovo server non riuscirebbe a collegarsi).
    for _ in range(60):
        if not pid or not process_alive(int(pid)):
            return
        time.sleep(0.2)


def process_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True
    return True


def open_when_ready():
    for _ in range(50):
        try:
            urllib.request.urlopen(URL + "api/state", timeout=0.5)
            subprocess.run(["open", "-a", "Safari", URL])
            return
        except OSError:
            time.sleep(0.2)


stop_previous_instance()
if not args.no_browser:
    threading.Thread(target=open_when_ready, daemon=True).start()
# Solo localhost: il controllo dell'hardware non viene esposto in rete.
# timeout_graceful_shutdown: senza limite lo spegnimento aspettava per sempre la fine dei flussi del live view
# (Safari li tiene aperti), con la porta del focheggiatore ancora occupata.
uvicorn.run("backend.main:api", host="127.0.0.1", port=args.port, log_level="warning", timeout_graceful_shutdown=3)
