"""Autofocus su un punto: serie di scatti (o fotogrammi del live view) a posizioni diverse del focheggiatore,
nitidezza misurata nell'area scelta, poi il focheggiatore va dove la nitidezza è massima.

Tecnica come «Linear 1 Pass» di Ekos (KStars), reimplementata senza il suo codice (KStars è GPL):
- una passata sempre nella stessa direzione della pila, partendo da prima del fuoco atteso (dopo il passaggio di
  compensazione del gioco), e alla fine un ritorno sulla posizione migliore arrivando dalla stessa parte;
- se il massimo cade sul bordo la passata continua (o riparte più indietro) invece di fermarsi su un valore falso;
- curva adattata sui punti vicini al massimo.

La misura (fs-rawstat --focus) è il gradiente di Sobel al quadrato diviso per la luminosità al quadrato. Nelle
prove sulle pile vere (2026-11-23) la curva non è una V ma un picco stretto con code piatte: si adatta quindi una
gaussiana (parabola sul logaritmo) ai 5 punti attorno al massimo, che ritrova il massimo vero entro mezzo scatto.

Valori predefiniti: dalla larghezza del picco attesa (passi a metà altezza). La prima volta si stima dalla
profondità di campo del profilo Ottica e dalla meccanica (µm per passo); dopo ogni autofocus riuscito si salva la
larghezza misurata per quel profilo, che vale da lì in poi (la stima dalla profondità di campo, nelle prove, era
da 9 a 30 volte più piccola del vero).
"""
from __future__ import annotations

import asyncio
import math
import time
from dataclasses import dataclass, field
from statistics import median
from typing import Awaitable, Callable

from . import rawstat
from .i18n import tr
from .optics import manifest_optics

WIDTH_PER_DOF = 15          # larghezza del picco ≈ 15 profondità di campo (misurata: 9–30)
MIN_WIDTH = 4               # passi
FINE_POINTS = 11            # scatti della passata fine
COARSE_STEP_WIDTHS = 1      # passo della ricerca ampia = una larghezza del picco: uno scatto cade sempre entro mezza
                            # larghezza dal fuoco, dove la nitidezza è ancora ~metà del massimo; la passata fine,
                            # che si allunga o riparte da sola, trova poi la cima
FINE_STEP_DIV = 4           # passo della passata fine = larghezza / 4 (~5 punti sopra metà altezza)
COARSE_RANGE_WIDTHS = 5     # ricerca ampia: ± 5 larghezze dalla posizione attuale
MIN_PROMINENCE = 0.3        # (massimo − mediana) / massimo sotto questa soglia = nessun picco
MAX_SHIFTS = 3              # quante volte la passata fine può ripartire più indietro
MAX_REFINES = 2             # quante volte la passata fine si ripete con un passo più fine (picco più stretto del passo)
MAX_POINTS = 60             # limite di sicurezza per una passata
MAX_PASSES = 3              # passate fini: ognuna attorno al fuoco della precedente, con metà passo
VERIFY_MIN = 0.8            # scatto di verifica sotto l'80 % del massimo della curva = probabile gioco


def dof_um(optics: dict) -> float | None:
    """Profondità di campo (Berek/Shillaber, come nella scheda Ottica) dai valori del manifesto."""
    na, px = optics.get("na"), optics.get("pixel_size_um")
    if not na or na <= 0:
        return None
    return 0.55 / (na * na) + (px / na if px else 0.0)


