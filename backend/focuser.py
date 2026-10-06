"""Driver seriale per myFocuserPro2 (Robert Brown) + simulatore.

Protocollo (riferimento: driver INDI drivers/focuser/myfocuserpro2.cpp):
  comando  ":" + 2 cifre + argomento opzionale + "#"   es. ":05012345#"
  risposta  1 carattere prefisso + valore + "#"          es. "P12345#"
  I comandi di impostazione/movimento NON restituiscono risposta.

Fine corsa: il firmware conosce solo 0 e "max passi". Questo driver aggiunge
limiti software (limit_min / limit_max): ogni movimento comandato dall'app
viene verificato prima di essere inviato. I pulsanti fisici del focheggiatore
non passano dall'app: per loro valgono solo 0 e il max del firmware, più il
watchdog del server che invia STOP se la posizione esce dai limiti.
"""
from __future__ import annotations

import asyncio
import glob
import math
import threading
import time

import serial
from serial.tools import list_ports


def list_serial_ports() -> list[dict]:
    ports = []
    for p in list_ports.comports():
        # Su macOS usare /dev/cu.* (non /dev/tty.* che attende il carrier detect)
        dev = p.device.replace("/dev/tty.", "/dev/cu.")
        if "Bluetooth" in dev or "debug-console" in dev:
            continue
        ports.append({"device": dev, "description": p.description or "", "hwid": p.hwid or ""})
    known = {p["device"] for p in ports}
    for dev in sorted(glob.glob("/dev/cu.usb*") + glob.glob("/dev/cu.wchusb*")):
        if dev not in known:
            ports.append({"device": dev, "description": "", "hwid": ""})
    return ports


class FocuserError(Exception):
    pass


class LimitError(FocuserError):
    pass


# Impostazioni motore del firmware: nome -> (comando get, formato comando set, tipo)
MOTOR_SETTINGS: dict[str, tuple[str, str, type]] = {
    "step_mode": (":29#", ":30{}#", int),          # 1,2,4,...,256 (microstep)
    "speed": (":43#", ":150{}#", int),             # 0 lenta, 1 media, 2 veloce
    "coil_power": (":11#", ":12{}#", bool),        # bobine alimentate a motore fermo
    "reverse": (":13#", ":14{}#", bool),           # inversione verso di rotazione
    "backlash_in_enabled": (":74#", ":73{}#", bool),
    "backlash_in_steps": (":78#", ":77{}#", int),
    "backlash_out_enabled": (":76#", ":75{}#", bool),
    "backlash_out_steps": (":80#", ":79{}#", int),
}


