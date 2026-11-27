"use strict";
// Ispettore del visualizzatore (come quello di Focus Fusion, in sola lettura): istogrammi R, G, B e
// luminosità, pixel bruciati (canali a 255) e neri (canali a 0) secondo una regola, segni rossi/blu
// sull'immagine, valori sotto il puntatore e statistiche dell'immagine intera.
// Aiuti presi dai monitor da ripresa: zone a fuoco colorate (focus peaking) con la nitidezza e il suo massimo,
// zebra e falsi colori per l'esposizione, forma d'onda; immagine capovolta o un solo canale (blocco Vista).
// Questi si calcolano su una copia ridotta dell'immagine (lato lungo WORK_MAX pixel: il live view resta intero)
// e si disegnano su una tela a quella risoluzione. I blocchi del pannello si possono nascondere e riordinare
// (pulsante ⚙): un blocco nascosto non ha effetti sull'immagine.
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

  const defaults = { open: true, marks: false, lo: true, hi: true, rule: "all", ch: [true, true, true, true], log: false, range: "all",
    expo: "marks", zHi: 95, zMid: false, zMidV: 50, zMidT: 5,
    focus: false, fSens: 8, fColor: "red", fBg: "color", fArea: false,
    flipH: false, flipV: false, chan: "all", wf: "luma", blocks: null };
  // blocchi del pannello nell'ordine predefinito (id = data-block dei <details>)
  const BLOCKS = ["view", "focus", "expo", "hist", "wave", "values"];

  // ---------------- fuoco, zebra e falsi colori: costanti ----------------
  const WORK_MAX = 2048;
  const PEAK_COLORS = { red: [255, 32, 32], yellow: [255, 230, 0], green: [40, 255, 90], blue: [50, 130, 255], white: [255, 255, 255] };
  // soglia del contrasto locale (gradiente di Sobel / luminosità media) per la sensibilità 1…15:
  // 1 = solo i bordi più netti, 15 = anche i dettagli deboli (e, con poca luce, il rumore). Tarata su pile vere
  // (calluna al microscopio): sfocato e grana stanno sotto 0,1-0,2, i bordi a fuoco sopra 0,4.
  const peakThreshold = (s) => 1.2 * Math.pow(0.12 / 1.2, (Math.min(15, Math.max(1, s)) - 1) / 14);
  // falsi colori: fasce della luminosità (% di 255, immagine a 8 bit mostrata); null = grigio
  const FALSE_COLORS = [
    [0, 2, [125, 60, 255], "Nero"], [2, 10, [47, 111, 224], "Ombre profonde"], [10, 45, null, ""],
    [45, 55, [47, 191, 91], "Toni medi"], [55, 85, null, ""], [85, 95, [242, 208, 59], "Luci"],
    [95, 99, [255, 140, 26], "Luci quasi bruciate"], [99, 100.01, [255, 31, 79], "Bruciato"],
  ];
  let ui = { ...defaults };
  try { ui = { ...defaults, ...JSON.parse(localStorage.getItem("fs-inspector") || "{}") }; } catch { /* opzionale */ }
  // elenco salvato + blocchi aggiunti dopo (in coda, visibili); quelli che non esistono più si scartano
  const fixBlocks = (list) => {
    const out = (Array.isArray(list) ? list : []).filter((b) => b && BLOCKS.includes(b.id) && typeof b.on === "boolean");
    for (const id of BLOCKS) if (!out.some((b) => b.id === id)) out.push({ id, on: true });
    return out.filter((b, i) => out.findIndex((c) => c.id === b.id) === i);
  };
  ui.blocks = fixBlocks(ui.blocks);
  const blockOn = (id) => ui.blocks.some((b) => b.id === id && b.on);
  // effetti sull'immagine che restano anche a Ispettore chiuso (lo dice l'etichetta sull'immagine)
  const viewFlip = () => ({ h: blockOn("view") && ui.flipH, v: blockOn("view") && ui.flipV });
  const viewChan = () => (blockOn("view") ? ui.chan : "all");
  const saveUi = () => { try { localStorage.setItem("fs-inspector", JSON.stringify(ui)); } catch { /* opzionale */ } };

  let el = {}, stats = null, classes = null, maskW = 0, maskH = 0, token = 0, source = null, hoverLevel = null;
  let work = null;            // copia ridotta: {w, h, luma, r, g, b, maxc, g2 (gradiente²), gchan, mean, srcW}
  let area = null;            // area dell'autofocus [x0, y0, x1, y1] in frazioni (dal visualizzatore), o null
  let sharp = null;           // {v, where} nitidezza dell'ultima immagine
  let peak = { v: 0, key: "", reset: false };   // massimo visto (si azzera con un'immagine non confrontabile)
  let lastCss = "", thick = false, thickTimer = 0;
  const workCanvas = document.createElement("canvas");
  let onToggle = () => {}, onView = () => {};
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
    if (!info.live && el.mask) { el.mask.classList.add("hidden"); if (el.view) el.view.classList.add("hidden"); }
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
    work = computeWork(img);
    measureSharp(!!info.prelim);
    setBusy(false);
    render();
    drawMask();
    drawView();
  }

  // ---------------- copia ridotta: luminosità, canale più alto, gradiente ----------------
  function computeWork(img) {
    const W0 = img.naturalWidth, H0 = img.naturalHeight, k = Math.min(1, WORK_MAX / Math.max(W0, H0));
    const w = Math.max(3, Math.round(W0 * k)), h = Math.max(3, Math.round(H0 * k));
    const c = workCanvas;
    c.width = w; c.height = h;
    const ctx = c.getContext("2d", { willReadFrequently: true });
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = "high";
    let data;
    try { ctx.drawImage(img, 0, 0, w, h); data = ctx.getImageData(0, 0, w, h).data; } catch { return null; }
    const n = w * h, luma = new Uint8Array(n), maxc = new Uint8Array(n);
    const R = new Uint8Array(n), G = new Uint8Array(n), Bc = new Uint8Array(n);
    for (let i = 0, o = 0; o < n; i += 4, o++) {
      const r = data[i], g = data[i + 1], b = data[i + 2];
      R[o] = r; G[o] = g; Bc[o] = b;
      luma[o] = luma8(r, g, b); maxc[o] = r > g ? (r > b ? r : b) : (g > b ? g : b);
    }
    c.width = c.height = 0;
    const wk = { w, h, luma, r: R, g: G, b: Bc, maxc, g2: new Float32Array(n), gchan: "", mean: 0, srcW: W0 };
    gradient(wk, viewChan());
    return wk;
  }

  // Sobel come in fs-rawstat (Tenengrad dell'autofocus): gx² + gy² per pixel, bordi a 0. Sulla luminosità oppure,
  // con un solo canale in vista, su quel canale: zone a fuoco e nitidezza seguono ciò che si vede
  // (confrontando R e B si vede l'aberrazione cromatica assiale)
  function gradient(wk, chan) {
    const src = chan === "r" ? wk.r : chan === "g" ? wk.g : chan === "b" ? wk.b : wk.luma, { w, h, g2 } = wk;
    let sum = 0;
    for (let i = 0; i < src.length; i++) sum += src[i];
    for (let y = 1; y < h - 1; y++) {
      const a = (y - 1) * w, m = y * w, z = (y + 1) * w;
      for (let x = 1; x < w - 1; x++) {
        const gx = (src[a + x + 1] + 2 * src[m + x + 1] + src[z + x + 1]) - (src[a + x - 1] + 2 * src[m + x - 1] + src[z + x - 1]);
        const gy = (src[z + x - 1] + 2 * src[z + x] + src[z + x + 1]) - (src[a + x - 1] + 2 * src[a + x] + src[a + x + 1]);
        g2[m + x] = gx * gx + gy * gy;
      }
    }
    wk.src = src; wk.gchan = chan; wk.mean = sum / src.length;
  }

  // area in pixel della copia ridotta (almeno 3×3), o tutta l'immagine
  function areaPx() {
    const W = work.w, H = work.h;
    if (!(ui.fArea && area)) return { x0: 0, y0: 0, x1: W, y1: H, inArea: false };
    let x0 = Math.max(0, Math.floor(area[0] * W)), y0 = Math.max(0, Math.floor(area[1] * H));
    let x1 = Math.min(W, Math.ceil(area[2] * W)), y1 = Math.min(H, Math.ceil(area[3] * H));
    if (x1 - x0 < 3) { x0 = Math.max(0, Math.min(W - 3, x0)); x1 = x0 + 3; }
    if (y1 - y0 < 3) { y0 = Math.max(0, Math.min(H - 3, y0)); y1 = y0 + 3; }
    return { x0, y0, x1, y1, inArea: true };
  }

  // nitidezza: Tenengrad normalizzato (Σ gradiente² / pixel / media²), la stessa misura dell'autofocus
  // prelim: anteprima ridotta in attesa della piena risoluzione: il valore si mostra ma non tocca il massimo
  function measureSharp(prelim = sharp ? sharp.prelim : false) {
    if (!work) { sharp = null; return; }
    const { x0, y0, x1, y1, inArea } = areaPx(), W = work.w;
    let sum = 0, acc = 0, n = 0;
    for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) sum += work.src[y * W + x];
    const mean = sum / ((x1 - x0) * (y1 - y0));
    for (let y = Math.max(1, y0 + 1); y < Math.min(work.h - 1, y1 - 1); y++) {
      for (let x = Math.max(1, x0 + 1); x < Math.min(W - 1, x1 - 1); x++) { acc += work.g2[y * W + x]; n++; }
    }
    const v = n && mean > 1e-9 ? acc / n / (mean * mean) : 0;
    sharp = { v, where: inArea ? "area" : "all", prelim, chan: work.gchan };
    if (prelim) return;
    // il massimo vale finché le immagini sono confrontabili: stessa risoluzione, stessa area, live o scatti
    const key = `${work.w}x${work.h}|${inArea ? area.map((f) => f.toFixed(4)).join(",") : "all"}|${stats && stats.live ? "live" : "shot"}|${work.gchan}`;
    if (key !== peak.key) peak = { v, key, reset: peak.key !== "" };
    else if (v > peak.v) peak.v = v;
  }

  function clear() {
    ++token;
    stats = null; classes = null; source = null; work = null; sharp = null;
    if (el.mask) { el.mask.width = el.mask.height = 0; }
    setBusy(false);
    render();
    drawView();
  }

  // ---------------- segni sull'immagine ----------------
  function drawMask() {
    const m = el.mask;
    if (!m) return;
    const show = ui.open && ui.marks && blockOn("expo") && ui.expo === "marks" && classes && (ui.lo || ui.hi);
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
    lastCss = css;
    el.mask.style.transform = css;
    el.mask.classList.toggle("pixelated", pixelated);
    placeView();
    // immagine rimpicciolita sullo schermo: i segni del fuoco larghi 1 pixel sparirebbero, si ingrossano
    const now = screenScale() < 1.3;
    if (now !== thick) { thick = now; clearTimeout(thickTimer); thickTimer = setTimeout(() => ui.focus && drawView(), 120); }
  }
  // pixel dello schermo (CSS) per pixel della copia ridotta
  function screenScale() {
    const m = /scale\(([-\d.e]+)\)/.exec(lastCss);
    return m && work ? Number(m[1]) * (work.srcW / work.w) : 1;
  }
  // la tela degli aiuti è alla risoluzione della copia ridotta: stessa trasformazione più il fattore di riduzione
  function placeView() {
    if (!el.view || !work) return;
    el.view.style.transform = `${lastCss} scale(${work.srcW / work.w})`;
  }

  // ---------------- fuoco, zebra e falsi colori sull'immagine ----------------
  const expoOn = () => ui.marks && blockOn("expo");
  const focusOn = () => ui.focus && blockOn("focus");
  const overlaysOn = () => ui.open && !!source && ((expoOn() && ui.expo !== "marks") || focusOn());

  // filtro CSS dell'immagine: un solo canale in grigio (filtri SVG #insp-ch-r/g/b nella pagina) e, sotto le zone
  // a fuoco, immagine grigia, scura o nera. Nessun calcolo sui pixel: lo fa il browser
  const BG_FILTER = { mono: "grayscale(1)", dim: "grayscale(1) brightness(.42)", black: "brightness(0)" };
  function applyImgFilter(showOverlays) {
    if (!el.img) return;
    const parts = [], ch = viewChan();
    if (ch !== "all") parts.push(`url(#insp-ch-${ch})`);
    const bg = showOverlays && focusOn() && !(expoOn() && ui.expo === "false") ? ui.fBg : "color";
    if (BG_FILTER[bg]) parts.push(BG_FILTER[bg]);
    el.img.style.filter = parts.join(" ");
    renderBadge();
  }
  // etichetta sull'immagine quando la vista è capovolta o su un solo canale (anche a Ispettore chiuso); clic = normale
  function renderBadge() {
    if (!el.badge) return;
    const f = viewFlip(), ch = viewChan(), bits = [];
    if (f.h && f.v) bits.push(t("ruotata di 180°"));
    else if (f.h) bits.push(t("capovolta in orizzontale"));
    else if (f.v) bits.push(t("capovolta in verticale"));
    if (ch !== "all") bits.push(t("solo canale {c}", { c: ch.toUpperCase() }));
    el.badge.textContent = bits.join(" · ");
    el.badge.classList.toggle("hidden", !bits.length);
  }
  function drawView() {
    const v = el.view;
    if (!v) return;
    const show = overlaysOn() && work;
    v.classList.toggle("hidden", !show);
    applyImgFilter(show);   // con i falsi colori l'immagine è coperta: niente filtro di sfondo
    if (!show) { v.width = v.height = 0; return; }
    if (work.gchan !== viewChan()) { gradient(work, viewChan()); measureSharp(); }
    const { w, h, luma, maxc, g2 } = work;
    if (v.width !== w || v.height !== h) { v.width = w; v.height = h; }
    placeView();
    const ctx = v.getContext("2d"), out = ctx.createImageData(w, h), d = out.data;
    const mode = expoOn() ? ui.expo : "";
    if (mode === "false") {
      const lut = new Uint8Array(256 * 3);
      for (let l = 0; l < 256; l++) {
        const pc = (l / 255) * 100, band = FALSE_COLORS.find(([a, b]) => pc >= a && pc < b);
        const col = band && band[2] ? band[2] : [l * 0.8, l * 0.8, l * 0.8];
        lut[l * 3] = col[0]; lut[l * 3 + 1] = col[1]; lut[l * 3 + 2] = col[2];
      }
      for (let i = 0, o = 0; i < luma.length; i++, o += 4) {
        const l = luma[i] * 3;
        d[o] = lut[l]; d[o + 1] = lut[l + 1]; d[o + 2] = lut[l + 2]; d[o + 3] = 255;
      }
    } else if (mode === "zebra") {
      const hi = Math.round((ui.zHi / 100) * 255);
      const mid = ui.zMid, mc = (ui.zMidV / 100) * 255, mt = (ui.zMidT / 100) * 255;
      for (let y = 0, i = 0; y < h; y++) {
        for (let x = 0; x < w; x++, i++) {
          const o = i * 4;
          // toni medi (scelti apposta, hanno la precedenza): righe azzurre a 135°; luci: bianche e nere a 45°
          if (mid && Math.abs(luma[i] - mc) <= mt) {
            if (((x - y) >> 2) & 1) { d[o] = 0; d[o + 1] = 210; d[o + 2] = 255; d[o + 3] = 170; }
          } else if (maxc[i] >= hi) {
            const on = ((x + y) >> 2) & 1;
            d[o] = d[o + 1] = d[o + 2] = on ? 0 : 255; d[o + 3] = on ? 200 : 120;
          }
        }
      }
    }
    if (focusOn()) {
      const { x0, y0, x1, y1, inArea } = areaPx();
      const thr = peakThreshold(ui.fSens), den = Math.max(work.mean, 48), lim = thr * thr * den * den;
      const [r, g, b] = PEAK_COLORS[ui.fColor] || PEAK_COLORS.red;
      thick = screenScale() < 1.3;
      const paint = (o) => { d[o] = r; d[o + 1] = g; d[o + 2] = b; d[o + 3] = 255; };
      for (let y = y0; y < y1; y++) {
        for (let x = x0, i = y * w + x0; x < x1; x++, i++) {
          if (g2[i] <= lim) continue;
          paint(i * 4);
          if (thick && x + 1 < w && y + 1 < h) { paint((i + 1) * 4); paint((i + w) * 4); paint((i + w + 1) * 4); }
        }
      }
      if (inArea) {   // contorno dell'area: le zone a fuoco si cercano solo lì dentro
        const dash = (k) => ((k >> 2) & 1) ? [0, 0, 0] : [255, 255, 255];
        const put = (x, y, k) => { const o = (y * w + x) * 4, c = dash(k); d[o] = c[0]; d[o + 1] = c[1]; d[o + 2] = c[2]; d[o + 3] = 230; };
        for (let x = x0; x < x1; x++) { put(x, y0, x); put(x, y1 - 1, x); }
        for (let y = y0; y < y1; y++) { put(x0, y, y); put(x1 - 1, y, y); }
      }
    }
    ctx.putImageData(out, 0, 0);
  }

  // area dell'autofocus dal visualizzatore (cambia di rado: si ridisegna solo se diversa)
  function setArea(rect) {
    const next = rect && rect.length === 4 ? rect.map(Number) : null;
    if (JSON.stringify(next) === JSON.stringify(area)) return;
    area = next;
    if (!work) { render(); return; }
    measureSharp(); render(); drawView();
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
    renderBlocks();
    renderFocus();
    el.flipH.setAttribute("aria-pressed", String(ui.flipH)); el.flipV.setAttribute("aria-pressed", String(ui.flipV));
    el.chan.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.chan === ui.chan)));
    el.wf.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.wf === ui.wf)));
    drawWave();
    el.expo.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.expo === ui.expo)));
    el.expo.forEach((b) => (b.disabled = !ui.marks));
    el.marksChips.classList.toggle("hidden", ui.expo !== "marks");
    el.zebra.classList.toggle("hidden", ui.expo !== "zebra");
    el.falseBox.classList.toggle("hidden", ui.expo !== "false");
    el.zHi.value = ui.zHi; el.zHiV.textContent = `${ui.zHi} %`;
    el.zMid.checked = ui.zMid; el.zMidV.value = ui.zMidV; el.zMidT.value = ui.zMidT;
    el.zMidV.disabled = el.zMidT.disabled = el.zMed.disabled = !ui.zMid;
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

  function renderFocus() {
    el.peak.checked = ui.focus;
    el.sens.value = ui.fSens; el.sensV.textContent = ui.fSens;
    el.pcolor.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.pcolor === ui.fColor)));
    el.pbg.forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.pbg === ui.fBg)));
    el.parea.checked = ui.fArea;
    for (const c of [el.sens, ...el.pcolor, ...el.pbg]) c.disabled = !ui.focus;
    // tre cifre significative (i valori dipendono dal soggetto: 0,0123 come 12,3)
    const s = sharp, fmtS = (v) => fmtNum(v, v > 0 ? Math.min(6, Math.max(0, 2 - Math.floor(Math.log10(v)))) : 0);
    el.sharp.textContent = s ? fmtS(s.v) : "—";
    el.sharpReset.disabled = !s;
    const frac = s && !s.prelim && peak.v > 0 ? Math.min(1, s.v / peak.v) : 0;
    el.sharpBar.style.width = `${(frac * 100).toFixed(1)}%`;
    el.sharpBar.classList.toggle("top", frac >= 0.98);
    let txt = "";
    if (s) {
      let where = s.where === "area" ? t("nell'area dell'autofocus") : ui.fArea ? t("su tutta l'immagine (nessuna area dell'autofocus)") : t("su tutta l'immagine");
      if (s.chan && s.chan !== "all") where += " · " + t("canale {c}", { c: s.chan.toUpperCase() });
      if (s.prelim) txt = `${where} · ${t("anteprima: il confronto col massimo arriva con la piena risoluzione")}`;
      else {
        txt = peak.v > 0 ? t("{p} % del massimo ({m}) · {where}", { p: fmtNum(frac * 100, 0), m: fmtS(peak.v), where }) : where;
        if (peak.reset && s.v === peak.v) txt += " · " + t("massimo ripartito: immagine o area diversa");
      }
    }
    el.sharpTxt.textContent = txt;
  }

  // ---------------- forma d'onda ----------------
  // In orizzontale la posizione nell'immagine (come si vede: segue il capovolgimento), in verticale il livello:
  // ogni punto è più chiaro quanti più pixel di quella colonna hanno quel livello. Fondo scuro anche col tema chiaro,
  // come i monitor. Luminosità, R G B sovrapposti o affiancati (parade).
  function drawWave() {
    const cv = el.wave;
    if (!cv || !ui.open || !blockOn("wave") || !el.waveBox.open) return;
    const dpr = window.devicePixelRatio || 1, Wc = Math.round((cv.clientWidth || 280) * dpr), Hc = Math.round((cv.clientHeight || 150) * dpr);
    if (cv.width !== Wc || cv.height !== Hc) { cv.width = Wc; cv.height = Hc; }
    const ctx = cv.getContext("2d");
    ctx.fillStyle = "#0c0f14"; ctx.fillRect(0, 0, Wc, Hc);
    const PAD = Math.round(4 * dpr), H = Hc - 2 * PAD;
    if (work) {
      const { w, h } = work, flip = viewFlip().h, mode = ui.wf;
      const chans = mode === "luma" ? [work.luma] : [work.r, work.g, work.b];
      const lanes = mode === "parade" ? 3 : 1, laneW = Math.floor(Wc / lanes);
      // conteggi per colonna e livello (256), poi ogni riga del grafico è la media dei livelli che copre: con più o
      // meno righe che livelli non compaiono strisce orizzontali
      const cnt = chans.map(() => new Uint32Array(Wc * 256));
      const colOf = new Int32Array(w);
      for (let x = 0; x < w; x++) colOf[x] = Math.min(laneW - 1, Math.floor(((flip ? w - 1 - x : x) * laneW) / w));
      for (let c = 0; c < chans.length; c++) {
        const src = chans[c], out = cnt[c], off = mode === "parade" ? c * laneW : 0;
        for (let y = 0, i = 0; y < h; y++) for (let x = 0; x < w; x++, i++) out[src[i] * Wc + colOf[x] + off]++;
      }
      // scala: un livello «pieno» quando ci cade la quota della colonna che avrebbe se fosse sparsa su un ottavo dei livelli
      const perCol = (w * h) / laneW, full = Math.max(1, perCol / 32);
      const img = ctx.createImageData(Wc, H), d = img.data;
      const tint = mode === "luma" ? [[200, 235, 210]] : [[255, 70, 70], [70, 230, 110], [80, 140, 255]];
      const gain = mode === "luma" ? 1 : 0.9;
      for (let r = 0; r < H; r++) {
        const l0 = Math.floor(((H - 1 - r) * 256) / H), l1 = Math.max(l0 + 1, Math.floor(((H - r) * 256) / H)), nl = l1 - l0;
        for (let c = 0; c < chans.length; c++) {
          const out = cnt[c], [tr, tg, tb] = tint[c];
          for (let x = 0; x < Wc; x++) {
            let n = 0;
            for (let l = l0; l < l1; l++) n += out[l * Wc + x];
            if (!n) continue;
            const k = Math.min(1, Math.sqrt(n / nl / full)) * gain, o = (r * Wc + x) * 4;
            d[o] = Math.min(255, d[o] + tr * k); d[o + 1] = Math.min(255, d[o + 1] + tg * k); d[o + 2] = Math.min(255, d[o + 2] + tb * k); d[o + 3] = 255;
          }
        }
      }
      ctx.putImageData(img, 0, PAD);
      if (lanes === 3) {
        ctx.strokeStyle = "rgba(255,255,255,.18)"; ctx.lineWidth = 1;
        for (let k = 1; k < 3; k++) { const x = k * laneW + 0.5; ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, Hc); ctx.stroke(); }
      }
    }
    // righe ogni 25 %
    ctx.strokeStyle = "rgba(200,210,225,.22)"; ctx.lineWidth = 1; ctx.fillStyle = "rgba(200,210,225,.55)";
    ctx.font = `${Math.round(9 * dpr)}px system-ui, sans-serif`; ctx.textBaseline = "middle";
    for (const q of [0, 25, 50, 75, 100]) {
      const y = Math.round(PAD + H - 1 - (q / 100) * (H - 1)) + 0.5;
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(Wc, y); ctx.stroke();
      ctx.fillText(String(q), 2 * dpr, Math.min(Hc - 5 * dpr, Math.max(5 * dpr, y - (q === 0 ? 5 : -5) * dpr)));
    }
  }

  // ---------------- blocchi: quali mostrare e in che ordine ----------------
  // Si chiama a ogni aggiornamento (col live view cinque volte al secondo): i blocchi si spostano solo se l'ordine
  // è cambiato. Spostarli sempre faceva perdere i clic, quando lo spostamento cadeva fra pressione e rilascio.
  function renderBlocks() {
    const want = ui.blocks.map((b) => el.blocks[b.id]).filter(Boolean);
    const now = [...el.panelBody.children].filter((c) => c.dataset.block);
    if (want.some((det, i) => now[i] !== det)) for (const det of want) el.panelBody.appendChild(det);
    for (const b of ui.blocks) el.blocks[b.id]?.classList.toggle("hidden", !b.on);
  }
  // elenco nel pannello ⚙: si ricostruisce solo quando si apre o cambia
  function renderBlockList() {
    if (el.cfgPanel.classList.contains("hidden")) return;
    el.cfgList.innerHTML = "";
    ui.blocks.forEach((b, i) => {
      const li = document.createElement("li");
      const name = el.blockNames[b.id] || b.id;
      li.innerHTML = `<label class="check"><input type="checkbox"${b.on ? " checked" : ""}> <span></span></label>` +
        `<button class="chip-btn mv" data-mv="-1" title="${t("Sposta su")}" aria-label="${t("Sposta su")}"${i === 0 ? " disabled" : ""}>↑</button>` +
        `<button class="chip-btn mv" data-mv="1" title="${t("Sposta giù")}" aria-label="${t("Sposta giù")}"${i === ui.blocks.length - 1 ? " disabled" : ""}>↓</button>`;
      li.querySelector("span").textContent = name;
      li.querySelector("input").onchange = (e) => { b.on = e.target.checked; blocksChanged(); };
      li.querySelectorAll("[data-mv]").forEach((btn) => (btn.onclick = () => {
        const j = i + Number(btn.dataset.mv);
        if (j < 0 || j >= ui.blocks.length) return;
        [ui.blocks[i], ui.blocks[j]] = [ui.blocks[j], ui.blocks[i]];
        blocksChanged();
        el.cfgList.querySelectorAll("li")[j]?.querySelector(`[data-mv="${btn.dataset.mv}"]`)?.focus();
      }));
      el.cfgList.appendChild(li);
    });
  }
  function blocksChanged() {
    saveUi(); render(); renderBlockList(); drawMask(); drawView(); onView();
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
    else { drawMask(); drawView(); }
    onToggle(on);
  }
  let lastInfo = {};

  function bind(opts) {
    const q = (id) => document.getElementById(id);
    onToggle = opts.onToggle || onToggle;
    onView = opts.onView || onView;
    el = {
      panel: q("insp"), toggle: q("insp-btn"), mask: q("clipmask"), busy: q("insp-busy"), basis: q("insp-basis"), note: q("insp-note"),
      marks: q("insp-marks"), chipLo: q("insp-lo"), chipHi: q("insp-hi"), rules: q("insp-rules"), countLine: q("insp-count"),
      hist: q("insp-hist"), level: q("insp-level"), chans: [...document.querySelectorAll("[data-ch]")],
      scale: [...document.querySelectorAll("[data-scale]")], zoom: [...document.querySelectorAll("[data-range]")],
      hoverCells: [...document.querySelectorAll("#insp-hover span")], whole: q("insp-whole"),
      px: [...document.querySelectorAll("#insp-px td")], pxPlace: q("insp-px-place"),
      view: q("inspview"), img: q("img"),
      peak: q("insp-peak"), sens: q("insp-sens"), sensV: q("insp-sens-v"), parea: q("insp-parea"),
      pcolor: [...document.querySelectorAll("[data-pcolor]")], pbg: [...document.querySelectorAll("[data-pbg]")],
      sharp: q("insp-sharp"), sharpBar: q("insp-sharp-bar"), sharpTxt: q("insp-sharp-txt"), sharpReset: q("insp-sharp-reset"),
      expo: [...document.querySelectorAll("[data-expo]")], marksChips: q("insp-marks-chips"), zebra: q("insp-zebra"),
      falseBox: q("insp-false"), zHi: q("insp-zhi"), zHiV: q("insp-zhi-v"), zMid: q("insp-zmid"), zMidV: q("insp-zmidv"),
      zMidT: q("insp-zmidt"), zMed: q("insp-zmed"), fcLegend: q("insp-fc"),
      flipH: q("insp-fliph"), flipV: q("insp-flipv"), chan: [...document.querySelectorAll("[data-chan]")], badge: q("view-badge"),
      wave: q("insp-wave"), waveBox: document.querySelector('[data-block="wave"]'), wf: [...document.querySelectorAll("[data-wf]")],
      panelBody: q("insp-body"), cfgBtn: q("insp-cfg"), cfgPanel: q("insp-cfg-panel"), cfgList: q("insp-cfg-list"), cfgReset: q("insp-cfg-reset"),
      blocks: {}, blockNames: {},
    };
    for (const det of document.querySelectorAll("#insp [data-block]")) {
      el.blocks[det.dataset.block] = det;
      el.blockNames[det.dataset.block] = det.querySelector("summary").textContent.trim();
    }
    const viewChanged = () => { saveUi(); render(); drawView(); applyImgFilter(overlaysOn() && !!work); onView(); };
    el.flipH.onclick = () => { ui.flipH = !ui.flipH; viewChanged(); };
    el.flipV.onclick = () => { ui.flipV = !ui.flipV; viewChanged(); };
    el.chan.forEach((b) => (b.onclick = () => { ui.chan = b.dataset.chan; if (work) { gradient(work, viewChan()); measureSharp(); } viewChanged(); }));
    // l'immagine sotto cattura il puntatore per il trascinamento: l'etichetta non deve passargli la pressione
    el.badge.addEventListener("pointerdown", (e) => e.stopPropagation());
    el.badge.onclick = () => { ui.flipH = ui.flipV = false; ui.chan = "all"; if (work) { gradient(work, "all"); measureSharp(); } viewChanged(); };
    el.wf.forEach((b) => (b.onclick = () => { ui.wf = b.dataset.wf; saveUi(); render(); }));
    el.waveBox.addEventListener("toggle", () => drawWave());
    new ResizeObserver(() => ui.open && drawWave()).observe(el.wave);
    el.cfgBtn.onclick = () => {
      const open = el.cfgPanel.classList.toggle("hidden") === false;
      el.cfgBtn.setAttribute("aria-expanded", String(open));
      renderBlockList();
    };
    el.cfgReset.onclick = () => { ui.blocks = fixBlocks(null); blocksChanged(); };
    const redraw = () => { saveUi(); render(); drawMask(); drawView(); };
    el.peak.onchange = () => { ui.focus = el.peak.checked; redraw(); };
    el.sens.oninput = () => { ui.fSens = Number(el.sens.value); redraw(); };
    el.parea.onchange = () => { ui.fArea = el.parea.checked; measureSharp(); redraw(); };
    el.pcolor.forEach((b) => (b.onclick = () => { ui.fColor = b.dataset.pcolor; redraw(); }));
    el.pbg.forEach((b) => (b.onclick = () => { ui.fBg = b.dataset.pbg; redraw(); }));
    el.sharpReset.onclick = () => { if (sharp) { peak.v = sharp.v; peak.reset = false; render(); } };
    el.expo.forEach((b) => (b.onclick = () => { ui.expo = b.dataset.expo; redraw(); }));
    el.zHi.oninput = () => { ui.zHi = Number(el.zHi.value); redraw(); };
    el.zMid.onchange = () => { ui.zMid = el.zMid.checked; redraw(); };
    const clampIn = (inp, lo, hi, dflt) => { const v = Number(inp.value); return Number.isFinite(v) && inp.value !== "" ? Math.min(hi, Math.max(lo, v)) : dflt; };
    el.zMidV.onchange = () => { ui.zMidV = clampIn(el.zMidV, 1, 99, 50); redraw(); };
    el.zMidT.onchange = () => { ui.zMidT = clampIn(el.zMidT, 1, 25, 5); redraw(); };
    // toni medi centrati sulla mediana della luminosità: con un flat, le zone senza righe sono quelle che si scostano
    el.zMed.onclick = () => {
      const s = stats && channelStats(stats.hist[3]);
      if (s) { ui.zMidV = Math.round((s.median / 255) * 100); redraw(); }
    };
    el.fcLegend.innerHTML = FALSE_COLORS.filter((f) => f[2]).map(([a, b, c, name]) =>
      `<span><i style="background:rgb(${c.join(",")})"></i>${t(name)}</span><em>${fmtNum(a, 0)}–${fmtNum(Math.min(100, b), 0)} %</em>`).join("");
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
    applyImgFilter(false);   // canale ed etichetta salvati valgono da subito, anche a Ispettore chiuso
  }

  return {
    bind, clear, transform, pointer, setArea,
    get overlays() { return overlaysOn() || (ui.open && blockOn("wave")); },
    get flip() { return viewFlip(); },
    analyze: (img, info) => { lastInfo = info || {}; return analyze(img, lastInfo); },
    toggle: () => setOpen(!ui.open),
    get open() { return ui.open; },
  };
})();
