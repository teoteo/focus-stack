"use strict";
// Ispettore del visualizzatore (come quello di Focus Fusion, in sola lettura): istogrammi R, G, B e
// luminosità, pixel bruciati (canali a 255) e neri (canali a 0) secondo una regola, segni rossi/blu
// sull'immagine, valori sotto il puntatore e statistiche dell'immagine intera.
//
// I numeri riguardano l'immagine a 8 bit mostrata (anteprima, piena risoluzione o fotogramma del live
// view): con i RAW è la conversione per lo schermo, non i dati del sensore.
const Inspector = (() => {
  const CH = ["#ff6060", "#48d078", "#609cff", "#d6dae2"];
  const CH_LIGHT = ["#e53935", "#1e9e5a", "#1f6fd1", "#5d6879"];   // tema chiaro
  const CH_NAME = ["R", "G", "B", "L"];
  // regole: bit c della maschera = canale c (0 R, 1 G, 2 B) al limite
  const RULES = {
    all: (m) => m === 7, any: (m) => m !== 0, r: (m) => (m & 1) !== 0, g: (m) => (m & 2) !== 0, b: (m) => (m & 4) !== 0,
  };
  const RULE_ORDER = ["all", "any", "r", "g", "b"];
  const RANGES = { shadows: [0, 16], all: [0, 256], highlights: [240, 256] };
  const luma8 = (r, g, b) => (r * 54 + g * 183 + b * 19 + 128) >> 8;
  const fmtInt = (n) => fmtNum(Math.round(n), 0);

  const defaults = { open: true, marks: false, lo: true, hi: true, rule: "all", ch: [true, true, true, true], log: false, range: "all" };
  let ui = { ...defaults };
  try { ui = { ...defaults, ...JSON.parse(localStorage.getItem("fs-inspector") || "{}") }; } catch { /* opzionale */ }
  const saveUi = () => { try { localStorage.setItem("fs-inspector", JSON.stringify(ui)); } catch { /* opzionale */ } };

  let el = {}, stats = null, classes = null, maskW = 0, maskH = 0, token = 0, source = null, hoverLevel = null;
  let onToggle = () => {};
  const probe = document.createElement("canvas");
  probe.width = probe.height = 1;
  const probeCtx = probe.getContext("2d", { willReadFrequently: true });

  const pct = (n, tot) => {
    if (!tot) return "—";
    if (!n) return "0 %";
    const p = (n / tot) * 100;
    return p < 0.01 ? `< ${fmtNum(0.01, 2)} %` : `${fmtNum(p, p < 1 ? 2 : 1)} %`;
  };

  function channelStats(h) {
    let n = 0, sum = 0;
    for (let v = 0; v < 256; v++) { n += h[v]; sum += v * h[v]; }
    if (!n) return null;
    let min = 0, max = 255;
    while (!h[min]) min++;
    while (!h[max]) max--;
    let acc = 0, median = max;
    const half = Math.ceil(n / 2);
    for (let v = 0; v < 256; v++) { acc += h[v]; if (acc >= half) { median = v; break; } }
    return { min, max, mean: sum / n, median };
  }

  const count = (m, rule) => { let s = 0; for (let k = 0; k < 8; k++) if (RULES[rule](k)) s += m[k]; return s; };

  // ---------------- calcolo (a bande, per non bloccare l'interfaccia) ----------------
  // source: <img> o Image caricata (stessa origine); info.basis = testo su cosa si misura
  async function analyze(img, info = {}) {
    const my = ++token;
    source = img;
    if (!ui.open) { stats = null; return; }
    // fino al nuovo calcolo i segni vecchi non corrispondono più all'immagine (altre dimensioni)
    if (!info.live && el.mask) el.mask.classList.add("hidden");
    const w = img.naturalWidth, h = img.naturalHeight;
    if (!w || !h) return;
    const c = document.createElement("canvas");
    c.width = w; c.height = h;
    const ctx = c.getContext("2d", { willReadFrequently: true });
    try { ctx.drawImage(img, 0, 0); } catch { return; }
    const hist = [0, 1, 2, 3].map(() => new Float64Array(256));
    const lo = new Float64Array(8), hi = new Float64Array(8);
    const cls = new Uint8Array(w * h);   // bit 0-2: canali a 0 · bit 3-5: canali a 255
    const BAND = Math.max(1, Math.floor(2_000_000 / w));
    if (!info.live) setBusy(true);
    for (let y0 = 0; y0 < h; y0 += BAND) {
      const bh = Math.min(BAND, h - y0);
      let data;
      try { data = ctx.getImageData(0, y0, w, bh).data; } catch { setBusy(false); return; }
      const [hr, hg, hb, hl] = hist;
      let o = y0 * w;
      for (let i = 0; i < data.length; i += 4, o++) {
        const r = data[i], g = data[i + 1], b = data[i + 2];
        hr[r]++; hg[g]++; hb[b]++; hl[luma8(r, g, b)]++;
        const ml = (r === 0 ? 1 : 0) | (g === 0 ? 2 : 0) | (b === 0 ? 4 : 0);
        const mh = (r === 255 ? 1 : 0) | (g === 255 ? 2 : 0) | (b === 255 ? 4 : 0);
        lo[ml]++; hi[mh]++;
        cls[o] = ml | (mh << 3);
      }
      if (!info.live && y0 + BAND < h) {
        await new Promise((r) => setTimeout(r, 0));
        if (my !== token) return;   // è arrivata un'altra immagine
      }
    }
    c.width = c.height = 0;   // libera la memoria della copia
    if (my !== token) return;
    stats = { w, h, n: w * h, hist, lo, hi, basis: info.basis || "", note: info.note || "", live: !!info.live };
    classes = cls; maskW = w; maskH = h;
    setBusy(false);
    render();
    drawMask();
  }

  function clear() {
    ++token;
    stats = null; classes = null; source = null;
    if (el.mask) { el.mask.width = el.mask.height = 0; }
    setBusy(false);
    render();
  }

  // ---------------- segni sull'immagine ----------------
  function drawMask() {
    const m = el.mask;
    if (!m) return;
    const show = ui.open && ui.marks && classes && (ui.lo || ui.hi);
    m.classList.toggle("hidden", !show);
    if (!show) { m.width = m.height = 0; return; }
    if (m.width !== maskW || m.height !== maskH) { m.width = maskW; m.height = maskH; }
    const ctx = m.getContext("2d");
    const out = ctx.createImageData(maskW, maskH), d = out.data, rule = RULES[ui.rule];
    for (let i = 0, o = 0; i < classes.length; i++, o += 4) {
      const c = classes[i];
      if (!c) continue;
      if (ui.hi && rule(c >> 3)) { d[o] = 255; d[o + 1] = 32; d[o + 2] = 32; d[o + 3] = 255; }
      else if (ui.lo && rule(c & 7)) { d[o] = 40; d[o + 1] = 120; d[o + 2] = 255; d[o + 3] = 255; }
    }
    ctx.putImageData(out, 0, 0);
  }

  // stessa trasformazione dell'immagine (chiamata dal visualizzatore a ogni zoom/pan)
  function transform(css, pixelated) {
    if (!el.mask) return;
    el.mask.style.transform = css;
    el.mask.classList.toggle("pixelated", pixelated);
  }

  // ---------------- pannello ----------------
  function setBusy(on) { el.busy && el.busy.classList.toggle("hidden", !on); }

  function render() {
    if (!el.panel) return;
    el.panel.classList.toggle("hidden", !ui.open);
    el.toggle.setAttribute("aria-pressed", String(ui.open));
    if (!ui.open) return;
    el.marks.checked = ui.marks;
    el.chipLo.setAttribute("aria-pressed", String(ui.lo));
    el.chipHi.setAttribute("aria-pressed", String(ui.hi));
    el.chipLo.disabled = el.chipHi.disabled = !ui.marks;
    el.basis.textContent = stats ? stats.basis : t("Nessuna immagine");
    el.note.textContent = stats ? stats.note : "";
    el.note.classList.toggle("hidden", !(stats && stats.note));
    // tabella delle regole
    for (const tr of el.rules.querySelectorAll("tr[data-rule]")) {
      const rule = tr.dataset.rule;
      tr.setAttribute("aria-selected", String(rule === ui.rule));
      const [cLo, cHi] = tr.querySelectorAll("td.n");
      if (stats) {
        const nl = count(stats.lo, rule), nh = count(stats.hi, rule);
        cLo.textContent = pct(nl, stats.n); cHi.textContent = pct(nh, stats.n);
        cLo.title = t("{n} pixel su {total}", { n: fmtInt(nl), total: fmtInt(stats.n) });
        cHi.title = t("{n} pixel su {total}", { n: fmtInt(nh), total: fmtInt(stats.n) });
        cLo.classList.toggle("warn-n", nl > 0); cHi.classList.toggle("bad-n", nh > 0);
      } else { cLo.textContent = cHi.textContent = "…"; cLo.title = cHi.title = ""; }
    }
    el.countLine.textContent = stats
      ? t("{lo} neri · {hi} bruciati su {total} pixel", { lo: fmtInt(count(stats.lo, ui.rule)), hi: fmtInt(count(stats.hi, ui.rule)), total: fmtInt(stats.n) })
      : "";
    // istogramma
    el.chans.forEach((b, c) => b.setAttribute("aria-pressed", String(ui.ch[c])));
    el.scale.forEach((b) => b.setAttribute("aria-pressed", String((b.dataset.scale === "log") === ui.log)));
    el.zoom.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.range === ui.range)));
    drawHist();
    // statistiche
    const rows = el.whole.querySelectorAll("tbody tr");
    rows.forEach((tr, c) => {
      const s = stats && channelStats(stats.hist[c]);
      const cells = tr.querySelectorAll("td");
      const vals = s ? [s.min, s.max, fmtNum(s.mean, 1), s.median] : ["…", "…", "…", "…"];
      cells.forEach((td, k) => (td.textContent = vals[k]));
    });
  }

  function drawHist() {
    const cv = el.hist, dpr = window.devicePixelRatio || 1;
    const W = cv.clientWidth || 280, H = cv.clientHeight || 140;
    if (cv.width !== Math.round(W * dpr)) { cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); }
    const ctx = cv.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    const [a, b] = RANGES[ui.range];
    const bw = W / (b - a);
    // griglia leggera ogni 64 livelli (o ogni 4 negli ingrandimenti)
    ctx.strokeStyle = "rgba(140,150,165,.18)"; ctx.lineWidth = 1;
    const stepGrid = b - a > 64 ? 64 : 4;
    for (let v = Math.ceil(a / stepGrid) * stepGrid; v <= b; v += stepGrid) {
      const x = Math.round((v - a) * bw) + 0.5;
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    if (!stats) return;
    const f = ui.log ? (x) => Math.log1p(x) : (x) => x;
    let peak = 0;
    for (let c = 0; c < 4; c++) if (ui.ch[c]) for (let v = a; v < b; v++) peak = Math.max(peak, f(stats.hist[c][v]));
    if (!peak) return;
    // tema scuro: i canali sovrapposti si sommano verso il bianco; tema chiaro: si moltiplicano verso il
    // nero (con "lighter" su fondo chiaro le sovrapposizioni diventerebbero quasi invisibili)
    const light = document.documentElement.dataset.theme === "light";
    const colors = light ? CH_LIGHT : CH;
    ctx.globalCompositeOperation = light ? "multiply" : "lighter";
    for (let c = 0; c < 4; c++) {
      if (!ui.ch[c]) continue;
      const h = stats.hist[c];
      ctx.fillStyle = colors[c] + (c === 3 ? "55" : "88");
      for (let v = a; v < b; v++) {
        const y = (f(h[v]) / peak) * (H - 4);
        if (y > 0) ctx.fillRect((v - a) * bw, H - Math.max(1, y), Math.max(1, bw - (bw > 4 ? 1 : 0)), Math.max(1, y));
      }
    }
    ctx.globalCompositeOperation = "source-over";
    if (hoverLevel != null && hoverLevel >= a && hoverLevel < b) {
      ctx.fillStyle = "rgba(255,255,255,.18)";
      ctx.fillRect((hoverLevel - a) * bw, 0, Math.max(1, bw), H);
    }
  }

  function renderHover() {
    const lv = hoverLevel;
    el.level.textContent = t("Livello {v}", { v: lv == null ? "—" : lv });
    el.hoverCells.forEach((span, c) => {
      span.textContent = lv == null || !stats ? `${CH_NAME[c]} —`
        : `${CH_NAME[c]} ${fmtInt(stats.hist[c][lv])} (${pct(stats.hist[c][lv], stats.n)})`;
    });
  }

  // valori del pixel sotto il puntatore (x, y nei pixel dell'immagine mostrata)
  function pointer(x, y) {
    if (!ui.open || !el.px) return;
    if (x == null || !source || !source.naturalWidth || x < 0 || y < 0 || x >= source.naturalWidth || y >= source.naturalHeight) {
      el.pxPlace.textContent = t("porta il puntatore sull'immagine");
      el.px.forEach((td) => (td.textContent = "—"));
      return;
    }
    try {
      probeCtx.clearRect(0, 0, 1, 1);
      probeCtx.drawImage(source, x, y, 1, 1, 0, 0, 1, 1);
      const [r, g, b] = probeCtx.getImageData(0, 0, 1, 1).data;
      el.pxPlace.textContent = `x ${x} · y ${y}`;
      [r, g, b, luma8(r, g, b)].forEach((v, c) => (el.px[c].textContent = v));
    } catch { /* immagine non leggibile */ }
  }

  function setOpen(on) {
    ui.open = on; saveUi();
    render();
    if (on && source) analyze(source, lastInfo);
    else drawMask();
    onToggle(on);
  }
  let lastInfo = {};

  function bind(opts) {
    const q = (id) => document.getElementById(id);
    onToggle = opts.onToggle || onToggle;
    el = {
      panel: q("insp"), toggle: q("insp-btn"), mask: q("clipmask"), busy: q("insp-busy"), basis: q("insp-basis"), note: q("insp-note"),
      marks: q("insp-marks"), chipLo: q("insp-lo"), chipHi: q("insp-hi"), rules: q("insp-rules"), countLine: q("insp-count"),
      hist: q("insp-hist"), level: q("insp-level"), chans: [...document.querySelectorAll("[data-ch]")],
      scale: [...document.querySelectorAll("[data-scale]")], zoom: [...document.querySelectorAll("[data-range]")],
      hoverCells: [...document.querySelectorAll("#insp-hover span")], whole: q("insp-whole"),
      px: [...document.querySelectorAll("#insp-px td")], pxPlace: q("insp-px-place"),
    };
    el.toggle.onclick = () => setOpen(!ui.open);
    el.marks.onchange = () => { ui.marks = el.marks.checked; saveUi(); render(); drawMask(); };
    el.chipLo.onclick = () => { ui.lo = !ui.lo; saveUi(); render(); drawMask(); };
    el.chipHi.onclick = () => { ui.hi = !ui.hi; saveUi(); render(); drawMask(); };
    for (const tr of el.rules.querySelectorAll("tr[data-rule]")) {
      tr.onclick = () => { ui.rule = tr.dataset.rule; saveUi(); render(); drawMask(); };
    }
    el.chans.forEach((b) => (b.onclick = () => { const c = Number(b.dataset.ch); ui.ch[c] = !ui.ch[c]; saveUi(); render(); }));
    el.scale.forEach((b) => (b.onclick = () => { ui.log = b.dataset.scale === "log"; saveUi(); render(); }));
    el.zoom.forEach((b) => (b.onclick = () => { ui.range = b.dataset.range; saveUi(); render(); }));
    el.hist.addEventListener("pointermove", (e) => {
      const r = el.hist.getBoundingClientRect(), [a, b] = RANGES[ui.range];
      hoverLevel = Math.min(b - 1, Math.max(a, Math.floor(a + ((e.clientX - r.left) / r.width) * (b - a))));
      drawHist(); renderHover();
    });
    el.hist.addEventListener("pointerleave", () => { hoverLevel = null; drawHist(); renderHover(); });
    new ResizeObserver(() => ui.open && drawHist()).observe(el.hist);
    render(); renderHover(); pointer(null);
  }

  return {
    bind, clear, transform, pointer,
    analyze: (img, info) => { lastInfo = info || {}; return analyze(img, lastInfo); },
    toggle: () => setOpen(!ui.open),
    get open() { return ui.open; },
  };
})();
