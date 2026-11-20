"use strict";
// Visualizzatore scatti: zoom +/−, adatta, 100% (pixel reali), pan con trascinamento,
// zoom con rotella centrato sul cursore, navigazione tra gli scatti, "segui ultimo" e live view.
const $ = (id) => document.getElementById(id);
const stage = $("stage"), img = $("img");

try { document.documentElement.dataset.theme = localStorage.getItem("fs-theme") || "dark"; } catch { /* opzionale */ }

let shots = [];          // scatti del gruppo corrente (la sequenza in corso o l'ultima, oppure le prove fatte dopo)
let allCount = 0;        // tutti gli scatti che il server tiene, anche dei gruppi precedenti (per «Svuota»)
let lastState = null;    // ultimo stato ricevuto dal WebSocket
let liveStopRev = null;  // ultimo valore visto di live_stop_rev (null fino al primo stato)
let current = null;      // id dello scatto mostrato
let currentKey = null;   // chiave unica dello scatto mostrato (gli id ripartono da 0 a ogni riavvio)
let follow = true;       // segue automaticamente l'ultimo scatto
let lockView = true;     // mantiene zoom/pan cambiando scatto
let lastRev = null;
let bootSignature = null; // versione del codice del server alla prima connessione

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
  $("z-val").textContent = natW ? `${fmtNum(devicePct, devicePct >= 10 ? 0 : 1)}%` : "—";
  img.classList.toggle("pixelated", devicePct > 150);
  Inspector.transform(img.style.transform, devicePct > 150);
  $("z-fit").setAttribute("aria-pressed", view.mode === "fit");
  drawGuides();
}

// ---------------- guide di composizione ----------------
// Un clic le alterna: terzi → incrocio al centro → terzi e centro → nessuna. Sono riferite all'immagine (seguono zoom
// e spostamento) e disegnate a 1 pixel fisico dello schermo.
const GUIDE_MODES = ["off", "thirds", "center", "both"];
let guideMode = "off";
try { const m = localStorage.getItem("fs-guides"); if (GUIDE_MODES.includes(m)) guideMode = m; } catch { /* opzionale */ }
const GUIDE_TITLES = {
  off: () => t("Guide di composizione: nessuna. Clic: terzi (G)"),
  thirds: () => t("Guide di composizione: terzi. Clic: centro (G)"),
  center: () => t("Guide di composizione: centro. Clic: terzi e centro (G)"),
  both: () => t("Guide di composizione: terzi e centro. Clic: nessuna (G)"),
};
function setGuides(mode) {
  guideMode = mode;
  try { localStorage.setItem("fs-guides", mode); } catch { /* opzionale */ }
  const b = $("guides");
  b.dataset.mode = mode;
  b.setAttribute("aria-pressed", String(mode !== "off"));
  b.title = GUIDE_TITLES[mode]();
  drawGuides();
}
function drawGuides() {
  const c = $("guides-canvas");
  const on = guideMode !== "off" && natW > 0 && img.hasAttribute("src") && img.style.visibility !== "hidden";
  c.classList.toggle("hidden", !on);
  if (!on) return;
  const r = stage.getBoundingClientRect(), d = DPR();
  const W = Math.round(r.width * d), H = Math.round(r.height * d);
  if (c.width !== W || c.height !== H) { c.width = W; c.height = H; }
  c.style.width = `${r.width}px`; c.style.height = `${r.height}px`;
  const ctx = c.getContext("2d");
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = "#fff";
  // riquadro dell'immagine in pixel fisici
  const x0 = view.tx * d, y0 = view.ty * d, w = natW * view.scale * d, h = natH * view.scale * d;
  const vline = (x, ya, yb) => {
    x = Math.floor(x); const a = Math.max(0, Math.round(ya)), b = Math.min(H, Math.round(yb));
    if (x >= 0 && x < W && b > a) ctx.fillRect(x, a, 1, b - a);
  };
  const hline = (y, xa, xb) => {
    y = Math.floor(y); const a = Math.max(0, Math.round(xa)), b = Math.min(W, Math.round(xb));
    if (y >= 0 && y < H && b > a) ctx.fillRect(a, y, b - a, 1);
  };
  if (guideMode === "thirds" || guideMode === "both") {
    for (const k of [1, 2]) {
      vline(x0 + (w * k) / 3, y0, y0 + h);
      hline(y0 + (h * k) / 3, x0, x0 + w);
    }
  }
  if (guideMode === "center" || guideMode === "both") {
    const cx = x0 + w / 2, cy = y0 + h / 2, arm = Math.max(12 * d, Math.min(w, h) / 24);
    vline(cx, cy - arm, cy + arm + 1);
    hline(cy, cx - arm, cx + arm + 1);
  }
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
    Inspector.analyze(el, inspectorInfo(shot, el, isFull));
    if (wasFit && !(isFull && view.mode === "free")) fit();
    else if (oldW) { view.scale *= oldW / natW; apply(); }   // stessa area sullo schermo
    else fit();
    if (isFull) $("loading").classList.add("hidden");
  };
  preview.onload = () => { if (!fullDone) swap(preview, false); };
  full.onload = () => { fullDone = true; swap(full, true); };
  full.onerror = () => {
    $("loading").textContent = t("Piena risoluzione non disponibile");
    // l'Ispettore resta sull'anteprima: lo dice invece di promettere numeri che non arriveranno
    if (token === loadToken && preview.naturalWidth) {
      Inspector.analyze(preview, { ...inspectorInfo(shot, preview, false),
        basis: `${t("Piena risoluzione non disponibile")} · ${preview.naturalWidth} × ${preview.naturalHeight}` });
    }
  };
  preview.src = `/api/shots/${id}/image?size=preview&v=${shot.key}`;
  full.src = `/api/shots/${id}/image?size=full&v=${shot.key}`;
}

