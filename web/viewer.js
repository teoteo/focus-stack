"use strict";
// Visualizzatore scatti: zoom +/−, adatta, 100% (pixel reali), pan con trascinamento,
// zoom con rotella centrato sul cursore, navigazione tra gli scatti, "segui ultimo".
const $ = (id) => document.getElementById(id);
const stage = $("stage"), img = $("img");

try { document.documentElement.dataset.theme = localStorage.getItem("fs-theme") || "dark"; } catch { /* opzionale */ }

let shots = [];          // elenco dal server
let current = null;      // id dello scatto mostrato
let currentKey = null;   // chiave unica dello scatto mostrato (gli id ripartono da 0 a ogni riavvio)
let live = true;         // segue automaticamente l'ultimo scatto
let lockView = true;     // mantiene zoom/pan cambiando scatto
let lastCount = -1;

// Vista: scale = pixel CSS per pixel immagine (naturale), tx/ty = traslazione in pixel CSS
const view = { scale: 1, tx: 0, ty: 0, mode: "fit" };   // mode: fit | free
let natW = 0, natH = 0;                                  // dimensioni dell'immagine mostrata
let fullW = 0;                                           // larghezza della piena risoluzione (se nota)
const DPR = () => window.devicePixelRatio || 1;
const MIN_ZOOM = 0.5, MAX_ZOOM_DEVICE = 16;              // min metà di 'adatta', max 1600% in pixel reali

// ---------------- trasformazione ----------------
function apply() {
  img.style.transform = `translate(${view.tx}px, ${view.ty}px) scale(${view.scale})`;
  // % riferita alla piena risoluzione e ai pixel fisici dello schermo
  const ratio = fullW && natW ? natW / fullW : 1;
  const devicePct = view.scale * ratio * DPR() * 100;
  $("z-val").textContent = natW ? `${devicePct >= 10 ? Math.round(devicePct) : devicePct.toFixed(1)}%` : "—";
  img.classList.toggle("pixelated", devicePct > 150);
  $("z-fit").setAttribute("aria-pressed", view.mode === "fit");
}

function fit() {
  if (!natW) return;
  const r = stage.getBoundingClientRect();
  view.scale = Math.min(r.width / natW, r.height / natH);
  view.tx = (r.width - natW * view.scale) / 2;
  view.ty = (r.height - natH * view.scale) / 2;
  view.mode = "fit";
  apply();
}

function zoomAt(newScale, cx, cy) {
  const ratio = fullW && natW ? natW / fullW : 1;
  const maxScale = MAX_ZOOM_DEVICE / (DPR() * ratio);
  const r = stage.getBoundingClientRect();
  const fitScale = natW ? Math.min(r.width / natW, r.height / natH) : 1;
  newScale = Math.max(fitScale * MIN_ZOOM, Math.min(maxScale, newScale));
  // il punto dell'immagine sotto (cx, cy) resta fermo
  const ix = (cx - view.tx) / view.scale, iy = (cy - view.ty) / view.scale;
  view.scale = newScale;
  view.tx = cx - ix * newScale;
  view.ty = cy - iy * newScale;
  view.mode = "free";
  apply();
}

function center() { const r = stage.getBoundingClientRect(); return [r.width / 2, r.height / 2]; }
const zoomBy = (k, cx, cy) => { if (cx == null) [cx, cy] = center(); zoomAt(view.scale * k, cx, cy); };

function actualPixels(cx, cy) {
  if (!natW) return;
  const ratio = fullW && natW ? natW / fullW : 1;
  if (cx == null) [cx, cy] = center();
  zoomAt(1 / (DPR() * ratio), cx, cy);
}

// ---------------- caricamento immagini ----------------
// Mostra subito l'anteprima, poi la sostituisce con la piena risoluzione mantenendo la vista.
let loadToken = 0;
function show(id, { keepView = lockView } = {}) {
  const shot = shots.find((s) => s.id === id);
  if (!shot) return;
  current = id;
  currentKey = shot.key;
  try { history.replaceState(null, "", `#${id}`); } catch { /* opzionale */ }
  renderMeta(shot);
  markStrip();
  const token = ++loadToken;
  const hadImage = natW > 0;
  const wasFit = view.mode === "fit" || !hadImage || !keepView;

  const preview = new Image();
  const full = new Image();
  let fullDone = false;
  $("loading").classList.remove("hidden");

  const swap = (el, isFull) => {
    if (token !== loadToken) return;
    const oldW = natW;
    natW = el.naturalWidth; natH = el.naturalHeight;
    if (isFull) fullW = natW;
    img.src = el.src;
    $("msg").classList.add("hidden");
    if (wasFit && !(isFull && view.mode === "free")) fit();
    else if (oldW) { view.scale *= oldW / natW; apply(); }   // stessa area sullo schermo
    else fit();
    if (isFull) $("loading").classList.add("hidden");
  };
  preview.onload = () => { if (!fullDone) swap(preview, false); };
  full.onload = () => { fullDone = true; swap(full, true); };
  full.onerror = () => { $("loading").textContent = "Piena risoluzione non disponibile"; };
  preview.src = `/api/shots/${id}/image?size=preview&v=${shot.key}`;
  full.src = `/api/shots/${id}/image?size=full&v=${shot.key}`;
}

