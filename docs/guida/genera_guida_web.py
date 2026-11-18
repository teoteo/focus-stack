"""Guida HTML dentro l'app, con indice e ricerca, dallo stesso testo delle guide PDF (testo_<lingua>.py).
    python3.11 docs/guida/genera_guida_web.py            (tutte le lingue)
Produce web/guide/<lingua>.html e copia le schermate in web/guide/img/<lingua>/. L'app la apre da
«? Guida» in alto a destra e dai «?» delle card (mappa GUIDE in web/app.js).

Le ancore sono uguali in tutte le lingue (le traduzioni hanno la stessa struttura: lo script controlla):
c<capitolo>, c<capitolo>-<sezione>, c<capitolo>-<sezione>-<sottosezione>, e per le parti collegate
dall'app un nome fisso (ALIASES): se i capitoli cambiano numero si aggiorna solo ALIASES, non l'app.
web/guide/ non sta nel repository: la rigenera build_release.sh a ogni pubblicazione.
"""
import json
import re
import shutil
import sys
from html import unescape
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import genera_guida as G  # noqa: E402

OUT = G.ROOT / "web" / "guide"

UI = {
    "it": {"title": "Guida", "search": "Cerca nella guida", "toc": "Indice", "none": "Nessun risultato",
           "results": "{n} risultati", "one": "1 risultato", "clear": "Cancella", "top": "Torna su",
           "version": "Versione dell'app {v}"},
    "en": {"title": "Guide", "search": "Search the guide", "toc": "Contents", "none": "No results",
           "results": "{n} results", "one": "1 result", "clear": "Clear", "top": "Back to top",
           "version": "App version {v}"},
    "fr": {"title": "Guide", "search": "Rechercher dans le guide", "toc": "Sommaire", "none": "Aucun résultat",
           "results": "{n} résultats", "one": "1 résultat", "clear": "Effacer", "top": "Haut de page",
           "version": "Version de l'app {v}"},
    "de": {"title": "Anleitung", "search": "In der Anleitung suchen", "toc": "Inhalt", "none": "Keine Treffer",
           "results": "{n} Treffer", "one": "1 Treffer", "clear": "Löschen", "top": "Nach oben",
           "version": "App-Version {v}"},
    "es": {"title": "Guía", "search": "Buscar en la guía", "toc": "Índice", "none": "Sin resultados",
           "results": "{n} resultados", "one": "1 resultado", "clear": "Borrar", "top": "Volver arriba",
           "version": "Versión de la app {v}"},
}

# nome fisso delle parti collegate dall'app (GUIDE in web/app.js e web/viewer.js) -> ancora numerica
ALIASES = {
    "lingua": "c2-4", "interfaccia": "c3", "collegare": "c4", "collegare-focheggiatore": "c4-1",
    "collegare-fotocamera": "c4-2", "focheggiatore": "c5", "fotocamera": "c6", "live-view": "c6-1",
    "sequenza": "c7-1", "sequenza-in-corso": "c7-2", "profili-ottici": "c7-3", "macro": "c7-4", "piu-scatti": "c7-5",
    "file-pila": "c7-6", "calibrazione": "c7-7", "calibrazione-esposizione": "c7-7-1", "calibrazione-frame": "c7-7-2",
    "calibrazione-libreria": "c7-7-3", "smartphone": "c7-8", "visualizzatore": "c8", "ispettore": "c8-1",
    "fine-corsa": "c9", "meccanica": "c10", "passo": "c11",
    "motore": "c12-1", "comandi-manuali": "c12-2", "aggiornamenti": "c12-3", "temperatura": "c12-4",
    "sessione-tipo": "c13", "problemi": "c14", "scorciatoie": "c15",
}
ALIAS_OF = {num: name for name, num in ALIASES.items()}

HEAD = re.compile(r"<h([123])((?:\s[^>]*)?)>(.*?)</h\1>", re.S)