// cosa misura l'Ispettore: anteprima o piena risoluzione; con i RAW è la conversione per lo schermo
const RAW_EXT = /\.(nef|nrw|cr2|cr3|crw|arw|srf|sr2|raf|orf|rw2|dng|pef|srw|3fr|iiq|x3f|erf|mef|mos|kdc|rwl)$/i;
function inspectorInfo(shot, el, isFull) {
  const w = el.naturalWidth, h = el.naturalHeight;
  const basis = isFull
    ? t("Tutti i pixel dell'immagine a 8 bit: {w} × {h} ({mp} MP)", { w, h, mp: fmtNum((w * h) / 1e6, 1) })
    : t("Anteprima ridotta ({w} × {h}): fra poco i numeri della piena risoluzione", { w, h });
  const files = shot.files || [shot.file];
  let note = "";
  if (RAW_EXT.test(shot.file)) note = t("Conversione del RAW per lo schermo: il RAW ha più margine nelle luci e nelle ombre.");
  else if (files.some((f) => RAW_EXT.test(f))) note = t("JPEG della fotocamera: il RAW salvato insieme ha più margine nelle luci e nelle ombre.");
  return { basis, note };
}

function renderMeta(shot) {
  $("v-name").textContent = shot.name;
  const pos = shots.indexOf(shot) + 1;
  const parts = [shot.kind === "sequence" ? t("scatto {n}", { n: shot.repeat ? `${shot.index}.${shot.repeat}` : shot.index })
    : shot.kind === "calibration" ? t("frame di calibrazione {n}", { n: pos })
    : shot.kind === "exposure" ? t("prova di esposizione {n}", { n: pos }) : t("prova {n}", { n: pos })];
  if (shot.position != null) parts.push(t("posizione {n}", { n: fmtNum(shot.position) }));
  if (shot.temperature != null) parts.push(`${fmtNum(shot.temperature, 1)} °C`);
  parts.push(shot.time);
  $("v-meta").textContent = parts.join(" · ");
  $("prev").disabled = pos <= 1;
  $("next").disabled = pos >= shots.length;
  document.title = `${shot.name} — ${t("Visualizzatore")}`;
}

