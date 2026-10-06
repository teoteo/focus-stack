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
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import settings as store
from . import flasher
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
        self.focuser: MyFocuserPro2 | None = None
        self.camera: GPhotoCamera | None = None
        self.log_lines: deque[str] = deque(maxlen=500)
        self.temp_history: deque[tuple[float, float]] = deque(maxlen=720)  # 2 h a 10 s
        self.shots: list[dict] = []          # galleria della sessione (prova + sequenze)
        self.alarm: str = ""                  # avviso fine corsa / movimento non comandato
        self.code_stale = False               # il codice su disco è più recente del server in esecuzione
        self.updater = AppUpdater(self.log)
        # aggiornamento del firmware in corso: fase e avanzamento per la pagina
        self.fw = {"busy": False, "phase": "", "progress": 0.0, "error": ""}
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
            "camera": self.camera.describe() if self.camera else {"connected": False},
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
            "code_stale": self.code_stale,
            "app": self.updater.describe(),
            "firmware_update": self.firmware_update_state(),
        }

    def firmware_update_state(self) -> dict:
        fw = bundled_firmware()
        f = self.focuser
        real = bool(f and f.connected and not f.simulated)
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
        raise HTTPException(404, "File non trovato")
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
                raise HTTPException(415, f"Impossibile convertire {path.name}")
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
                last_pos = f.position
            except Exception as exc:  # noqa: BLE001
                app_state.log(f"Errore lettura focheggiatore: {exc}")
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
        msg = f"Posizione {f.position} fuori dai fine corsa ({lo} – {hi})"
        if f.moving:
            asyncio.get_running_loop().create_task(f.halt())
            msg += ": motore fermato"
        if app_state.alarm != msg:
            app_state.alarm = msg
            app_state.log("⚠ " + msg)
    elif app_state.alarm.startswith("Posizione"):
        app_state.alarm = ""
    # Movimento non comandato dall'app: pulsanti fisici del focheggiatore
    if last_pos is not None and f.position != last_pos and not f.commanded:
        if "manual" not in _once:
            _once.add("manual")
            app_state.log(f"Movimento dai pulsanti del focheggiatore (da {last_pos})")
    elif last_pos is not None and f.position == last_pos:
        _once.discard("manual")


_once: set[str] = set()


async def update_check_loop():
    """Controlla le nuove versioni su GitHub all'avvio e poi ogni CHECK_INTERVAL."""
    while True:
        if app_state.updater.due():
            await asyncio.to_thread(app_state.updater.check_blocking)
            u = app_state.updater.describe()
            if u["available"]:
                app_state.log(f"È disponibile Focus Stack {u['latest']} (installata {u['version']})")
        await asyncio.sleep(600)


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(poll_loop())
    update_task = asyncio.create_task(update_check_loop())
    app_state.log(f"Server avviato (Focus Stack {app_state.updater.describe()['version']})")
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
        return Response("Host non consentito", status_code=403)
    if request.method == "POST" and request.headers.get("x-focusstack") != "1":
        return Response("Richiesta non consentita", status_code=403)
    return await call_next(request)


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
    app_state.log("Spegnimento del server…")
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
            app_state.log(f"Errore: {exc}")
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:  # errori gphoto2 e simili
            app_state.log(f"Errore: {exc}")
            raise HTTPException(500, str(exc)) from exc
    return wrapper


def need_focuser() -> MyFocuserPro2:
    if not app_state.focuser or not app_state.focuser.connected:
        raise HTTPException(400, "Focheggiatore non connesso")
    return app_state.focuser


def need_camera() -> GPhotoCamera:
    if not app_state.camera or not app_state.camera.connected:
        raise HTTPException(400, "Fotocamera non connessa")
    return app_state.camera


