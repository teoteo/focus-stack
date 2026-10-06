"""Versioni e aggiornamenti: dell'app (release su GitHub) e del firmware incluso nell'app.

L'app pubblicata è un unico "Focus Stack.app" che contiene Python, il codice e il firmware.
All'avvio (e poi ogni 6 ore) si legge l'ultima release di GitHub; se è più recente la pagina
propone l'aggiornamento. L'installazione scarica lo zip della release, lo estrae accanto
all'app attuale, chiude l'app e la sostituisce con uno script esterno che poi la riapre.
I file scaricati dall'app stessa non ricevono la "quarantena" di macOS, quindi l'avviso di
sicurezza compare solo alla prima installazione.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parent.parent
GITHUB_REPO = "teoteo/focus-stack"
ASSET_RE = re.compile(r"^FocusStack-.*\.zip$")
CHECK_INTERVAL = 6 * 3600

# Firmware incluso nell'app (preparato da build_release.sh); nel progetto di sviluppo
# compare dopo una build, altrimenti l'aggiornamento del firmware non è disponibile.
FIRMWARE_DIR = APP_ROOT / "firmware" / "build"


def app_version() -> str:
    try:
        return (APP_ROOT / "VERSION").read_text().strip()
    except OSError:
        return "sviluppo"


def app_bundle() -> Path | None:
    """Percorso di "Focus Stack.app" se il server è stato avviato dall'app pubblicata."""
    p = os.environ.get("FOCUSSTACK_APP")
    return Path(p) if p and Path(p, "Contents").is_dir() else None


def parse_version(v: str) -> tuple[int, ...]:
    nums = re.findall(r"\d+", v)
    return tuple(int(n) for n in nums) if nums else (0,)


# ---------------- firmware ----------------
def bundled_firmware() -> dict | None:
    """{"build": int, "hex": Path} del firmware incluso, oppure None."""
    try:
        manifest = json.loads((FIRMWARE_DIR / "manifest.json").read_text())
        hex_path = FIRMWARE_DIR / manifest["hex"]
        return {"build": int(manifest["build"]), "hex": hex_path} if hex_path.exists() else None
    except (OSError, ValueError, KeyError):
        return None


# ---------------- aggiornamenti dell'app ----------------
class AppUpdater:
    def __init__(self, log):
        self.log = log
        self.latest: str | None = None      # versione dell'ultima release
        self.notes: str = ""
        self.asset_url: str | None = None
        self.checked_at = 0.0
        self.error = ""
        self.installing = False

    def describe(self) -> dict:
        current = app_version()
        available = bool(self.latest and self.asset_url and current != "sviluppo"
                         and parse_version(self.latest) > parse_version(current))
        return {"version": current, "latest": self.latest, "available": available,
                "can_install": available and app_bundle() is not None, "notes": self.notes[:2000],
                "installing": self.installing, "error": self.error}

    def check_blocking(self) -> None:
        req = urllib.request.Request(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                                     headers={"Accept": "application/vnd.github+json",
                                              "User-Agent": "FocusStack"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                rel = json.load(r)
        except Exception as exc:  # noqa: BLE001 - senza rete si riprova più tardi
            self.error = f"Controllo aggiornamenti non riuscito: {exc}"
            self.checked_at = time.time()
            return
        self.error = ""
        self.checked_at = time.time()
        self.latest = str(rel.get("tag_name", "")).lstrip("v") or None
        self.notes = rel.get("body") or ""
        self.asset_url = next((a["browser_download_url"] for a in rel.get("assets", [])
                               if ASSET_RE.match(a.get("name", ""))), None)

    def due(self) -> bool:
        return time.time() - self.checked_at > CHECK_INTERVAL

    def install_blocking(self) -> None:
        """Scarica e prepara la nuova versione, poi avvia lo script che sostituisce l'app."""
        bundle = app_bundle()
        if not bundle:
            raise RuntimeError("Aggiornamento possibile solo dall'app Focus Stack installata")
        if not self.asset_url:
            raise RuntimeError("Nessun aggiornamento disponibile")
        parent = bundle.parent
        if not os.access(parent, os.W_OK):
            raise RuntimeError(f"Non ho i permessi per scrivere in {parent}: sposta Focus Stack "
                               "in Applicazioni con un account amministratore")
        self.installing = True
        try:
            work = Path(tempfile.mkdtemp(prefix="FocusStack-update-"))
            zip_path = work / "FocusStack.zip"
            self.log(f"Scaricamento della versione {self.latest}…")
            req = urllib.request.Request(self.asset_url, headers={"User-Agent": "FocusStack"})
            with urllib.request.urlopen(req, timeout=60) as r, open(zip_path, "wb") as out:
                shutil.copyfileobj(r, out)
            subprocess.run(["ditto", "-x", "-k", str(zip_path), str(work / "x")], check=True)
            new_app = next((work / "x").glob("*.app"), None)
            if not new_app or not (new_app / "Contents" / "Info.plist").exists():
                raise RuntimeError("Il pacchetto scaricato non contiene l'app")
            # copia accanto a quella attuale: lo scambio finale è un semplice rename
            staged = parent / f".{bundle.stem}-aggiornamento.app"
            shutil.rmtree(staged, ignore_errors=True)
            subprocess.run(["ditto", str(new_app), str(staged)], check=True)
            script = work / "installa.sh"
            script.write_text(_INSTALL_SCRIPT)
            subprocess.Popen(["/bin/zsh", str(script), str(bundle), str(staged), str(work)],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
            self.log(f"Installazione della versione {self.latest}: Focus Stack si riavvia…")
        except Exception:
            self.installing = False
            raise


# Eseguito fuori dall'app: la chiude (l'app spegne il server), scambia le cartelle e la riapre.
_INSTALL_SCRIPT = r"""#!/bin/zsh
OLD="$1"; NEW="$2"; WORK="$3"
osascript -e 'tell application id "local.focusstack.app" to quit' >/dev/null 2>&1
# attende che app e server siano terminati. Si cercano solo i processi il cui comando INIZIA
# con un eseguibile del pacchetto: un Terminale o uno script che nomina il percorso non conta.
APPRE="^${OLD//./\\.}/Contents/(MacOS/applet|Resources/python-[a-z0-9_]+/bin/python3)"
for i in {1..120}; do
  pgrep -f "$APPRE" >/dev/null || break
  sleep 0.5
done
pkill -f "$APPRE" 2>/dev/null
sleep 1
BACKUP="${OLD%.app}-precedente.app"
rm -rf "$BACKUP"
if mv "$OLD" "$BACKUP" && mv "$NEW" "$OLD"; then
  rm -rf "$BACKUP"
else
  [ -d "$OLD" ] || mv "$BACKUP" "$OLD"
fi
rm -rf "$WORK"
open "$OLD"
"""
