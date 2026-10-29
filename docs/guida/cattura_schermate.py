"""Schermate della guida: avvia prima un'istanza di prova con i simulatori
    .venv/bin/python run.py --no-browser --port 8799
e poi esegui (serve Playwright con Google Chrome), una volta per lingua:
    python3.11 docs/guida/cattura_schermate.py --lang it [URL] [cartella-sequenza]
    python3.11 docs/guida/cattura_schermate.py --lang en
Salva le immagini in docs/guida/img/<lingua>/ e in img/<lingua>/annotazioni.json la posizione di ogni
elemento numerato, relativa all'immagine (0–1). Imposta la lingua dell'app e alla fine la rimette su
"auto". ATTENZIONE: modifica le impostazioni dell'app (meccanica, fine corsa, sequenza, lingua): farne
prima una copia e ripristinarla dopo.
"""
import argparse
import json
import time
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("base", nargs="?", default="http://127.0.0.1:8799")
ap.add_argument("seq_dir", nargs="?", default=None, help="cartella per la sequenza di prova")
ap.add_argument("--lang", choices=("it", "en", "fr", "de", "es"), default="it")
ARGS = ap.parse_args()
BASE, LANG = ARGS.base, ARGS.lang
OUT = Path(__file__).parent / "img" / LANG
OUT.mkdir(parents=True, exist_ok=True)
SEQ_DIR = ARGS.seq_dir or str(OUT.parent.parent / "_sequenza_prova")
# testi d'esempio iniettati nella pagina, nella forma della lingua
SAMPLE = {
    "it": {"f_info": "/dev/cu.usbserial-110 · firmware 330 · max 50.000"},
    "en": {"f_info": "/dev/cu.usbserial-110 · firmware 330 · max 50,000"},
    "fr": {"f_info": "/dev/cu.usbserial-110 · firmware 330 · max 50\u202f000"},
    "de": {"f_info": "/dev/cu.usbserial-110 · Firmware 330 · max. 50.000"},
    "es": {"f_info": "/dev/cu.usbserial-110 · firmware 330 · máx. 50.000"},
}[LANG]
notes: dict = {}