def not_running():
    if app_state.runner.busy:
        raise HTTPException(409, "Sequenza in corso")


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
            raise ValueError("Seleziona una porta seriale")
        f = MyFocuserPro2(body.port, body.baud)
    app_state.log(f"Connessione focheggiatore {f.port}…")
    await f.connect()
    app_state.focuser = f
    app_state.apply_limits()
    if not body.simulate:
        app_state.cfg["focuser_port"] = body.port
        app_state.cfg["focuser_baud"] = body.baud
        store.save(app_state.cfg)
    probe = f"{f.temperature:.1f} °C" if f.temperature is not None else "sonda assente"
    app_state.log(f"Focheggiatore connesso (firmware {f.firmware}, max {f.max_step} passi, {probe})")
    lo, hi = f.bounds()
    if f.position < lo or (hi is not None and f.position > hi):
        app_state.log(f"⚠ La posizione attuale {f.position} è fuori dai fine corsa impostati")
    return f.describe()


@api.post("/api/focuser/disconnect")
@guard
async def focuser_disconnect():
    not_running()
    if app_state.focuser:
        await app_state.focuser.disconnect()
        app_state.focuser = None
        app_state.alarm = ""
        app_state.log("Focheggiatore disconnesso")
    return {"ok": True}


async def run_firmware_update(port: str, baud: int, hex_path: Path, build: int) -> None:
    fw = app_state.fw

    def progress(phase: str, frac: float) -> None:
        fw["phase"], fw["progress"] = phase, frac

    try:
        await asyncio.to_thread(flasher.flash, port, hex_path, progress)
        app_state.log(f"Firmware aggiornato (build {build})")
    except Exception as exc:  # noqa: BLE001
        fw["error"] = str(exc)
        app_state.log(f"⚠ Aggiornamento firmware non riuscito: {exc}")
    # ricollega in ogni caso: se la scrittura è fallita il bootloader resta e il vecchio
    # firmware (o nessuno) risponde; l'errore è comunque mostrato nella pagina
    fw["phase"] = "Ricollegamento"
    try:
        f = MyFocuserPro2(port, baud)
        await f.connect()
        app_state.focuser = f
        app_state.apply_limits()
        app_state.log(f"Focheggiatore ricollegato (firmware {f.firmware}, build {f.fs_build})")
    except Exception as exc:  # noqa: BLE001
        app_state.log(f"Focheggiatore non ricollegato: {exc}")
    fw["busy"] = False
    fw["phase"] = ""


@api.post("/api/firmware/update")
@guard
async def firmware_update():
    not_running()
    if app_state.fw["busy"]:
        raise ValueError("Aggiornamento del firmware già in corso")
    f = need_focuser()
    if f.simulated:
        raise ValueError("Il simulatore non ha firmware da aggiornare")
    fw = bundled_firmware()
    if not fw:
        raise ValueError("Questa copia dell'app non contiene il firmware")
    if f.moving:
        raise ValueError("Attendi che il motore sia fermo")
    port, baud = f.port, f.baud
    app_state.fw.update(busy=True, phase="Preparazione", progress=0.0, error="")
    app_state.log(f"Aggiornamento firmware alla build {fw['build']} su {port}…")
    await f.disconnect()
    app_state.focuser = None
    asyncio.get_running_loop().create_task(run_firmware_update(port, baud, fw["hex"], fw["build"]))
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
        raise ValueError("Attendi la fine dell'aggiornamento del firmware")
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
        raise LimitError("Fine corsa raggiunto")
    await f.move_to(clamped)
    return {"ok": True, "target": clamped, "clamped": clamped != target}


@api.post("/api/focuser/halt")
@guard
async def focuser_halt():
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
    app_state.log(f"Posizione sincronizzata a {body.position}: verifica i fine corsa!")
    return {"ok": True}


@api.post("/api/focuser/maxstep")
@guard
async def focuser_maxstep(body: Position):
    not_running()
    f = need_focuser()
    await f.set_max_step(body.position)
    if f.max_step != body.position:
        app_state.log(f"⚠ Il firmware ha mantenuto max = {f.max_step} (richiesto {body.position})")
    else:
        app_state.log(f"Max passi del firmware impostato a {f.max_step}")
    return f.describe()