// ---------------- contatore della pila e linea di avanzamento ----------------
// A sinistra: ultimo scatto fatto / totale della sequenza (non cambia guardando uno scatto più vecchio);
// per le prove, quante sono. In alto, durante la pila, una linea azzurra di 2 px da 0 a 100 %.
function renderCounter() {
  const q = (lastState && lastState.sequence) || {}, box = $("v-count"), line = $("v-topline");
  const running = ["running", "paused", "stopping"].includes(q.state);
  const last = shots[shots.length - 1];
  let num = "", lbl = "";
  if (running || (last && last.kind === "sequence")) {
    // lo scatto arriva un attimo prima che la sequenza aggiorni il suo indice: vale il più alto dei due
    const lastSeq = last && last.kind === "sequence" ? last.index : 0;
    const total = q.total || lastSeq, done = q.total ? Math.max(q.index, running ? lastSeq : 0) : lastSeq;
    num = `${done}<small>/${total}</small>`;
    lbl = { running: t("in corso"), paused: t("in pausa"), stopping: t("arresto…"), done: t("completata") }[q.state]
      || (q.total && q.index < q.total ? t("interrotta") : t("completata"));
  } else if (last) {
    num = String(shots.length);
    lbl = last.kind === "calibration" ? t("calibrazione") : shots.length === 1 ? t("prova") : t("prove");
  }
  box.classList.toggle("hidden", !num);
  box.classList.toggle("live", running);
  $("v-count-num").innerHTML = num;
  $("v-count-lbl").textContent = lbl;
  const lastSeqIdx = last && last.kind === "sequence" ? last.index : 0;
  const pct = running && q.total ? Math.round((Math.min(q.total, Math.max(q.index, lastSeqIdx)) / q.total) * 100) : 0;
  line.classList.toggle("hidden", !running);
  line.style.width = `${pct}%`;
  line.setAttribute("aria-valuenow", pct);
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
    b.innerHTML = `<img loading="lazy" alt="" src="/api/shots/${s.id}/image?size=preview&v=${s.key}"><span>${s.kind === "sequence" ? (s.repeat ? `${s.index}.${s.repeat}` : s.index) : s.kind === "calibration" ? t("C") : s.kind === "exposure" ? t("E") : t("P")}</span>`;
    b.onclick = () => { setLiveView(false, { restore: false }); setFollow(s.id === shots[shots.length - 1].id); show(s.id); };
    strip.appendChild(b);
  }
  markStrip();
}
function markStrip() {
  for (const b of $("strip").children) {
    const on = !liveOn && Number(b.dataset.id) === current;
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
  allCount = data.count ?? data.items.length;
  // la striscia ricomincia a ogni sequenza; gli scatti di prova fatti dopo ne aprono una nuova
  shots = data.group == null ? data.items : data.items.filter((s) => s.group === data.group);
  $("clear").disabled = !allCount;
  renderCounter();
  renderStrip();
  // server riavviato: lo scatto mostrato non esiste più
  if (current != null && !shots.some((s) => s.id === current && s.key === currentKey)) {
    current = currentKey = null;
    if (!liveOn) {
      natW = natH = fullW = 0;
      img.removeAttribute("src");
      Inspector.clear();
      $("msg").classList.remove("hidden");
      $("v-name").textContent = t("Nessuno scatto");
      $("v-meta").textContent = "";
      try { history.replaceState(null, "", location.pathname); } catch { /* opzionale */ }
    }
  }
  if (!shots.length || liveOn) return;   // durante il live view arrivano solo le miniature
  const hashId = Number(location.hash.slice(1));
  if (current == null) {
    const fromHash = location.hash && shots.some((s) => s.id === hashId);
    // aperto su uno scatto specifico che non è l'ultimo: non saltare subito all'ultimo
    if (fromHash && hashId !== shots[shots.length - 1].id) setFollow(false);
    show(fromHash ? hashId : shots[shots.length - 1].id, { keepView: false });
  }
  else if (follow) show(shots[shots.length - 1].id);
  else renderMeta(shots.find((s) => s.id === current));
}

// aggiornamenti: il WebSocket di stato segnala quando arriva un nuovo scatto
function connectWS() {
  const ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = (ev) => {
    const st = JSON.parse(ev.data);
    // server ripartito con codice nuovo (aggiornamento dell'app): ricarica la pagina per avere i comandi nuovi
    if (bootSignature != null && st.boot_signature !== bootSignature) { location.reload(); return; }
    bootSignature = st.boot_signature;
    if (st.language && st.language !== LANG) { location.reload(); return; }   // lingua cambiata in Configurazione
    camState = st.camera;
    lastState = st;
    // «Ferma live» premuto in un'altra finestra
    if (liveStopRev != null && st.live_stop_rev > liveStopRev && liveOn) setLiveView(false);
    liveStopRev = st.live_stop_rev ?? liveStopRev;
    seqRunning = ["running", "paused", "stopping"].includes(st.sequence.state);
    seqLivePaused = seqRunning && !st.sequence.live_ok;   // in pausa dall'arrivo della slitta al primo piano
    // primo scatto della sequenza con il live view acceso: si chiude il live e si seguono gli scatti nuovi.
    // Fino a lì resta acceso, per guardare la slitta che torna all'inizio.
    const seqShots = seqRunning ? st.sequence.shots || 0 : 0;
    if (seqShots > 0 && seqShotsPrev === 0 && liveOn) {
      setFollow(true);
      setLiveView(false);
      notice(t("Primo scatto della sequenza: live view chiuso, ora segue l'ultimo scatto"));
    }
    seqShotsPrev = seqShots;
    if (wantLive && camState.connected) setLiveView(true);
    wantLive = false;
    renderLiveView();
    renderCounter();
    // shots_rev cambia a ogni scatto e a ogni "Svuota" (shot_count: server di versioni precedenti)
    const rev = st.shots_rev ?? st.shot_count;
    if (rev !== lastRev) { lastRev = rev; loadShots().catch(() => {}); }
  };
  ws.onclose = () => setTimeout(connectWS, 1500);
}

// ---------------- live view (stream MJPEG del server nella stessa <img>, con zoom e pan) ----------------
let liveOn = false, liveStartedAt = 0, liveTimer = 0;
let camState = { connected: false }, seqRunning = false, seqLivePaused = false, seqShotsPrev = 0;
let wantLive = location.hash === "#live";   // aperto dalla finestra principale con il live view acceso
let noticeTimer = 0;

function notice(text) {
  $("notice").textContent = text;
  $("notice").classList.remove("hidden");
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => $("notice").classList.add("hidden"), 8000);
}