function renderMeta(shot) {
  $("v-name").textContent = shot.name;
  const pos = shots.indexOf(shot) + 1;
  const parts = [`${pos} / ${shots.length}`];
  parts.push(shot.kind === "sequence" ? `sequenza · scatto ${shot.index}` : "scatto di prova");
  if (shot.position != null) parts.push(`posizione ${shot.position.toLocaleString("it-IT")}`);
  if (shot.temperature != null) parts.push(`${shot.temperature.toFixed(1)} °C`);
  parts.push(shot.time);
  $("v-meta").textContent = parts.join(" · ");
  $("prev").disabled = pos <= 1;
  $("next").disabled = pos >= shots.length;
  document.title = `${shot.name} — Visualizzatore`;
}

// ---------------- striscia miniature ----------------
function renderStrip() {
  const strip = $("strip");
  // dopo un riavvio del server gli scatti sono altri: via le miniature che non esistono più
  const keys = new Set(shots.map((s) => s.key));
  for (const b of [...strip.children]) if (!keys.has(b.dataset.key)) b.remove();
  const have = new Set([...strip.children].map((b) => b.dataset.key));
  for (const s of shots) {
    if (have.has(s.key)) continue;
    const b = document.createElement("button");
    b.dataset.id = s.id;
    b.dataset.key = s.key;
    b.title = s.name;
    b.innerHTML = `<img loading="lazy" alt="" src="/api/shots/${s.id}/image?size=preview&v=${s.key}"><span>${s.kind === "sequence" ? s.index : "P"}</span>`;
    b.onclick = () => { setLive(s.id === shots[shots.length - 1].id); show(s.id); };
    strip.appendChild(b);
  }
  markStrip();
}
function markStrip() {
  for (const b of $("strip").children) {
    const on = Number(b.dataset.id) === current;
    b.classList.toggle("active", on);
    if (on) b.scrollIntoView({ block: "nearest", inline: "nearest" });
  }
}

let loading = null;
function loadShots() {
  loading = (loading || Promise.resolve()).then(fetchShots, fetchShots);
  return loading;
}
async function fetchShots() {
  const r = await fetch("/api/shots");
  const data = await r.json();
  shots = data.items;
  renderStrip();
  // server riavviato: lo scatto mostrato non esiste più
  if (current != null && !shots.some((s) => s.id === current && s.key === currentKey)) {
    current = currentKey = null;
    natW = natH = fullW = 0;
    img.removeAttribute("src");
    $("msg").classList.remove("hidden");
    $("v-name").textContent = "Nessuno scatto";
    $("v-meta").textContent = "";
    try { history.replaceState(null, "", location.pathname); } catch { /* opzionale */ }
  }
  if (!shots.length) return;
  const hashId = Number(location.hash.slice(1));
  if (current == null) {
    const fromHash = location.hash && shots.some((s) => s.id === hashId);
    // aperto su uno scatto specifico che non è l'ultimo: non saltare subito all'ultimo
    if (fromHash && hashId !== shots[shots.length - 1].id) setLive(false);
    show(fromHash ? hashId : shots[shots.length - 1].id, { keepView: false });
  }
  else if (live) show(shots[shots.length - 1].id);
  else renderMeta(shots.find((s) => s.id === current));
}

// aggiornamenti: il WebSocket di stato segnala quando arriva un nuovo scatto
function connectWS() {
  const ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = (ev) => {
    const st = JSON.parse(ev.data);
    if (st.shot_count !== lastCount) { lastCount = st.shot_count; loadShots().catch(() => {}); }
  };
  ws.onclose = () => setTimeout(connectWS, 1500);
}

