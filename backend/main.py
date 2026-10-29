"""Server locale: API REST + WebSocket di stato + interfaccia web (PWA) per Safari."""
from __future__ import annotations

import asyncio
import functools
import hashlib
import json
import subprocess
import time
from collections import deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import settings as store
from . import flasher
from . import i18n
from .i18n import tr
from .camera import GPHOTO_AVAILABLE, CameraError, GPhotoCamera, SimulatedCamera
from .focuser import FocuserError, LimitError, MyFocuserPro2, SimulatedFocuser, list_serial_ports
from .sequence import SequenceParams, SequenceRunner
from .updater import AppUpdater, bundled_firmware

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
CACHE_DIR = Path.home() / "Library" / "Caches" / "MyFocuserStack"
BROWSER_FORMATS = (".jpg", ".jpeg", ".png", ".webp", ".gif")
PREVIEW_PX = 1200
CODE_DIRS = (Path(__file__).resolve().parent, WEB_DIR)


def code_signature() -> float:
    """Data di modifica più recente del codice: serve a capire se il server va riavviato."""
    return max(p.stat().st_mtime for d in CODE_DIRS for p in d.iterdir()
               if p.suffix in (".py", ".js", ".html", ".css"))


BOOT_SIGNATURE = code_signature()
BOOT_ID = f"{time.time():.6f}"


class App:
    def __init__(self):
        self.cfg = store.load()
        i18n.set_language(i18n.resolve(self.cfg.get("language")))
        self.focuser: MyFocuserPro2 | None = None
        self.camera: GPhotoCamera | None = None
        self.log_lines: deque[str] = deque(maxlen=500)
        self.temp_history: deque[tuple[float, float]] = deque(maxlen=720)  # 2 h a 10 s
        self.shots: list[dict] = []          # galleria della sessione (prova + sequenze)
        self.alarm: str = ""                  # avviso fine corsa / movimento non comandato
        self.alarm_kind: str = ""             # "limits" = posizione fuori dai fine corsa (il testo è tradotto)
        self.code_stale = False               # il codice su disco è più recente del server in esecuzione
        self.updater = AppUpdater(self.log)
        # aggiornamento del firmware in corso: fase e avanzamento per la pagina
        self.fw = {"busy": False, "phase": "", "progress": 0.0, "error": ""}
        # movimento continuo (pulsante della pagina tenuto premuto): verso (-1/+1, 0 = nessuno) e
        # scadenza: la pagina la rinnova di continuo, se smette il motore viene fermato
        self.hold_dir = 0
        self.hold_deadline = 0.0
        # live view: pagine collegate allo stream e ultimo errore (es. fotocamera senza live view)
        self.live_clients = 0
        self.live_error = ""
        self.runner = SequenceRunner(lambda: self.focuser if self.focuser and self.focuser.connected else None,
                                     lambda: self.camera if self.camera and self.camera.connected else None,
                                     self.log, self.add_sequence_shot)

    def log(self, msg: str) -> None:
        self.log_lines.append(f"{time.strftime('%H:%M:%S')}  {msg}")

    # ---------- calibrazione / limiti ----------
    def um_per_step(self) -> float:
        mech = self.cfg["mechanics"]
        if mech.get("mode") == "computed":
            micro = (self.focuser.motor.get("step_mode") if self.focuser else None) or 1
            denom = mech["motor_steps_per_rev"] * micro * mech["gear_ratio"]
            return mech["um_per_knob_rev"] / denom if denom else 0.0
        return float(self.cfg.get("um_per_step") or 0)

    def apply_limits(self) -> None:
        if self.focuser:
            self.focuser.limit_min = int(self.cfg.get("limit_min") or 0)
            lm = self.cfg.get("limit_max")
            self.focuser.limit_max = int(lm) if lm is not None else None

    # ---------- galleria ----------
    def add_shot(self, files: list[str], kind: str, position: int | None, temperature: float | None,
                 index: int | None = None) -> None:
        if not files:
            return
        # file per il browser: preferisce il JPEG se la fotocamera salva RAW+JPEG
        display = next((f for f in files if f.lower().endswith(BROWSER_FORMATS)), files[0])
        # chiave unica per scatto: dopo un riavvio gli id ripartono da 0, la chiave no
        # (evita che il browser mostri dalla cache un'immagine di una sessione precedente)
        try:
            mtime = Path(display).stat().st_mtime_ns
        except OSError:
            mtime = 0
        key = hashlib.sha1(f"{BOOT_ID}:{display}:{mtime}".encode()).hexdigest()[:16]
        self.shots.append({"id": len(self.shots), "key": key, "kind": kind, "file": display, "files": files,
                           "name": Path(display).name, "position": position, "temperature": temperature,
                           "index": index, "time": time.strftime("%H:%M:%S")})
        asyncio.get_running_loop().create_task(warm_cache(display))

    def add_sequence_shot(self, record: dict) -> None:
        self.add_shot(record["files"], "sequence", record["position"], record["temperature"], record["index"])

    def state(self) -> dict:
        st = self.runner.status
        last = self.shots[-1] if self.shots else None
        return {
            "focuser": self.focuser.describe() if self.focuser else {"connected": False},
            "camera": {**self.camera.describe(), "live_error": self.live_error} if self.camera
            else {"connected": False},
            "gphoto": GPHOTO_AVAILABLE,
            "sequence": {**st.__dict__, "files": st.files[-3:], "file_count": len(st.files)},
            "settings": self.cfg,
            "um_per_step": self.um_per_step(),
            "alarm": self.alarm,
            "temp_history": [t for _, t in list(self.temp_history)[-180:]],
            "last_shot": last,
            "shot_count": len(self.shots),
            "log": list(self.log_lines)[-200:],
            "boot_signature": BOOT_SIGNATURE,
            "language": i18n.current(),
            "code_stale": self.code_stale,
            "app": self.updater.describe(),
            "firmware_update": self.firmware_update_state(),
        }

    def firmware_update_state(self) -> dict:
        f = self.focuser
        real = bool(f and f.connected and not f.simulated)
        fw = bundled_firmware(f.board if real else "myfp2")
        installed = f.fs_build if real else None
        return {**self.fw, "bundled": fw["build"] if fw else None,
                "installed": installed,
                # firmware originale (nessuna build) o build più vecchia di quella inclusa nell'app
                "available": bool(fw and real and (installed is None or installed < fw["build"]))}