// restore: all'uscita torna allo scatto mostrato prima (all'ultimo con "segui ultimo")
function setLiveView(on, { restore = true } = {}) {
  if (on === liveOn) return;
  liveOn = on;
  liveStartedAt = Date.now();
  ++loadToken;                      // annulla i caricamenti di scatti in corso
  clearInterval(liveTimer);
  Inspector.clear();
  natW = natH = fullW = 0;
  $("loading").classList.add("hidden");
  $("liveview").setAttribute("aria-pressed", String(on));
  $("liveview").textContent = on ? t("■ Ferma live") : t("● Live");
  $("live-badge").classList.toggle("hidden", !on);
  markStrip();
  if (on) {
    $("notice").classList.add("hidden");
    img.style.visibility = "hidden";   // niente scatto vecchio finché non arriva il primo fotogramma
    img.src = `/api/camera/live?t=${liveStartedAt}`;
    $("msg").textContent = t("Avvio del live view…");
    $("msg").classList.remove("hidden");
    try { history.replaceState(null, "", "#live"); } catch { /* opzionale */ }
    // l'evento load di uno stream MJPEG non è affidabile: si controllano le dimensioni del fotogramma
    liveTimer = setInterval(checkLiveFrame, 100);
    liveInspect();
    renderLiveView();
    return;
  }
  // togliere src chiude la connessione: il server spegne il live view della fotocamera
  clearInterval(liveInspTimer);
  img.removeAttribute("src");
  img.style.visibility = "";
  drawGuides();   // nessuna immagine: niente guide
  $("msg").textContent = t("In attesa del primo scatto…");
  $("msg").classList.remove("hidden");
  $("v-name").textContent = t("Nessuno scatto");
  $("v-meta").textContent = "";
  document.title = t("Visualizzatore");
  try { history.replaceState(null, "", location.pathname); } catch { /* opzionale */ }
  if (restore && shots.length) {
    const back = !follow && shots.some((s) => s.id === current) ? current : shots[shots.length - 1].id;
    show(back, { keepView: false });
  } else if (shots.length) {
    $("prev").disabled = $("next").disabled = false;
  }
}

