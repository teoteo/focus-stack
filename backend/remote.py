"""Pagina di sola lettura per seguire la sequenza da un altro dispositivo della rete locale (es. uno smartphone).

Il server principale ascolta solo su 127.0.0.1 perché comanda l'hardware. Questo è un secondo server,
su una porta separata e aperto alla rete locale, che espone soltanto:
  /           pagina con avanzamento e tempo rimanente
  /status     gli stessi dati in JSON
  /preview    anteprima piccola dell'ultimo scatto, generata solo quando viene chiesta
Ogni richiesta deve portare il codice del link (?k=…): chi è sulla stessa rete senza il link non vede nulla.
Non c'è nessuna richiesta che modifichi qualcosa.
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import os
import secrets
import socket
import subprocess
import time
from pathlib import Path
from typing import Awaitable, Callable

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response

from . import i18n
from .i18n import tr

DEFAULT_PORT = 8766
# solo per le prove: "127.0.0.1" evita di aprire la porta alla rete (e la richiesta del firewall di macOS)
BIND_HOST = os.environ.get("FOCUS_STACK_REMOTE_HOST", "0.0.0.0")
MOBILE_PX = 640          # lato lungo dell'anteprima per il telefono
MOBILE_QUALITY = 70


def new_token() -> str:
    return secrets.token_urlsafe(9)


def lan_address() -> str | None:
    """Indirizzo IPv4 del Mac sulla rete locale (quello della route predefinita).
    Il connect di un socket UDP non invia pacchetti: serve solo a far scegliere l'interfaccia al sistema."""
    with contextlib.suppress(OSError), socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("192.0.2.1", 9))   # indirizzo di documentazione (RFC 5737), mai raggiunto
        ip = s.getsockname()[0]
        if ip and not ip.startswith("127."):
            return ip
    return None