def expected_width(cfg: dict, um_per_step: float, profile: str, travel: int | None) -> tuple[int, str]:
    """Larghezza del picco attesa in passi e da dove viene: learned | dof | travel | default."""
    learned = ((cfg.get("autofocus") or {}).get("widths") or {}).get(profile or "")
    if learned:
        return max(MIN_WIDTH, int(round(learned))), "learned"
    o = (cfg.get("optics_profiles") or {}).get(profile) if profile else None
    d = dof_um(manifest_optics(o)) if o else None
    if d and um_per_step > 0:
        return max(MIN_WIDTH, int(round(WIDTH_PER_DOF * d / um_per_step))), "dof"
    if travel:
        return max(MIN_WIDTH, travel // 50), "travel"
    return 40, "default"


def computed_defaults(width: int, travel: int | None, backlash: int = 0) -> dict:
    """Valori calcolati (quelli che la Configurazione mostra quando il campo è vuoto). overscan: sovracorsa per il
    gioco, cioè quanto si torna indietro oltre una posizione per arrivarci sempre nel verso della scansione: la
    compensazione del gioco della sequenza, ma almeno una larghezza del picco (anche se la sequenza non ne ha)."""
    coarse_range = COARSE_RANGE_WIDTHS * width
    if travel:
        coarse_range = min(coarse_range, max(1, travel // 2))
    return {"fine_step": max(1, round(width / FINE_STEP_DIV)), "fine_points": FINE_POINTS, "passes": 1,
            "coarse_step": max(1, round(width * COARSE_STEP_WIDTHS)), "coarse_range": int(coarse_range),
            "overscan": max(int(backlash or 0), width)}


@dataclass
class AFParams:
    roi: tuple[float, float, float, float]   # frazioni dell'immagine: x0, y0, x1, y1
    source: str = "live"                     # shot | live
    fine_step: int = 10
    fine_points: int = FINE_POINTS
    coarse: bool = False
    coarse_range: int = 200
    coarse_step: int = 15
    settle_ms: int = 1500
    overscan: int = 0                        # sovracorsa per il gioco (vedi computed_defaults)
    passes: int = 1                          # passate fini
    direction: int = 1                       # verso della pila: +1 passi crescenti, −1 decrescenti
    profile: str = ""


@dataclass
class AFStatus:
    state: str = "idle"          # idle | running | stopping | done | failed | error
    phase: str = ""              # coarse | fine | moving | verify
    rev: int = 0                 # cresce a ogni autofocus avviato (le finestre ricominciano il grafico)
    points: list = field(default_factory=list)   # passata in corso: [{pos, v}]; la grossa sparisce con la fine
    index: int = 0               # scatti fatti nella passata
    total: int = 0               # scatti previsti nella passata (può crescere se il picco è al bordo)
    target: int | None = None
    step: int = 0
    roi: list = field(default_factory=list)
    source: str = "live"
    best: int | None = None
    fit: dict | None = None
    pass_no: int = 1             # passata fine in corso
    passes: int = 1
    verify: dict | None = None   # scatto di verifica sulla posizione scelta: {pos, v, ratio (sul massimo della curva)}
    message: str = ""
    warning: str = ""
    started_at: float | None = None


class AutofocusError(Exception):
    pass


def fit_peak(points: list[dict]) -> dict | None:
    """Gaussiana sui 5 punti attorno al massimo (parabola sul logaritmo). center in passi (anche frazionario),
    width = larghezza a metà altezza in passi, r2 sul logaritmo. None se non c'è una curva verso il basso."""
    pts = sorted(points, key=lambda p: p["pos"])
    if len(pts) < 3:
        return None
    k = max(range(len(pts)), key=lambda i: pts[i]["v"])
    lo, hi = max(0, k - 2), min(len(pts), k + 3)
    sel = [p for p in pts[lo:hi] if p["v"] > 0]
    if len(sel) < 3:
        return None
    x0 = pts[k]["pos"]
    xs = [float(p["pos"] - x0) for p in sel]
    ys = [math.log(p["v"]) for p in sel]
    # minimi quadrati per y = a x² + b x + c (sistema normale 3×3)
    s = [sum(x ** n for x in xs) for n in range(5)]
    t = [sum(y * x ** n for x, y in zip(xs, ys)) for n in range(3)]
    m = [[s[4], s[3], s[2], t[2]], [s[3], s[2], s[1], t[1]], [s[2], s[1], s[0], t[0]]]
    for i in range(3):   # eliminazione di Gauss con pivot
        piv = max(range(i, 3), key=lambda r: abs(m[r][i]))
        if abs(m[piv][i]) < 1e-12:
            return None
        m[i], m[piv] = m[piv], m[i]
        for r in range(3):
            if r != i:
                f = m[r][i] / m[i][i]
                m[r] = [a - f * b for a, b in zip(m[r], m[i])]
    a, b, c = (m[i][3] / m[i][i] for i in range(3))
    if a >= 0:
        return None
    center = -b / (2 * a)
    # il centro resta fra i punti vicini al massimo (fuori sarebbe un'estrapolazione)
    left = pts[max(0, k - 1)]["pos"] - x0
    right = pts[min(len(pts) - 1, k + 1)]["pos"] - x0
    center = min(max(center, min(left, right)), max(left, right))
    sigma = math.sqrt(-1 / (2 * a))
    mean_y = sum(ys) / len(ys)
    ss_tot = sum((y - mean_y) ** 2 for y in ys)
    ss_res = sum((y - (a * x * x + b * x + c)) ** 2 for x, y in zip(xs, ys))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    # peak: altezza della curva adattata nel centro (la cima vera, di solito un po' sopra il punto più alto misurato)
    return {"center": x0 + center, "width": 2 * math.sqrt(2 * math.log(2)) * sigma, "r2": round(r2, 4),
            "peak": math.exp(a * center * center + b * center + c)}


def prominence(points: list[dict]) -> float:
    vals = [p["v"] for p in points]
    if not vals or max(vals) <= 0:
        return 0.0
    top = max(vals)
    return (top - median(vals)) / top


def peak_found(points: list[dict], direction: int) -> bool:
    """Un picco vero: il massimo è dentro la passata (non al primo né all'ultimo punto), la nitidezza cambia
    davvero (almeno del 30 %) e scende di almeno un quarto da entrambe le parti."""
    v = [q["v"] for q in sorted(points, key=lambda q: q["pos"] * direction)]
    if len(v) < 3 or max(v) <= 0:
        return False
    top = max(v)
    k = v.index(top)
    if k == 0 or k == len(v) - 1 or (top - min(v)) / top < MIN_PROMINENCE:
        return False
    return (top - min(v[:k])) / top >= 0.25 and (top - min(v[k + 1:])) / top >= 0.25


def second_peak(points: list[dict]) -> bool:
    """Un altro massimo locale alto almeno metà del principale, separato da una valle vera: nell'area ci sono
    due cose a profondità diverse (nelle prove: zampa e corpo della vespa, tacche della squadra)."""
    pts = sorted(points, key=lambda p: p["pos"])
    v = [p["v"] for p in pts]
    if len(v) < 5:
        return False
    k = max(range(len(v)), key=lambda i: v[i])
    for i in range(1, len(v) - 1):
        if abs(i - k) < 2 or not (v[i] >= v[i - 1] and v[i] >= v[i + 1]) or v[i] < 0.5 * v[k]:
            continue
        a, b = sorted((i, k))
        if min(v[a:b + 1]) <= 0.7 * v[i]:
            return True
    return False


class AutofocusRunner:
    """grab(source, position) → file da misurare (scatto vero o fotogramma del live view)."""

    def __init__(self, focuser_getter: Callable, grab: Callable[[str, int], Awaitable[str]],
                 log: Callable[[str], None], on_width: Callable[[str, float], None]):
        self._focuser = focuser_getter
        self._grab = grab
        self._log = log
        self._on_width = on_width
        self.status = AFStatus()
        self._task: asyncio.Task | None = None
        self._stop = False
        self._source = "auto"     # sorgente di fs-rawstat: decisa al primo scatto, poi sempre quella

    @property
    def busy(self) -> bool:
        return self._task is not None and not self._task.done()

    def start(self, p: AFParams) -> None:
        if self.busy:
            raise RuntimeError(tr("Autofocus già in corso"))
        if self._focuser() is None:
            raise RuntimeError(tr("Focheggiatore non connesso"))
        self._stop = False
        self._source = "auto"
        self.status = AFStatus(state="running", rev=self.status.rev + 1, roi=list(p.roi), source=p.source,
                               started_at=time.time(), message=tr("Autofocus…"), passes=max(1, p.passes))
        self._task = asyncio.create_task(self._run(p))

    async def stop(self) -> None:
        if not self.busy:
            return
        self._stop = True
        self.status.state = "stopping"
        f = self._focuser()
        if f:
            await f.halt()

    def _check(self) -> None:
        if self._stop:
            raise asyncio.CancelledError

    def _clamp(self, pos: int) -> int:
        lo, hi = self._focuser().bounds()
        pos = max(lo, pos)
        return min(hi, pos) if hi is not None else pos

    async def _go(self, pos: int, p: AFParams, approach: bool) -> None:
        """Movimento; con approach=True passa prima da dietro della sovracorsa, così si arriva sempre nel verso della
        scansione: tornando indietro direttamente il gioco della meccanica sposterebbe il fuoco."""
        f = self._focuser()
        if approach and p.overscan > 0:
            before = self._clamp(pos - p.direction * p.overscan)
            if before != pos:
                await f.move_to(before, wait=True)
                self._check()
        await f.move_to(pos, wait=True)
        self._check()

    async def _measure_at(self, pos: int, p: AFParams) -> float:
        f = self._focuser()
        await asyncio.sleep(p.settle_ms / 1000)
        self._check()
        await f.poll()
        if f.position != pos or f.moving:
            raise AutofocusError(tr("Movimento manuale rilevato ({actual} invece di {pos}): autofocus fermato",
                                    actual=f.position, pos=pos))
        path = await self._grab(p.source, pos)
        self._check()
        try:
            r = await rawstat.focus(path, p.roi, self._source)
        except rawstat.RawStatError as exc:
            raise AutofocusError(str(exc)) from exc
        if self._source == "auto":
            self._source = r.get("source") if r.get("source") in ("preview", "raw") else "auto"
        return float(r["focus"])

    async def _scan(self, start: int, step: int, count: int, p: AFParams, phase: str,
                    early_stop: bool, extend: bool) -> list[dict]:
        """Passata da start nel verso della pila: count posizioni a passo step. early_stop: si ferma quando il
        picco è superato (due punti sotto metà altezza dopo il massimo). extend: finché il picco non è superato la
        passata continua; se la nitidezza sale ancora, con un passo che raddoppia ogni 5 punti in salita (fino a 8
        volte): il picco può essere più largo del previsto."""
        st = self.status
        st.phase, st.points, st.index, st.total, st.step = phase, [], 0, count, step
        st.warning = ""
        lo, hi = self._focuser().bounds()
        positions = [start + p.direction * step * i for i in range(count)]
        positions = [x for x in positions if x >= lo and (hi is None or x <= hi)]
        if not positions:
            raise AutofocusError(tr("Nessuna posizione dentro i fine corsa"))
        st.total = len(positions)
        extra = 0
        i = 0
        first = True
        while i < len(positions) and i < MAX_POINTS:
            pos = positions[i]
            st.target = pos
            await self._go(pos, p, approach=first)
            first = False
            v = await self._measure_at(pos, p)
            st.points.append({"pos": pos, "v": v})
            st.index = len(st.points)
            vals = [q["v"] for q in st.points]
            k = len(vals) - 1 - vals[::-1].index(max(vals))   # a pari merito, l'ultimo
            if early_stop and len(vals) >= 5 and k <= len(vals) - 3:
                half = min(vals) + 0.5 * (max(vals) - min(vals))
                if vals[-1] < half and vals[-2] < half:
                    break
            # in fondo alla passata senza aver visto il picco scendere: si continua (più veloce se sale ancora)
            flat = max(vals) <= 0 or (max(vals) - min(vals)) / max(vals) < MIN_PROMINENCE
            if extend and i == len(positions) - 1 and not flat:
                climbing = k == len(vals) - 1
                extra = extra + 1 if climbing else extra
                nxt = pos + p.direction * (step * min(8, 2 ** (extra // 5)) if climbing else step)
                if hi is not None and p.direction > 0:
                    nxt = min(nxt, hi)
                nxt = max(nxt, lo) if p.direction < 0 else nxt
                if nxt != pos and nxt >= lo and (hi is None or nxt <= hi):
                    positions.append(nxt)
                    st.total = len(positions)
            i += 1
        st.total = len(st.points)
        return st.points

    def _best(self, pts: list[dict]) -> tuple[int, dict | None]:
        """Posizione di fuoco della passata: centro della curva adattata, o il punto più alto se l'adattamento non riesce."""
        fit = fit_peak(pts)
        top = max(pts, key=lambda q: q["v"])["pos"]
        return self._clamp(int(round(fit["center"])) if fit else top), fit

    async def _run(self, p: AFParams) -> None:
        st = self.status
        f = self._focuser()
        try:
            await f.poll()
            here = f.position
            self._log(tr("Autofocus: area {w}×{h} % dell'immagine, da {pos}",
                         w=round((p.roi[2] - p.roi[0]) * 100, 1), h=round((p.roi[3] - p.roi[1]) * 100, 1), pos=here))
            center = here
            if p.coarse:
                n = 2 * max(1, p.coarse_range // max(1, p.coarse_step)) + 1
                start = self._clamp(here - p.direction * (n // 2) * p.coarse_step)
                st.message = tr("Ricerca ampia")
                pts = await self._scan(start, p.coarse_step, n, p, "coarse", early_stop=False, extend=False)
                vals = [q["v"] for q in pts]
                if max(vals) <= 0 or (max(vals) - min(vals)) / max(vals) < MIN_PROMINENCE:
                    raise AutofocusError(tr("Nessun punto a fuoco trovato nella ricerca ampia: allarga la ricerca, "
                                            "avvicina il fuoco a mano o scegli un'area con più dettagli"))
                center = max(pts, key=lambda q: q["v"])["pos"]
                self._log(tr("Ricerca ampia: fuoco vicino a {pos}", pos=center))
            n = max(5, p.fine_points)
            step = p.fine_step
            st.message = tr("Passata fine")
            pts: list[dict] = []
            for refine in range(MAX_REFINES + 1):
                half = (n - 1) // 2 * step
                start = self._clamp(center - p.direction * half)
                for shift in range(MAX_SHIFTS + 1):
                    pts = await self._scan(start, step, n, p, "fine", early_stop=True, extend=True)
                    ordered = sorted(pts, key=lambda q: q["pos"] * p.direction)
                    vals = [q["v"] for q in ordered]
                    k = max(range(len(ordered)), key=lambda i: ordered[i]["v"])
                    flat = max(vals) <= 0 or (max(vals) - min(vals)) / max(vals) < MIN_PROMINENCE
                    if k >= 2 or flat or shift == MAX_SHIFTS:
                        break
                    # il massimo è all'inizio: il fuoco è prima della passata, si riparte più indietro
                    new_start = self._clamp(start - p.direction * 2 * half)
                    if new_start == start:
                        break
                    self._log(tr("Il picco è prima dell'inizio della passata: riparto da {pos}", pos=new_start))
                    start = new_start
                if not peak_found(pts, p.direction):
                    lo, hi = self._focuser().bounds()
                    edge = [q["pos"] for q in pts if q["pos"] in (lo, hi)]
                    top = max(pts, key=lambda q: q["v"])["pos"]
                    if top in edge:
                        raise AutofocusError(tr("La nitidezza cresce fino al fine corsa ({pos}): il fuoco è oltre. "
                                                "Controlla i fine corsa in Configurazione", pos=top))
                    raise AutofocusError(
                        tr("Nessun picco di nitidezza: l'area è senza dettagli oppure il fuoco è lontano. Attiva la "
                           "ricerca ampia in Configurazione › Autofocus o scegli un'area con più dettagli")
                        if not p.coarse else
                        tr("Nessun picco di nitidezza nella passata fine: scegli un'area con più dettagli"))
                # un picco va visto da almeno 3 punti sopra metà altezza: con meno, è più stretto del passo (o è un
                # valore isolato, es. una vibrazione) → si ripete attorno al massimo con un passo 4 volte più fine
                vals = [q["v"] for q in pts]
                half_h = min(vals) + 0.5 * (max(vals) - min(vals))
                if sum(v >= half_h for v in vals) >= 3 or step <= 1 or refine == MAX_REFINES:
                    break
                # passo vicino al massimo (dopo un tratto in salita può essere più largo di quello iniziale)
                ordered = sorted(pts, key=lambda q: q["pos"])
                k = max(range(len(ordered)), key=lambda i: ordered[i]["v"])
                gaps = [abs(ordered[j]["pos"] - ordered[k]["pos"]) for j in (k - 1, k + 1) if 0 <= j < len(ordered)]
                center = ordered[k]["pos"]
                step = max(1, min(gaps or [step]) // 4)
                self._log(tr("Picco più stretto del passo: ripeto attorno a {pos} con passo {s}", pos=center, s=step))
            best, fit = self._best(pts)
            first_fit, first_step = fit, step   # la larghezza del picco si misura sulla prima passata, che lo vede intero
            # passate in più: attorno al fuoco trovato, ognuna con metà passo della precedente
            for k in range(2, min(MAX_PASSES, max(1, p.passes)) + 1):
                if step <= 1:
                    break
                step = max(1, step // 2)
                st.pass_no = k
                st.message = tr("Passata {i} di {n}", i=k, n=st.passes)
                self._log(tr("Passata {i} di {n}: attorno a {pos} con passo {s}", i=k, n=st.passes, pos=best, s=step))
                half = (n - 1) // 2 * step
                more = await self._scan(self._clamp(best - p.direction * half), step, n, p, "fine",
                                        early_stop=True, extend=True)
                # la passata in più guarda solo la cima del picco: basta che il massimo sia dentro e la curva scenda
                # da entrambe le parti (l'adattamento riesce), senza chiedere code piatte come alla prima
                ordered = sorted(more, key=lambda q: q["pos"] * p.direction)
                kk = max(range(len(ordered)), key=lambda i: ordered[i]["v"])
                if not (0 < kk < len(ordered) - 1 and fit_peak(more)):
                    self._log(tr("Passata {i}: picco non chiaro, resta {pos}", i=k, pos=best))
                    break
                pts = more
                best, fit = self._best(pts)
            st.fit = {**fit, "prominence": round(prominence(pts), 3)} if fit else {"prominence": round(prominence(pts), 3)}
            if second_peak(pts):
                st.warning = tr("Nell'area ci sono due cose a fuoco diverso: rimpicciolisci l'area sul dettaglio che ti interessa")
                self._log(st.warning)
            st.best = best
            st.phase, st.target = "moving", best
            st.message = tr("Vado al fuoco: {pos}", pos=best)
            await self._go(best, p, approach=True)
            # scatto di verifica sulla posizione scelta: deve essere vicino al massimo della curva
            st.phase = "verify"
            st.message = tr("Scatto di verifica a {pos}", pos=best)
            v = await self._measure_at(best, p)
            # confronto con la cima della curva adattata (non col punto più alto misurato: il fuoco scelto cade di
            # solito fra due misure, più vicino alla cima, e la verifica supererebbe il 100 %)
            top_v = max(fit["peak"] if fit else 0.0, max(q["v"] for q in pts))
            ratio = v / top_v if top_v > 0 else 0.0
            st.verify = {"pos": best, "v": v, "ratio": round(ratio, 3)}
            if ratio < VERIFY_MIN:
                st.warning = tr("Lo scatto di verifica ha solo il {pct} % della nitidezza massima della curva: probabile "
                                "gioco della meccanica. Aumenta la sovracorsa in Configurazione › Autofocus e rifai",
                                pct=round(ratio * 100))
                self._log(st.warning)
            # larghezza misurata: da qui in poi i valori predefiniti di questo profilo (solo se la verifica conferma
            # il fuoco: con il gioco la curva può essere spostata o deformata)
            if (first_fit and first_fit["r2"] >= 0.9 and first_step <= first_fit["width"] < 100 * first_step
                    and ratio >= VERIFY_MIN):
                self._on_width(p.profile, first_fit["width"])
            st.state = "done"
            st.message = tr("Fuoco a {pos}", pos=best)
            self._log(tr("Autofocus completato: fuoco a {pos}", pos=best)
                      + (f" (± {fit['width'] / 2:.0f}, R² {fit['r2']:.2f})" if fit else "")
                      + " · " + tr("verifica {pct} %", pct=round(ratio * 100)))
        except asyncio.CancelledError:
            st.state = "idle"
            st.message = tr("Autofocus interrotto")
            self._log(tr("Autofocus interrotto"))
        except AutofocusError as exc:
            st.state = "failed"
            st.message = str(exc)
            self._log(tr("Autofocus non riuscito: {exc}", exc=exc))
        except Exception as exc:  # noqa: BLE001
            if self._stop:   # l'halt durante un movimento genera un errore di posizione: è un'interruzione
                st.state = "idle"
                st.message = tr("Autofocus interrotto")
                self._log(tr("Autofocus interrotto"))
            else:
                st.state = "error"
                st.message = str(exc)
                self._log(tr("ERRORE autofocus: {exc}", exc=exc))
        finally:
            st.target = None if st.state != "done" else st.best
            if st.phase in ("moving", "verify") and st.state != "done":
                st.phase = ""