function checkLiveFrame() {
  if (!liveOn || !img.naturalWidth) return;
  if (img.naturalWidth === natW && img.naturalHeight === natH) return;
  const oldW = natW;
  natW = img.naturalWidth; natH = img.naturalHeight; fullW = natW;   // 100% = pixel del live view
  img.style.visibility = "";
  $("msg").classList.add("hidden");
  if (!oldW || view.mode === "fit") fit();
  else { view.scale *= oldW / natW; apply(); }   // la fotocamera ha cambiato risoluzione
}

// Ispettore sul live view: i numeri del fotogramma corrente, ricalcolati due volte al secondo
let liveInspTimer = 0;
function liveInspect() {
  clearInterval(liveInspTimer);
  if (!liveOn) return;
  liveInspTimer = setInterval(() => {
    if (!liveOn || !Inspector.open || !img.naturalWidth || seqLivePaused) return;
    Inspector.analyze(img, { live: true,
      basis: t("Fotogramma del live view ({w} × {h}), aggiornato di continuo", { w: img.naturalWidth, h: img.naturalHeight }),
      note: t("Il live view è un'anteprima compressa della fotocamera: controlla l'esposizione anche su uno scatto di prova.") });
  }, 500);
}

function renderLiveView() {
  $("liveview").disabled = !camState.connected;
  if (!liveOn) return;
  if (!camState.connected) { setLiveView(false); notice(t("Fotocamera scollegata: live view chiuso")); return; }
  // l'errore di uno stream precedente può arrivare ancora per un attimo dopo il riavvio
  if (camState.live_error && Date.now() - liveStartedAt > 2000) {
    const err = camState.live_error;
    setLiveView(false);
    notice(err);
    return;
  }
  const badge = $("live-badge");
  badge.textContent = seqLivePaused ? t("IN PAUSA") : camState.busy ? t("SCATTO…") : t("LIVE");
  badge.classList.toggle("paused", seqLivePaused || camState.busy);
  $("v-name").textContent = t("Live view");
  $("v-meta").textContent = seqLivePaused ? t("In pausa durante la sequenza") : camState.model || "";
  $("prev").disabled = $("next").disabled = !shots.length;
  document.title = `${t("Live view")} — ${t("Visualizzatore")}`;
}

// ---------------- interazione ----------------
function step(delta) {
  if (liveOn) { setLiveView(false); return; }   // esce dal live view tornando allo scatto di prima
  const i = shots.findIndex((s) => s.id === current);
  const n = shots[i + delta];
  if (!n) return;
  setFollow(n === shots[shots.length - 1]);
  show(n.id);
}
function setFollow(on) { follow = on; $("follow").setAttribute("aria-pressed", on); }
function setLock(on) { lockView = on; $("lock").setAttribute("aria-pressed", on); }

