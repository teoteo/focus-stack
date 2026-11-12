"""Schermate della guida: avvia prima un'istanza di prova con i simulatori
    .venv/bin/python run.py --no-browser --port 8799
e poi esegui (serve Playwright con Google Chrome), una volta per lingua:
    python3.11 docs/guida/cattura_schermate.py --lang it [URL] [cartella-sequenza]
    python3.11 docs/guida/cattura_schermate.py --lang en
Salva le immagini in docs/guida/img/<lingua>/ e in img/<lingua>/annotazioni.json la posizione di ogni
elemento numerato, relativa all'immagine (0–1), più un sequence.txt d'esempio nella lingua.
Imposta la lingua dell'app e alla fine la rimette su "auto". ATTENZIONE: modifica le impostazioni
dell'app (meccanica, fine corsa, sequenza, profili ottici, lingua): avviare l'istanza di prova con una
home separata, per esempio  HOME=/tmp/fs-home .venv/bin/python run.py --no-browser --port 8799
"""
import argparse
import json
import sys
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
    "it": {"f_info": "/dev/cu.usbserial-110 · firmware 330 · max 50.000", "obj": "Plan 10×/0,25",
           "illum": "Epifluorescenza", "notes": "ala di farfalla", "relay": "raccordo T2"},
    "en": {"f_info": "/dev/cu.usbserial-110 · firmware 330 · max 50,000", "obj": "Plan 10×/0.25",
           "illum": "Epifluorescence", "notes": "butterfly wing", "relay": "T2 adapter"},
    "fr": {"f_info": "/dev/cu.usbserial-110 · firmware 330 · max 50\u202f000", "obj": "Plan 10×/0,25",
           "illum": "Épifluorescence", "notes": "aile de papillon", "relay": "bague T2"},
    "de": {"f_info": "/dev/cu.usbserial-110 · Firmware 330 · max. 50.000", "obj": "Plan 10×/0,25",
           "illum": "Epifluoreszenz", "notes": "Schmetterlingsflügel", "relay": "T2-Adapter"},
    "es": {"f_info": "/dev/cu.usbserial-110 · firmware 330 · máx. 50.000", "obj": "Plan 10×/0,25",
           "illum": "Epifluorescencia", "notes": "ala de mariposa", "relay": "adaptador T2"},
}[LANG]
PROFILE = "10× GFP"
PROFILE_OPTOVAR = "10× GFP + Optovar 1,6×" if LANG != "en" else "10× GFP + Optovar 1.6×"
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
    sample_optics = {
        "objective": SAMPLE["obj"], "objective_magnification": 10, "na": 0.25, "immersion": "air", "sensor_pixel_um": 3.9,
        "dof_overlap": 30, "filter_mode": "filter",
        "filter": {"name": "GFP", "type": "bandpass", "center_nm": 525, "bandwidth_nm": 50},
        "illumination": {"type": SAMPLE["illum"], "level_percent": 80}, "notes": SAMPLE["notes"]}
    post("/api/optics/profiles/save", {"name": PROFILE, "optics": sample_optics})
    # lo stesso microscopio con il cambio d'ingrandimento Optovar 1,6× e la fotocamera su un raccordo T2 (1×)
    post("/api/optics/profiles/save", {"name": PROFILE_OPTOVAR, "optics": {
        **sample_optics, "intermediate": {"name": "Optovar", "factor": 1.6},
        "relay": {"name": SAMPLE["relay"], "factor": 1}}})
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
    page.fill("#s-repeats", "1"); page.dispatch_event("#s-repeats", "input")
    page.select_option("#s-optics", PROFILE); page.dispatch_event("#s-optics", "change")
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
        (5, "#s-optics", "l"), (6, "#s-summary", "l"), (7, "#s-folder", "l"), (8, "#s-repeats", "l"),
        (9, "#s-settle", "l"), (10, "#s-backlash", "l"), (11, "#s-mode", "l"), (12, "#s-name", "l"),
        (13, "#s-return", "l"), (14, "#s-preset", "l"), (15, ".progress-box", "l"), (16, ".seq-actions", "l"),
        (17, "#s-finder", "l")))
    shot(page, "fotocamera", "#card-camera", m(
        (1, "#c-chip", "r"), (2, "#c-connected-line", "l"), (3, "#c-shutter", "l"), (4, "#c-aperture", "l"),
        (5, "#c-target", "l"), (6, "#c-bulb", "l"), (7, "#c-mirror", "l"), (8, "#c-reload", "l"), (9, "#c-test", "r")))
    shot(page, "ultimo-scatto", "#card-last", m(
        (1, "#live-btn", "l"), (2, "#v-open", "r"), (3, "#last-thumb", "t"), (4, "#last-meta", "l")))
    page.click("#live-btn")
    page.wait_for_timeout(2000)
    shot(page, "live", "#card-last", m((1, "#live-btn", "l"), (2, "#live-badge", "r"), (3, "#live-meta", "l")))
    page.click("#live-btn")

    # ---- ottica: profili e profondità di campo ----
    page.click(".tabs button[data-tab=optics]")
    page.wait_for_timeout(800)
    page.select_option("#o-profile", PROFILE_OPTOVAR); page.dispatch_event("#o-profile", "change")
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)
    page.evaluate("document.querySelector('#card-optics .subsection').style.display = 'none'")
    shot(page, "ottica", "#card-optics", m(
        (1, "#o-profile", "l"), (2, "#o-profile-save", "l"), (3, "#o-profile-del", "r"),
        # in ordine fisico, come nella pagina: sensore, adattatore, cambio intermedio, obiettivo
        (4, "#d-px", "l"), (5, "#o-relay-name", "l"), (6, "#o-inter-name", "l"), (7, "#o-objective", "l"),
        (8, "#d-mag", "l"), (9, "#d-na", "l"), (10, "#o-immersion", "l"), (11, "#o-pxcal", "l"), (12, "#o-pxresult", "l"),
        (13, "#o-filter-mode", "l"), (14, "#o-fname", "l"), (15, "#o-fcenter", "l"), (16, "#o-illum", "l"),
        (17, "#o-notes", "l"), (18, "#o-save", "l"), (19, "#o-chip", "r")))
    page.evaluate("document.querySelector('#card-optics .subsection').style.display = ''")
    # profondità di campo: profilo senza Optovar (come gli esempi del capitolo 11), riquadro stretto
    # perché i tre numeri non si sovrappongano
    page.select_option("#o-profile", PROFILE); page.dispatch_event("#o-profile", "change")
    page.wait_for_timeout(300)
    page.evaluate("Object.assign(document.querySelector('#card-optics .subsection').style, {width: '520px'})")
    shot(page, "profondita", "#card-optics .subsection", m(
        (1, "#d-ov", "l"), (2, "#d-result", "l"), (3, "#d-apply", "l")), pad=0)
    page.evaluate("document.querySelector('#card-optics .subsection').style.width = ''")
    notes["profondita"]["text"] = page.inner_text("#d-result")

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
    # 1 a sinistra e 2 a destra: le due righe sono troppo vicine per due numeri uno sopra l'altro
    shot(page, "aggiornamenti", "#card-updates", m((1, "#up-app", "l"), (2, "#up-fw", "r"), (3, "#fw-update", "l"), (4, "#up-check", "r")))
    shot(page, "temperatura", "#card-temp", m((1, "#t-value", "l"), (2, "#t-spark", "l")))
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
                                 "settle_ms": 800, "post_shot_ms": 200, "output_root": SEQ_DIR, "session_name": "stack",
                                 "optics_profile": PROFILE})
    page.wait_for_timeout(9000)
    shot(page, "sequenza-in-corso", "#card-seq", m(
        (1, "#s-chip", "r"), (2, ".progress-box", "l"), (3, ".seq-actions", "l")))
    shot(page, "barra-posizione", "#card-focuser .position", pad=0)
    # 2 sotto la fascia della sequenza, 3 sopra la linea della posizione (che sta dentro la fascia)
    shot(page, "binario", "#rail", m((1, "#rail-forb-l", "l"), (2, "#rail-seq", "b"), (3, "#rail-pos", "t")), pad=6)
    post("/api/sequence/stop")
    time.sleep(1.5)
    browser.close()