@api.post("/api/focuser/motor")
@guard
async def focuser_motor(body: MotorSetting):
    not_running()
    f = need_focuser()
    motor = await f.set_motor(body.name, body.value)
    app_state.log(f"Motore: {body.name} = {motor.get(body.name)}")
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
        raise ValueError("Disponibile solo con il simulatore")
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
        raise ValueError("Il fine corsa inferiore non può essere negativo")
    if body.limit_max is not None and body.limit_max <= body.limit_min:
        raise ValueError("Il fine corsa superiore deve essere maggiore di quello inferiore")
    f = app_state.focuser
    if f and f.max_step and body.limit_max and body.limit_max > f.max_step:
        raise ValueError(f"Il fine corsa superiore supera il max del firmware ({f.max_step}): "
                         "aumenta prima il max del firmware")
    app_state.cfg["limit_min"] = body.limit_min
    app_state.cfg["limit_max"] = body.limit_max
    if body.toward_specimen in ("increasing", "decreasing"):
        app_state.cfg["toward_specimen"] = body.toward_specimen
    store.save(app_state.cfg)
    app_state.apply_limits()
    app_state.log(f"Fine corsa: {body.limit_min} – {body.limit_max if body.limit_max is not None else 'max firmware'}")
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
    app_state.log(f"Zero impostato sulla posizione {shift}: limiti e sequenza traslati di −{shift}")
    return {"ok": True}


@api.post("/api/mechanics")
@guard
async def set_mechanics(body: MechanicsBody):
    if body.mode not in ("manual", "computed"):
        raise ValueError("Modalità non valida")
    if body.motor_steps_per_rev <= 0 or body.gear_ratio <= 0 or body.um_per_knob_rev <= 0:
        raise ValueError("I valori meccanici devono essere positivi")
    data = body.model_dump()
    um = data.pop("um_per_step")
    app_state.cfg["mechanics"].update(data)
    if um is not None and um > 0:
        app_state.cfg["um_per_step"] = um
    store.save(app_state.cfg)
    app_state.log(f"Meccanica aggiornata: {app_state.um_per_step():.4f} µm/passo")
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


@api.post("/api/camera/detect")
@guard
async def camera_detect():
    cams = await GPhotoCamera.detect()
    app_state.log(f"Fotocamere rilevate: {', '.join(c['model'] for c in cams) or 'nessuna'}")
    return cams


@api.post("/api/camera/connect")
@guard
async def camera_connect(body: CameraConnect):
    not_running()
    if app_state.camera:
        await app_state.camera.disconnect()
        app_state.camera = None
    cam = SimulatedCamera() if body.simulate else GPhotoCamera(body.model, body.port)
    app_state.log(f"Connessione fotocamera {body.model or ('simulata' if body.simulate else 'automatica')}…")
    await cam.connect()
    app_state.camera = cam
    app_state.log(f"Fotocamera connessa: {cam.model}")
    return cam.describe()


@api.post("/api/camera/disconnect")
@guard
async def camera_disconnect():
    not_running()
    if app_state.camera:
        await app_state.camera.disconnect()
        app_state.camera = None
        app_state.log("Fotocamera disconnessa")
    return {"ok": True}


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
    app_state.log(f"{body.name} = {actual}" + ("" if actual == body.value else f" (richiesto {body.value})"))
    return settings