$("prev").onclick = () => step(-1);
$("next").onclick = () => step(1);
$("z-in").onclick = () => zoomBy(1.25);
$("z-out").onclick = () => zoomBy(1 / 1.25);
$("z-fit").onclick = fit;
$("z-reset").onclick = fit;
$("z-100").onclick = () => actualPixels();
$("follow").onclick = () => {
  setFollow(liveOn || !follow);
  setLiveView(false, { restore: false });
  if (follow && shots.length) show(shots[shots.length - 1].id, { keepView: false });
};
$("liveview").onclick = () => {
  // «Ferma live» la ferma anche nella finestra principale: passa dal server, vedi live_stop_rev
  if (liveOn) fetch("/api/camera/live/stop", { method: "POST", headers: { "X-FocusStack": "1" } }).catch(() => {});
  setLiveView(!liveOn);
};
$("guide-btn").href = `/guide/${["it", "en", "fr", "de", "es"].includes(LANG) ? LANG : "en"}.html#visualizzatore`;
// live avviato dalla finestra principale: parte anche qui (non durante la sequenza)
if ("BroadcastChannel" in window) {
  new BroadcastChannel("focus-stack").onmessage = (ev) => {
    if (ev.data && ev.data.live && !liveOn && !seqLivePaused && camState.connected) setLiveView(true);
  };
}
$("lock").onclick = () => setLock(!lockView);
$("guides").onclick = () => setGuides(GUIDE_MODES[(GUIDE_MODES.indexOf(guideMode) + 1) % GUIDE_MODES.length]);
$("clear").onclick = async () => {
  if (!allCount) return;
  if (!confirm(t("Ricominciare da capo? Gli scatti ({n}) escono dal visualizzatore e la sequenza torna «Pronta».", { n: allCount }) + "\n\n" +
    t("I file già salvati restano nella cartella sul disco. La prossima sequenza avrà una cartella nuova, con i suoi sequence.json e sequence.txt."))) return;
  setFollow(true);
  await fetch("/api/shots/clear", { method: "POST", headers: { "X-FocusStack": "1" } });
  loadShots().catch(() => {});
};
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
  if (!drag) {
    if (!Inspector.open || !natW) return;
    const r = stage.getBoundingClientRect();
    Inspector.pointer(Math.floor((e.clientX - r.left - view.tx) / view.scale), Math.floor((e.clientY - r.top - view.ty) / view.scale));
    return;
  }
  view.tx = drag.tx + (e.clientX - drag.x);
  view.ty = drag.ty + (e.clientY - drag.y);
  view.mode = "free";
  apply();
});
const endDrag = () => { drag = null; stage.classList.remove("dragging"); };
stage.addEventListener("pointerup", endDrag);
stage.addEventListener("pointerleave", () => Inspector.pointer(null));
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
  else if (k === "l" || k === "L") { if (!$("liveview").disabled) $("liveview").click(); }
  else if (k === "u" || k === "U") $("follow").click();
  else if (k === "k" || k === "K") $("lock").click();
  else if (k === "f" || k === "F") $("fs").click();
  else if (k === "i" || k === "I") Inspector.toggle();
  else if (k === "g" || k === "G") $("guides").click();
  else return;
  e.preventDefault();
});

// in modalità "adatta" la vista segue il ridimensionamento della finestra
new ResizeObserver(() => { if (view.mode === "fit") fit(); else drawGuides(); }).observe(stage);
window.addEventListener("hashchange", () => {
  // la finestra principale chiede il live view (#live) o uno scatto (#id)
  if (location.hash === "#live") { if (!liveOn) { if (camState.connected) setLiveView(true); else wantLive = true; } return; }
  const id = Number(location.hash.slice(1));
  if (location.hash && (id !== current || liveOn) && shots.some((s) => s.id === id)) {
    setLiveView(false, { restore: false }); setFollow(false); show(id);
  }
});

Inspector.bind({
  // aperto o chiuso: lo spazio dell'immagine cambia; sul live view riparte il calcolo periodico
  onToggle: () => { if (view.mode === "fit") requestAnimationFrame(fit); if (liveOn) liveInspect(); },
});
// barra che va a capo: un separatore rimasto in fondo alla riga (il gruppo dopo è sceso sotto) si nasconde.
// visibility e non display: lo spazio resta, così nascondendolo la barra non cambia di nuovo il modo di andare a capo
function tidySeparators() {
  for (const sep of document.querySelectorAll(".vbar .sep")) {
    const next = sep.nextElementSibling;
    sep.style.visibility = next && next.offsetTop > sep.offsetTop + sep.offsetHeight ? "hidden" : "";
  }
}
new ResizeObserver(tidySeparators).observe(document.querySelector(".vbar"));
setGuides(guideMode);
apply();
connectWS();   // il primo messaggio di stato carica l'elenco degli scatti
