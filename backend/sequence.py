"""Motore delle sequenze di focus stacking: muovi -> attendi -> verifica -> scatta -> ripeti."""
from __future__ import annotations

import asyncio
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from . import summary
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
    shots_per_position: int = 1  # più scatti per posizione: la media la fa il software di fusione

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
    repeats: int = 1             # scatti per posizione
    repeat: int = 0              # scatto in corso nella posizione (0 = primo)


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

    def reset(self) -> bool:
        """Riporta lo stato a "pronta" (nuovo progetto): dimentica la sequenza finita e la sua cartella.
        Non fa nulla durante una sequenza. I file sul disco non si toccano."""
        if self.busy:
            return False
        self.status = SequenceStatus()
        return True

    def start(self, params: SequenceParams, context: dict | None = None) -> None:
        """context: dati per il manifesto (software, µm/passo, verso di z, ottica, filtro…)."""
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
        ctx = {"um_per_step": 0.0, "z_sign": 1, **(context or {})}
        self._task = asyncio.create_task(self._run(params, ctx))

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

    async def _run(self, p: SequenceParams, ctx: dict) -> None:
        focuser, camera = self._focuser(), self._camera()
        positions = p.positions()
        repeats = max(1, int(p.shots_per_position or 1))
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in p.session_name) or "stack"
        # ogni sequenza ha sempre una cartella nuova, anche se ne parte un'altra nello stesso secondo
        folder = Path(p.output_root).expanduser() / f"{safe_name}_{stamp}"
        n = 2
        while folder.exists():
            folder = Path(p.output_root).expanduser() / f"{safe_name}_{stamp}-{n}"
            n += 1
        download = p.capture_mode == "download"
        manifest = build_manifest(p, ctx, positions, repeats)
        frames: list[dict] = manifest["frames"]
        um, z_sign = ctx["um_per_step"], ctx["z_sign"]

        summary_error: list = []

        def write_meta(state: str) -> None:
            manifest["state"] = state
            manifest["updated"] = now_iso()
            data = manifest
            if state != "running":   # "finished" subito dopo "updated", per leggibilità
                data = {}
                for key, value in manifest.items():
                    data[key] = value
                    if key == "updated":
                        data["finished"] = value
            write_atomic(folder / "sequence.json", data)
            # riepilogo per le persone, nella lingua dell'app: un errore qui non ferma la sequenza
            try:
                write_text_atomic(folder / "sequence.txt", summary.render(data))
            except Exception as exc:  # noqa: BLE001
                if not summary_error:
                    summary_error.append(exc)
                    self._log(tr("Impossibile scrivere sequence.txt: {exc}", exc=exc))

        # Il manifesto si scrive in tutte le modalità: con "solo scheda" o "solo trigger" la cartella
        # contiene solo sequence.json (posizioni e orari, da abbinare ai file della scheda in ordine).
        meta_ok = True
        try:
            folder.mkdir(parents=True, exist_ok=True)
            write_meta("running")
        except OSError as exc:
            if download:
                raise
            meta_ok = False
            self._log(tr("Impossibile scrivere sequence.json: {exc}", exc=exc))

        def save_meta(state: str) -> None:
            if meta_ok:
                write_meta(state)

        self.status = SequenceStatus(state="running", total=len(positions), started_at=time.time(),
                                     folder=str(folder) if meta_ok else None,
                                     start=p.start, end=p.end, step=p.step, repeats=repeats)
        self._log(tr("Avvio sequenza: {n} scatti da {start} a {end}, passo {step}",
                     n=len(positions), start=p.start, end=p.end, step=p.step)
                  + (" · " + tr("{k} scatti per posizione", k=repeats) if repeats > 1 else ""))
        shot_times: list[float] = []
        try:
            approach = p.approach_position()
            if approach is not None:
                self._log(tr("Compensazione gioco: passaggio da {pos}", pos=approach))
                await focuser.move_to(approach, wait=True)
            for i, pos in enumerate(positions):
                t0 = time.time()
                self.status.index = i
                self.status.current_target = pos
                frame = {"index": i, "z_um": round((pos - p.start) * um * z_sign, 4) if um else None,
                         "position_steps": pos, "temperature_c": None, "exposures": []}
                if not um:
                    frame.pop("z_um")
                k, need_move = 0, True
                while k < repeats:
                    await self._checkpoint()
                    self.status.repeat = k
                    if need_move:
                        await focuser.move_to(pos, wait=True)
                        await self._checkpoint()
                        await asyncio.sleep(p.settle_ms / 1000)
                        need_move = False
                    # Verifica che nessuno abbia mosso il motore (pulsanti fisici) durante l'attesa.
                    await focuser.poll(with_temp=True)
                    if focuser.position != pos or focuser.moving:
                        self.pause(tr("movimento manuale rilevato ({actual} invece di {pos}). "
                                      "Premi Riprendi per ripetere lo scatto", actual=focuser.position, pos=pos))
                        await self._checkpoint()
                        need_move = True
                        continue  # torna alla posizione e ripete lo scatto
                    if repeats > 1:
                        base = folder / f"{safe_name}_{i + 1:04d}_{k + 1}" if download else None
                    else:
                        base = folder / f"{safe_name}_{i + 1:04d}" if download else None
                    shot_time = now_iso()
                    files = await camera.capture(mode=p.capture_mode, dest_base=base, bulb_s=p.bulb_s,
                                                 mirror_s=p.mirror_delay_ms / 1000)
                    if frame["temperature_c"] is None and focuser.temperature is not None:
                        frame["temperature_c"] = round(focuser.temperature, 2)
                    exposure = {"repeat": k, "time": shot_time, "files": [Path(f).name for f in files]}
                    if focuser.temperature is not None:
                        exposure["temperature_c"] = round(focuser.temperature, 2)
                    frame["exposures"].append(exposure)
                    if k == 0:
                        frames.append(frame)
                    save_meta("running")
                    record = {"index": i + 1, "repeat": k + 1, "repeats": repeats, "position": pos,
                              "temperature": focuser.temperature, "time": shot_time, "files": files}
                    self.status.files.extend(files)
                    self._on_shot(record)
                    temp = f", {focuser.temperature:.1f} °C" if focuser.temperature is not None else ""
                    label = tr("Scatto {i}/{n} @ {pos}", i=i + 1, n=len(positions), pos=pos)
                    if repeats > 1:
                        label += f" ({k + 1}/{repeats})"
                    self._log(label + temp + (f" → {Path(files[0]).name}" if files else ""))
                    await asyncio.sleep(p.post_shot_ms / 1000)
                    k += 1
                shot_times.append(time.time() - t0)
                self.status.index = i + 1
                avg = sum(shot_times[-5:]) / len(shot_times[-5:])
                self.status.eta_s = avg * (len(positions) - i - 1)
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
                save_meta({"done": "completed", "idle": "interrupted"}.get(self.status.state, self.status.state))
            except OSError:
                pass
            if p.return_to_start and not self._stop and focuser.connected:
                try:
                    await focuser.move_to(p.start, wait=False)
                    self._log(tr("Ritorno alla posizione iniziale {pos}", pos=p.start))
                except Exception as exc:  # noqa: BLE001
                    self._log(tr("Ritorno all'inizio fallito: {exc}", exc=exc))