class MyFocuserPro2:
    simulated = False

    def __init__(self, port: str, baud: int = 9600):
        self.port = port
        self.baud = baud
        self._ser: serial.Serial | None = None
        self._lock = threading.Lock()
        self.position = 0
        self.moving = False
        self.temperature: float | None = None
        self.max_step: int | None = None
        self.firmware: str | None = None
        self.fs_build: int | None = None   # build del firmware Focus Stack (:97#); None = firmware originale
        self.has_temp_probe = False
        self.motor: dict = {}
        self.limit_min = 0
        self.limit_max: int | None = None
        # True mentre è in corso un movimento comandato dall'app (per distinguere i pulsanti fisici)
        self.commanded = False
        self._cmd_time = 0.0
        self._last_polled_position: int | None = None

    def _mark_commanded(self) -> None:
        self.commanded = True
        self._cmd_time = time.monotonic()

    def _update_commanded(self) -> None:
        # Il movimento resta "comandato" finché il motore non è fermo anche nella posizione:
        # con le rampe del firmware l'ultimo tratto fra due letture può essere lungo e non va
        # scambiato per una pressione dei pulsanti fisici.
        settled = self.position == self._last_polled_position
        self._last_polled_position = self.position
        if self.commanded and not self.moving and settled and time.monotonic() - self._cmd_time > 0.8:
            self.commanded = False

    @property
    def connected(self) -> bool:
        return self._ser is not None and self._ser.is_open

    # ---------- I/O di basso livello (bloccante, eseguito in thread) ----------
    def _open(self) -> None:
        self._ser = serial.Serial(self.port, self.baud, timeout=2, write_timeout=2)
        # L'apertura della porta asserisce DTR e resetta l'Arduino: attendere il boot.
        time.sleep(2.0)
        self._ser.reset_input_buffer()

    def _query(self, cmd: str, timeout: float = 2.0) -> str:
        with self._lock:
            ser = self._ser
            if ser is None:
                raise FocuserError("Non connesso")
            ser.timeout = timeout
            ser.reset_input_buffer()
            ser.write(cmd.encode("ascii"))
            ser.flush()
            raw = ser.read_until(b"#", 32)
        if not raw.endswith(b"#"):
            raise FocuserError(f"Nessuna risposta a {cmd}")
        return raw.decode("ascii", "replace")[:-1]

    def _send(self, cmd: str) -> None:
        with self._lock:
            if self._ser is None:
                raise FocuserError("Non connesso")
            self._ser.reset_input_buffer()
            self._ser.write(cmd.encode("ascii"))
            self._ser.flush()

    def _value(self, cmd: str, timeout: float = 2.0) -> str:
        # Rimuove esattamente un carattere di prefisso (alcuni prefissi sono cifre).
        return self._query(cmd, timeout)[1:]

    def _connect_blocking(self) -> None:
        self._open()
        last_exc: Exception | None = None
        for _ in range(3):
            try:
                reply = self._query(":03#")
                if reply.startswith("F"):
                    self.firmware = reply[1:]
                    break
            except FocuserError as exc:
                last_exc = exc
                time.sleep(0.5)
        else:
            self._close_blocking()
            raise FocuserError(f"Il dispositivo non risponde come myFocuserPro2 ({last_exc})")
        self._send(":16#")  # temperatura in °C
        self.max_step = int(self._value(":08#"))
        try:
            self.fs_build = int(self._value(":97#", 0.8))  # i firmware non Focus Stack non rispondono
        except (FocuserError, ValueError):
            self.fs_build = None
        try:
            self.has_temp_probe = self._value(":83#", 0.8) == "1"
        except FocuserError:
            self.has_temp_probe = False
        self._read_motor_blocking()
        self._poll_blocking(with_temp=True)

    def _read_motor_blocking(self) -> dict:
        out = {}
        for name, (get_cmd, _, kind) in MOTOR_SETTINGS.items():
            try:
                raw = self._value(get_cmd, 0.8)
                out[name] = (raw == "1") if kind is bool else int(raw)
            except (FocuserError, ValueError):
                continue  # firmware più vecchi non implementano tutti i comandi
        self.motor = out
        return out

    def _close_blocking(self) -> None:
        if self._ser:
            try:
                self._ser.close()
            finally:
                self._ser = None

    def _poll_blocking(self, with_temp: bool = False) -> None:
        self.position = int(self._value(":00#"))
        self.moving = self._value(":01#") == "1"
        self._update_commanded()
        if with_temp and self.has_temp_probe:
            try:
                self.temperature = float(self._value(":06#"))
            except (FocuserError, ValueError):
                pass

    # ---------- limiti ----------
    def bounds(self) -> tuple[int, int | None]:
        lo = max(0, int(self.limit_min or 0))
        hi_candidates = [v for v in (self.limit_max, self.max_step) if v is not None]
        hi = min(hi_candidates) if hi_candidates else None
        return lo, hi

    def check(self, pos: int) -> int:
        lo, hi = self.bounds()
        if pos < lo or (hi is not None and pos > hi):
            raise LimitError(f"Posizione {pos} fuori dai fine corsa ({lo} – {hi if hi is not None else '∞'})")
        return int(pos)

    def clamp(self, pos: int) -> int:
        lo, hi = self.bounds()
        pos = max(lo, int(pos))
        return min(pos, hi) if hi is not None else pos

    # ---------- API asincrona ----------
    async def connect(self) -> None:
        await asyncio.to_thread(self._connect_blocking)

    async def disconnect(self) -> None:
        await asyncio.to_thread(self._close_blocking)

    async def poll(self, with_temp: bool = False) -> None:
        await asyncio.to_thread(self._poll_blocking, with_temp)

    async def move_to(self, pos: int, wait: bool = False, timeout: float = 600) -> None:
        pos = self.check(pos)
        self._mark_commanded()
        await asyncio.to_thread(self._send, f":05{pos}#")
        self.moving = True
        if wait:
            await self.wait_idle(timeout, target=pos)

    async def wait_idle(self, timeout: float = 600, target: int | None = None) -> None:
        deadline = time.monotonic() + timeout
        await asyncio.sleep(0.15)
        while True:
            await self.poll()
            if not self.moving:
                if target is not None and self.position != target:
                    raise FocuserError(f"Movimento terminato a {self.position} invece di {target}")
                return
            if time.monotonic() > deadline:
                raise FocuserError("Timeout movimento")
            await asyncio.sleep(0.1)

    async def halt(self) -> None:
        await asyncio.to_thread(self._send, ":27#")

    async def sync(self, pos: int) -> None:
        await asyncio.to_thread(self._send, f":31{max(0, int(pos))}#")
        await self.poll()

    async def set_max_step(self, value: int) -> None:
        await asyncio.to_thread(self._send, f":07{int(value):06d}#")
        await asyncio.sleep(0.1)
        self.max_step = int(await asyncio.to_thread(self._value, ":08#"))

    async def read_motor(self) -> dict:
        return await asyncio.to_thread(self._read_motor_blocking)

    async def set_motor(self, name: str, value) -> dict:
        if name not in MOTOR_SETTINGS:
            raise FocuserError(f"Impostazione motore sconosciuta: {name}")
        _, set_fmt, kind = MOTOR_SETTINGS[name]
        arg = int(bool(value)) if kind is bool else int(value)
        if name == "step_mode" and arg not in (1, 2, 4, 8, 16, 32, 64, 128, 256):
            raise FocuserError("Microstep non valido")
        if name == "speed" and arg not in (0, 1, 2):
            raise FocuserError("Velocità non valida")
        await asyncio.to_thread(self._send, set_fmt.format(arg))
        await asyncio.sleep(0.1)
        return await self.read_motor()

    def describe(self) -> dict:
        lo, hi = self.bounds()
        return {
            "connected": self.connected, "simulated": self.simulated, "port": self.port,
            "position": self.position, "moving": self.moving, "temperature": self.temperature,
            "has_temp_probe": self.has_temp_probe, "max_step": self.max_step, "firmware": self.firmware,
            "fs_build": self.fs_build,
            "motor": self.motor, "bounds": [lo, hi],
        }


