"""Avvia il server locale e apre l'interfaccia in Safari."""
import argparse
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
    try:
        req = urllib.request.Request(URL + "api/shutdown", data=b"{}", method="POST",
                                     headers={"X-FocusStack": "1", "Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=3)
    except OSError:
        pass
    for _ in range(50):
        if not port_busy():
            return
        time.sleep(0.2)
    sys.exit(f"La porta {args.port} è occupata da un altro programma (o da una versione vecchia di Focus Stack).\n"
             "Chiudi le altre finestre del Terminale di Focus Stack e riprova.")


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
uvicorn.run("backend.main:api", host="127.0.0.1", port=args.port, log_level="warning")