@api.post("/api/camera/test")
@guard
async def camera_test(body: TestShot):
    not_running()
    cam = need_camera()
    test_dir = Path(store.CONFIG_DIR) / "test-shots"
    test_dir.mkdir(parents=True, exist_ok=True)
    # tiene solo gli ultimi scatti di prova
    old = sorted(test_dir.iterdir(), key=lambda p: p.stat().st_mtime)
    for p in old[:-20]:
        p.unlink(missing_ok=True)
    app_state.log("Scatto di prova…")
    files = await cam.capture(mode="download", dest_base=test_dir / f"prova_{time.strftime('%H%M%S')}",
                              bulb_s=body.bulb_s)
    f = app_state.focuser
    app_state.add_shot(files, "test", f.position if f and f.connected else None,
                       f.temperature if f and f.connected else None)
    app_state.log(f"Scatto di prova completato ({len(files)} file)")
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
        raise HTTPException(404, "Scatto di una sessione precedente")
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
        raise ValueError("Il passo deve essere almeno 1")
    if body.capture_mode not in ("download", "card", "trigger"):
        raise ValueError("Modalità di scatto non valida")
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


class PresetBody(BaseModel):
    name: str
    data: dict | None = None


def validate_output_root(raw: str) -> str:
    """Normalizza la cartella di salvataggio, la crea se manca e verifica che sia scrivibile."""
    import os
    path = Path(raw.strip()).expanduser()
    if not raw.strip() or not path.is_absolute():
        raise ValueError("Indica un percorso completo, per esempio ~/Pictures/FocusStack")
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ValueError(f"Impossibile creare la cartella {path}: permesso negato o disco non disponibile") from exc
    if not path.is_dir() or not os.access(path, os.W_OK):
        raise ValueError(f"Non è possibile scrivere nella cartella {path}")
    return str(path)


@api.post("/api/settings")
@guard
async def save_settings(body: SettingsBody):
    if body.output_root is not None:
        app_state.cfg["output_root"] = validate_output_root(body.output_root)
        app_state.log(f"Cartella di salvataggio: {app_state.cfg['output_root']}")
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
        "-e", 'set f to choose folder with prompt "Cartella in cui salvare gli scatti" '
              'default location (POSIX file (item 1 of argv))',
        "-e", "return POSIX path of f",
        "-e", "end run",
        str(start),
    ]
    proc = await asyncio.create_subprocess_exec("osascript", *script, stdout=asyncio.subprocess.PIPE,
                                                stderr=asyncio.subprocess.PIPE)
    out, err = await proc.communicate()
    if proc.returncode != 0:
        if b"-128" in err:            # l'utente ha premuto Annulla
            return {"cancelled": True}
        raise RuntimeError(f"Impossibile aprire la finestra di selezione: {err.decode().strip()}")
    app_state.cfg["output_root"] = validate_output_root(out.decode().strip().rstrip("/") or "/")
    store.save(app_state.cfg)
    app_state.log(f"Cartella di salvataggio: {app_state.cfg['output_root']}")
    return {"path": app_state.cfg["output_root"]}


@api.post("/api/presets/save")
async def preset_save(body: PresetBody):
    if not body.name.strip() or body.data is None:
        raise HTTPException(400, "Nome e dati obbligatori")
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
        raise HTTPException(400, "Nessuna sequenza scaricata da aprire")
    images = sorted(p for p in Path(folder).iterdir()
                    if p.suffix.lower() != ".json" and not p.name.startswith("."))
    if not images:
        raise HTTPException(400, "La cartella non contiene immagini")
    for app_name in ("Helicon Focus 8", "Helicon Focus 7", "Helicon Focus", "HeliconFocus"):
        proc = subprocess.run(["open", "-a", app_name, *map(str, images)], capture_output=True)
        if proc.returncode == 0:
            app_state.log(f"Aperte {len(images)} immagini in {app_name}")
            return {"ok": True}
    raise HTTPException(400, "Helicon Focus non trovato in /Applications")


# ---------------- file statici (PWA) ----------------
@api.get("/sw.js")
async def service_worker():
    return FileResponse(WEB_DIR / "sw.js", media_type="text/javascript",
                        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"})


@api.get("/manifest.webmanifest")
async def manifest():
    return Response((WEB_DIR / "manifest.webmanifest").read_text(), media_type="application/manifest+json")


api.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