def qr_png(text: str, out: Path) -> bool:
    """Codice QR con il generatore incluso in macOS (CoreImage), senza librerie esterne.
    Un pixel per modulo: la pagina lo ingrandisce con image-rendering: pixelated."""
    script = """
ObjC.import('Cocoa'); ObjC.import('CoreImage');
function run(argv) {
  var f = $.CIFilter.filterWithName('CIQRCodeGenerator');
  f.setValueForKey($(argv[0]).dataUsingEncoding($.NSUTF8StringEncoding), 'inputMessage');
  f.setValueForKey($('M'), 'inputCorrectionLevel');
  var rep = $.NSBitmapImageRep.alloc.initWithCIImage(f.outputImage);
  var png = rep.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $());
  return png.writeToFileAtomically(argv[1], true) ? 'ok' : 'fail';
}"""
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        r = subprocess.run(["osascript", "-l", "JavaScript", "-e", script, text, str(out)],
                           capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0 and out.exists()


class _QuietServer(uvicorn.Server):
    """uvicorn senza gestione dei segnali: quella resta al server principale (Ctrl-C, spegnimento)."""

    @contextlib.contextmanager
    def capture_signals(self):
        yield


class RemoteServer:
    def __init__(self, status: Callable[[], dict], preview: Callable[[], Awaitable[Path | None]],
                 cache_dir: Path) -> None:
        self._status = status
        self._preview = preview
        self._cache = cache_dir
        self._server: _QuietServer | None = None
        self._task: asyncio.Task | None = None
        self.token = ""
        self.port = DEFAULT_PORT
        self.error = ""

    # ---------- ciclo di vita ----------
    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self, port: int, token: str) -> None:
        await self.stop()
        self.port, self.token, self.error = port, token, ""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((BIND_HOST, port))
        except OSError as exc:
            sock.close()
            self.error = tr("Porta {port} occupata: {exc}", port=port, exc=exc.strerror or exc)
            raise RuntimeError(self.error) from exc
        sock.listen(16)
        sock.setblocking(False)
        config = uvicorn.Config(self._build_app(), log_level="warning", lifespan="off", access_log=False)
        self._server = _QuietServer(config)
        self._task = asyncio.create_task(self._serve(self._server, sock))

    async def _serve(self, server: _QuietServer, sock: socket.socket) -> None:
        try:
            await server.serve(sockets=[sock])
        except (Exception, SystemExit) as exc:  # noqa: BLE001 - un errore qui non deve fermare l'app
            self.error = str(exc) or type(exc).__name__
        finally:
            sock.close()

    async def stop(self) -> None:
        server, task = self._server, self._task
        if server and task and not task.done():
            server.should_exit = True
            with contextlib.suppress(asyncio.TimeoutError, asyncio.CancelledError):
                await asyncio.wait_for(asyncio.shield(task), timeout=3)
        if task and not task.done():
            task.cancel()
        self._server = self._task = None

    def url(self) -> str | None:
        ip = lan_address()
        return f"http://{ip}:{self.port}/?k={self.token}" if ip and self.token else None

    def describe(self) -> dict:
        return {"running": self.running, "port": self.port, "url": self.url() if self.running else None,
                "error": self.error}

    # ---------- pagina ----------
    def _ok(self, request: Request) -> bool:
        return bool(self.token) and secrets.compare_digest(request.query_params.get("k", ""), self.token)

    def _build_app(self) -> FastAPI:
        app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
        denied = lambda: Response(tr("Link non valido: riaprilo dal Mac (Configurazione › Avanzamento da smartphone)"),  # noqa: E731
                                  status_code=403, media_type="text/plain; charset=utf-8")
        nostore = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}

        @app.get("/")
        async def page(request: Request):
            if not self._ok(request):
                return denied()
            return HTMLResponse(render_page(), headers=nostore)

        @app.get("/status")
        async def status(request: Request):
            if not self._ok(request):
                return denied()
            return JSONResponse({**self._status(), "now": time.time()}, headers=nostore)

        @app.get("/preview")
        async def preview(request: Request):
            if not self._ok(request):
                return denied()
            src = await self._preview()
            if src is None:
                return Response(status_code=404)
            out = await self._small(src)
            if out is None:
                return Response(status_code=415)
            # l'URL contiene la chiave dello scatto (?v=): la stessa immagine può restare in cache
            return FileResponse(out, media_type="image/jpeg",
                                headers={"Cache-Control": "private, max-age=3600", "Referrer-Policy": "no-referrer"})

        return app

    async def _small(self, src: Path) -> Path | None:
        """JPEG piccolo per il telefono, ricavato dall'anteprima già pronta; tenuto in cache."""
        out = self._cache / f"m-{src.stem}-{src.stat().st_mtime_ns}.jpg"
        if out.exists():
            return out
        self._cache.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".part.jpg")
        proc = await asyncio.create_subprocess_exec(
            "sips", "-s", "format", "jpeg", "-s", "formatOptions", str(MOBILE_QUALITY), "-Z", str(MOBILE_PX),
            str(src), "--out", str(tmp), stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
        await proc.wait()
        if proc.returncode != 0 or not tmp.exists():
            return None
        tmp.replace(out)
        return out


def render_page() -> str:
    """Pagina autonoma (niente file esterni), nella lingua dell'app."""
    labels = {
        "idle": tr("Nessuna sequenza in corso"), "running": tr("In corso"), "paused": tr("In pausa"),
        "stopping": tr("Arresto…"), "done": tr("Completata"), "error": tr("Errore"),
        "left": tr("restano ~{t}"), "end_at": tr("fine prevista alle {t}"),
        "offline": tr("Mac non raggiungibile: riprovo…"), "show": tr("Mostra l'ultimo scatto"),
        "refresh": tr("Aggiorna l'ultimo scatto"), "no_shot": tr("Ancora nessuno scatto"),
        "loading": tr("Preparo l'anteprima…"), "shot": tr("Scatto {i} · {t}"),
    }
    title = tr("Avanzamento")
    return PAGE.replace("__LANG__", i18n.current()).replace("__TITLE__", title).replace("__L__", json.dumps(labels, ensure_ascii=False)) \
        .replace("__READONLY__", tr("Solo lettura: i comandi restano sul Mac."))


PAGE = """<!doctype html>
<html lang="__LANG__"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="color-scheme" content="dark light">
<meta name="referrer" content="no-referrer">
<title>Focus Stack · __TITLE__</title>
<style>
:root { --bg:#14171c; --card:#1d2128; --line:#2c323c; --fg:#e8ebf0; --muted:#97a0ad; --accent:#5aa9ff; --ok:#4cc38a; --warn:#f0b44c; --bad:#ef6464; }
@media (prefers-color-scheme: light) { :root { --bg:#f3f5f8; --card:#fff; --line:#dde2e8; --fg:#1b2027; --muted:#5f6977; --accent:#1f74d6; } }
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:16px/1.4 -apple-system, BlinkMacSystemFont, sans-serif;
  padding: max(16px, env(safe-area-inset-top)) 16px max(24px, env(safe-area-inset-bottom)); }
main { max-width: 560px; margin: 0 auto; display: grid; gap: 14px; }
.card { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; }
h1 { font-size:15px; font-weight:600; margin:0 0 2px; color:var(--muted); }
#name { font-size:19px; font-weight:600; overflow-wrap:anywhere; }
#count { font-size:44px; font-weight:700; font-variant-numeric:tabular-nums; letter-spacing:-.5px; margin:10px 0 6px; }
.bar { height:10px; background:var(--line); border-radius:6px; overflow:hidden; }
#fill { height:100%; width:0; background:var(--accent); transition:width .6s; }
#eta { font-size:20px; font-weight:600; margin-top:10px; font-variant-numeric:tabular-nums; }
#end, #msg { color:var(--muted); margin-top:2px; }
.chip { display:inline-block; font-size:13px; padding:2px 10px; border-radius:999px; border:1px solid var(--line); color:var(--muted); float:right; }
.chip.running { color:var(--accent); border-color:var(--accent); } .chip.done { color:var(--ok); border-color:var(--ok); }
.chip.paused, .chip.stopping { color:var(--warn); border-color:var(--warn); } .chip.error { color:var(--bad); border-color:var(--bad); }
button { width:100%; font:inherit; font-weight:600; padding:12px; border-radius:10px; border:1px solid var(--line);
  background:var(--bg); color:var(--fg); }
#img { display:block; width:100%; border-radius:8px; margin-top:12px; background:#000; }
#cap { color:var(--muted); font-size:14px; margin-top:6px; }
#off { color:var(--warn); display:none; }
footer { color:var(--muted); font-size:13px; text-align:center; }
</style></head>
<body><main>
<div class="card">
  <span class="chip" id="chip"></span>
  <h1>Focus Stack</h1>
  <div id="name">—</div>
  <div id="count">— / —</div>
  <div class="bar"><div id="fill"></div></div>
  <div id="eta"></div>
  <div id="end"></div>
  <div id="msg"></div>
  <div id="off"></div>
</div>
<div class="card">
  <button id="btn"></button>
  <img id="img" alt="" hidden>
  <div id="cap"></div>
</div>
<footer>__READONLY__</footer>
</main>
<script>
const L = __L__;
const K = new URLSearchParams(location.search).get("k") || "";
const $ = (id) => document.getElementById(id);
const fmt = (s) => { s = Math.max(0, Math.round(s)); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), r = s % 60;
  return h ? `${h}h ${String(m).padStart(2, "0")}m` : m ? `${m}m ${String(r).padStart(2, "0")}s` : `${r}s`; };
const tr = (k, v) => L[k].replace(/\\{(\\w+)\\}/g, (_, n) => v[n]);
let last = null, shown = null;
$("btn").textContent = L.show;
async function poll() {
  try {
    const r = await fetch(`status?k=${encodeURIComponent(K)}`, { cache: "no-store" });
    if (!r.ok) throw new Error(r.status);
    const s = await r.json();
    $("off").style.display = "none";
    const run = ["running", "paused", "stopping"].includes(s.state);
    $("chip").textContent = L[s.state] || s.state; $("chip").className = "chip " + s.state;
    $("name").textContent = s.name || "—";
    $("count").textContent = s.total ? `${s.index} / ${s.total}` : "— / —";
    $("fill").style.width = s.total ? `${100 * s.index / s.total}%` : "0";
    const eta = run && s.eta_s != null ? s.eta_s : null;
    $("eta").textContent = eta != null ? tr("left", { t: fmt(eta) }) : "";
    $("end").textContent = eta != null ? tr("end_at", { t: new Date(Date.now() + eta * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) }) : "";
    $("msg").textContent = s.message || "";
    last = s.last;
    $("btn").textContent = shown ? L.refresh : L.show;
    document.title = s.total ? `${s.index}/${s.total} · Focus Stack` : "Focus Stack";
  } catch (e) {
    $("off").textContent = L.offline; $("off").style.display = "block";
  }
}
$("btn").onclick = () => {
  if (!last) { $("cap").textContent = L.no_shot; return; }
  const img = $("img");
  $("cap").textContent = L.loading;
  img.onload = () => { img.hidden = false; $("cap").textContent = tr("shot", { i: last.label, t: last.time }); };
  img.onerror = () => { $("cap").textContent = L.offline; };
  shown = last.key;
  img.src = `preview?k=${encodeURIComponent(K)}&v=${encodeURIComponent(last.key)}`;
  $("btn").textContent = L.refresh;
};
poll(); setInterval(poll, 3000);
document.addEventListener("visibilitychange", () => { if (!document.hidden) poll(); });
</script>
</body></html>
"""
