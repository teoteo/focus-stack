"""Genera la guida all'uso in PDF, in italiano e in inglese, dalle schermate in img/<lingua>/.
    python3.11 docs/guida/genera_guida.py [it|en|all]      (predefinito: all)
Produce docs/Guida Focus Stack.pdf (it) e docs/Focus Stack Guide.pdf (en).
Il testo sta in testo_it.py e testo_en.py; le schermate e le posizioni dei numeri si rifanno con
cattura_schermate.py --lang <lingua>. Se mancano le schermate di una lingua usa quelle italiane.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
VERSION = (ROOT / "VERSION").read_text().strip()
ICON = (ROOT / "web" / "icon.svg").read_text()
LANGS = ("it", "en", "fr", "de", "es")


def make_fig(notes, img_dir):
    def fig(name, legend=(), layout="side", width=None, caption="", anchors=None):
        """Schermata con i numeri sopra gli elementi e, accanto o sotto, la legenda numerata.
        anchors {numero: ancora} sostituisce l'ancora salvata: "b" = sotto l'elemento, centrato
        (per le barre di pulsanti fitti, dove a sinistra il numero coprirebbe il pulsante vicino)."""
        marks = []
        for mk in notes.get(name, {}).get("marks", []):
            x, y, w, h = mk["x"], mk["y"], mk["w"], mk["h"]
            mk = {**mk, "anchor": (anchors or {}).get(mk["n"], mk["anchor"])}
            if mk["anchor"] == "b":
                cx, cy = x + w / 2, y + h
            elif mk["anchor"] == "r":
                cx, cy = x + w, y + h / 2
            elif mk["anchor"] == "t":
                cx, cy = x, y
            else:
                cx, cy = x, y + h / 2
            marks.append(f'<span class="mk {mk["anchor"]}" style="left:{cx * 100:.2f}%;top:{cy * 100:.2f}%">{mk["n"]}</span>')
        style = f' style="width:{width}"' if width else ""
        img = (f'<figure class="shot"{style}><div class="frame"><img src="{img_dir}/{name}.png" alt="">'
               f'{"".join(marks)}</div>{f"<figcaption>{caption}</figcaption>" if caption else ""}</figure>')
        if not legend:
            return f'<div class="fig-wrap {layout}">{img}</div>'
        items = "".join(f'<li><span class="num">{i}</span><div>{text}</div></li>' for i, text in enumerate(legend, 1))
        return f'<div class="fig-wrap {layout}">{img}<ol class="legend">{items}</ol></div>'
    return fig


def frac(num, den):
    return f'<span class="frac"><span>{num}</span><span>{den}</span></span>'


CSS = """
@page { size: A4; margin: 17mm 16mm 18mm 16mm; }
@page :first { margin: 0; }
* { box-sizing: border-box; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; font-size: 10.3pt;
  line-height: 1.5; color: #1d232b; hyphens: auto; }
h1 { font-size: 22pt; line-height: 1.15; margin: 0 0 4mm; color: #0f1c2e; break-before: page;
  padding-bottom: 3mm; border-bottom: 2.5px solid #2f81f7; }
h1 .n { color: #2f81f7; margin-right: 3mm; }
h2 { font-size: 13.5pt; margin: 7mm 0 2mm; color: #0f1c2e; break-after: avoid; }
h3 { font-size: 11pt; margin: 5mm 0 1.5mm; color: #23364f; break-after: avoid; }
p { margin: 0 0 2.6mm; }
ul, ol { margin: 0 0 3mm; padding-left: 5.5mm; }
li { margin-bottom: 1mm; }
b, strong { color: #0f1c2e; }
code, kbd { font-family: "SF Mono", Menlo, monospace; font-size: 8.8pt; background: #eef2f7;
  border: 1px solid #d6dde8; border-radius: 3px; padding: 0 1.2mm; }
.ui { font-weight: 700; color: #0f1c2e; white-space: nowrap; }
.lead { font-size: 11.2pt; color: #33475f; }
table { width: 100%; border-collapse: collapse; margin: 2mm 0 4mm; font-size: 9.5pt; break-inside: avoid; }
th, td { text-align: left; padding: 1.6mm 2.2mm; border-bottom: 1px solid #dfe5ee; vertical-align: top; }
th { background: #eef3fa; color: #23364f; font-weight: 700; }
td.r, th.r { text-align: right; font-variant-numeric: tabular-nums; }
.box { border-radius: 2.5mm; padding: 3mm 4mm; margin: 3mm 0 4mm; break-inside: avoid; }
.box.tip { background: #eaf4ff; border-left: 4px solid #2f81f7; }
.box.warn { background: #fff5e5; border-left: 4px solid #e8a33a; }
.box.danger { background: #fdecec; border-left: 4px solid #d9534f; }
.box > :last-child { margin-bottom: 0; }
.box .t { font-weight: 700; display: block; margin-bottom: 1mm; }
.formula { background: #f4f7fb; border: 1px solid #d6dde8; border-radius: 2.5mm; padding: 4mm 5mm;
  margin: 3mm 0 4mm; text-align: center; font-size: 13pt; break-inside: avoid; }
.formula .lbl { display: block; font-size: 9pt; color: #5a6b80; margin-top: 2mm; text-align: center; }
.frac { display: inline-flex; flex-direction: column; vertical-align: middle; text-align: center; margin: 0 1mm; }
.frac > span:first-child { border-bottom: 1.3px solid currentColor; padding: 0 1.5mm 0.6mm; }
.frac > span:last-child { padding: 0.6mm 1.5mm 0; }
.calc { font-family: "SF Mono", Menlo, monospace; font-size: 9.2pt; background: #f7f9fc; border: 1px solid #e1e7ef;
  border-radius: 2mm; padding: 2.5mm 3.5mm; margin: 2mm 0 3.5mm; white-space: pre-wrap; break-inside: avoid; line-height: 1.55; }
.calc b { color: #1a5fc9; }

.fig-wrap { margin: 3mm 0 5mm; break-inside: avoid; }
.fig-wrap.side { display: grid; grid-template-columns: 54% 1fr; gap: 7mm; align-items: start; }
.fig-wrap.side.narrow { grid-template-columns: 44% 1fr; }
.fig-wrap.full .legend { columns: 2; column-gap: 7mm; margin-top: 4mm; }
.fig-wrap.full .legend li { break-inside: avoid; }
/* rientro: i numeri appena fuori dalle schermate non devono finire nel margine (Chrome non lo stampa) */
figure.shot { margin: 0; padding: 0 6mm; }
figure.shot .frame { position: relative; }
figure.shot img { display: block; width: 100%; border-radius: 2mm; box-shadow: 0 0 0 1px #c9d2de; }
figcaption { font-size: 8.8pt; color: #5a6b80; margin-top: 1.5mm; text-align: center; }
.mk { position: absolute; transform: translate(-50%, -50%); width: 5.4mm; height: 5.4mm; border-radius: 50%;
  background: #ffc531; color: #111; font-size: 8.2pt; font-weight: 800; display: grid; place-items: center;
  box-shadow: 0 0 0 1.4px #111, 0 0.6mm 1.4mm rgba(0,0,0,.45); line-height: 1; }
/* il numero sta appena fuori dal bordo dell'elemento (a sinistra o a destra), per non coprirne il testo */
.mk.l { transform: translate(calc(-100% - 0.5mm), -50%); }
.mk.r { transform: translate(0.5mm, -50%); }
.mk.b { transform: translate(-50%, 0.6mm); }
.fig-wrap.below-marks figure.shot { padding-bottom: 6.5mm; }
.legend { list-style: none; padding: 0; margin: 0; font-size: 9.6pt; }
.legend li { display: grid; grid-template-columns: 6.5mm 1fr; gap: 2mm; margin-bottom: 2.1mm; }
.legend .num { width: 5mm; height: 5mm; border-radius: 50%; background: #ffc531; color: #111; font-weight: 800;
  font-size: 7.8pt; display: grid; place-items: center; box-shadow: 0 0 0 1.2px #111; margin-top: 0.3mm; }

.cover { height: 297mm; width: 210mm; background: #0d1117; color: #e8edf4; padding: 34mm 22mm 20mm;
  display: flex; flex-direction: column; break-after: page; }
.cover .icon { width: 34mm; height: 34mm; }
.cover .icon svg { width: 100%; height: 100%; }
.cover h1.title { border: 0; color: #fff; font-size: 40pt; margin: 12mm 0 3mm; break-before: auto; padding: 0; }
.cover .sub { font-size: 16pt; color: #9fb3c8; margin-bottom: 14mm; }
.cover .shot-c { margin-top: auto; border-radius: 3mm; overflow: hidden; box-shadow: 0 0 0 1px #2a3442; }
.cover .shot-c img { width: 100%; display: block; }
.cover .meta { margin-top: 8mm; font-size: 10pt; color: #8193a8; display: flex; justify-content: space-between; }

.toc { columns: 1; font-size: 11pt; }
.toc ol { padding-left: 0; list-style: none; }
.toc li { padding: 1.6mm 0; border-bottom: 1px dotted #c9d2de; }
.toc li span { color: #2f81f7; font-weight: 700; display: inline-block; width: 9mm; }
.toc li em { display: block; font-style: normal; color: #5a6b80; font-size: 9.2pt; padding-left: 9mm; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; }
.keep { break-inside: avoid; }
svg.diagram { width: 100%; height: auto; display: block; margin: 2mm 0 4mm; }
.steps { counter-reset: s; list-style: none; padding-left: 0; }
.steps > li { counter-increment: s; position: relative; padding-left: 9mm; margin-bottom: 2.4mm; break-inside: avoid; }
.steps > li::before { content: counter(s); position: absolute; left: 0; top: 0; width: 6mm; height: 6mm; border-radius: 50%;
  background: #2f81f7; color: #fff; font-weight: 700; font-size: 8.8pt; display: grid; place-items: center; }
"""

# ---------------------------------------------------------------- schema della trasmissione
# le etichette arrivano dal testo di ogni lingua (DIAGRAM_LABELS)
DIAGRAM = """
<svg class="diagram" viewBox="0 0 760 250" xmlns="http://www.w3.org/2000/svg" font-family="Helvetica Neue, Helvetica, Arial" font-size="13">
  <defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
    <path d="M0,0 L10,5 L0,10 z" fill="#2f81f7"/></marker></defs>
  <g fill="#f4f7fb" stroke="#9fb0c5" stroke-width="1.5">
    <rect x="10" y="40" width="130" height="92" rx="10"/>
    <rect x="170" y="40" width="120" height="92" rx="10" stroke-dasharray="5 4"/>
    <rect x="320" y="40" width="150" height="92" rx="10"/>
    <rect x="500" y="40" width="120" height="92" rx="10"/>
    <rect x="650" y="40" width="100" height="92" rx="10"/>
  </g>
  <g fill="#0f1c2e" font-weight="700" text-anchor="middle">
    <text x="75" y="66">{motor}</text><text x="230" y="66">{gearbox}</text><text x="395" y="66">{pulleys}</text>
    <text x="560" y="66">{knob}</text><text x="700" y="66">{stage}</text>
  </g>
  <g fill="#33475f" text-anchor="middle" font-size="12">
    <text x="75" y="88">{motor1}</text><text x="75" y="106">{motor2}</text>
    <text x="230" y="88">{gearbox1}</text><text x="230" y="106">{gearbox2}</text>
    <text x="395" y="88">{pulleys1}</text><text x="395" y="106">{pulleys2}</text>
    <text x="560" y="88">{knob1}</text><text x="560" y="106">{knob2}</text>
    <text x="700" y="88">{stage1}</text><text x="700" y="106">{stage2}</text>
  </g>
  <g stroke="#2f81f7" stroke-width="2.5" marker-end="url(#ar)">
    <line x1="141" y1="86" x2="166" y2="86"/><line x1="291" y1="86" x2="316" y2="86"/>
    <line x1="471" y1="86" x2="496" y2="86"/><line x1="621" y1="86" x2="646" y2="86"/>
  </g>
  <path d="M170 150 h300" stroke="#e8a33a" stroke-width="2"/><path d="M170 144 v12 M470 144 v12" stroke="#e8a33a" stroke-width="2"/>
  <text x="320" y="176" text-anchor="middle" fill="#9a6412" font-weight="700">{ratio}</text>
  <path d="M10 205 h610" stroke="#2f81f7" stroke-width="2"/><path d="M10 199 v12 M620 199 v12" stroke="#2f81f7" stroke-width="2"/>
  <text x="315" y="232" text-anchor="middle" fill="#1a5fc9" font-weight="700">{steps}</text>
</svg>
"""


def diagram(labels):
    return DIAGRAM.format(**labels)


def table(head, rows, right=()):
    th = "".join(f'<th class="{"r" if i in right else ""}">{h}</th>' for i, h in enumerate(head))
    trs = "".join("<tr>" + "".join(f'<td class="{"r" if i in right else ""}">{c}</td>' for i, c in enumerate(r)) + "</tr>"
                  for r in rows)
    return f"<table><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table>"


def make_num(lang):
    # separatore delle migliaia e dei decimali: it/de/es 5.370,25 · en 5,370.25 · fr 5 370,25 (spazio fine)
    group, dec = {"en": (",", "."), "fr": ("\u202f", ",")}.get(lang, (".", ","))

    def num(x, d=2):
        s = f"{x:,.{d}f}"
        return s.replace(",", "§").replace(".", dec).replace("§", group)
    return num


def app_strings(lang):
    """Traduzioni dell'app ({testo italiano: traduzione}): i nomi dei comandi nella guida sono gli stessi."""
    out = {}
    for p in sorted((ROOT / "web" / "lang").glob(f"{lang}-*.json")):
        out.update(json.loads(p.read_text(encoding="utf-8")))
    return out


# ---------------------------------------------------------------- calcoli degli esempi
GEAR17 = 26 + 103 / 121


def um_step(knob, spr, micro, ratio):
    return knob / (spr * micro * ratio)


def dof(na, mag, px):
    return 0.55 * 1.0 / na ** 2 + 1.0 * px / (mag * na)


UA = um_step(100, 400, 1, 3)
UB = um_step(100, 200, 1, GEAR17)
OBJ = [(4, .10), (10, .25), (20, .40), (40, .65), (60, .85), (100, 1.25)]   # ingrandimento, NA


def build(lang):
    """Esegue testo_<lang>.py con gli helper comuni e restituisce (META, html)."""
    img_dir = f"img/{lang}"
    if not (HERE / img_dir / "annotazioni.json").exists():
        print(f"ATTENZIONE: mancano le schermate in {img_dir}/, uso quelle italiane")
        img_dir = "img/it"
    notes = json.loads((HERE / img_dir / "annotazioni.json").read_text(encoding="utf-8"))
    ns = {"fig": make_fig(notes, img_dir), "frac": frac, "table": table, "num": make_num(lang), "diagram": diagram,
          "APP": app_strings(lang),
          "VERSION": VERSION, "ICON": ICON, "IMG": img_dir, "UA": UA, "UB": UB, "GEAR17": GEAR17,
          "um_step": um_step, "dof": dof, "OBJ": OBJ}
    path = HERE / f"testo_{lang}.py"
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), ns)
    meta = ns["META"]
    html = (f'<!doctype html><html lang="{meta["lang"]}"><head><meta charset="utf-8"><title>{meta["title"]}</title>'
            f'<style>{CSS}</style></head><body>{"".join(ns["H"])}</body></html>')
    return meta, html


def render(lang, browser):
    meta, html = build(lang)
    out_html = HERE / f"guida-{lang}.html"
    out_pdf = HERE.parent / meta["pdf"]
    out_html.write_text(html, encoding="utf-8")
    page = browser.new_page()
    page.goto(out_html.as_uri())
    page.wait_for_load_state("networkidle")
    page.pdf(path=str(out_pdf), format="A4", print_background=True, prefer_css_page_size=True,
             display_header_footer=True, header_template="<span></span>",
             footer_template=f'<div style="width:100%;font-size:8px;color:#8193a8;padding:0 16mm;display:flex;'
                             f'justify-content:space-between;font-family:Helvetica"><span>Focus Stack {VERSION} · {meta["footer"]}</span>'
                             '<span class="pageNumber"></span></div>')
    page.close()
    print("PDF:", out_pdf)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    langs = LANGS if which == "all" else (which,)
    if any(lang not in LANGS for lang in langs):
        sys.exit(f"Lingua non valida: {which} (it, en o all)")
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        for lang in langs:
            render(lang, b)
        b.close()