def post(path, body=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body or {}).encode(), method="POST",
                                 headers={"X-FocusStack": "1", "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req).read() or b"{}")


def state():
    return json.loads(urllib.request.urlopen(BASE + "/api/state").read())


def shot(page, name, target, marks=(), pad=0):
    """Schermata dell'elemento `target` con i riquadri degli elementi numerati `marks`
    [(numero, selettore, ancora)], ancora: l (sinistra), r (destra), t (in alto a sinistra)."""
    el = page.locator(target).first
    el.scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    box = el.bounding_box()
    clip = {"x": box["x"] - pad, "y": box["y"] - pad, "width": box["width"] + 2 * pad, "height": box["height"] + 2 * pad}
    page.screenshot(path=str(OUT / f"{name}.png"), clip=clip)
    items = []
    for num, sel, anchor in marks:
        b = page.locator(sel).first.bounding_box()
        if not b:
            print("  elemento non visibile:", sel)
            continue
        items.append({"n": num, "anchor": anchor,
                      "x": (b["x"] - clip["x"]) / clip["width"], "y": (b["y"] - clip["y"]) / clip["height"],
                      "w": b["width"] / clip["width"], "h": b["height"] / clip["height"]})
    notes[name] = {"w": clip["width"], "h": clip["height"], "marks": items}
    print("ok", name)


def m(*specs):
    return [(n, s, a) for n, s, a in specs]


post("/api/settings", {"language": LANG})   # la pagina si apre già nella lingua della guida

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=2)
    page = ctx.new_page()
    page.goto(BASE + "/")
    page.wait_for_timeout(1500)

    # ---- connessione (prima di connettere) ----
    page.evaluate("""() => {
      const s = document.getElementById('f-port');
      s.innerHTML = '<option>/dev/cu.usbserial-110</option>';
    }""")
    shot(page, "connessione-focheggiatore", "#f-connect-box", m(
        (1, "#f-port", "l"), (2, "#f-refresh", "r"), (3, "#f-sim", "l"), (4, "#f-connect", "r")), pad=8)
    shot(page, "connessione-fotocamera", "#c-connect-box", m(
        (1, "#c-model", "l"), (2, "#c-detect", "r"), (3, "#c-sim", "l"), (4, "#c-connect", "r")), pad=8)

    # ---- stato di esempio: simulatori, meccanica, fine corsa, sequenza ----
    post("/api/focuser/connect", {"simulate": True})
    post("/api/camera/connect", {"simulate": True})
    post("/api/focuser/sync", {"position": 25000})
    post("/api/mechanics", {"mode": "computed", "motor_steps_per_rev": 400, "gear_ratio": 3, "um_per_knob_rev": 100})
    post("/api/limits", {"limit_min": 2000, "limit_max": 45000, "toward_specimen": "decreasing"})
    post("/api/settings", {"jog_max": 10000, "jog_hold": True})
    for _ in range(3):
        post("/api/camera/test")
        time.sleep(1.2)
    page.reload()
    page.wait_for_timeout(2500)
    page.click("#s-more summary")   # i campi dentro <details> vanno prima resi visibili
    page.wait_for_timeout(300)
    page.fill("#s-start", "24000"); page.dispatch_event("#s-start", "input")
    page.fill("#s-end", "26000"); page.dispatch_event("#s-end", "input")
    page.fill("#s-step", "87"); page.dispatch_event("#s-step", "input")
    page.fill("#s-backlash", "200"); page.dispatch_event("#s-backlash", "input")
    page.fill("#s-settle", "1500"); page.dispatch_event("#s-settle", "input")
    page.fill("#s-post", "500"); page.dispatch_event("#s-post", "input")
    page.fill("#s-name", "stack"); page.dispatch_event("#s-name", "input")
    page.wait_for_timeout(1200)

    # testi che nella guida devono sembrare quelli di un focheggiatore e una fotocamera veri
    fake = """() => {
      const set = (id, t) => { const e = document.getElementById(id); if (e) e.textContent = t; };
      set('f-info', '""" + SAMPLE["f_info"] + """');
      set('c-info', 'Nikon DSC D5600');
      set('s-root-label', '\u200e~/Pictures/FocusStack\u200e');
    }"""
    page.evaluate(f"setInterval({fake}, 30)")
    page.evaluate("document.activeElement && document.activeElement.blur()")
    page.wait_for_timeout(100)
    page.evaluate("window.scrollTo(0, 0)")
    page.screenshot(path=str(OUT / "sessione.png"))
    notes["sessione"] = {"w": 1440, "h": 1000, "marks": []}
    print("ok sessione")

    page.set_viewport_size({"width": 1440, "height": 2600})
    page.wait_for_timeout(500)
    shot(page, "barra-superiore", "header.topbar", m(
        (1, ".tabs", "l"), (2, "#st-link", "l"), (3, "#st-temp", "l"), (4, "#theme-btn", "r")))
    shot(page, "focheggiatore", "#card-focuser", m(
        (1, "#f-chip", "r"), (2, "#f-connected-line", "l"), (3, ".pos-main", "l"), (4, ".pos-side", "r"),
        (5, "#rail", "l"), (6, "#jog-size", "l"), (7, "#jog-um", "l"), (8, ".jog-buttons", "l"),
        (9, ".row.goto", "l"), (10, "#f-halt", "l")))
    shot(page, "sequenza", "#card-seq", m(
        (1, "#s-chip", "r"), (2, "#s-start", "l"), (3, "#s-step", "l"), (4, "#s-count", "l"),
        (5, "#s-summary", "l"), (6, "#s-folder", "l"), (7, "#s-settle", "l"), (8, "#s-backlash", "l"),
        (9, "#s-mode", "l"), (10, "#s-name", "l"), (11, "#s-return", "l"), (12, "#s-preset", "l"),
        (13, ".progress-box", "l"), (14, ".seq-actions", "l"), (15, "#s-helicon", "l")))
    shot(page, "fotocamera", "#card-camera", m(
        (1, "#c-chip", "r"), (2, "#c-connected-line", "l"), (3, "#c-shutter", "l"), (4, "#c-aperture", "l"),
        (5, "#c-target", "l"), (6, "#c-bulb", "l"), (7, "#c-mirror", "l"), (8, "#c-reload", "l"), (9, "#c-test", "r")))
    shot(page, "ultimo-scatto", "#card-last", m(
        (1, "#live-btn", "l"), (2, "#v-open", "r"), (3, "#last-thumb", "t"), (4, "#last-meta", "l")))
    page.click("#live-btn")
    page.wait_for_timeout(2000)
    shot(page, "live", "#card-last", m((1, "#live-btn", "l"), (2, "#live-badge", "r"), (3, "#live-meta", "l")))
    page.click("#live-btn")

    # ---- configurazione ----
    page.click(".tabs button[data-tab=config]")
    page.wait_for_timeout(1200)
    page.evaluate("window.scrollTo(0, 0)")
    shot(page, "fine-corsa", "#card-limits", m(
        (1, "#lim-min", "l"), (2, "#lim-max", "l"), (3, "#lim-dir", "l"), (4, "#lim-save", "l"),
        (5, "#lim-zero", "l"), (6, "#lim-fw", "l")))
    shot(page, "meccanica", "#card-mech", m(
        (1, "#mech-mode", "l"), (2, "#m-spr", "l"), (3, "#m-micro", "r"), (4, "#m-gear", "l"),
        (5, "#m-umrev", "r"), (6, "#m-result", "l"), (7, "#m-save", "l")))
    page.click("#mech-mode button[data-mode=manual]")
    page.fill("#m-umstep", "0.083"); page.dispatch_event("#m-umstep", "input")   # il valore misurato dell'esempio
    page.wait_for_timeout(200)
    shot(page, "meccanica-manuale", "#card-mech", m((1, "#mech-mode", "l"), (2, "#m-umstep", "l"), (3, "#m-result", "l")))
    page.click("#mech-mode button[data-mode=computed]")
    shot(page, "comandi-manuali", "#card-jog", m((1, "#jog-max", "l"), (2, "#jog-hold", "l")))
    shot(page, "motore", "#card-motor", m(
        (1, "#mo-step_mode", "l"), (2, "#mo-speed", "l"), (3, "#mo-coil_power", "l"), (4, "#mo-reverse", "l"),
        (5, "#mo-backlash_in_enabled", "l"), (6, "#mo-backlash_in_steps", "l"), (7, "#mo-reload", "r")))
    shot(page, "aggiornamenti", "#card-updates", m((1, "#up-app", "l"), (2, "#up-fw", "l"), (3, "#fw-update", "l"), (4, "#up-check", "r")))
    shot(page, "temperatura", "#card-temp", m((1, "#t-value", "l"), (2, "#t-spark", "l")))
    shot(page, "profondita", "#card-dof", m(
        (1, "#d-na", "l"), (2, "#d-mag", "l"), (3, "#d-px", "l"), (4, "#d-ov", "l"), (5, "#d-result", "l"), (6, "#d-apply", "l")))
    notes["profondita"]["text"] = page.inner_text("#d-result")
    notes["meccanica"]["text"] = page.inner_text("#m-result")

    page.click(".tabs button[data-tab=log]")
    page.wait_for_timeout(500)
    shot(page, "registro", "#view-log .log-card")

    # ---- visualizzatore ----
    vw = ctx.new_page()
    vw.set_viewport_size({"width": 1500, "height": 860})
    vw.goto(BASE + "/viewer.html")
    vw.wait_for_timeout(2500)
    vw.click("#z-100")
    vw.wait_for_timeout(800)
    shot(vw, "visualizzatore", "body", m(
        (1, "#prev", "l"), (2, "#v-name", "l"), (3, "#liveview", "l"), (4, "#z-out", "l"), (5, "#z-fit", "l"),
        (6, "#follow", "l"), (7, "#lock", "l"), (8, "#reveal", "l"), (9, "#fs", "r"), (10, "#strip", "l")))
    vw.click("#liveview")
    vw.wait_for_timeout(2000)
    shot(vw, "visualizzatore-live", "body", m((1, "#liveview", "l"), (2, "#live-badge", "r")))
    vw.close()

    # ---- sequenza in corso ----
    page.click(".tabs button[data-tab=session]")
    page.wait_for_timeout(500)
    st = state()["settings"]["sequence"]
    post("/api/sequence/start", {**st, "start": 24000, "end": 26000, "step": 87, "backlash": 200,
                                 "settle_ms": 800, "post_shot_ms": 200, "output_root": SEQ_DIR, "session_name": "stack"})
    page.wait_for_timeout(9000)
    shot(page, "sequenza-in-corso", "#card-seq", m(
        (1, "#s-chip", "r"), (2, ".progress-box", "l"), (3, ".seq-actions", "l")))
    shot(page, "barra-posizione", "#card-focuser .position", pad=0)
    shot(page, "binario", "#rail", m((1, "#rail-forb-l", "l"), (2, "#rail-seq", "t"), (3, "#rail-pos", "t")), pad=6)
    post("/api/sequence/stop")
    time.sleep(1)
    browser.close()

post("/api/settings", {"language": "auto"})

(OUT / "annotazioni.json").write_text(json.dumps(notes, indent=1, ensure_ascii=False), encoding="utf-8")
print("annotazioni salvate")
