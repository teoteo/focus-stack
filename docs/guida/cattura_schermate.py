"""Schermate della guida: avvia prima un'istanza di prova con i simulatori
    HOME=/tmp/fs-home .venv/bin/python run.py --no-browser --port 8797
e poi esegui (serve Playwright con Google Chrome), una volta per lingua:
    python3.11 docs/guida/cattura_schermate.py --lang it [URL] [cartella-sequenza]
    python3.11 docs/guida/cattura_schermate.py --lang en
Salva le immagini in docs/guida/img/<lingua>/ e in img/<lingua>/annotazioni.json la posizione di ogni
elemento numerato, relativa all'immagine (0–1), più un sequence.txt d'esempio nella lingua.
Imposta la lingua dell'app e alla fine la rimette su "auto". ATTENZIONE: modifica le impostazioni
dell'app (meccanica, fine corsa, sequenza, profili ottici, lingua): avviare l'istanza di prova con una
home separata, come sopra. NON usare la porta 8799: è quella dell'app di prova («Focus Stack Prova»), che usa le
impostazioni vere; se è aperta, lo script le modificherebbe. Lo script si ferma se la cartella degli scatti del server
è quella dell'utente (~/Pictures).
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("base", nargs="?", default="http://127.0.0.1:8797")
ap.add_argument("seq_dir", nargs="?", default=None, help="cartella per la sequenza di prova")
ap.add_argument("--lang", choices=("it", "en", "fr", "de", "es"), default="it")
ap.add_argument("--only", default="", help="rifà solo queste figure (nomi separati da virgole); le altre restano")
ARGS = ap.parse_args()
BASE, LANG = ARGS.base, ARGS.lang
OUT = Path(__file__).parent / "img" / LANG
OUT.mkdir(parents=True, exist_ok=True)
SEQ_DIR = ARGS.seq_dir or str(OUT.parent.parent / "_sequenza_prova")
# testi d'esempio iniettati nella pagina, nella forma della lingua
SAMPLE = {
    "it": {"f_info": "/dev/cu.usbserial-110 · firmware 330 · max 50.000", "obj": "Plan 10×/0,25",
           "illum": "Epifluorescenza", "notes": "ala di farfalla", "relay": "raccordo T2", "illum_macro": "LED ad anello"},
    "en": {"f_info": "/dev/cu.usbserial-110 · firmware 330 · max 50,000", "obj": "Plan 10×/0.25",
           "illum": "Epifluorescence", "notes": "butterfly wing", "relay": "T2 adapter", "illum_macro": "Ring LED"},
    "fr": {"f_info": "/dev/cu.usbserial-110 · firmware 330 · max 50\u202f000", "obj": "Plan 10×/0,25",
           "illum": "Épifluorescence", "notes": "aile de papillon", "relay": "bague T2", "illum_macro": "LED annulaire"},
    "de": {"f_info": "/dev/cu.usbserial-110 · Firmware 330 · max. 50.000", "obj": "Plan 10×/0,25",
           "illum": "Epifluoreszenz", "notes": "Schmetterlingsflügel", "relay": "T2-Adapter", "illum_macro": "LED-Ringlicht"},
    "es": {"f_info": "/dev/cu.usbserial-110 · firmware 330 · máx. 50.000", "obj": "Plan 10×/0,25",
           "illum": "Epifluorescencia", "notes": "ala de mariposa", "relay": "adaptador T2", "illum_macro": "LED anular"},
}[LANG]
PROFILE = "10× GFP"
PROFILE_OPTOVAR = "10× GFP + Optovar 1,6×" if LANG != "en" else "10× GFP + Optovar 1.6×"
PROFILE_MACRO = "Sony 90 macro + Raynox"
notes: dict = {}
ONLY = {n.strip() for n in ARGS.only.split(",") if n.strip()}
if ONLY:   # le annotazioni delle figure non rifatte restano quelle di prima
    notes = json.loads((OUT / "annotazioni.json").read_text(encoding="utf-8"))
# nella guida pubblicata non devono comparire l'indirizzo di rete del Mac, il nome utente nei percorsi della cartella
# di prova né la fotocamera simulata: SCRUB li sostituisce in tutta la pagina, prima di ogni schermata
FAKE_URL = "http://192.168.1.20:8766/?k=Ab3dE5fG7hK2"
import base64, subprocess, tempfile  # noqa: E402,E401
_qr = Path(tempfile.mkdtemp()) / "qr.png"
# lo stesso generatore di backend/remote.qr_png (CoreImage via osascript): quel modulo importa il server
_JXA = """ObjC.import('Cocoa'); ObjC.import('CoreImage');
function run(argv) {
  var f = $.CIFilter.filterWithName('CIQRCodeGenerator');
  f.setValueForKey($(argv[0]).dataUsingEncoding($.NSUTF8StringEncoding), 'inputMessage');
  f.setValueForKey($('M'), 'inputCorrectionLevel');
  var rep = $.NSBitmapImageRep.alloc.initWithCIImage(f.outputImage);
  var png = rep.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $());
  return png.writeToFileAtomically(argv[1], true) ? 'ok' : 'fail';
}"""
subprocess.run(["osascript", "-l", "JavaScript", "-e", _JXA, FAKE_URL, str(_qr)], capture_output=True, timeout=20)
FAKE_QR = "data:image/png;base64," + base64.b64encode(_qr.read_bytes()).decode() if _qr.exists() else ""
SCRUB = """() => {
  const fix = (t) => t.split(SEQ).join('~/Pictures/FocusStack').split(SIM).join('Nikon DSC D5600')
    .replace(/https?:\\/\\/[0-9.]+:[0-9]+\\/\\?k=[A-Za-z0-9_-]+/g, FAKE_URL);
  const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  while (w.nextNode()) { const n = w.currentNode, v = fix(n.nodeValue); if (v !== n.nodeValue) n.nodeValue = v; }
  const a = document.getElementById('r-url'); if (a && a.href !== FAKE_URL) a.href = FAKE_URL;
  const q = document.getElementById('r-qr'); if (q && FAKE_QR && q.src !== FAKE_QR) q.src = FAKE_QR;
}"""


def post(path, body=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(body or {}).encode(), method="POST",
                                 headers={"X-FocusStack": "1", "Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req).read() or b"{}")
    except urllib.error.HTTPError as exc:   # il server spiega il motivo nel corpo della risposta
        raise RuntimeError(f"{path}: {exc.code} {exc.read().decode(errors='replace')}") from exc


def state():
    return json.loads(urllib.request.urlopen(BASE + "/api/state").read())


# sicurezza: lo script cambia meccanica, fine corsa, preset e lingua. Se il server risponde con la cartella degli
# scatti dell'utente, è l'app vera (o l'app di prova, porta 8799) e non un'istanza con HOME separata: ci si ferma.
_root = state()["settings"].get("output_root") or ""
if _root.startswith(str(Path.home())):
    sys.exit(f"Il server su {BASE} usa le impostazioni vere ({_root}): avvia un'istanza con HOME separata "
             "(vedi l'inizio del file) e riprova.")


# ---- foto vere al posto di quelle del simulatore ----
# Le immagini degli scatti di prova, della sequenza e del live view vengono sostituite da fotogrammi veri di una pila
# (docs/guida/campione/: Calluna vulgaris, Sony A6400 + 70-350 a 2,8×). Dark e flat restano quelli del simulatore.
SAMPLE_DIR = Path(__file__).parent / "campione"
SAMPLES = sorted(f for f in SAMPLE_DIR.glob("calluna_*.jpg") if f.stem[-4:].isdigit())
SAMPLE_LIVE = SAMPLE_DIR / "calluna_live.jpg"
# figure con una foto dentro: in JPEG (le foto in PNG pesano 5-10 volte tanto); le altre restano PNG, più nitide sul testo
PHOTO_FIGS = {"sessione", "ultimo-scatto", "live", "visualizzatore", "ispettore", "visualizzatore-live", "smartphone-pagina",
              "visualizzatore-autofocus"}


def save_shot(page, name: str, **kw) -> None:
    """Salva la figura come <name>.jpg (foto) o <name>.png e toglie il file dell'altro formato rimasto da prima."""
    jpg = name in PHOTO_FIGS
    out = OUT / f"{name}.{'jpg' if jpg else 'png'}"
    page.screenshot(path=str(out), **({"type": "jpeg", "quality": 72} if jpg else {}), **kw)
    (OUT / f"{name}.{'png' if jpg else 'jpg'}").unlink(missing_ok=True)