app_state = App()


# ---------------- conversione immagini per la visualizzazione ----------------
_render_locks: dict[str, asyncio.Lock] = {}


async def render_image(src: str, size: str) -> Path:
    """Restituisce un file visualizzabile dal browser: l'originale se è già JPEG/PNG,
    altrimenti una conversione (anche da RAW) con `sips` di macOS, in cache."""
    path = Path(src)
    if not path.exists():
        raise HTTPException(404, tr("File non trovato"))
    if path.suffix.lower() in BROWSER_FORMATS:
        # sips -Z ingrandirebbe le immagini piccole: l'anteprima serve solo se l'originale è grande
        if size == "full" or max(await image_size(path)) <= PREVIEW_PX:
            return path
    key = hashlib.sha1(f"{path}:{path.stat().st_mtime_ns}:{size}".encode()).hexdigest()[:20]
    out = CACHE_DIR / f"{key}.jpg"
    lock = _render_locks.setdefault(key, asyncio.Lock())
    async with lock:
        if not out.exists():
            CACHE_DIR.mkdir(parents=True, exist_ok=True)
            args = ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "92"]
            if size == "preview" and max(await image_size(path)) > PREVIEW_PX:
                args += ["-Z", str(PREVIEW_PX)]
            tmp = out.with_suffix(".part.jpg")
            proc = await asyncio.create_subprocess_exec(*args, str(path), "--out", str(tmp),
                                                        stdout=asyncio.subprocess.DEVNULL,
                                                        stderr=asyncio.subprocess.DEVNULL)
            await proc.wait()
            if proc.returncode != 0 or not tmp.exists():
                raise HTTPException(415, tr("Impossibile convertire {name}", name=path.name))
            tmp.replace(out)
    _render_locks.pop(key, None)
    return out


