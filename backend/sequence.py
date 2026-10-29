"""Motore delle sequenze di focus stacking: muovi -> attendi -> verifica -> scatta -> ripeti."""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from .i18n import tr


@dataclass
class SequenceParams:
    start: int
    end: int
    step: int
    settle_ms: int = 1500        # attesa anti-vibrazione dopo il movimento
    post_shot_ms: int = 500      # pausa dopo lo scatto (scrittura card, flash...)
    mirror_delay_ms: int = 0     # reflex: attesa fra sollevamento dello specchio e scatto
    backlash: int = 0            # overshoot per avvicinarsi sempre dalla stessa direzione
    return_to_start: bool = True
    capture_mode: str = "download"   # download | card | trigger
    session_name: str = "stack"
    output_root: str = ""
    bulb_s: float = 0            # >0 = posa B controllata dal computer

    def positions(self) -> list[int]:
        step = abs(int(self.step)) or 1
        direction = 1 if self.end >= self.start else -1
        pos, out = self.start, []
        while (pos - self.end) * direction <= 0:
            out.append(pos)
            pos += step * direction
        if out[-1] != self.end:
            out.append(self.end)
        return out

    def approach_position(self) -> int | None:
        """Posizione da cui partire per recuperare il gioco (None se non serve)."""
        if self.backlash <= 0:
            return None
        direction = 1 if self.end >= self.start else -1
        return self.start - direction * self.backlash


@dataclass
class SequenceStatus:
    state: str = "idle"          # idle | running | paused | stopping | done | error
    index: int = 0
    total: int = 0
    current_target: int | None = None
    started_at: float | None = None
    eta_s: float | None = None
    folder: str | None = None
    files: list[str] = field(default_factory=list)
    message: str = ""
    start: int | None = None
    end: int | None = None
    step: int | None = None