// ---------------- interazione ----------------
function step(delta) {
  const i = shots.findIndex((s) => s.id === current);
  const n = shots[i + delta];
  if (!n) return;
  setLive(n === shots[shots.length - 1]);
  show(n.id);
}
function setLive(on) { live = on; $("live").setAttribute("aria-pressed", on); }
function setLock(on) { lockView = on; $("lock").setAttribute("aria-pressed", on); }

$("prev").onclick = () => step(-1);
$("next").onclick = () => step(1);
$("z-in").onclick = () => zoomBy(1.25);
$("z-out").onclick = () => zoomBy(1 / 1.25);
$("z-fit").onclick = fit;
$("z-reset").onclick = fit;
$("z-100").onclick = () => actualPixels();
$("live").onclick = () => { setLive(!live); if (live && shots.length) show(shots[shots.length - 1].id); };
$("lock").onclick = () => setLock(!lockView);
$("reveal").onclick = () => current != null && fetch(`/api/shots/${current}/reveal`, { method: "POST", headers: { "X-FocusStack": "1" } });
$("fs").onclick = () => (document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen?.());

// pan con il mouse (pointer events: funziona anche con trackpad e touch)
let drag = null;
stage.addEventListener("pointerdown", (e) => {
  if (e.button !== 0 || !natW) return;
  drag = { x: e.clientX, y: e.clientY, tx: view.tx, ty: view.ty };
  stage.setPointerCapture(e.pointerId);
  stage.classList.add("dragging");
});
stage.addEventListener("pointermove", (e) => {
  if (!drag) return;
  view.tx = drag.tx + (e.clientX - drag.x);
  view.ty = drag.ty + (e.clientY - drag.y);
  view.mode = "free";
  apply();
});
const endDrag = () => { drag = null; stage.classList.remove("dragging"); };
stage.addEventListener("pointerup", endDrag);
stage.addEventListener("pointercancel", endDrag);

// rotella: zoom centrato sul cursore. Trackpad: pinch = zoom, scorrimento a due dita = pan.
stage.addEventListener("wheel", (e) => {
  if (!natW) return;
  e.preventDefault();
  const r = stage.getBoundingClientRect();
  const cx = e.clientX - r.left, cy = e.clientY - r.top;
  const isTrackpadPan = !e.ctrlKey && (e.deltaX !== 0 || (e.deltaMode === 0 && Math.abs(e.deltaY) < 40 && !Number.isInteger(e.deltaY)));
  if (isTrackpadPan) {
    view.tx -= e.deltaX; view.ty -= e.deltaY; view.mode = "free"; apply();
    return;
  }
  const dy = e.deltaMode === 1 ? e.deltaY * 33 : e.deltaY;
  zoomAt(view.scale * Math.exp(-dy * (e.ctrlKey ? 0.01 : 0.0018)), cx, cy);
}, { passive: false });

// Safari: gesto di pinch nativo
let gestureStart = 1;
stage.addEventListener("gesturestart", (e) => { e.preventDefault(); gestureStart = view.scale; });
stage.addEventListener("gesturechange", (e) => {
  e.preventDefault();
  const r = stage.getBoundingClientRect();
  zoomAt(gestureStart * e.scale, e.clientX - r.left, e.clientY - r.top);
});

stage.addEventListener("dblclick", (e) => {
  const r = stage.getBoundingClientRect();
  if (view.mode === "fit") actualPixels(e.clientX - r.left, e.clientY - r.top);
  else fit();
});

document.addEventListener("keydown", (e) => {
  if (e.metaKey || e.ctrlKey) return;
  const k = e.key;
  if (k === "+" || k === "=") zoomBy(1.25);
  else if (k === "-" || k === "_") zoomBy(1 / 1.25);
  else if (k === "0" || k === "r" || k === "R") fit();
  else if (k === "1") actualPixels();
  else if (k === "ArrowLeft") step(-1);
  else if (k === "ArrowRight") step(1);
  else if (k === "l" || k === "L") $("live").click();
  else if (k === "k" || k === "K") $("lock").click();
  else if (k === "f" || k === "F") $("fs").click();
  else return;
  e.preventDefault();
});

// in modalità "adatta" la vista segue il ridimensionamento della finestra
new ResizeObserver(() => { if (view.mode === "fit") fit(); }).observe(stage);
window.addEventListener("hashchange", () => {
  const id = Number(location.hash.slice(1));
  if (location.hash && id !== current && shots.some((s) => s.id === id)) { setLive(false); show(id); }
});

apply();
connectWS();   // il primo messaggio di stato carica l'elenco degli scatti