async def image_size(path: Path) -> tuple[int, int]:
    proc = await asyncio.create_subprocess_exec("sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path),
                                                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
    out, _ = await proc.communicate()
    vals = [int(line.split(":")[1]) for line in out.decode().splitlines() if "pixel" in line]
    return (vals[0], vals[1]) if len(vals) == 2 else (0, 0)


async def warm_cache(src: str) -> None:
    """Prepara anteprima e piena risoluzione appena arriva un nuovo scatto."""
    for size in ("preview", "full"):
        try:
            await render_image(src, size)
        except HTTPException:
            return


# ---------------- ciclo di lettura + watchdog fine corsa ----------------
async def poll_loop():
    tick = 0
    last_pos: int | None = None
    while True:
        f = app_state.focuser
        # Durante la sequenza è il runner stesso a interrogare il motore.
        if f and f.connected and not app_state.runner.busy:
            try:
                await f.poll(with_temp=(tick % 20 == 0))
                watchdog(f, last_pos)
                hold_watchdog(f)
                last_pos = f.position
            except Exception as exc:  # noqa: BLE001
                app_state.log(tr("Errore lettura focheggiatore: {exc}", exc=exc))
                await asyncio.sleep(2)
        elif not (f and f.connected):
            last_pos = None
        if tick % 10 == 0:
            try:
                app_state.code_stale = code_signature() > BOOT_SIGNATURE + 1
            except OSError:
                pass
        if f and f.connected and f.temperature is not None and tick % 20 == 0:
            app_state.temp_history.append((time.time(), f.temperature))
        tick += 1
        await asyncio.sleep(0.2 if f and f.moving else 0.5)


def watchdog(f: MyFocuserPro2, last_pos: int | None) -> None:
    lo, hi = f.bounds()
    outside = f.position < lo or (hi is not None and f.position > hi)
    if outside:
        if f.moving:
            asyncio.get_running_loop().create_task(f.halt())
            msg = tr("Posizione {pos} fuori dai fine corsa ({lo} – {hi}): motore fermato", pos=f.position, lo=lo, hi=hi)
        else:
            msg = tr("Posizione {pos} fuori dai fine corsa ({lo} – {hi})", pos=f.position, lo=lo, hi=hi)
        if app_state.alarm != msg:
            app_state.alarm, app_state.alarm_kind = msg, "limits"
            app_state.log("⚠ " + msg)
    elif app_state.alarm_kind == "limits":
        app_state.alarm, app_state.alarm_kind = "", ""
    # Movimento non comandato dall'app: pulsanti fisici del focheggiatore
    if last_pos is not None and f.position != last_pos and not f.commanded:
        if "manual" not in _once:
            _once.add("manual")
            app_state.log(tr("Movimento dai pulsanti del focheggiatore (da {pos})", pos=last_pos))
    elif last_pos is not None and f.position == last_pos:
        _once.discard("manual")


_once: set[str] = set()

HOLD_TIMEOUT = 1.0  # s senza conferma dalla pagina prima di fermare il movimento continuo


def hold_watchdog(f: MyFocuserPro2) -> None:
    if not app_state.hold_dir:
        return
    if not f.moving:  # arrivato al fine corsa o fermato in altro modo
        app_state.hold_dir = 0
    elif time.monotonic() > app_state.hold_deadline:
        app_state.hold_dir = 0
        asyncio.get_running_loop().create_task(f.halt())
        app_state.log(tr("Movimento continuo fermato: la pagina non risponde"))


async def update_check_loop():
    """Controlla le nuove versioni su GitHub all'avvio e poi ogni CHECK_INTERVAL."""
    while True:
        if app_state.updater.due():
            await asyncio.to_thread(app_state.updater.check_blocking)
            u = app_state.updater.describe()
            if u["available"]:
                app_state.log(tr("È disponibile Focus Stack {latest} (installata {version})",
                                 latest=u["latest"], version=u["version"]))
        await asyncio.sleep(600)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(poll_loop())
    update_task = asyncio.create_task(update_check_loop())
    app_state.log(tr("Server avviato (Focus Stack {version})", version=app_state.updater.describe()["version"]))
    yield
    task.cancel()
    update_task.cancel()
    if app_state.focuser:
        await app_state.focuser.disconnect()
    if app_state.camera:
        await app_state.camera.disconnect()


api = FastAPI(title="Focus Stack", lifespan=lifespan)

ALLOWED_HOSTS = {"localhost", "127.0.0.1", "[::1]"}


@api.middleware("http")
async def local_only(request, call_next):
    """Il server comanda hardware reale: accetta solo richieste dalla propria interfaccia.
    - Host deve essere localhost (blocca il DNS rebinding);
    - i POST devono avere l'intestazione X-FocusStack: un sito esterno non può aggiungerla
      senza un preflight CORS, che questo server non autorizza."""
    host = (request.headers.get("host") or "").rsplit(":", 1)[0]
    if host not in ALLOWED_HOSTS:
        return Response(tr("Host non consentito"), status_code=403)
    if request.method == "POST" and request.headers.get("x-focusstack") != "1":
        return Response(tr("Richiesta non consentita"), status_code=403)
    response = await call_next(request)
    # pagine e script dell'interfaccia: senza questa intestazione Safari può riusare la copia vecchia
    # dopo un aggiornamento (era successo con il visualizzatore). Con no-cache ricontrolla sempre (ETag).
    if not request.url.path.startswith("/api") and "cache-control" not in response.headers:
        response.headers["Cache-Control"] = "no-cache"
    return response


@api.post("/api/shutdown")
async def shutdown():
    """Spegne il server (pulsante ⏻ dell'interfaccia, oppure run.py per sostituire un'istanza
    avviata con codice vecchio). Prima ferma sequenza e motore; le connessioni a focheggiatore
    e fotocamera vengono chiuse dal lifespan."""
    import os
    import signal
    if app_state.runner.busy:
        await app_state.runner.stop()
    elif app_state.focuser and app_state.focuser.connected:
        try:
            await app_state.focuser.halt()
        except Exception:  # noqa: BLE001
            pass
    app_state.log(tr("Spegnimento del server…"))
    # il ritardo lascia il tempo di inviare la risposta alla pagina
    asyncio.get_running_loop().call_later(0.5, os.kill, os.getpid(), signal.SIGINT)
    return {"ok": True}


def guard(fn):
    """Converte gli errori di dominio in risposte HTTP leggibili dalla UI."""
    @functools.wraps(fn)
    async def wrapper(*a, **kw):
        try:
            return await fn(*a, **kw)
        except HTTPException:
            raise
        except (FocuserError, CameraError, RuntimeError, ValueError, OSError) as exc:
            app_state.log(tr("Errore: {exc}", exc=exc))
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:  # errori gphoto2 e simili
            app_state.log(tr("Errore: {exc}", exc=exc))
            raise HTTPException(500, str(exc)) from exc
    return wrapper


def need_focuser() -> MyFocuserPro2:
    if not app_state.focuser or not app_state.focuser.connected:
        raise HTTPException(400, tr("Focheggiatore non connesso"))
    return app_state.focuser


def need_camera() -> GPhotoCamera:
    if not app_state.camera or not app_state.camera.connected:
        raise HTTPException(400, tr("Fotocamera non connessa"))
    return app_state.camera


def not_running():
    if app_state.runner.busy:
        raise HTTPException(409, tr("Sequenza in corso"))


# ---------------- stato ----------------
@api.get("/api/state")
async def get_state():
    return app_state.state()


@api.websocket("/ws")
async def ws_state(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_text(json.dumps(app_state.state()))
            await asyncio.sleep(0.25)
    except (WebSocketDisconnect, RuntimeError):
        pass


# ---------------- focheggiatore ----------------
class FocuserConnect(BaseModel):
    port: str = ""
    baud: int = 9600
    simulate: bool = False


class Position(BaseModel):
    position: int


class Delta(BaseModel):
    delta: int


class MotorSetting(BaseModel):
    name: str
    value: int | bool


@api.get("/api/ports")
async def ports():
    return list_serial_ports()


@api.post("/api/focuser/connect")
@guard
async def focuser_connect(body: FocuserConnect):
    not_running()
    if app_state.focuser:
        await app_state.focuser.disconnect()
    if body.simulate:
        f = SimulatedFocuser()
    else:
        if not body.port:
            raise ValueError(tr("Seleziona una porta seriale"))
        f = MyFocuserPro2(body.port, body.baud)
    app_state.log(tr("Connessione focheggiatore {port}…", port=tr("simulatore") if f.simulated else f.port))
    await f.connect()
    app_state.focuser = f
    app_state.apply_limits()
    if not body.simulate:
        app_state.cfg["focuser_port"] = body.port
        app_state.cfg["focuser_baud"] = body.baud
        store.save(app_state.cfg)
    probe = f"{f.temperature:.1f} °C" if f.temperature is not None else tr("sonda assente")
    app_state.log(tr("Focheggiatore connesso (firmware {firmware}, max {max} passi, {probe})",
                     firmware=f.firmware, max=f.max_step, probe=probe))
    lo, hi = f.bounds()
    if f.position < lo or (hi is not None and f.position > hi):
        app_state.log(tr("⚠ La posizione attuale {pos} è fuori dai fine corsa impostati", pos=f.position))
    return f.describe()


@api.post("/api/focuser/disconnect")
@guard
async def focuser_disconnect():
    not_running()
    if app_state.focuser:
        await app_state.focuser.disconnect()
        app_state.focuser = None
        app_state.alarm, app_state.alarm_kind = "", ""
        app_state.log(tr("Focheggiatore disconnesso"))
    return {"ok": True}


async def run_firmware_update(port: str, baud: int, hex_path: Path, build: int, manual_reset: bool) -> None:
    fw = app_state.fw

    def progress(phase: str, frac: float) -> None:
        fw["phase"], fw["progress"] = phase, frac

    try:
        await asyncio.to_thread(flasher.flash, port, hex_path, progress, manual_reset)
        app_state.log(tr("Firmware aggiornato (build {build})", build=build))
    except Exception as exc:  # noqa: BLE001
        fw["error"] = str(exc)
        app_state.log(tr("⚠ Aggiornamento firmware non riuscito: {exc}", exc=exc))
    # ricollega in ogni caso: se la scrittura è fallita il bootloader resta e il vecchio
    # firmware (o nessuno) risponde; l'errore è comunque mostrato nella pagina
    fw["phase"] = tr("Ricollegamento")
    try:
        f = MyFocuserPro2(port, baud)
        await f.connect()
        app_state.focuser = f
        app_state.apply_limits()
        app_state.log(tr("Focheggiatore ricollegato (firmware {firmware}, build {build})", firmware=f.firmware, build=f.fs_build))
    except Exception as exc:  # noqa: BLE001
        app_state.log(tr("Focheggiatore non ricollegato: {exc}", exc=exc))
    fw["busy"] = False
    fw["phase"] = ""


@api.post("/api/firmware/update")
@guard
async def firmware_update():
    not_running()
    if app_state.fw["busy"]:
        raise ValueError(tr("Aggiornamento del firmware già in corso"))
    f = need_focuser()
    if f.simulated:
        raise ValueError(tr("Il simulatore non ha firmware da aggiornare"))
    fw = bundled_firmware(f.board)
    if not fw:
        raise ValueError(tr("Questa copia dell'app non contiene il firmware per questa scheda"))
    if f.moving:
        raise ValueError(tr("Attendi che il motore sia fermo"))
    port, baud = f.port, f.baud
    app_state.fw.update(busy=True, phase=tr("Preparazione"), progress=0.0, error="")
    app_state.log(tr("Aggiornamento firmware alla build {build} su {port}…", build=fw["build"], port=port))
    await f.disconnect()
    app_state.focuser = None
    # l'Ardufocus ha un condensatore che impedisce il riavvio da USB: serve il tasto reset
    manual = f.board == "ardufocus"
    asyncio.get_running_loop().create_task(run_firmware_update(port, baud, fw["hex"], fw["build"], manual))
    return {"ok": True}


# ---------------- aggiornamenti dell'app ----------------
@api.post("/api/app/check")
@guard
async def app_check():
    await asyncio.to_thread(app_state.updater.check_blocking)
    return app_state.updater.describe()


@api.post("/api/app/update")
@guard
async def app_update():
    not_running()
    if app_state.fw["busy"]:
        raise ValueError(tr("Attendi la fine dell'aggiornamento del firmware"))
    await asyncio.to_thread(app_state.updater.install_blocking)
    return {"ok": True}


@api.post("/api/focuser/move")
@guard
async def focuser_move(body: Position):
    not_running()
    f = need_focuser()
    await f.move_to(body.position)
    return {"ok": True}


@api.post("/api/focuser/jog")
@guard
async def focuser_jog(body: Delta):
    not_running()
    f = need_focuser()
    await f.poll()
    target = f.position + body.delta
    clamped = f.clamp(target)
    if clamped == f.position and clamped != target:
        raise LimitError(tr("Fine corsa raggiunto"))
    await f.move_to(clamped)
    return {"ok": True, "target": clamped, "clamped": clamped != target}


class Hold(BaseModel):
    direction: int  # -1 / +1 = muovi verso il fine corsa e continua; 0 = fermati


@api.post("/api/focuser/hold")
@guard
async def focuser_hold(body: Hold):
    """Movimento continuo mentre un pulsante della pagina è tenuto premuto.

    La pagina ripete la chiamata ogni 250 ms: ogni chiamata rinnova la scadenza e, se la pagina
    smette (rete, scheda chiusa), hold_watchdog ferma il motore. Il firmware rallenta e si ferma
    con la rampa sia al rilascio (:27#) sia arrivando al fine corsa.
    """
    f = need_focuser()
    if body.direction == 0:
        if app_state.hold_dir:
            app_state.hold_dir = 0
            await f.halt()
        return {"ok": True}
    not_running()
    if body.direction not in (-1, 1):
        raise ValueError(tr("Verso non valido"))
    app_state.hold_deadline = time.monotonic() + HOLD_TIMEOUT
    if app_state.hold_dir == body.direction:
        return {"ok": True}
    await f.poll()
    if f.moving:  # il firmware ignora un nuovo target mentre si muove (es. sta ancora rallentando)
        await f.wait_idle(timeout=5)
    lo, hi = f.bounds()
    target = lo if body.direction < 0 else (hi if hi is not None else f.position + 1_000_000)
    if target == f.position:
        raise LimitError(tr("Fine corsa raggiunto"))
    app_state.hold_dir = body.direction
    app_state.hold_deadline = time.monotonic() + HOLD_TIMEOUT
    await f.move_to(target)
    return {"ok": True, "target": target}


@api.post("/api/focuser/halt")
@guard
async def focuser_halt():
    app_state.hold_dir = 0
    if app_state.runner.busy:
        await app_state.runner.stop()
    elif app_state.focuser and app_state.focuser.connected:
        await app_state.focuser.halt()
    return {"ok": True}


@api.post("/api/focuser/sync")
@guard
async def focuser_sync(body: Position):
    not_running()
    await need_focuser().sync(body.position)
    app_state.log(tr("Posizione sincronizzata a {pos}: verifica i fine corsa!", pos=body.position))
    return {"ok": True}


@api.post("/api/focuser/maxstep")
@guard
async def focuser_maxstep(body: Position):
    not_running()
    f = need_focuser()
    await f.set_max_step(body.position)
    if f.max_step != body.position:
        app_state.log(tr("⚠ Il firmware ha mantenuto max = {max} (richiesto {requested})", max=f.max_step, requested=body.position))
    else:
        app_state.log(tr("Max passi del firmware impostato a {max}", max=f.max_step))
    return f.describe()


@api.post("/api/focuser/motor")
@guard
async def focuser_motor(body: MotorSetting):
    not_running()
    f = need_focuser()
    motor = await f.set_motor(body.name, body.value)
    app_state.log(tr("Motore: {name} = {value}", name=body.name, value=motor.get(body.name)))
    return motor


@api.post("/api/focuser/motor/reload")
@guard
async def focuser_motor_reload():
    not_running()
    return await need_focuser().read_motor()


@api.post("/api/focuser/sim-button")
@guard
async def focuser_sim_button(body: Delta):
    """Solo simulatore: riproduce la pressione dei pulsanti fisici (per provare il watchdog)."""
    f = need_focuser()
    if not isinstance(f, SimulatedFocuser):
        raise ValueError(tr("Disponibile solo con il simulatore"))
    f.simulate_button(body.delta)
    return {"ok": True}


# ---------------- fine corsa / meccanica ----------------
class LimitsBody(BaseModel):
    limit_min: int
    limit_max: int | None = None
    toward_specimen: str | None = None


class MechanicsBody(BaseModel):
    mode: str
    motor_steps_per_rev: int = 200
    gear_ratio: float = 1.0
    um_per_knob_rev: float = 100.0
    um_per_step: float | None = None


@api.post("/api/limits")
@guard
async def set_limits(body: LimitsBody):
    if body.limit_min < 0:
        raise ValueError(tr("Il fine corsa inferiore non può essere negativo"))
    if body.limit_max is not None and body.limit_max <= body.limit_min:
        raise ValueError(tr("Il fine corsa superiore deve essere maggiore di quello inferiore"))
    f = app_state.focuser
    if f and f.max_step and body.limit_max and body.limit_max > f.max_step:
        raise ValueError(tr("Il fine corsa superiore supera il max del firmware ({max}): aumenta prima il max del firmware",
                            max=f.max_step))
    app_state.cfg["limit_min"] = body.limit_min
    app_state.cfg["limit_max"] = body.limit_max
    if body.toward_specimen in ("increasing", "decreasing"):
        app_state.cfg["toward_specimen"] = body.toward_specimen
    store.save(app_state.cfg)
    app_state.apply_limits()
    app_state.log(tr("Fine corsa: {lo} – {hi}", lo=body.limit_min,
                     hi=body.limit_max if body.limit_max is not None else tr("max firmware")))
    return {"ok": True}


@api.post("/api/limits/zero-here")
@guard
async def zero_here():
    """Rende la posizione attuale lo zero: da qui in giù neanche i pulsanti fisici possono scendere."""
    not_running()
    f = need_focuser()
    await f.poll()
    shift = f.position
    await f.sync(0)
    lm = app_state.cfg.get("limit_max")
    app_state.cfg["limit_min"] = 0
    if lm is not None:
        app_state.cfg["limit_max"] = max(1, lm - shift)
    seq = app_state.cfg["sequence"]
    seq["start"], seq["end"] = max(0, seq["start"] - shift), max(0, seq["end"] - shift)
    store.save(app_state.cfg)
    app_state.apply_limits()
    app_state.log(tr("Zero impostato sulla posizione {shift}: limiti e sequenza traslati di −{shift}", shift=shift))
    return {"ok": True}


@api.post("/api/mechanics")
@guard
async def set_mechanics(body: MechanicsBody):
    if body.mode not in ("manual", "computed"):
        raise ValueError(tr("Modalità non valida"))
    if body.motor_steps_per_rev <= 0 or body.gear_ratio <= 0 or body.um_per_knob_rev <= 0:
        raise ValueError(tr("I valori meccanici devono essere positivi"))
    data = body.model_dump()
    um = data.pop("um_per_step")
    app_state.cfg["mechanics"].update(data)
    if um is not None and um > 0:
        app_state.cfg["um_per_step"] = um
    store.save(app_state.cfg)
    app_state.log(tr("Meccanica aggiornata: {um} µm/passo", um=f"{app_state.um_per_step():.4f}"))
    return {"um_per_step": app_state.um_per_step()}


# ---------------- fotocamera ----------------
class CameraConnect(BaseModel):
    model: str = ""
    port: str = ""
    simulate: bool = False


class CameraSetting(BaseModel):
    name: str
    value: str


class TestShot(BaseModel):
    bulb_s: float = 0
    mirror_delay_ms: int = 0


def check_mirror_delay(ms: int) -> None:
    if not 0 <= ms <= 2500:
        raise ValueError(tr("Il ritardo dello specchio deve essere fra 0 e 2,5 secondi"))


@api.post("/api/camera/detect")
@guard
async def camera_detect():
    cams = await GPhotoCamera.detect()
    app_state.log(tr("Fotocamere rilevate: {list}", list=", ".join(c["model"] for c in cams) or tr("nessuna")))
    return cams


@api.post("/api/camera/connect")
@guard
async def camera_connect(body: CameraConnect):
    not_running()
    if app_state.camera:
        await app_state.camera.disconnect()
        app_state.camera = None
    cam = SimulatedCamera() if body.simulate else GPhotoCamera(body.model, body.port)
    app_state.log(tr("Connessione fotocamera {model}…",
                     model=body.model or (tr("simulata") if body.simulate else tr("automatica"))))
    await cam.connect()
    cam.log = app_state.log
    if isinstance(cam, SimulatedCamera):
        cam.focus_position = lambda: (app_state.focuser.position
                                      if app_state.focuser and app_state.focuser.connected else None)
    app_state.camera = cam
    app_state.log(tr("Fotocamera connessa: {model}", model=cam.model))
    return cam.describe()


@api.post("/api/camera/disconnect")
@guard
async def camera_disconnect():
    not_running()
    if app_state.camera:
        await app_state.camera.disconnect()
        app_state.camera = None
        app_state.log(tr("Fotocamera disconnessa"))
    return {"ok": True}


LIVE_BOUNDARY = "fsframe"
LIVE_MAX_FPS = 15
# ultimo fotogramma letto, condiviso fra le pagine collegate (finestra principale e visualizzatore):
# la fotocamera ne produce uno solo per volta, al massimo LIVE_MAX_FPS al secondo
live_lock = asyncio.Lock()
live_frame: dict | None = None


async def next_live_frame(cam: GPhotoCamera, last_seq: int) -> dict:
    """Il fotogramma più recente non ancora inviato a questo client: riusa quello appena letto
    per un'altra pagina, altrimenti ne legge uno nuovo rispettando LIVE_MAX_FPS."""
    global live_frame
    async with live_lock:
        f = live_frame if live_frame and live_frame["cam"] is cam else None
        if f:
            # appena letto per un'altra pagina: la freschezza si misura dalla fine della lettura,
            # perché una fotocamera vera (Nikon ~120 ms) impiega più di 1/LIVE_MAX_FPS per fotogramma
            if f["seq"] != last_seq and time.monotonic() - f["done"] < 0.5:
                return f
            await asyncio.sleep(max(0.0, 1 / LIVE_MAX_FPS - (time.monotonic() - f["t"])))
        t0 = time.monotonic()
        data = await cam.preview()
        live_frame = {"cam": cam, "seq": f["seq"] + 1 if f else 1, "t": t0, "done": time.monotonic(), "data": data}
        return live_frame


async def live_frames(cam: GPhotoCamera):
    """Fotogrammi del live view come multipart/x-mixed-replace (MJPEG): il browser li mostra
    in un normale <img>. Si mette in pausa durante scatti e sequenza e si spegne quando
    l'ultima pagina chiude la connessione."""
    global live_frame
    app_state.live_clients += 1
    seq = 0
    try:
        while cam.connected and app_state.camera is cam:
            if app_state.runner.busy:
                # la sequenza scatta come senza live view (specchio, ritardi): live view spento
                if cam.live:
                    await cam.end_preview()
                await asyncio.sleep(0.3)
                continue
            if cam.busy:
                await asyncio.sleep(0.1)
                continue
            try:
                frame = await next_live_frame(cam, seq)
            except Exception as exc:  # noqa: BLE001
                app_state.live_error = str(exc)
                app_state.log(tr("Live view interrotto: {exc}", exc=exc))
                return
            app_state.live_error = ""
            seq, data = frame["seq"], frame["data"]
            mime = "image/png" if data[:4] == b"\x89PNG" else "image/jpeg"
            yield (f"--{LIVE_BOUNDARY}\r\nContent-Type: {mime}\r\nContent-Length: {len(data)}\r\n\r\n"
                   .encode() + data + b"\r\n")
    finally:
        app_state.live_clients -= 1
        if app_state.live_clients == 0:
            live_frame = None
            if cam.connected and cam.live:
                # la connessione può chiudersi con il generatore cancellato: spegne in un task a parte
                asyncio.get_running_loop().create_task(cam.end_preview())


@api.get("/api/camera/live")
async def camera_live():
    cam = need_camera()
    app_state.live_error = ""
    return StreamingResponse(live_frames(cam), media_type=f"multipart/x-mixed-replace; boundary={LIVE_BOUNDARY}",
                             headers={"Cache-Control": "no-store"})


@api.post("/api/camera/settings/reload")
@guard
async def camera_reload():
    not_running()
    return await need_camera().read_settings()


@api.post("/api/camera/settings")
@guard
async def camera_set(body: CameraSetting):
    not_running()
    settings = await need_camera().set_setting(body.name, body.value)
    actual = settings.get(body.name, {}).get("current")
    app_state.log(f"{body.name} = {actual}" if actual == body.value
                  else tr("{name} = {actual} (richiesto {requested})", name=body.name, actual=actual, requested=body.value))
    return settings


@api.post("/api/camera/test")
@guard
async def camera_test(body: TestShot):
    not_running()
    check_mirror_delay(body.mirror_delay_ms)
    cam = need_camera()
    test_dir = Path(store.CONFIG_DIR) / "test-shots"
    test_dir.mkdir(parents=True, exist_ok=True)
    # tiene solo gli ultimi scatti di prova
    old = sorted(test_dir.iterdir(), key=lambda p: p.stat().st_mtime)
    for p in old[:-20]:
        p.unlink(missing_ok=True)
    app_state.log(tr("Scatto di prova…"))
    files = await cam.capture(mode="download", dest_base=test_dir / f"prova_{time.strftime('%H%M%S')}",
                              bulb_s=body.bulb_s, mirror_s=body.mirror_delay_ms / 1000)
    f = app_state.focuser
    app_state.add_shot(files, "test", f.position if f and f.connected else None,
                       f.temperature if f and f.connected else None)
    app_state.log(tr("Scatto di prova completato ({n} file)", n=len(files)))
    return {"files": files}


# ---------------- galleria / visualizzatore ----------------
@api.get("/api/shots")
async def shots():
    return {"items": app_state.shots[-500:], "count": len(app_state.shots)}


@api.get("/api/shots/{shot_id}/image")
async def shot_image(shot_id: int, size: str = "full", v: str = ""):
    if shot_id < 0 or shot_id >= len(app_state.shots):
        raise HTTPException(404)
    if v and v != app_state.shots[shot_id]["key"]:
        raise HTTPException(404, tr("Scatto di una sessione precedente"))
    if size not in ("full", "preview"):
        raise HTTPException(400)
    out = await render_image(app_state.shots[shot_id]["file"], size)
    # no-cache = il browser può tenere l'immagine ma deve ricontrollare (ETag) prima di riusarla
    return FileResponse(out, headers={"Cache-Control": "private, no-cache"})


@api.post("/api/shots/{shot_id}/reveal")
async def shot_reveal(shot_id: int):
    if shot_id < 0 or shot_id >= len(app_state.shots):
        raise HTTPException(404)
    subprocess.Popen(["open", "-R", app_state.shots[shot_id]["file"]])
    return {"ok": True}


# ---------------- sequenza ----------------
class SequenceBody(BaseModel):
    start: int
    end: int
    step: int
    settle_ms: int = 1500
    post_shot_ms: int = 500
    mirror_delay_ms: int = 0
    backlash: int = 0
    return_to_start: bool = True
    capture_mode: str = "download"
    session_name: str = "stack"
    output_root: str = ""
    bulb_s: float = 0


@api.post("/api/sequence/start")
@guard
async def sequence_start(body: SequenceBody):
    data = body.model_dump()
    if body.step < 1:
        raise ValueError(tr("Il passo deve essere almeno 1"))
    if body.capture_mode not in ("download", "card", "trigger"):
        raise ValueError(tr("Modalità di scatto non valida"))
    check_mirror_delay(body.mirror_delay_ms)
    need_focuser()
    data["output_root"] = (validate_output_root(body.output_root or app_state.cfg["output_root"])
                           if body.capture_mode == "download" else body.output_root or app_state.cfg["output_root"])
    app_state.runner.start(SequenceParams(**data))   # verifica anche i fine corsa
    app_state.cfg["sequence"].update({k: v for k, v in data.items() if k != "output_root"})
    app_state.cfg["output_root"] = data["output_root"]
    store.save(app_state.cfg)
    return {"ok": True}


@api.post("/api/sequence/pause")
async def sequence_pause():
    app_state.runner.pause()
    return {"ok": True}


@api.post("/api/sequence/resume")
async def sequence_resume():
    app_state.runner.resume()
    return {"ok": True}


@api.post("/api/sequence/stop")
async def sequence_stop():
    await app_state.runner.stop()
    return {"ok": True}


# ---------------- impostazioni / preset ----------------
class SettingsBody(BaseModel):
    output_root: str | None = None
    jog_max: int | None = None
    jog_hold: bool | None = None
    language: str | None = None   # "auto" (lingua di macOS) oppure un codice di i18n.SUPPORTED


class PresetBody(BaseModel):
    name: str
    data: dict | None = None


def validate_output_root(raw: str) -> str:
    """Normalizza la cartella di salvataggio, la crea se manca e verifica che sia scrivibile."""
    import os
    path = Path(raw.strip()).expanduser()
    if not raw.strip() or not path.is_absolute():
        raise ValueError(tr("Indica un percorso completo, per esempio ~/Pictures/FocusStack"))
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValueError(tr("Impossibile creare la cartella {path}: permesso negato o disco non disponibile", path=path)) from exc
    if not path.is_dir() or not os.access(path, os.W_OK):
        raise ValueError(tr("Non è possibile scrivere nella cartella {path}", path=path))
    return str(path)


@api.post("/api/settings")
@guard
async def save_settings(body: SettingsBody):
    if body.language is not None:
        if body.language not in ("auto", *i18n.SUPPORTED):
            raise ValueError(tr("Lingua non valida"))
        app_state.cfg["language"] = body.language
        i18n.set_language(i18n.resolve(body.language))
    if body.output_root is not None:
        app_state.cfg["output_root"] = validate_output_root(body.output_root)
        app_state.log(tr("Cartella di salvataggio: {path}", path=app_state.cfg["output_root"]))
    if body.jog_max is not None:
        if body.jog_max not in (1000, 10_000, 100_000):
            raise ValueError(tr("Ampiezza massima non valida"))
        app_state.cfg["jog_max"] = body.jog_max
    if body.jog_hold is not None:
        app_state.cfg["jog_hold"] = body.jog_hold
    store.save(app_state.cfg)
    return app_state.cfg


@api.post("/api/choose-folder")
@guard
async def choose_folder():
    """Apre il pannello "Scegli cartella" di macOS. Safari non può fornire percorsi reali del
    disco a una pagina web, quindi la finestra la apre il server, che gira sullo stesso Mac."""
    current = Path(app_state.cfg["output_root"]).expanduser()
    start = current if current.is_dir() else Path.home()
    # il percorso iniziale passa come argomento (argv), non dentro il testo dello script
    script = [
        "-e", "on run argv",
        "-e", "tell current application to activate",
        "-e", "set f to choose folder with prompt (item 2 of argv) default location (POSIX file (item 1 of argv))",
        "-e", "return POSIX path of f",
        "-e", "end run",
        str(start), tr("Cartella in cui salvare gli scatti"),
    ]
    proc = await asyncio.create_subprocess_exec("osascript", *script, stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    if proc.returncode != 0:
        if b"-128" in err:            # l'utente ha premuto Annulla
            return {"cancelled": True}
        raise RuntimeError(tr("Impossibile aprire la finestra di selezione: {err}", err=err.decode().strip()))
    app_state.cfg["output_root"] = validate_output_root(out.decode().strip().rstrip("/") or "/")
    store.save(app_state.cfg)
    app_state.log(tr("Cartella di salvataggio: {path}", path=app_state.cfg["output_root"]))
    return {"path": app_state.cfg["output_root"]}


@api.post("/api/presets/save")
async def preset_save(body: PresetBody):
    if not body.name.strip() or body.data is None:
        raise HTTPException(400, tr("Nome e dati obbligatori"))
    app_state.cfg["presets"][body.name.strip()] = body.data
    store.save(app_state.cfg)
    return app_state.cfg["presets"]


@api.post("/api/presets/delete")
async def preset_delete(body: PresetBody):
    app_state.cfg["presets"].pop(body.name, None)
    store.save(app_state.cfg)
    return app_state.cfg["presets"]


# ---------------- integrazione Finder / Helicon Focus ----------------
@api.post("/api/open-folder")
async def open_folder():
    folder = app_state.runner.status.folder
    target = Path(folder) if folder and Path(folder).exists() else Path(app_state.cfg["output_root"]).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(["open", str(target)])
    return {"ok": True}


@api.post("/api/open-helicon")
async def open_helicon():
    folder = app_state.runner.status.folder
    if not folder or not Path(folder).exists():
        raise HTTPException(400, tr("Nessuna sequenza scaricata da aprire"))
    images = sorted(p for p in Path(folder).iterdir()
                    if p.suffix.lower() != ".json" and not p.name.startswith("."))
    if not images:
        raise HTTPException(400, tr("La cartella non contiene immagini"))
    for app_name in ("Helicon Focus 8", "Helicon Focus 7", "Helicon Focus", "HeliconFocus"):
        proc = subprocess.run(["open", "-a", app_name, *map(str, images)], capture_output=True)
        if proc.returncode == 0:
            app_state.log(tr("Aperte {n} immagini in {app}", n=len(images), app=app_name))
            return {"ok": True}
    raise HTTPException(400, tr("Helicon Focus non trovato in /Applications"))


# ---------------- file statici (PWA) ----------------
@api.get("/lang.js")
async def lang_js():
    """Lingua effettiva e traduzioni per la pagina, caricate prima degli script dell'interfaccia."""
    code = i18n.current()
    body = (f"window.FS_LANG = {json.dumps(code)};\n"
            f"window.FS_STRINGS = {json.dumps(i18n.strings(code), ensure_ascii=False)};\n")
    return Response(body, media_type="text/javascript; charset=utf-8", headers={"Cache-Control": "no-cache"})


@api.get("/sw.js")
async def service_worker():
    return FileResponse(WEB_DIR / "sw.js", media_type="text/javascript",
                        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"})


@api.get("/manifest.webmanifest")
async def manifest():
    return Response((WEB_DIR / "manifest.webmanifest").read_text(), media_type="application/manifest+json")


api.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