def plain(html: str) -> str:
    """Testo senza tag, spazi compattati (per indice e ricerca)."""
    text = re.sub(r"<svg.*?</svg>", " ", html, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", unescape(text)).strip()


def number_headings(body: str):
    """Aggiunge le ancore ai titoli e restituisce (html, titoli) con titoli = [(livello, id, testo)]."""
    heads, c, k, j = [], 0, 0, 0

    def repl(m):
        nonlocal c, k, j
        level, attrs, inner = int(m.group(1)), m.group(2) or "", m.group(3)
        if level == 1:
            c, k, j = c + 1, 0, 0
            hid = f"c{c}"
        elif level == 2:
            k, j = k + 1, 0
            hid = f"c{c}-{k}"
        else:
            j += 1
            hid = f"c{c}-{k}-{j}"
        attrs = re.sub(r'\sstyle="[^"]*"', "", attrs)   # interruzioni di pagina e margini del PDF
        hid = ALIAS_OF.get(hid, hid)
        heads.append((level, hid, plain(inner)))
        return f'<h{level} id="{hid}"{attrs}>{inner}</h{level}>'

    return HEAD.sub(repl, body), heads


def search_index(body: str, heads):
    """Un blocco per titolo: testo fra quel titolo e il successivo (per la ricerca nella pagina)."""
    cuts = [m.start() for m in HEAD.finditer(body)] + [len(body)]
    blocks, chapter = [], ""
    for (level, hid, title), a, b in zip(heads, cuts, cuts[1:]):
        if level == 1:
            chapter = title
        text = plain(HEAD.sub("", body[a:b], count=1))
        blocks.append({"id": hid, "t": title, "c": chapter if level > 1 else "", "x": text})
    return blocks


def toc_html(heads) -> str:
    out, open_ch = [], False
    for level, hid, title in heads:
        if level == 1:
            if open_ch:
                out.append("</ol></li>")
            m = re.match(r"(\d+)\s+(.*)", title)
            n, t = (m.group(1), m.group(2)) if m else ("", title)
            out.append(f'<li class="ch"><a href="#{hid}"><span class="n">{n}</span>{t}</a><ol>')
            open_ch = True
        elif level == 2:
            out.append(f'<li><a href="#{hid}">{title}</a></li>')
    if open_ch:
        out.append("</ol></li>")
    return "<ol>" + "".join(out) + "</ol>"


def build_web(lang: str):
    _meta, sections, img_dir = G.parts(lang)
    # niente copertina né indice del PDF: l'indice qui è nella colonna laterale
    body = "".join(s for s in sections if 'class="cover"' not in s and 'class="toc"' not in s)
    body, heads = number_headings(body)
    ui = UI[lang]
    data = {"ui": ui, "blocks": search_index(body, heads)}
    page = (PAGE.replace("__LANG__", lang)
            .replace("__TITLE__", f"Focus Stack · {ui['title']}")
            .replace("__CSS__", WEB_CSS)
            .replace("__TOC__", toc_html(heads))
            .replace("__BODY__", body)
            .replace("__SEARCH__", ui["search"])
            .replace("__TOCLABEL__", ui["toc"])
            .replace("__CLEAR__", ui["clear"])
            .replace("__TOP__", ui["top"])
            .replace("__VERSION__", ui["version"].format(v=G.VERSION))
            .replace("__HEADTITLE__", ui["title"])
            .replace("__ICON__", G.ICON)
            .replace("__DATA__", json.dumps(data, ensure_ascii=False).replace("</", "<\\/")))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{lang}.html").write_text(page, encoding="utf-8")
    # schermate: le immagini usate da questa lingua (img/<lingua> o, se mancano, quelle italiane)
    dst = OUT / img_dir
    dst.mkdir(parents=True, exist_ok=True)
    srcs = [f for f in (HERE / img_dir).iterdir() if f.suffix in (".png", ".jpg")]
    names = {f.name for f in srcs}
    for old in dst.iterdir():   # figure che hanno cambiato formato o non esistono più
        if old.suffix in (".png", ".jpg") and old.name not in names:
            old.unlink()
    for src in srcs:
        target = dst / src.name
        if not target.exists() or target.stat().st_mtime < src.stat().st_mtime:
            shutil.copy2(src, target)
    return [(lvl, hid) for lvl, hid, _ in heads]


WEB_CSS = """
:root { --bg:#0d1117; --panel:#141a22; --line:#262f3b; --fg:#e6eaf0; --muted:#9aa6b5; --accent:#5aa9ff;
  --head:#ffffff; --code:#1b2330; --tip:#11243a; --warn:#2f2413; --danger:#341a1c; --mark:#ffc531; --mark-fg:#111; }
:root[data-theme="light"] { --bg:#f4f6f9; --panel:#ffffff; --line:#dde3ea; --fg:#1d232b; --muted:#5a6b80; --accent:#1f74d6;
  --head:#0f1c2e; --code:#eef2f7; --tip:#eaf4ff; --warn:#fff5e5; --danger:#fdecec; }
* { box-sizing: border-box; }
html { scroll-padding-top: 76px; }
body { margin:0; background:var(--bg); color:var(--fg); font:17px/1.6 -apple-system, BlinkMacSystemFont, "Helvetica Neue", sans-serif; }
a { color: var(--accent); }
header.top { position:sticky; top:0; z-index:5; display:flex; align-items:center; gap:14px; padding:10px 18px;
  background:var(--panel); border-bottom:1px solid var(--line); }
header.top .brand { display:flex; align-items:center; gap:10px; font-weight:700; white-space:nowrap; color:var(--head); }
header.top .brand svg { width:28px; height:28px; }
#q { flex:1; max-width:520px; font:inherit; font-size:16px; padding:9px 14px; border-radius:10px; border:1px solid var(--line);
  background:var(--bg); color:var(--fg); }
#q::placeholder { color:var(--muted); font-style:italic; }
#menu { display:none; font:inherit; font-size:15px; padding:8px 12px; border-radius:10px; border:1px solid var(--line);
  background:var(--bg); color:var(--fg); }
header.top .ver { margin-left:auto; color:var(--muted); font-size:13px; white-space:nowrap; }
.layout { display:grid; grid-template-columns: 320px minmax(0, 1fr); }
nav.side { position:sticky; top:57px; height:calc(100vh - 57px); overflow:auto; padding:14px 10px 40px 18px;
  border-right:1px solid var(--line); font-size:15px; }
nav.side ol { list-style:none; margin:0; padding:0; }
nav.side li.ch > a { font-weight:700; margin-top:8px; }
nav.side li.ch > ol a { padding-left:30px; font-size:14px; color:var(--muted); }
nav.side a { display:block; padding:4px 8px; border-radius:7px; text-decoration:none; color:var(--fg); }
nav.side a:hover, nav.side a.on { background:var(--code); }
nav.side a.on { color:var(--accent); }
nav.side .n { display:inline-block; min-width:24px; color:var(--accent); }
#results { display:none; }
#results.show { display:block; }
#results .count { color:var(--muted); font-size:13px; padding:4px 8px 8px; }
#results a { margin-bottom:6px; }
#results a b { display:block; }
#results a small { display:block; color:var(--muted); font-size:13px; line-height:1.4; }
#results mark, main mark { background:var(--mark); color:var(--mark-fg); border-radius:3px; padding:0 1px; }
main { padding:10px 36px 120px; max-width:980px; }
main h1 { font-size:30px; line-height:1.2; color:var(--head); margin:56px 0 14px; padding-bottom:10px; border-bottom:2px solid var(--accent); }
main h1:first-child { margin-top:24px; }
main h1 .n { color:var(--accent); margin-right:12px; }
main h2 { font-size:22px; color:var(--head); margin:36px 0 8px; }
main h3 { font-size:18px; color:var(--head); margin:24px 0 6px; }
main h1.flash, main h2.flash, main h3.flash { animation: flash 2.2s ease-out; }
@keyframes flash { 0%, 40% { background:rgba(90,169,255,.28); } 100% { background:transparent; } }
main p { margin:0 0 12px; }
main ul, main ol { margin:0 0 14px; padding-left:24px; }
main li { margin-bottom:5px; }
main b, main strong { color:var(--head); }
main code, main kbd { font-family:"SF Mono", Menlo, monospace; font-size:.86em; background:var(--code); border:1px solid var(--line);
  border-radius:5px; padding:0 5px; }
.ui { font-weight:700; color:var(--head); }
.lead { font-size:18.5px; color:var(--muted); }
table { width:100%; border-collapse:collapse; margin:10px 0 18px; font-size:15px; }
th, td { text-align:left; padding:7px 9px; border-bottom:1px solid var(--line); vertical-align:top; }
th { background:var(--code); color:var(--head); }
td.r, th.r { text-align:right; font-variant-numeric:tabular-nums; }
.box { border-radius:10px; padding:12px 16px; margin:12px 0 18px; }
.box.tip { background:var(--tip); border-left:4px solid #2f81f7; }
.box.warn { background:var(--warn); border-left:4px solid #e8a33a; }
.box.danger { background:var(--danger); border-left:4px solid #d9534f; }
.box > :last-child { margin-bottom:0; }
.box .t { font-weight:700; display:block; margin-bottom:4px; }
.formula { background:var(--code); border:1px solid var(--line); border-radius:10px; padding:14px 18px; margin:12px 0 18px;
  text-align:center; font-size:20px; overflow-x:auto; }
.formula .lbl { display:block; font-size:14px; color:var(--muted); margin-top:8px; }
.frac { display:inline-flex; flex-direction:column; vertical-align:middle; text-align:center; margin:0 4px; }
.frac > span:first-child { border-bottom:1.5px solid currentColor; padding:0 6px 2px; }
.frac > span:last-child { padding:2px 6px 0; }
.calc { font-family:"SF Mono", Menlo, monospace; font-size:14px; background:var(--code); border:1px solid var(--line);
  border-radius:8px; padding:10px 14px; margin:8px 0 16px; white-space:pre-wrap; line-height:1.55; overflow-x:auto; }
.calc b { color:var(--accent); }
.fig-wrap { margin:14px 0 22px; }
.fig-wrap.side { display:grid; grid-template-columns:56% 1fr; gap:26px; align-items:start; }
.fig-wrap.side.narrow { grid-template-columns:46% 1fr; }
.fig-wrap.full .legend { columns:2; column-gap:26px; margin-top:16px; }
.fig-wrap.full .legend li { break-inside:avoid; }
figure.shot { margin:0; padding:0 24px; }
figure.shot .frame { position:relative; }
figure.shot img { display:block; width:100%; border-radius:8px; box-shadow:0 0 0 1px var(--line); cursor:zoom-in; }
figcaption { font-size:13px; color:var(--muted); margin-top:6px; text-align:center; }
.mk { position:absolute; transform:translate(-50%, -50%); width:22px; height:22px; border-radius:50%; background:#ffc531;
  color:#111; font-size:12px; font-weight:800; display:grid; place-items:center; box-shadow:0 0 0 1.5px #111, 0 0 0 3px #fff; line-height:1; }
.mk.dd, .legend .num.dd { font-size:10px; }
.mk.l { transform:translate(calc(-100% - 2px), -50%); }
.mk.r { transform:translate(2px, -50%); }
.mk.b { transform:translate(-50%, 2px); }
.fig-wrap.below-marks figure.shot { padding-bottom:26px; }
.legend { list-style:none; padding:0; margin:0; font-size:15px; }
.legend li { display:grid; grid-template-columns:28px 1fr; gap:8px; margin-bottom:8px; }
.legend .num { width:21px; height:21px; border-radius:50%; background:#ffc531; color:#111; font-weight:800; font-size:11.5px;
  display:grid; place-items:center; box-shadow:0 0 0 1.3px #111; margin-top:3px; }
.two { display:grid; grid-template-columns:1fr 1fr; gap:24px; }
svg.diagram { width:100%; height:auto; display:block; margin:10px 0 18px; background:#f4f7fb; border-radius:10px; padding:6px; }
.steps { counter-reset:s; list-style:none; padding-left:0; }
.steps > li { counter-increment:s; position:relative; padding-left:38px; margin-bottom:10px; }
.steps > li::before { content:counter(s); position:absolute; left:0; top:1px; width:26px; height:26px; border-radius:50%;
  background:#2f81f7; color:#fff; font-weight:700; font-size:14px; display:grid; place-items:center; }
#zoom { position:fixed; inset:0; z-index:20; background:rgba(0,0,0,.88); display:none; place-items:center; cursor:zoom-out; padding:20px; }
#zoom.show { display:grid; }
#zoom img { max-width:100%; max-height:100%; border-radius:8px; }
#top { position:fixed; right:22px; bottom:22px; padding:9px 14px; border-radius:10px; border:1px solid var(--line);
  background:var(--panel); color:var(--fg); font:inherit; font-size:14px; display:none; cursor:pointer; }
#top.show { display:block; }
@media (max-width: 900px) {
  html { scroll-padding-top: 118px; }
  header.top { flex-wrap:wrap; gap:8px 10px; padding:8px 12px; }
  header.top .brand .long { display:none; }
  #menu { display:block; white-space:nowrap; margin-left:auto; }
  #q { order:3; flex:1 1 100%; max-width:none; }
  .layout { grid-template-columns: minmax(0, 1fr); }
  main { overflow-wrap:anywhere; }
  main table { display:block; overflow-x:auto; }
  nav.side { display:none; position:fixed; top:104px; left:0; right:0; bottom:0; height:auto; z-index:6; background:var(--panel); }
  nav.side.open { display:block; }
  main { padding:6px 16px 100px; }
  main h1 { font-size:25px; margin-top:40px; }
  .calc { font-size:12.5px; }
  header.top .ver { display:none; }
  .fig-wrap.side, .fig-wrap.side.narrow, .two { grid-template-columns:1fr; }
  .fig-wrap.full .legend { columns:1; }
  figure.shot { padding:0 18px; }
}
"""

PAGE = """<!doctype html>
<html lang="__LANG__"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<title>__TITLE__</title>
<script>try { document.documentElement.dataset.theme = localStorage.getItem("fs-theme") || "dark"; } catch (e) {}</script>
<style>__CSS__</style></head>
<body>
<header class="top">
  <span class="brand">__ICON__ <span>Focus Stack<span class="long"> · __HEADTITLE__</span></span></span>
  <button id="menu" type="button">☰ __TOCLABEL__</button>
  <input id="q" type="search" placeholder="__SEARCH__…" aria-label="__SEARCH__" autocomplete="off" spellcheck="false">
  <span class="ver">__VERSION__</span>
</header>
<div class="layout">
  <nav class="side" aria-label="__TOCLABEL__">
    <div id="results"></div>
    <div id="toc">__TOC__</div>
  </nav>
  <main id="doc">__BODY__</main>
</div>
<div id="zoom"><img alt=""></div>
<button id="top" type="button">↑ __TOP__</button>
<script>
const DATA = __DATA__;
const UIL = DATA.ui, $ = (s) => document.querySelector(s);
const norm = (s) => s.normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toLowerCase();
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const blocks = DATA.blocks.map((b) => ({ ...b, nt: norm(b.t), nx: norm(b.x) }));

// ---- ancora: porta al capitolo e lo fa lampeggiare (link dall'app: guide/it.html#c7-1)
function go(id, flash = true) {
  const el = document.getElementById(id);
  if (!el) return;
  el.scrollIntoView({ block: "start" });
  if (flash) { el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash"); }
  $("nav.side").classList.remove("open");
}
window.addEventListener("hashchange", () => go(location.hash.slice(1)));
if (location.hash) requestAnimationFrame(() => go(location.hash.slice(1)));
// le schermate caricate dopo spostano i titoli più in basso: a pagina completa si torna al capitolo
window.addEventListener("load", () => { if (location.hash) go(location.hash.slice(1), false); });

// ---- ricerca: tutte le parole, senza badare a maiuscole e accenti; i titoli contano di più
function snippet(text, ntext, words) {
  const i = Math.max(0, ntext.indexOf(words[0]));
  let a = Math.max(0, i - 70), b = Math.min(text.length, i + 150);
  let s = (a ? "…" : "") + esc(text.slice(a, b)) + (b < text.length ? "…" : "");
  return mark(s, words);
}
function mark(html, words) {   // evidenzia nel testo già "escapato" (gli accenti restano quelli originali)
  const n = norm(html);
  const hits = [];
  for (const w of words) { let i = 0; while ((i = n.indexOf(w, i)) >= 0) { hits.push([i, i + w.length]); i += w.length; } }
  hits.sort((x, y) => x[0] - y[0]);
  let out = "", pos = 0;
  for (const [a, b] of hits) { if (a < pos) continue; out += html.slice(pos, a) + "<mark>" + html.slice(a, b) + "</mark>"; pos = b; }
  return out + html.slice(pos);
}
function clearMarks() {
  document.querySelectorAll("main mark").forEach((m) => m.replaceWith(document.createTextNode(m.textContent)));
  $("main").normalize();
}
function markDoc(words) {
  clearMarks();
  if (!words.length) return;
  const walker = document.createTreeWalker($("main"), NodeFilter.SHOW_TEXT, {
    acceptNode: (n) => n.parentElement.closest("svg, script, style") ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (const node of nodes) {
    const t = node.nodeValue, n = norm(t);
    if (n.length !== t.length || !words.some((w) => n.includes(w))) continue;
    const span = document.createElement("span");
    span.innerHTML = mark(esc(t), words);
    node.replaceWith(...span.childNodes);
  }
}
function search() {
  const q = norm($("#q").value.trim());
  const words = q.split(/\\s+/).filter((w) => w.length > 1);
  const res = $("#results"), toc = $("#toc");
  if (!words.length) { res.classList.remove("show"); toc.hidden = false; clearMarks(); return; }
  const hits = [];
  for (const b of blocks) {
    if (!words.every((w) => b.nt.includes(w) || b.nx.includes(w))) continue;
    const score = words.reduce((s, w) => s + (b.nt.includes(w) ? 10 : 0) + (b.nx.split(w).length - 1), 0);
    hits.push([score, b]);
  }
  hits.sort((x, y) => y[0] - x[0]);
  const count = hits.length === 0 ? UIL.none : hits.length === 1 ? UIL.one : UIL.results.replace("{n}", hits.length);
  res.innerHTML = `<div class="count">${count}</div>` + hits.slice(0, 40).map(([, b]) =>
    `<a href="#${b.id}"><b>${mark(esc(b.t), words)}</b>${b.c ? `<small>${esc(b.c)}</small>` : ""}<small>${snippet(b.x, b.nx, words)}</small></a>`).join("");
  res.classList.add("show"); toc.hidden = true;
  markDoc(words);
}
let timer = 0;
$("#q").addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(search, 150); });
$("#q").addEventListener("keydown", (e) => {
  if (e.key === "Escape") { $("#q").value = ""; search(); }
  if (e.key === "Enter") { const a = $("#results a"); if (a) { location.hash = ""; location.hash = a.getAttribute("href"); } }
});
document.addEventListener("keydown", (e) => {
  if ((e.key === "/" || (e.key === "f" && (e.metaKey || e.ctrlKey))) && document.activeElement !== $("#q")) {
    e.preventDefault(); $("#q").focus(); $("#q").select();
  }
});
$("#menu").onclick = () => $("nav.side").classList.toggle("open");

// ---- capitolo corrente evidenziato nell'indice
const tocLinks = new Map([...document.querySelectorAll("#toc a")].map((a) => [a.getAttribute("href").slice(1), a]));
const heads = [...document.querySelectorAll("main h1[id], main h2[id]")];
let current = null;
function spy() {
  let id = null;
  for (const h of heads) { if (h.getBoundingClientRect().top < 120) id = h.id; else break; }
  if (id !== current) {
    if (current && tocLinks.get(current)) tocLinks.get(current).classList.remove("on");
    current = id;
    const a = id && tocLinks.get(id);
    if (a) { a.classList.add("on"); a.scrollIntoView({ block: "nearest" }); }
  }
  $("#top").classList.toggle("show", window.scrollY > 800);
}
window.addEventListener("scroll", () => requestAnimationFrame(spy), { passive: true });
spy();
$("#top").onclick = () => window.scrollTo({ top: 0 });

// ---- schermate: un clic le apre grandi
$("main").addEventListener("click", (e) => {
  const img = e.target.closest("figure.shot img");
  if (!img) return;
  $("#zoom img").src = img.src; $("#zoom").classList.add("show");
});
$("#zoom").onclick = () => $("#zoom").classList.remove("show");
</script>
</body></html>
"""


if __name__ == "__main__":
    structures = {}
    for lang in G.LANGS:
        structures[lang] = build_web(lang)
        print(f"web/guide/{lang}.html: {sum(1 for lvl, _ in structures[lang] if lvl == 1)} capitoli, "
              f"{len(structures[lang])} titoli")
    missing = sorted(set(ALIASES) - {hid for _lvl, hid in structures["it"]})
    if missing:
        sys.exit(f"ATTENZIONE: ALIASES punta a titoli che non esistono: {', '.join(missing)}")
    ref = structures["it"]
    bad = [lang for lang, s in structures.items() if s != ref]
    if bad:
        sys.exit(f"ATTENZIONE: struttura dei titoli diversa dall'italiano in {', '.join(bad)}: "
                 "i link «?» dell'app porterebbero al capitolo sbagliato")