_kinds: dict[int, str] = {}


def _shot_kind(sid: int) -> str:
    if sid not in _kinds:
        for it in json.loads(urllib.request.urlopen(BASE + "/api/shots").read()).get("items", []):
            _kinds[it["id"]] = it.get("kind", "")
    return _kinds.get(sid, "")


def _jpeg(route, path: Path) -> None:
    route.fulfill(path=str(path), headers={"Content-Type": "image/jpeg", "Cache-Control": "no-store"})


def real_shot(route) -> None:
    m = re.search(r"/api/shots/(\d+)/image\?size=(\w+)", route.request.url)
    if not m or not SAMPLES or _shot_kind(int(m[1])) == "calibration":
        return route.continue_()
    f = SAMPLES[int(m[1]) % len(SAMPLES)]
    _jpeg(route, f if m[2] == "full" else f.with_name(f.stem + "_anteprima.jpg"))


def real_live(route) -> None:
    return _jpeg(route, SAMPLE_LIVE) if SAMPLE_LIVE.exists() else route.continue_()


def real_remote(route) -> None:   # anteprima della pagina per lo smartphone
    if not SAMPLES:
        return route.continue_()
    f = SAMPLES[-1]
    _jpeg(route, f if "z=1" in route.request.url else f.with_name(f.stem + "_anteprima.jpg"))