# ---------------- manifesto della pila (sequence.json) ----------------
MANIFEST_FORMAT = "focus-stack-manifest"
MANIFEST_VERSION = 1


def now_iso() -> str:
    """Ora locale ISO 8601 con millisecondi e fuso orario (es. 2026-11-12T14:03:12.480+01:00)."""
    return datetime.now().astimezone().isoformat(timespec="milliseconds")


def write_atomic(path: Path, data: dict) -> None:
    """Scrive su un file temporaneo e poi lo rinomina: il file resta sempre valido."""
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def write_text_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def build_manifest(p: SequenceParams, ctx: dict, positions: list[int], repeats: int) -> dict:
    """Intestazione del manifesto; "frames" viene riempito durante la sequenza.

    Regola dei campi: assente = non si sa; null = "nessuno" (solo per il filtro).
    """
    um, z_sign = ctx["um_per_step"], ctx["z_sign"]
    direction = 1 if p.end >= p.start else -1
    rail = {"model": ctx.get("rail_model"), "firmware": ctx.get("firmware"),
            "position_feedback": "open_loop",
            "settle_ms": p.settle_ms, "post_shot_ms": p.post_shot_ms}
    if um:
        rail["um_per_step"] = um
        rail["um_per_step_source"] = ctx.get("um_per_step_source")
    if ctx.get("microstep"):
        rail["microstep"] = ctx["microstep"]
    if p.backlash > 0:
        rail["backlash_overshoot_steps"] = p.backlash
        if um:
            rail["backlash_overshoot_um"] = round(p.backlash * um, 4)
    # verso di avvicinamento: lo stesso per tutti i fotogrammi (la compensazione del gioco lo garantisce)
    rail["approach"] = "toward_objective" if direction * z_sign > 0 else "away_from_objective"
    rail = {k: v for k, v in rail.items() if v is not None}

    sequence = {"start_steps": p.start, "end_steps": p.end, "step_steps": p.step,
                "positions": len(positions), "shots_per_position": repeats,
                "capture_mode": p.capture_mode, "mirror_delay_ms": p.mirror_delay_ms,
                "return_to_start": p.return_to_start}
    if um:
        sequence["step_um"] = round(p.step * um, 3)
        sequence["span_um"] = round(abs(p.end - p.start) * um, 3)
    if p.bulb_s:
        sequence["bulb_s"] = p.bulb_s

    m = {"format": MANIFEST_FORMAT, "version": MANIFEST_VERSION,
         "software": ctx.get("software"), "state": "running",
         "started": now_iso(), "updated": None, "session_name": p.session_name,
         "z_axis": {"unit": "um", "origin": "first_frame", "positive": "toward_objective",
                    "note": "z_um = height of the focal plane relative to frame 0; "
                            "larger values are closer to the objective"},
         "rail": rail, "sequence": sequence}
    if ctx.get("camera"):
        m["camera"] = ctx["camera"]
    for key in ("optics", "illumination"):
        if ctx.get(key):
            m[key] = ctx[key]
    if "filter" in ctx:          # None = nessun filtro; chiave assente = non indicato
        m["filter"] = ctx["filter"]
    if ctx.get("notes"):
        m["notes"] = ctx["notes"]
    if ctx.get("optics_profile"):
        m["optics_profile"] = ctx["optics_profile"]
    m["frames"] = []
    m["extra"] = {}
    return m