class SequenceRunner:
    def __init__(self, focuser_getter: Callable, camera_getter: Callable, log: Callable[[str], None],
                 on_shot: Callable[[dict], None] | None = None):
        self._focuser = focuser_getter
        self._camera = camera_getter
        self._log = log
        self._on_shot = on_shot or (lambda _r: None)
        self.status = SequenceStatus()
        self._task: asyncio.Task | None = None
        self._resume = asyncio.Event()
        self._resume.set()
        self._stop = False

    @property
    def busy(self) -> bool:
        return self._task is not None and not self._task.done()

    def start(self, params: SequenceParams) -> None:
        if self.busy:
            raise RuntimeError(tr("Sequenza già in corso"))
        focuser = self._focuser()
        if focuser is None:
            raise RuntimeError(tr("Focheggiatore non connesso"))
        if self._camera() is None:
            raise RuntimeError(tr("Fotocamera non connessa"))
        # Verifica preventiva: nessun movimento della sequenza deve uscire dai fine corsa.
        focuser.check(params.start)
        focuser.check(params.end)
        approach = params.approach_position()
        if approach is not None:
            try:
                focuser.check(approach)
            except Exception as exc:
                raise RuntimeError(tr("La compensazione del gioco porterebbe fuori dai limiti: {exc}. "
                                      "Riduci il gioco o sposta l'inizio.", exc=exc)) from exc
        self._stop = False
        self._resume.set()
        self._task = asyncio.create_task(self._run(params))

    def pause(self, reason: str = "") -> None:
        if self.busy and self.status.state == "running":
            self._resume.clear()
            self.status.state = "paused"
            self.status.message = reason
            self._log(tr("Sequenza in pausa: {reason}", reason=reason) if reason else tr("Sequenza in pausa"))

    def resume(self) -> None:
        if self.busy and self.status.state == "paused":
            self.status.state = "running"
            self.status.message = ""
            self._resume.set()
            self._log(tr("Sequenza ripresa"))

    async def stop(self) -> None:
        if not self.busy:
            return
        self._stop = True
        self.status.state = "stopping"
        self._resume.set()
        focuser = self._focuser()
        if focuser:
            await focuser.halt()

    async def _checkpoint(self) -> None:
        await self._resume.wait()
        if self._stop:
            raise asyncio.CancelledError

    async def _run(self, p: SequenceParams) -> None:
        focuser, camera = self._focuser(), self._camera()
        positions = p.positions()
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in p.session_name) or "stack"
        folder = Path(p.output_root).expanduser() / f"{safe_name}_{stamp}"
        download = p.capture_mode == "download"
        shots: list[dict] = []

        def write_meta(state: str) -> None:
            if download:
                (folder / "sequence.json").write_text(json.dumps(
                    {"state": state, "params": asdict(p), "positions": positions,
                     "camera": {k: v for k, v in camera.describe().items() if k != "busy"},
                     "focuser": {"firmware": focuser.firmware, "motor": focuser.motor},
                     "shots": shots}, indent=2, ensure_ascii=False))

        if download:
            folder.mkdir(parents=True, exist_ok=True)
            write_meta("running")

        self.status = SequenceStatus(state="running", total=len(positions), started_at=time.time(),
                                     folder=str(folder) if download else None,
                                     start=p.start, end=p.end, step=p.step)
        self._log(tr("Avvio sequenza: {n} scatti da {start} a {end}, passo {step}",
                     n=len(positions), start=p.start, end=p.end, step=p.step))
        shot_times: list[float] = []
        try:
            approach = p.approach_position()
            if approach is not None:
                self._log(tr("Compensazione gioco: passaggio da {pos}", pos=approach))
                await focuser.move_to(approach, wait=True)
            i = 0
            while i < len(positions):
                pos = positions[i]
                await self._checkpoint()
                t0 = time.time()
                self.status.index = i
                self.status.current_target = pos
                await focuser.move_to(pos, wait=True)
                await self._checkpoint()
                await asyncio.sleep(p.settle_ms / 1000)
                # Verifica che nessuno abbia mosso il motore (pulsanti fisici) durante l'attesa.
                await focuser.poll(with_temp=True)
                if focuser.position != pos or focuser.moving:
                    self.pause(tr("movimento manuale rilevato ({actual} invece di {pos}). "
                                  "Premi Riprendi per ripetere lo scatto", actual=focuser.position, pos=pos))
                    await self._checkpoint()
                    continue  # ripete la stessa posizione
                base = folder / f"{safe_name}_{i + 1:04d}" if download else None
                files = await camera.capture(mode=p.capture_mode, dest_base=base, bulb_s=p.bulb_s,
                                             mirror_s=p.mirror_delay_ms / 1000)
                record = {"index": i + 1, "position": pos, "temperature": focuser.temperature,
                          "time": datetime.now().isoformat(timespec="seconds"), "files": files}
                shots.append(record)
                self.status.files.extend(files)
                self._on_shot(record)
                temp = f", {focuser.temperature:.1f} °C" if focuser.temperature is not None else ""
                self._log(tr("Scatto {i}/{n} @ {pos}", i=i + 1, n=len(positions), pos=pos) + temp
                          + (f" → {Path(files[0]).name}" if files else ""))
                await asyncio.sleep(p.post_shot_ms / 1000)
                shot_times.append(time.time() - t0)
                self.status.index = i + 1
                avg = sum(shot_times[-5:]) / len(shot_times[-5:])
                self.status.eta_s = avg * (len(positions) - i - 1)
                i += 1
            self.status.state = "done"
            self.status.message = tr("Sequenza completata")
            self._log(tr("Sequenza completata"))
        except asyncio.CancelledError:
            self.status.state = "idle"
            self.status.message = tr("Sequenza interrotta")
            self._log(tr("Sequenza interrotta dall'utente"))
        except Exception as exc:  # noqa: BLE001
            if self._stop:  # l'halt durante un movimento genera un errore di posizione: è un'interruzione
                self.status.state = "idle"
                self.status.message = tr("Sequenza interrotta")
                self._log(tr("Sequenza interrotta dall'utente"))
            else:
                self.status.state = "error"
                self.status.message = str(exc)
                self._log(tr("ERRORE sequenza: {exc}", exc=exc))
        finally:
            self.status.eta_s = None
            try:
                write_meta(self.status.state)
            except OSError:
                pass
            if p.return_to_start and not self._stop and focuser.connected:
                try:
                    await focuser.move_to(p.start, wait=False)
                    self._log(tr("Ritorno alla posizione iniziale {pos}", pos=p.start))
                except Exception as exc:  # noqa: BLE001
                    self._log(tr("Ritorno all'inizio fallito: {exc}", exc=exc))
