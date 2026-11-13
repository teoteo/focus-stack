"""Versioni e aggiornamenti: dell'app (release su GitHub) e del firmware incluso nell'app.

L'app pubblicata è un unico "Focus Stack.app" che contiene Python, il codice e il firmware.
All'avvio (e poi ogni 6 ore) si legge l'ultima release di GitHub; se è più recente la pagina
propone l'aggiornamento. L'installazione scarica lo zip della release, lo estrae accanto
all'app attuale, chiude l'app e la sostituisce con uno script esterno che poi la riapre.
I file scaricati dall'app stessa non ricevono la "quarantena" di macOS, quindi l'avviso di
sicurezza compare solo alla prima installazione.
"""
from __future__ import annotations

import hashlib
import http.client
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path

from .i18n import tr
from .settings import CONFIG_DIR

APP_ROOT = Path(__file__).resolve().parent.parent
GITHUB_REPO = "teoteo/focus-stack"
ASSET_RE = re.compile(r"^FocusStack-.*\.zip$")
CHECK_INTERVAL = 6 * 3600
RETRY_INTERVAL = 5 * 60      # dopo un controllo non riuscito (per esempio rete non ancora pronta all'avvio)
INSTALL_TIMEOUT = 5 * 60     # se dopo tanto l'app non si è ancora chiusa, l'installazione non è andata
# versione che si sta installando: alla riapertura dice se lo scambio dell'app è riuscito
PENDING_FILE = CONFIG_DIR / "aggiornamento-in-corso.json"
DOWNLOAD_ATTEMPTS = 4        # se la connessione cade, si riprende da dove si era arrivati
DOWNLOAD_TIMEOUT = 30        # secondi senza ricevere dati = connessione persa

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
def bundled_firmware(board: str = "myfp2") -> dict | None:
    """{"build": int, "hex": Path} del firmware incluso per la scheda indicata, oppure None.

    manifest.json: "hex" è il firmware per la scheda myFocuserPro2 (lo leggono anche le versioni
    dell'app precedenti); "boards" elenca i file per le altre schede, per esempio "ardufocus".
    """
    try:
        manifest = json.loads((FIRMWARE_DIR / "manifest.json").read_text())
        name = manifest["hex"] if board == "myfp2" else manifest.get("boards", {})[board]
        hex_path = FIRMWARE_DIR / name
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
        self.asset_size: int | None = None     # dimensione e sha256 dello zip dichiarati da GitHub:
        self.asset_sha256: str | None = None   # servono a riconoscere un download incompleto o rovinato
        self.checked_at = 0.0
        self.error = ""
        self.installing = False
        self.installing_since = 0.0           # quando è partito lo script che sostituisce l'app (0 = non ancora)
        self.install_error = ""
        self.progress: float | None = None    # avanzamento dello scaricamento (0–1), None se non noto
        self._check_pending()

    def _check_pending(self) -> None:
        """Dopo un riavvio per aggiornamento: se la versione non è cambiata lo script non è riuscito
        a sostituire l'app (per esempio permessi della cartella): lo si dice e si ripropone."""
        try:
            target = json.loads(PENDING_FILE.read_text()).get("version", "")
        except (OSError, ValueError):
            return
        try:
            PENDING_FILE.unlink()
        except OSError:
            pass
        current = app_version()
        if target and current != "sviluppo" and parse_version(current) < parse_version(target):
            self.install_error = tr("L'installazione della versione {version} non si è conclusa: riprova, oppure "
                                    "scarica l'app da GitHub e sostituiscila in Applicazioni", version=target)
            self.log("⚠ " + self.install_error)
        elif target:
            self.log(tr("Aggiornamento a Focus Stack {version} completato", version=current))

    def describe(self) -> dict:
        current = app_version()
        # installazione avviata ma l'app è ancora qui: lo script non è riuscito a sostituirla.
        # Si torna a proporre l'aggiornamento invece di restare "in corso" per sempre.
        # (il tempo conta solo dallo scambio: lo scaricamento su una linea lenta può durare di più)
        if self.installing and self.installing_since and time.time() - self.installing_since > INSTALL_TIMEOUT:
            self.installing = False
            self.install_error = tr("L'installazione della versione {version} non si è conclusa: riprova, oppure "
                                    "scarica l'app da GitHub e sostituiscila in Applicazioni", version=self.latest)
            self.log("⚠ " + self.install_error)
        available = bool(self.latest and self.asset_url and current != "sviluppo"
                         and parse_version(self.latest) > parse_version(current))
        return {"version": current, "latest": self.latest, "available": available,
                "can_install": available and app_bundle() is not None, "notes": self.notes[:2000],
                "installing": self.installing, "error": self.error, "install_error": self.install_error,
                "progress": self.progress if self.installing else None}

    def check_blocking(self) -> None:
        req = urllib.request.Request(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                                     headers={"Accept": "application/vnd.github+json",
                                              "User-Agent": "FocusStack"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                rel = json.load(r)
        except Exception as exc:  # noqa: BLE001 - senza rete si riprova più tardi
            self.error = tr("Controllo aggiornamenti non riuscito: {exc}", exc=exc)
            self.checked_at = time.time()
            return
        self.error = ""
        self.checked_at = time.time()
        self.latest = str(rel.get("tag_name", "")).lstrip("v") or None
        self.notes = rel.get("body") or ""
        asset = next((a for a in rel.get("assets", []) if ASSET_RE.match(a.get("name", ""))), None)
        self.asset_url = asset["browser_download_url"] if asset else None
        self.asset_size = asset.get("size") if asset else None
        digest = (asset or {}).get("digest") or ""
        self.asset_sha256 = digest.split(":", 1)[1].lower() if digest.startswith("sha256:") else None

    def due(self) -> bool:
        return time.time() - self.checked_at > (RETRY_INTERVAL if self.error else CHECK_INTERVAL)

    def install_blocking(self) -> None:
        """Scarica e prepara la nuova versione, poi avvia lo script che sostituisce l'app."""
        bundle = app_bundle()
        if not bundle:
            raise RuntimeError(tr("Aggiornamento possibile solo dall'app Focus Stack installata"))
        if not self.asset_url:
            raise RuntimeError(tr("Nessun aggiornamento disponibile"))
        parent = bundle.parent
        if not os.access(parent, os.W_OK):
            raise RuntimeError(tr("Non ho i permessi per scrivere in {path}: sposta Focus Stack "
                                  "in Applicazioni con un account amministratore", path=parent))
        self.installing = True
        self.installing_since = 0.0
        self.install_error = ""
        self.progress = 0.0
        work = Path(tempfile.mkdtemp(prefix="FocusStack-update-"))
        staged = parent / f".{bundle.stem}-aggiornamento.app"
        launched = False
        try:
            zip_path = work / "FocusStack.zip"
            self._download(zip_path)
            try:
                subprocess.run(["ditto", "-x", "-k", str(zip_path), str(work / "x")], check=True,
                               capture_output=True)
            except subprocess.CalledProcessError:
                raise RuntimeError(tr("Il file scaricato è incompleto o rovinato: riprova")) from None
            new_app = next((work / "x").glob("*.app"), None)
            if not new_app or not (new_app / "Contents" / "Info.plist").exists():
                raise RuntimeError(tr("Il pacchetto scaricato non contiene l'app"))
            # copia accanto a quella attuale: lo scambio finale è un semplice rename
            shutil.rmtree(staged, ignore_errors=True)
            subprocess.run(["ditto", str(new_app), str(staged)], check=True, capture_output=True)
            try:
                CONFIG_DIR.mkdir(parents=True, exist_ok=True)
                PENDING_FILE.write_text(json.dumps({"version": self.latest, "from": app_version()}))
            except OSError:
                pass
            script = work / "installa.sh"
            script.write_text(_INSTALL_SCRIPT)
            subprocess.Popen(["/bin/zsh", str(script), str(bundle), str(staged), str(work)],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
            launched = True
            self.installing_since = time.time()
            self.progress = None
            self.log(tr("Installazione della versione {version}: Focus Stack si riavvia…", version=self.latest))
        except Exception as exc:
            self.installing = False
            self.progress = None
            self.install_error = str(exc)
            raise
        finally:
            # se non si arriva allo scambio, l'app installata resta com'è e non restano file a metà
            if not launched:
                shutil.rmtree(work, ignore_errors=True)
                shutil.rmtree(staged, ignore_errors=True)

    def _download(self, dest: Path) -> None:
        """Scarica lo zip della release. Se la connessione cade riprova e riprende da dove era
        arrivato (richiesta Range); alla fine controlla dimensione e sha256 dichiarati da GitHub."""
        self.log(tr("Scaricamento della versione {version}…", version=self.latest))
        last_exc: Exception | None = None
        for attempt in range(1, DOWNLOAD_ATTEMPTS + 1):
            have = dest.stat().st_size if dest.exists() else 0
            headers = {"User-Agent": "FocusStack"}
            if have:
                headers["Range"] = f"bytes={have}-"
            try:
                req = urllib.request.Request(self.asset_url, headers=headers)
                with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as r:
                    resumed = have and r.status == 206
                    expected = r.headers.get("Content-Length")
                    expected = int(expected) if expected and expected.isdigit() else None
                    got = 0
                    with open(dest, "ab" if resumed else "wb") as out:
                        while chunk := r.read(1 << 16):
                            out.write(chunk)
                            got += len(chunk)
                            if self.asset_size:
                                self.progress = min(1.0, ((have if resumed else 0) + got) / self.asset_size)
                    if expected is not None and got < expected:
                        raise http.client.IncompleteRead(b"", expected - got)
                size = dest.stat().st_size
                if self.asset_size and size != self.asset_size:
                    raise http.client.IncompleteRead(b"", max(0, self.asset_size - size))
                break
            except (OSError, http.client.HTTPException) as exc:
                last_exc = exc
                if isinstance(exc, urllib.error.HTTPError) and exc.code == 416:
                    dest.unlink(missing_ok=True)   # file parziale non valido: si ricomincia
                if attempt < DOWNLOAD_ATTEMPTS:
                    self.log(tr("Scaricamento interrotto ({exc}): nuovo tentativo ({n} di {tot})…",
                                exc=_short(exc), n=attempt + 1, tot=DOWNLOAD_ATTEMPTS))
                    time.sleep(3 * attempt)
        else:
            raise RuntimeError(tr("Scaricamento interrotto: la connessione a internet si è persa ({exc}). "
                                  "Riprova quando la rete è stabile: Focus Stack non è stata modificata",
                                  exc=_short(last_exc)))
        if self.asset_sha256:
            h = hashlib.sha256()
            with open(dest, "rb") as f:
                while chunk := f.read(1 << 20):
                    h.update(chunk)
            if h.hexdigest() != self.asset_sha256:
                dest.unlink(missing_ok=True)
                raise RuntimeError(tr("Il file scaricato è incompleto o rovinato: riprova"))


def _short(exc: Exception | None) -> str:
    """Errore di rete in breve, per il registro e per la pagina."""
    if isinstance(exc, urllib.error.URLError) and not isinstance(exc, urllib.error.HTTPError):
        exc = exc.reason if isinstance(exc.reason, Exception) else exc
    if isinstance(exc, http.client.IncompleteRead):
        return tr("file incompleto")
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return tr("nessuna risposta")
    return getattr(exc, "strerror", None) or str(exc)


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