def shot(page, name, target, marks=(), pad=0):
    """Schermata dell'elemento `target` con i riquadri degli elementi numerati `marks`
    [(numero, selettore, ancora)], ancora: l (sinistra), r (destra), t (in alto a sinistra)."""
    if ONLY and name not in ONLY:
        return
    el = page.locator(target).first
    # le sezioni delle schede di impostazioni non hanno margine proprio: si prende un po' del riquadro intorno
    if pad < 14 and el.evaluate("e => e.classList.contains('set-sec')"):
        pad = 14
    el.scroll_into_view_if_needed()
    page.wait_for_timeout(150)
    box = el.bounding_box()
    clip = {"x": box["x"] - pad, "y": box["y"] - pad, "width": box["width"] + 2 * pad, "height": box["height"] + 2 * pad}
    save_shot(page, name, clip=clip)
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


def wait_calibration(limit_s=180):
    """Aspetta la fine dell'esposizione automatica o di una serie di calibrazione."""
    time.sleep(1)
    for _ in range(limit_s * 2):
        if not state()["calibration"]["busy"]:
            return
        time.sleep(0.5)
    print("  calibrazione ancora in corso dopo", limit_s, "s")


def m(*specs):
    return [(n, s, a) for n, s, a in specs]


post("/api/settings", {"language": LANG})   # la pagina si apre già nella lingua della guida

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    ctx = browser.new_context(viewport={"width": 1440, "height": 1000}, device_scale_factor=2)
    ctx.route("**/api/shots/*/image*", real_shot)
    ctx.route("**/api/camera/live*", real_live)
    page = ctx.new_page()
    page.on("dialog", lambda d: d.accept())
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
    post("/api/optics/profiles/save", {"name": PROFILE_MACRO, "optics": {
        "kind": "macro", "sensor_pixel_um": 3.9, "dof_overlap": 30, "filter_mode": "none",
        "illumination": {"type": SAMPLE["illum_macro"], "level_percent": 80, "color_temp_k": 5500},
        "macro": {"lens": {"maker": "Sony", "model": "FE 90mm F2.8 Macro G OSS", "focal_mm": 90, "max_aperture": 2.8,
                           "source": "lensfun"},
                  "lens_magnification": 0.5, "f_number": 8, "extension_mm": 0,
                  "closeup": [{"name": "Raynox DCR-250", "diopters": 8}]}}})
    Path(SEQ_DIR).mkdir(parents=True, exist_ok=True)
    post("/api/settings", {"output_root": SEQ_DIR})
    # libreria di calibrazione d'esempio (pochi fotogrammi): flat e dark dei flat, poi l'esposizione dei light e
    # i dark allo stesso tempo di posa, così tutti e tre i set risultano adatti alla prossima pila
    for kind in ("flat", "flat_dark"):
        post("/api/calibration/start", {"kind": kind, "count": 4, "target_pct": 50})
        wait_calibration()
    post("/api/exposure/auto", {"target_pct": 85, "stat": "highlights"})
    wait_calibration()
    post("/api/calibration/start", {"kind": "dark", "count": 4})
    wait_calibration()
    REMOTE_URL = post("/api/remote", {"enabled": True})["url"]
    REMOTE_URL = "http://127.0.0.1:" + REMOTE_URL.split(":", 2)[2]   # l'istanza di prova ascolta solo su 127.0.0.1
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
      set('sum-phonex', new URL(window.FAKE_URL).host);   // riepilogo della Configurazione: niente indirizzo vero
      const root = document.getElementById('k-root');
      if (root && root.textContent.includes(SEQ)) root.textContent = root.textContent.replace(SEQ, '~/Pictures/FocusStack');
      document.querySelectorAll('#k-table td').forEach((td) => { if (td.textContent === SIM) td.textContent = 'Nikon DSC D5600'; });
    }"""
    page.evaluate(f"window.SEQ = {json.dumps(SEQ_DIR)}; window.SIM = {json.dumps(state()['camera']['model'])}; "
                  f"window.FAKE_URL = {json.dumps(FAKE_URL)}; window.FAKE_QR = {json.dumps(FAKE_QR)};")
    page.evaluate(f"setInterval({fake}, 30)")
    page.evaluate(f"setInterval({SCRUB}, 50)")
    page.evaluate("document.activeElement && document.activeElement.blur()")
    page.wait_for_timeout(100)
    page.evaluate("window.scrollTo(0, 0)")
    if not ONLY or "sessione" in ONLY:
        save_shot(page, "sessione")
    notes["sessione"] = {"w": 1440, "h": 1000, "marks": []}
    print("ok sessione")

    page.set_viewport_size({"width": 1440, "height": 2600})
    page.wait_for_timeout(500)
    shot(page, "barra-superiore", "header.topbar", m(
        (1, ".tabs", "l"), (2, "#st-link", "l"), (3, "#st-temp", "l"), (4, "#guide-btn", "r"), (5, "#theme-btn", "r")))
    shot(page, "focheggiatore", "#card-focuser", m(
        (1, "#f-chip", "r"), (2, "#f-connected-line", "l"), (3, ".pos-main", "l"), (4, ".pos-side", "r"),
        (5, "#rail", "l"), (6, "#jog-size", "l"), (7, "#jog-um", "l"), (8, ".jog-buttons", "l"),
        (9, ".row.goto", "l"), (10, "#f-halt", "l")))
    # «＋ Nuova pila» compare solo a pila finita: nella figura si mostra lo stesso
    keep_new = page.add_style_tag(content="#s-new.hidden { display: inline-flex !important; }")
    page.wait_for_timeout(100)
    # riepilogo aperto: nella figura si vedono anche le righe del profilo ottico e della calibrazione
    page.evaluate("document.getElementById('s-sum-more').open || document.querySelector('#s-sum-more > summary').click()")
    page.wait_for_timeout(100)
    shot(page, "sequenza", "#card-seq", m(
        (1, "#s-chip", "r"), (2, "#s-name", "l"), (3, "#s-new", "r"), (4, "#s-start", "l"), (5, "#s-step", "l"),
        (6, "#s-count", "l"), (7, "#s-settle", "l"), (8, "#s-optics", "l"), (9, "#s-summary", "l"), (10, "#s-folder", "l"),
        (11, "#s-repeats", "l"), (12, "#s-post", "l"), (13, "#s-backlash", "l"), (14, "#s-mode", "l"),
        (15, "label.check:has(#s-return)", "r"), (16, "#s-sound", "l"), (17, "#s-preset", "l"), (18, "#card-seq .progress-box", "l"),
        (19, "#card-seq .seq-actions", "l"), (20, "#s-finder", "l")))
    keep_new.evaluate("e => e.remove()")
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
    # gruppo «Strumenti» (profondità di campo) nascosto: ha la sua figura
    hide_tools = "document.querySelectorAll('#card-optics > .set-group')[3].style.display = document.querySelector('#opt-dof').parentElement.style.display = '{v}'"
    page.evaluate(hide_tools.format(v="none"))
    # una modifica non salvata: compare la barra in alto con Annulla, Salva come nuovo e Salva profilo
    page.fill("#o-level", "70"); page.dispatch_event("#o-level", "input")
    page.wait_for_timeout(300)
    page.evaluate("window.scrollTo(0, 0)")
    shot(page, "ottica", "#view-optics", m(
        (1, "#o-profile", "l"), (2, "#o-profile-save", "l"), (3, "#o-profile-del", "r"), (4, "#o-kind", "r"),
        # in ordine fisico, come nella pagina: sensore, adattatore, cambio intermedio, obiettivo
        (5, "#d-px", "l"), (6, "#o-relay-name", "r"), (7, "#o-inter-name", "l"), (8, "#o-objective", "r"),
        (9, "#d-mag", "l"), (10, "#d-na", "r"), (11, "#o-immersion", "l"), (12, "#o-pxcal", "r"), (13, "#o-pxresult", "l"),
        (14, "#o-filter-mode", "r"), (15, "#o-fname", "l"), (16, "#o-fcenter", "r"), (17, "#o-illum", "l"),
        (18, "#o-notes", "r"), (19, "#o-save", "l"), (20, "#o-chip", "r"), (21, "#opt-nav", "t"), (22, "#opt-sum", "t")))
    page.click("#o-undo")
    page.wait_for_timeout(200)
    page.evaluate(hide_tools.format(v=""))
    # profondità di campo: profilo senza Optovar (come gli esempi del capitolo 11)
    page.select_option("#o-profile", PROFILE); page.dispatch_event("#o-profile", "change")
    page.wait_for_timeout(300)
    shot(page, "profondita", "#opt-dof", m(
        (1, "#d-ov", "l"), (2, "#d-result", "l"), (3, "#d-apply", "r")), pad=6)
    notes["profondita"]["text"] = page.inner_text("#d-result")
    # profilo macro: lo stesso esempio del capitolo 7.3 (90 mm a 1:2, f/8, Raynox +8 diottrie)
    page.select_option("#o-profile", PROFILE_MACRO); page.dispatch_event("#o-profile", "change")
    page.wait_for_timeout(500)
    page.evaluate("window.scrollTo(0, 0)")
    page.evaluate(hide_tools.format(v="none"))
    shot(page, "ottica-macro", "#card-optics", m(
        (1, "#o-kind", "l"), (2, "#m-search", "l"), (3, "#m-maker", "r"), (4, "#m-focal", "l"), (5, "#m-lens-add", "r"),
        (6, "#m-mag", "l"), (7, "#m-fnum", "r"), (8, "#m-ext", "l"), (9, "#m-closeups", "r"), (10, "#o-pxresult", "l")))
    page.evaluate(hide_tools.format(v=""))
    page.select_option("#o-profile", PROFILE); page.dispatch_event("#o-profile", "change")
    page.wait_for_timeout(300)

    # ---- calibrazione: esposizione, frame, libreria (set veri fatti col simulatore) ----
    page.click(".tabs button[data-tab=calib]")
    page.wait_for_timeout(1200)
    page.evaluate("window.scrollTo(0, 0)")
    shot(page, "calibrazione-esposizione", "#card-expo", m(
        (1, "#x-stat", "l"), (2, "#x-target", "r"), (3, "#x-start", "l"), (4, "#x-result", "r")))
    page.click("#k-kind button[data-kind=flat]")
    page.wait_for_timeout(300)
    shot(page, "calibrazione-frame", "#card-calib", m(
        (1, "#k-kind", "l"), (2, "#k-count", "r"), (3, "#k-target", "l"), (4, "#card-calib .progress-box", "l"),
        (5, "#card-calib .set-actions", "l")))
    shot(page, "calibrazione-libreria", "#card-library", m((1, "#k-open", "l"), (2, "#k-match", "l"), (3, "#k-table", "l")))
    shot(page, "calibrazione-riepilogo", "#cal-sum", m((1, "#ksum-dark", "l"), (2, "#t-value", "l"), (3, "#t-spark", "l")), pad=4)

    # ---- configurazione ----
    page.click(".tabs button[data-tab=config]")
    page.wait_for_timeout(1200)
    page.evaluate("window.scrollTo(0, 0)")
    page.fill("#lim-max", "44000"); page.dispatch_event("#lim-max", "input")
    page.wait_for_timeout(200)
    shot(page, "fine-corsa", "#card-limits", m(
        (1, "#lim-min", "l"), (2, "#lim-max", "l"), (3, "#lim-dir", "l"), (4, "#lim-save", "r"),
        (5, "#lim-zero", "l"), (6, "#lim-fw", "l")))
    page.click("#lim-undo")
    # la pagina intera, con l'indice a sinistra e il riepilogo a destra
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(300)
    shot(page, "configurazione", "#view-config", m(
        (1, "#cfg-search", "l"), (2, "#cfg-nav a[href='#card-motor']", "l"), (3, "#card-motor .card-head h2", "l"),
        (4, "#card-motor .set-details summary", "l"), (5, "#cfg-sum", "t")))
    shot(page, "meccanica", "#card-mech", m(
        (1, "#mech-mode", "l"), (2, "#m-spr", "r"), (3, "#m-micro", "l"), (4, "#m-gear", "r"),
        (5, "#m-umrev", "l"), (6, "#m-result", "l")))
    page.click("#mech-mode button[data-mode=manual]")
    page.fill("#m-umstep", "0.083"); page.dispatch_event("#m-umstep", "input")   # il valore misurato dell'esempio
    page.wait_for_timeout(200)
    shot(page, "meccanica-manuale", "#card-mech", m((1, "#mech-mode", "l"), (2, "#m-umstep", "r"), (3, "#m-result", "l")))
    page.click("#mech-mode button[data-mode=computed]")
    shot(page, "comandi-manuali", "#card-jog", m((1, "#jog-max", "l"), (2, "#jog-hold", "r"), (3, "#jog-chunk", "l")))
    # autofocus: ricerca ampia accesa, così si vede anche la riga «Cerca entro ±»
    post("/api/autofocus/settings", {"source": "shot", "roi_px": 256, "coarse": True, "forget_width": True})
    page.wait_for_timeout(1200)
    shot(page, "autofocus-config", "#card-af", m(
        (1, "#af-src", "l"), (2, "#af-roi", "l"), (3, "#af-fine-step", "l"), (4, "#af-coarse", "l"),
        (5, "#af-coarse-range", "l"), (6, "#af-width", "l")))
    # bobine spente a motore fermo: compare l'opzione "Alimentale comunque durante la sequenza"
    post("/api/focuser/motor", {"name": "coil_power", "value": False})
    page.wait_for_timeout(1500)
    shot(page, "motore", "#card-motor", m(
        (1, "#mo-step_mode", "l"), (2, "#mo-speed", "r"), (3, "#mo-coil_power", "l"), (4, "#opt-coil-seq", "r"),
        (5, "#mo-reverse", "l"), (6, "#mo-backlash_in_enabled", "r"), (7, "#mo-backlash_in_steps", "r"), (8, "#mo-reload", "r")))
    post("/api/focuser/motor", {"name": "coil_power", "value": True})
    shot(page, "smartphone", "#card-remote", m((1, "#r-enabled", "l"), (2, "#r-qr", "l"), (3, "#r-new", "l")))
    # 1 a sinistra e 2 a destra: le due righe sono troppo vicine per due numeri uno sopra l'altro
    shot(page, "aggiornamenti", "#card-updates", m((1, "#up-app", "r"), (2, "#up-fw", "l"), (3, "#fw-update", "r"), (4, "#up-check", "r")))
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
        (1, "#prev", "l"), (2, "#v-count", "l"), (3, "#liveview", "l"), (4, "#z-out", "l"), (5, "#z-fit", "l"),
        (6, "#follow", "l"), (7, "#lock", "l"), (8, "#guides", "l"), (9, "#clear", "l"), (10, "#insp-btn", "l"),
        (11, "#fs", "l"), (12, "#guide-btn", "r"), (13, "#strip", "l")))
    vw.set_viewport_size({"width": 1500, "height": 1250})   # il pannello dell'Ispettore intero, fino ai valori sotto il puntatore
    vw.click("#z-fit")
    vw.click("#insp-btn")
    vw.wait_for_timeout(1500)
    vw.check("#insp-marks")
    box = vw.locator("#stage").bounding_box() or {"x": 300, "y": 300, "width": 400, "height": 300}
    for dx in (0.38, 0.4):   # due movimenti: i valori sotto il puntatore si aggiornano al movimento
        vw.mouse.move(box["x"] + box["width"] * dx, box["y"] + box["height"] * 0.3)
        vw.wait_for_timeout(400)
    vw.wait_for_timeout(1000)
    shot(vw, "ispettore", "body", m((1, "#insp-marks", "l"), (2, "#insp-hist", "l"), (3, "#insp-px", "l")))
    vw.click("#insp-btn")
    vw.wait_for_timeout(300)
    vw.set_viewport_size({"width": 1500, "height": 860})
    vw.click("#liveview")
    vw.wait_for_timeout(2000)
    shot(vw, "visualizzatore-live", "body", m((1, "#liveview", "l"), (2, "#live-badge", "r")))
    # autofocus su un punto, con il live view (predefinito): il live del simulatore è una scacchiera uniforme, a fuoco a
    # 25 000, quindi la curva è pulita in qualsiasi punto dell'immagine (che nella figura è la foto vera del live)
    post("/api/autofocus/settings", {"source": "live", "roi_px": 256, "coarse": False, "settle_ms": 100,
                                     "passes": 1, "forget_width": True})
    post("/api/focuser/move", {"position": 24000})
    for _ in range(120):
        f = state()["focuser"]
        if f["position"] == 24000 and not f["moving"]:
            break
        time.sleep(0.5)
    vw.wait_for_timeout(1500)
    vw.keyboard.press("a")
    vw.wait_for_timeout(300)
    box = vw.locator("#stage").bounding_box() or {"x": 300, "y": 300, "width": 400, "height": 300}
    vw.mouse.click(box["x"] + box["width"] * 0.42, box["y"] + box["height"] * 0.45)
    vw.wait_for_timeout(300)
    vw.click("#af-start")
    time.sleep(2)
    for _ in range(400):
        if not state()["autofocus"]["busy"]:
            break
        time.sleep(0.5)
    vw.wait_for_timeout(2500)
    shot(vw, "visualizzatore-autofocus", "body", m(
        (1, "#af-btn", "r"), (2, "#af-roi", "t"), (3, ".af-src", "r"), (4, "#af-chart", "l"), (5, "#af-status", "l"),
        (6, "#af-use-start", "l")))
    post("/api/autofocus/settings", {"source": "live", "roi_px": 256, "coarse": False})
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
    phone_ctx = browser.new_context(viewport={"width": 390, "height": 1200}, device_scale_factor=2,
                                    is_mobile=True, has_touch=True, color_scheme="dark")
    phone_ctx.route("**/preview*", real_remote)
    ph = phone_ctx.new_page()
    ph.goto(REMOTE_URL)
    ph.wait_for_timeout(2500)
    ph.click("#btn")
    ph.wait_for_timeout(3000)
    shot(ph, "smartphone-pagina", "main", m((1, "#count", "l"), (2, "#snd", "l"), (3, "#btn", "l"), (4, "#view", "t")), pad=12)
    phone_ctx.close()
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

post("/api/remote", {"enabled": False})
post("/api/settings", {"language": "auto"})

(OUT / "annotazioni.json").write_text(json.dumps(notes, indent=1, ensure_ascii=False), encoding="utf-8")
print("annotazioni salvate")