# ---- sequence.txt d'esempio: breve sequenza completa, 2 scatti per posizione ----
st = state()["settings"]["sequence"]
post("/api/sequence/start", {**st, "start": 24000, "end": 24435, "step": 87, "backlash": 200, "settle_ms": 300,
                             "post_shot_ms": 100, "shots_per_position": 2, "output_root": SEQ_DIR,
                             "session_name": "stack", "optics_profile": PROFILE})
for _ in range(240):
    time.sleep(0.5)
    if state()["sequence"]["state"] in ("done", "error", "idle"):
        break
manifest = json.loads((Path(state()["sequence"]["folder"]) / "sequence.json").read_text(encoding="utf-8"))
# dati che nella guida devono sembrare quelli di un focheggiatore e una fotocamera veri
manifest["rail"].update(model="myFocuserPro2", firmware="330 build 3")
manifest["camera"] = {"model": "Nikon DSC D5600", "iso": "100", "shutterspeed": "1/60", "imageformat": "NEF (Raw)"}
for frame in manifest["frames"]:
    for exp in frame["exposures"]:
        exp["files"] = [f.rsplit(".", 1)[0] + ".NEF" for f in exp["files"]]
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend import i18n, summary  # noqa: E402
i18n.set_language(LANG)
(OUT / "sequence.txt").write_text(summary.render(manifest), encoding="utf-8")
print("ok sequence.txt")

post("/api/settings", {"language": "auto"})

(OUT / "annotazioni.json").write_text(json.dumps(notes, indent=1, ensure_ascii=False), encoding="utf-8")
print("annotazioni salvate")