class SimulatedFocuser(MyFocuserPro2):
    """Simula motore (circa 400 passi/s), sonda di temperatura e impostazioni del firmware."""
    simulated = True
    SPEED = 400.0

    def __init__(self):
        super().__init__("simulatore")
        self._open_flag = False
        self._target = 5000
        self._pos = 5000.0
        self._t = time.monotonic()
        self.max_step = 50000
        self.firmware = "SIM"
        self.temperature = 21.5
        self.has_temp_probe = True
        self.motor = {"step_mode": 1, "speed": 2, "coil_power": True, "reverse": False,
                      "backlash_in_enabled": False, "backlash_in_steps": 0,
                      "backlash_out_enabled": False, "backlash_out_steps": 0}

    @property
    def connected(self) -> bool:
        return self._open_flag

    def _advance(self) -> None:
        now = time.monotonic()
        dt, self._t = now - self._t, now
        delta = self._target - self._pos
        step = self.SPEED * dt
        self._pos = float(self._target) if abs(delta) <= step else self._pos + step * (1 if delta > 0 else -1)
        self.position = int(round(self._pos))
        self.moving = self.position != self._target

    def simulate_button(self, delta: int) -> None:
        """Simula la pressione dei pulsanti fisici (ignora i limiti software, rispetta 0 e max)."""
        self._advance()
        self._target = max(0, min(self.max_step, self.position + delta))

    async def connect(self) -> None:
        await asyncio.sleep(0.3)
        self._open_flag = True
        self._t = time.monotonic()
        self._advance()

    async def disconnect(self) -> None:
        self._open_flag = False

    async def poll(self, with_temp: bool = False) -> None:
        self._advance()
        self._update_commanded()
        if with_temp:
            self.temperature = round(21.5 + 0.6 * math.sin(time.time() / 300), 2)

    async def move_to(self, pos: int, wait: bool = False, timeout: float = 600) -> None:
        pos = self.check(pos)
        self._mark_commanded()
        self._advance()
        self._target = pos
        self.moving = self._target != self.position
        if wait:
            await self.wait_idle(timeout, target=self._target)

    async def halt(self) -> None:
        self._advance()
        self._target = self.position
        self._pos = float(self.position)

    async def sync(self, pos: int) -> None:
        self._advance()
        self._target = self.position = max(0, int(pos))
        self._pos = float(self._target)

    async def set_max_step(self, value: int) -> None:
        self.max_step = int(value)

    async def read_motor(self) -> dict:
        return self.motor

    async def set_motor(self, name: str, value) -> dict:
        if name not in MOTOR_SETTINGS:
            raise FocuserError(f"Impostazione motore sconosciuta: {name}")
        kind = MOTOR_SETTINGS[name][2]
        self.motor[name] = bool(value) if kind is bool else int(value)
        return self.motor
