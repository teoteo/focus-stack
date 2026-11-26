"""Motore delle sequenze di focus stacking: muovi -> attendi -> verifica -> scatta -> ripeti."""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable

from . import power, summary
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
    sound_on_end: bool = True    # suono sul Mac a fine sequenza (completata o errore)

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
    shots: int = 0               # scatti fatti finora (contando le ripetizioni)
    live_ok: bool = False        # il live view può restare acceso: la slitta sta ancora raggiungendo l'inizio


# suoni di sistema di macOS: uno chiaro se la sequenza è completata, uno grave se si è fermata per un errore
END_SOUND_OK = "/System/Library/Sounds/Glass.aiff"
END_SOUND_ERROR = "/System/Library/Sounds/Basso.aiff"


def play_end_sound(ok: bool, times: int = 3) -> None:
    """Suona a fine sequenza senza bloccare: afplay in un thread, ripetuto per farsi sentire anche da lontano."""
    sound = END_SOUND_OK if ok else END_SOUND_ERROR

    def run() -> None:
        for _ in range(times):
            try:
                subprocess.run(["afplay", sound], timeout=10, check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (OSError, subprocess.TimeoutExpired):
                return
    threading.Thread(target=run, daemon=True).start()


CAPTURE_RETRIES = 2     # nuovi tentativi dopo uno scatto fallito (prima dell'ultimo si ricollega la fotocamera)
RETRY_WAIT_S = 3        # attesa prima del primo nuovo tentativo (poi 6 s)


class _RepeatShot(Exception):
    """La sequenza è stata in pausa per la fotocamera e poi ripresa: si torna alla posizione e si ripete lo scatto."""


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
        self._hold_coils = False

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

    def start(self, params: SequenceParams, context: dict | None = None, hold_coils: bool = False) -> None:
        """context: dati per il manifesto (software, µm/passo, verso di z, ottica, filtro…).
        hold_coils: se il firmware spegne le bobine a motore fermo, le accende per la durata della sequenza."""
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
        self._hold_coils = hold_coils
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

    async def _reconnect(self, camera) -> bool:
        self._log(tr("Ricollego la fotocamera…"))
        try:
            await camera.reconnect()
            self._log(tr("Fotocamera ricollegata: {model}", model=camera.model))
            return True
        except Exception as exc:  # noqa: BLE001
            self._log(tr("Fotocamera non ricollegata: {exc}", exc=exc))
            return False

    async def _end_live(self, camera) -> None:
        """La slitta è al primo piano: il live view si spegne prima dell'attesa anti-vibrazione (Canon e Nikon
        abbassano lo specchio), così il primo scatto parte come senza live view. Fino a qui si poteva guardare
        il ritorno all'inizio. Lo spegne lo stream (main.live_frames, che vede live_ok falso); se nessuno lo
        guarda è già spento, altrimenti dopo 3 s lo spegne questa funzione."""
        self.status.live_ok = False
        for _ in range(30):
            if not getattr(camera, "live", False):
                return
            await asyncio.sleep(0.1)
        try:
            await camera.end_preview()
        except Exception as exc:  # noqa: BLE001
            self._log(tr("Live view non spento: {exc}", exc=exc))

    async def _capture(self, camera, p: SequenceParams, base: Path | None) -> list[str]:
        """Scatto con nuovi tentativi: se la fotocamera non risponde (sta ancora scrivendo il RAW precedente,
        in autofocus non trova il fuoco, oppure è sparita dall'USB) aspetta 3 s e riprova; al secondo errore
        ricollega la fotocamera e riprova dopo 6 s. Se non scatta ancora la sequenza va in PAUSA (non si
        ferma): si sistema la fotocamera, si preme Riprendi e lo scatto si ripete dalla stessa posizione."""
        last_exc: Exception | None = None
        for attempt in range(CAPTURE_RETRIES + 1):
            try:
                return await camera.capture(mode=p.capture_mode, dest_base=base, bulb_s=p.bulb_s,
                                            mirror_s=p.mirror_delay_ms / 1000)
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001  (errori di gphoto2 e della fotocamera)
                if self._stop:
                    raise
                last_exc = exc
                if attempt == CAPTURE_RETRIES:
                    break
                wait = RETRY_WAIT_S * (attempt + 1)
                msg = tr("Scatto non riuscito ({exc}): nuovo tentativo fra {s} s ({a} di {n})",
                         exc=exc, s=wait, a=attempt + 1, n=CAPTURE_RETRIES)
                self._log(msg)
                self.status.message = msg
                if attempt == CAPTURE_RETRIES - 1:   # forse la sessione USB non c'è più (stop del Mac, cavo)
                    await self._reconnect(camera)
                await asyncio.sleep(wait)
                await self._checkpoint()
                self.status.message = ""
        if p.sound_on_end:
            play_end_sound(False, times=1)
        self.pause(tr("la fotocamera non ha scattato dopo {n} tentativi ({exc}). Controlla che sia accesa e "
                      "collegata, batteria, scheda e messa a fuoco manuale (MF), poi premi Riprendi: lo scatto "
                      "si ripete dalla stessa posizione", n=CAPTURE_RETRIES + 1, exc=last_exc))
        await self._checkpoint()
        await self._reconnect(camera)
        raise _RepeatShot

    async def _run(self, p: SequenceParams, ctx: dict) -> None:
        focuser, camera = self._focuser(), self._camera()
        positions = p.positions()
        repeats = max(1, int(p.shots_per_position or 1))
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        # al massimo 80 caratteri: cartella e file (nome_0001_1.NEF, …) restano sotto i 255 byte di macOS
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in p.session_name)[:80] or "stack"
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
                                     start=p.start, end=p.end, step=p.step, repeats=repeats, live_ok=True)
        self._log(tr("Avvio sequenza: {n} scatti da {start} a {end}, passo {step}",
                     n=len(positions), start=p.start, end=p.end, step=p.step)
                  + (" · " + tr("{k} scatti per posizione", k=repeats) if repeats > 1 else ""))
        shot_times: list[float] = []
        awake_error = power.hold()   # niente stop del Mac durante la pila: sospenderebbe l'USB
        if awake_error:
            self._log(tr("Impossibile impedire lo stop del Mac ({exc}): disattiva lo stop automatico nelle "
                         "Impostazioni di Sistema (Batteria o Risparmio energia)", exc=awake_error))
        # bobine accese per tutta la pila (anche in pausa) se il firmware le spegne a motore fermo:
        # altrimenti il carico può riportare indietro la slitta a ogni fermata e la pila resta sullo stesso piano
        coils_on_here = False
        if self._hold_coils and focuser.motor.get("coil_power") is False:
            try:
                await focuser.set_motor("coil_power", True)
                coils_on_here = True
                self._log(tr("Bobine alimentate durante la sequenza"))
            except Exception as exc:  # noqa: BLE001
                self._log(tr("Impossibile alimentare le bobine: {exc}", exc=exc))
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
                        if self.status.live_ok:
                            await self._end_live(camera)
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
                    try:
                        files = await self._capture(camera, p, base)
                    except _RepeatShot:
                        need_move = True   # dopo la pausa: ricontrolla la posizione e ripete lo scatto
                        continue
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
                    self.status.shots += 1
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
            self.status.live_ok = False
            power.release()
            self.status.eta_s = None
            if p.sound_on_end and self.status.state in ("done", "error"):
                play_end_sound(self.status.state == "done")
            try:
                save_meta({"done": "completed", "idle": "interrupted"}.get(self.status.state, self.status.state))
            except OSError:
                pass
            if p.return_to_start and not self._stop and focuser.connected:
                try:
                    # con le bobine da rispegnere si aspetta l'arrivo: spente durante il movimento, la slitta scivolerebbe
                    await focuser.move_to(p.start, wait=coils_on_here)
                    self._log(tr("Ritorno alla posizione iniziale {pos}", pos=p.start))
                except Exception as exc:  # noqa: BLE001
                    self._log(tr("Ritorno all'inizio fallito: {exc}", exc=exc))
            if coils_on_here and focuser.connected:
                try:
                    await focuser.set_motor("coil_power", False)
                    self._log(tr("Bobine di nuovo spente a motore fermo"))
                except Exception as exc:  # noqa: BLE001
                    self._log(tr("Impossibile rispegnere le bobine: {exc}", exc=exc))


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
    if ctx.get("calibration"):   # set della libreria _calibrazione adatti a questa pila (percorsi relativi)
        m["calibration"] = ctx["calibration"]
    if ctx.get("sensor"):        # profilo del sensore all'ISO della pila (analisi del sensore, percorso relativo)
        m["sensor"] = ctx["sensor"]
    m["frames"] = []
    m["extra"] = {}
    return m
