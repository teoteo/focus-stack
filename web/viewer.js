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
  drawAfRoi();
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
    // con l'area dell'autofocus in vista l'incrocio ne segna il centro (si sposta con lei), altrimenti il centro
    const roi = afShownRect();
    const cx = roi ? x0 + ((roi[0] + roi[2]) / 2) * w : x0 + w / 2, cy = roi ? y0 + ((roi[1] + roi[3]) / 2) * h : y0 + h / 2;
    const arm = Math.max(12 * d, Math.min(w, h) / 24);
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
    if (isFull) {   // pixel del sensore: il lato dell'area dell'autofocus è in questi
      fullW = afSensorW = natW;
      try { localStorage.setItem("fs-sensor-w", String(natW)); } catch { /* opzionale */ }
    }
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
    : shot.kind === "exposure" ? t("prova di esposizione {n}", { n: pos })
    : shot.kind === "autofocus" ? t("autofocus {n}", { n: pos }) : t("prova {n}", { n: pos })];
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
    lbl = last.kind === "calibration" ? t("calibrazione") : last.kind === "autofocus" ? t("autofocus")
      : shots.length === 1 ? t("prova") : t("prove");
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
    b.innerHTML = `<img loading="lazy" alt="" src="/api/shots/${s.id}/image?size=preview&v=${s.key}"><span>${s.kind === "sequence" ? (s.repeat ? `${s.index}.${s.repeat}` : s.index) : s.kind === "calibration" ? t("C") : s.kind === "exposure" ? t("E") : s.kind === "autofocus" ? t("AF") : t("P")}</span>`;
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
  $("clear").classList.toggle("hidden", !allCount);
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
    onAfState(st);
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
    // scatto di prova con il live acceso: si mostra lo scatto; il live riparte quando si muove il focheggiatore
    const park = st.live_park || {};
    if (liveParkRev != null && park.rev > liveParkRev && liveOn) {
      setFollow(true);
      setLiveView(false, { restore: false });
      liveResume = { pos: park.pos };
      if (shots.length) show(shots[shots.length - 1].id, { keepView: false });   // poi loadShots porta quello nuovo
      notice(park.why === "af" ? t("Autofocus con scatti veri: il live view riparte quando muovi il focheggiatore")
        : t("Scatto di prova: il live view riparte quando muovi il focheggiatore"));
    }
    else if (liveParkRev != null && park.rev > liveParkRev && liveResume) liveResume = { pos: park.pos };
    liveParkRev = park.rev ?? liveParkRev;
    if (liveResume && !liveOn && !(st.autofocus && st.autofocus.busy)) {   // durante l'autofocus il live resta da parte
      const f = st.focuser || {};
      if (!camState.connected || seqRunning) liveResume = null;
      else if (f.connected && (f.moving || (liveResume.pos != null && f.position !== liveResume.pos))) setLiveView(true);
    }
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
// live view messo da parte da uno scatto di prova: {pos} finché il focheggiatore non si muove, poi riparte
let liveParkRev = null, liveResume = null;
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
  liveResume = null;   // acceso o spento in qualsiasi altro modo: niente ripresa automatica
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

// ---------------- autofocus su un punto ----------------
// Modalità autofocus (pulsante ⌖ o tasto A): un clic sull'immagine mette l'area (quadrata, lato in pixel del
// sensore) sul dettaglio; Avvia chiede al server la serie di scatti. La curva della nitidezza si riempie scatto per
// scatto dallo stato del server (autofocus.points); quando parte la passata fine i punti della ricerca ampia
// spariscono. L'area è in frazioni dell'immagine, così resta sullo stesso punto cambiando scatto o passando al live.
let afPanelOpen = false;     // pannello aperto: un clic sull'immagine sceglie l'area (tranne durante la misura)
let afHover = null;          // punto del grafico sotto il puntatore (indice in points, o "verify")
let afRoi = null;            // {cx, cy, s}: centro e lato in frazioni della larghezza dell'immagine
let afSizePx = 256;          // lato dell'area in pixel del sensore (Configurazione › Autofocus)
// larghezza della piena risoluzione dell'ultimo scatto visto (pixel del sensore), ricordata anche dopo: con il solo
// live view non si conosce, e il lato dell'area in «pixel del sensore» diventava in pixel del fotogramma live
let afSensorW = 0;
try { afSensorW = Number(localStorage.getItem("fs-sensor-w")) || 0; } catch { /* opzionale */ }
let afState = null;          // stato dell'autofocus dal server
let afRevSeen = null;        // ultimo autofocus visto: uno nuovo (anche da un'altra finestra) apre il pannello
let afSizeSaveTimer = 0;
const afBusy = () => !!(afState && afState.busy);
const refW = () => afSensorW || fullW || natW;

async function post(path, body) {
  const r = await fetch(path, { method: "POST", headers: { "X-FocusStack": "1", "Content-Type": "application/json" },
    body: JSON.stringify(body || {}) });
  let data = null;
  try { data = await r.json(); } catch { /* risposta vuota */ }
  if (!r.ok) throw new Error((data && data.detail) || `HTTP ${r.status}`);
  return data;
}

function openAf() {
  afPanelOpen = true;
  $("af-btn").setAttribute("aria-pressed", "true");
  renderAf();
}

function closeAf() {
  afPanelOpen = false;
  stage.classList.remove("af-mode");
  $("af-btn").setAttribute("aria-pressed", "false");
  renderAf();
}

// area per il server: frazioni x0, y0, x1, y1 (quadrata in pixel dell'immagine), dentro l'immagine
function afRoiRect(roi = afRoi) {
  if (!roi || !natW) return null;
  const sw = roi.s, sh = (roi.s * natW) / natH;
  const cx = Math.min(1 - sw / 2, Math.max(sw / 2, roi.cx)), cy = Math.min(1 - sh / 2, Math.max(sh / 2, roi.cy));
  return [cx - sw / 2, cy - sh / 2, cx + sw / 2, cy + sh / 2];
}

function afPlace(clientX, clientY) {
  if (!natW) return;
  const r = stage.getBoundingClientRect();
  const ix = (clientX - r.left - view.tx) / view.scale, iy = (clientY - r.top - view.ty) / view.scale;
  if (ix < 0 || iy < 0 || ix > natW || iy > natH) return;
  afRoi = { cx: ix / natW, cy: iy / natH, s: Math.min(0.9, afSizePx / refW()) };
  renderAf();
}

function setAfSize(px, save = true) {
  const max = Number($("af-size").max) || 1024;
  afSizePx = Math.round(Math.max(16, Math.min(max, px)) / 8) * 8;
  $("af-size").value = afSizePx;
  $("af-size-val").textContent = `${fmtNum(afSizePx)} px`;
  if (afRoi) afRoi.s = Math.min(0.9, afSizePx / refW());
  drawAfRoi();
  if (!save) return;
  clearTimeout(afSizeSaveTimer);
  afSizeSaveTimer = setTimeout(() => afSaveSettings({ roi_px: afSizePx }).catch(() => {}), 600);
}

// le impostazioni si mandano intere: si parte da quelle del server e si cambia solo il necessario
function afSaveSettings(change) {
  const a = (lastState && lastState.settings && lastState.settings.autofocus) || {};
  const keys = ["mode", "roi_px", "coarse", "coarse_range", "coarse_step", "settle_ms", "overscan", "max_travel"];
  const body = Object.fromEntries(keys.filter((k) => k in a).map((k) => [k, a[k]]));
  return post("/api/autofocus/settings", { ...body, ...change });
}

// area dell'autofocus mostrata sull'immagine (frazioni x0, y0, x1, y1) o null: quella della misura in corso,
// altrimenti quella scelta, solo con il pannello aperto
function afShownRect() {
  const running = afBusy() && afState.roi && afState.roi.length === 4;
  const rect = running ? afState.roi : afRoiRect();
  return (afPanelOpen || running) && rect && natW > 0 && img.style.visibility !== "hidden" ? rect : null;
}

function drawAfRoi() {
  const box = $("af-roi");
  const running = afBusy() && afState.roi && afState.roi.length === 4;
  const rect = afShownRect();
  const show = !!rect;
  box.classList.toggle("hidden", !show);
  drawGuides();   // l'incrocio delle guide segue l'area
  if (!show) return;
  box.classList.toggle("running", running);
  const [x0, y0, x1, y1] = rect;
  box.style.transform = `translate(${view.tx + x0 * natW * view.scale}px, ${view.ty + y0 * natH * view.scale}px)`;
  box.style.width = `${(x1 - x0) * natW * view.scale}px`;
  box.style.height = `${(y1 - y0) * natH * view.scale}px`;
}

// curva: x = posizione del focheggiatore, y = nitidezza (scala dal minimo al massimo della passata in corso)
let afChartGeom = null;   // funzioni di scala dell'ultimo disegno, per trovare il punto sotto il puntatore
const AF_W = 400, AF_H = 190;   // dimensioni del grafico (viewBox)
// Zoom del grafico: intervallo mostrato e animazione verso quello nuovo (ease-out). Si anima solo quando l'intervallo
// cambia molto (inizio della passata fine dopo la ricerca ampia); gli allargamenti di un punto alla volta no.
let afView = null, afAnim = null, afAnimRaf = 0;
function afZoom(x0, x1, olds) {
  const now = performance.now();
  if (!afView || !olds.length) { afView = [x0, x1]; afAnim = null; return afView; }
  const [v0, v1] = afAnim ? afAnim.to : afView;
  if (v0 !== x0 || v1 !== x1) {
    const big = (x1 - x0) < 0.6 * (v1 - v0);
    if (big && !afAnim) afAnim = { from: afView.slice(), to: [x0, x1], t0: now };
    else if (afAnim) afAnim.to = [x0, x1];
    else afView = [x0, x1];
  }
  if (afAnim) {
    const k = Math.min(1, (now - afAnim.t0) / 700), e = 1 - Math.pow(1 - k, 3);
    afView = [afAnim.from[0] + (afAnim.to[0] - afAnim.from[0]) * e, afAnim.from[1] + (afAnim.to[1] - afAnim.from[1]) * e];
    if (k >= 1) afAnim = null;
    else { cancelAnimationFrame(afAnimRaf); afAnimRaf = requestAnimationFrame(drawAfChart); }
  }
  return afView;
}
function drawAfChart() {
  afChartGeom = null;
  const svg = $("af-chart");
  const a = afState || {};
  const pts = (a.points || []).slice();
  const W = AF_W, H = AF_H, L = 10, R = 10, T = 24, B = 26;
  const ns = "http://www.w3.org/2000/svg";
  svg.replaceChildren();
  const el = (tag, attrs, text) => {
    const e = document.createElementNS(ns, tag);
    for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
    if (text != null) e.textContent = text;
    svg.appendChild(e);
    return e;
  };
  for (let i = 0; i <= 3; i++) el("line", { class: "grid", x1: L, x2: W - R, y1: T + ((H - T - B) * i) / 3, y2: T + ((H - T - B) * i) / 3 });
  const cps = (a.confirm_points || []).slice();
  const prevs = (a.prev_passes || []).filter((ps) => ps && ps.length);   // passate finite, dalla più vecchia
  const olds = prevs.flat();
  if (!pts.length && !olds.length) {
    afView = null;
    el("text", { x: W / 2, y: H / 2 + 4, "text-anchor": "middle" }, t("La curva della nitidezza compare qui, scatto per scatto"));
    return;
  }
  // prima del primo punto della passata fine si vede ancora tutta la ricerca ampia
  const xs = (pts.length ? pts : olds).map((p) => p.pos)
    .concat(cps.map((p) => p.pos), a.target != null ? [a.target] : [], a.best != null ? [a.best] : []);
  let x0 = Math.min(...xs), x1 = Math.max(...xs);
  if (x1 === x0) { x0 -= 1; x1 += 1; }
  // zoom animato: quando l'intervallo cambia molto (dalla ricerca ampia alla passata fine) ci si arriva in 0,7 s
  [x0, x1] = afZoom(x0, x1, olds);
  const ver = a.verify && a.state === "done" ? a.verify : null;
  // scala verticale: la passata in corso e, delle passate precedenti, solo i punti dentro la zona mostrata
  const inView = olds.filter((p) => p.pos >= x0 && p.pos <= x1);
  const vs = pts.map((p) => p.v).concat(ver && !ver.shot ? [ver.v] : [], (pts.length ? inView : olds).map((p) => p.v));
  const vmin = Math.min(...vs), vmax = Math.max(...vs), span = vmax - vmin || 1;
  const top = Math.max(...(pts.length ? pts : olds).map((p) => p.v)) || 1;   // le percentuali sono sul massimo della passata
  const X = (pos) => L + ((pos - x0) / (x1 - x0)) * (W - L - R);
  const Y = (v) => T + (1 - (v - vmin) / span) * (H - T - B);
  // area del grafico: i punti fuori dall'intervallo (ricerca ampia, durante lo zoom) non escono dai bordi
  const clip = document.createElementNS(ns, "clipPath");
  clip.setAttribute("id", "af-clip");
  const cr = document.createElementNS(ns, "rect");
  for (const [k, v] of Object.entries({ x: L - 6, y: 0, width: W - L - R + 12, height: H - B + 6 })) cr.setAttribute(k, v);
  clip.appendChild(cr);
  svg.appendChild(clip);
  // passate precedenti sotto quella in corso: la più recente un po' visibile, le altre sempre più tenui
  prevs.forEach((ps, i) => {
    const g = document.createElementNS(ns, "g");
    g.setAttribute("class", "old");
    g.setAttribute("opacity", String(0.38 * Math.pow(0.6, prevs.length - 1 - i)));
    g.setAttribute("clip-path", "url(#af-clip)");
    const os = ps.slice().sort((p, q) => p.pos - q.pos);
    const pl = document.createElementNS(ns, "polyline");
    pl.setAttribute("class", "curve");
    pl.setAttribute("points", os.map((p) => `${X(p.pos).toFixed(1)},${Y(p.v).toFixed(1)}`).join(" "));
    g.appendChild(pl);
    for (const p of os) {
      const c = document.createElementNS(ns, "circle");
      for (const [k, v] of Object.entries({ class: "pt coarse", cx: X(p.pos), cy: Y(p.v), r: 3.5 })) c.setAttribute(k, v);
      g.appendChild(c);
    }
    svg.appendChild(g);
  });
  const sorted = pts.slice().sort((p, q) => p.pos - q.pos);
  el("polyline", { class: "curve", points: sorted.map((p) => `${X(p.pos).toFixed(1)},${Y(p.v).toFixed(1)}`).join(" ") });
  if (a.busy && a.target != null && a.phase !== "moving") el("line", { class: "target", x1: X(a.target), x2: X(a.target), y1: T - 6, y2: H - B });
  const coarse = a.phase === "coarse";
  const last = pts[pts.length - 1];
  for (const p of pts) {
    el("circle", { class: `pt${coarse ? " coarse" : ""}${p === last && a.busy ? " last" : ""}`, cx: X(p.pos), cy: Y(p.v), r: coarse ? 4.5 : 3.2 });
  }
  // conferma con scatti veri: hanno una scala diversa dal live, il più nitido si disegna alla stessa altezza del
  // massimo della curva del live
  const cmax = Math.max(0, ...cps.map((p) => p.v)) || 1;
  const Yc = (v) => Y(vmin + (v / cmax) * (vmax - vmin));
  if (cps.length) {
    const cs = cps.slice().sort((p, q) => p.pos - q.pos);
    el("polyline", { class: "ccurve", points: cs.map((p) => `${X(p.pos).toFixed(1)},${Yc(p.v).toFixed(1)}`).join(" ") });
    for (const p of cps) el("rect", { class: "cpt", x: X(p.pos) - 4, y: Yc(p.v) - 4, width: 8, height: 8 });
  }
  if (ver) {   // scatto di verifica: rombo verde sulla posizione scelta
    const cx = X(ver.pos), cy = ver.shot && cps.length ? Yc(ver.v) : Y(ver.v), r = 5.5;
    el("polygon", { class: "verify", points: `${cx},${cy - r} ${cx + r},${cy} ${cx},${cy + r} ${cx - r},${cy}` });
  }
  if (a.best != null && (a.phase === "moving" || a.phase === "verify" || a.state === "done")) {
    el("line", { class: "best", x1: X(a.best), x2: X(a.best), y1: T - 8, y2: H - B });
    const right = X(a.best) > W * 0.6;
    el("text", { class: "best-lbl", x: X(a.best) + (right ? -5 : 5), y: 13, "text-anchor": right ? "end" : "start" }, fmtNum(a.best));
  }
  // valori del punto sotto il puntatore
  const isC = typeof afHover === "string" && afHover.startsWith("c");
  const hov = afHover === "verify" ? ver : isC ? cps[Number(afHover.slice(1))] : Number.isInteger(afHover) ? pts[afHover] : null;
  if (hov) {
    const shotScale = isC || (afHover === "verify" && ver.shot && cps.length);
    const pct = fmtNum((hov.v / (shotScale ? cmax : top)) * 100);
    const label = afHover === "verify"
      ? t("verifica · posizione {pos} · {pct} %", { pos: fmtNum(hov.pos), pct })
      : isC ? t("scatto vero {i} · posizione {pos} · {pct} %", { i: Number(afHover.slice(1)) + 1, pos: fmtNum(hov.pos), pct })
        : t("scatto {i} · posizione {pos} · {pct} %", { i: afHover + 1, pos: fmtNum(hov.pos), pct });
    const tx = el("text", { class: "tip-txt", x: 0, y: 0 }, label);
    const w = tx.getComputedTextLength ? tx.getComputedTextLength() + 12 : label.length * 6;
    const hy = shotScale ? Yc(hov.v) : Y(hov.v);
    let bx = X(hov.pos) - w / 2, by = hy - 26;
    bx = Math.max(2, Math.min(W - w - 2, bx));
    if (by < 2) by = hy + 10;
    const box = document.createElementNS(ns, "rect");
    for (const [k, v] of Object.entries({ class: "tip-box", x: bx, y: by, width: w, height: 18, rx: 4 })) box.setAttribute(k, v);
    svg.insertBefore(box, tx);
    tx.setAttribute("x", bx + 6);
    tx.setAttribute("y", by + 13);
    el("circle", { class: "pt-hover", cx: X(hov.pos), cy: hy, r: 6 });
  }
  afChartGeom = { X, Y, Yc, pts, cps, ver };
  el("text", { x: L, y: H - 8 }, fmtNum(x0));
  el("text", { x: W - R, y: H - 8, "text-anchor": "end" }, fmtNum(x1));
  if (a.step) el("text", { x: W / 2, y: H - 8, "text-anchor": "middle" }, t("passo {s}", { s: fmtNum(a.step) }));
}

// Testi e classi riscritti solo se cambiano: renderAf gira a ogni messaggio di stato (4 volte al secondo) e in WebKit
// riscrivere il testo di un pulsante mentre lo si preme fa perdere il clic (Avvia/Rifai andava premuto più volte).
function setText(el, text) { if (el.textContent !== text) el.textContent = text; }
function setClass(el, cls) { if (el.className !== cls) el.className = cls; }

function renderAf() {
  const a = afState || {};
  const f = (lastState && lastState.focuser) || {};
  const ready = camState.connected && f.connected;
  const busy = afBusy();
  $("af-btn").disabled = !ready && !busy && !afPanelOpen;
  stage.classList.toggle("af-mode", afPanelOpen && !busy);
  $("af-panel").classList.toggle("hidden", !(afPanelOpen || busy));
  const cfg = (lastState && lastState.settings && lastState.settings.autofocus) || {};
  const mode = a.mode || "precise";
  for (const b of document.querySelectorAll("[data-af-mode]")) {
    b.setAttribute("aria-pressed", String(b.dataset.afMode === mode));
    b.disabled = busy;
  }
  $("af-coarse-chip").setAttribute("aria-pressed", String(!!cfg.coarse));
  $("af-coarse-chip").disabled = busy;
  const mused = (((a.modes || {})[mode]) || {}).used;
  setText($("af-mode-sum"), afModeSummary(mused));
  renderTravel(a, f, mode);
  const max = Math.max(64, Math.min(2048, Math.floor((refW() || 2048) / 2)));
  if (Number($("af-size").max) !== max) { $("af-size").max = max; setAfSize(afSizePx, false); }
  $("af-size").disabled = busy;
  const seqBusy = lastState && (["running", "paused", "stopping"].includes(lastState.sequence.state) || lastState.calibration.busy);
  $("af-start").disabled = busy || !ready || !afRoi || !natW || seqBusy;
  setText($("af-start"), a.state === "done" || a.state === "failed" ? t("Rifai") : t("Avvia"));
  $("af-start").classList.toggle("hidden", busy);
  $("af-stop").classList.toggle("hidden", !busy);
  $("af-stop").disabled = a.state === "stopping";
  const doneHere = a.state === "done" && !busy && a.best != null && f.connected && f.position === a.best && !f.moving;
  $("af-use").classList.toggle("hidden", !doneHere);
  // stato
  const st = $("af-status");
  let cls = "af-status";
  let text = "";
  if (busy) {
    const n = Math.min((a.index || 0) + 1, a.total || 0);
    const pos = a.target != null ? fmtNum(a.target) : "—";
    if (a.state === "stopping") text = t("Arresto…");
    else if (a.phase === "coarse") text = t("Ricerca ampia · scatto {i} di {n} · posizione {pos}", { i: n, n: a.total, pos });
    else if (a.phase === "fine" && a.passes > 1) text = t("Passata {k} di {m} · scatto {i} di {n} · posizione {pos}", { k: a.pass_no, m: a.passes, i: n, n: a.total, pos });
    else if (a.phase === "fine") text = t("Passata fine · scatto {i} di {n} · posizione {pos}", { i: n, n: a.total, pos });
    else if (a.phase === "confirm") text = t("Conferma con scatti veri · scatto {i} di {n} · posizione {pos}", { i: n, n: a.total, pos });
    else text = a.message || t("Autofocus…");
  } else if (a.state === "done") {
    cls += " ok";
    text = t("Fuoco a {pos}", { pos: fmtNum(a.best) });
    if (a.verify) text += " · " + t("verifica {pct} %", { pct: fmtNum(a.verify.ratio * 100) });
    if (a.fit && a.fit.width) text += " · " + t("picco largo {w} passi", { w: fmtNum(a.fit.width) });
  } else if (a.state === "failed" || a.state === "error") {
    cls += " bad";
    text = a.message;
  } else if (a.state === "idle" && a.message && afRevSeen != null) text = a.message;
  setClass(st, cls);
  setText(st, text);
  setText($("af-warn"), a.warning || "");
  $("af-warn").classList.toggle("hidden", !a.warning);
  let hint = "";
  if (!ready) hint = t("Collega fotocamera e focheggiatore per usare l'autofocus.");
  else if (!busy && !afRoi) hint = t("Clic sul dettaglio da mettere a fuoco, poi Avvia.");
  else if (!busy) hint = t("Puoi spostare l'area con un altro clic e cambiarne il lato con [ e ].");
  setText($("af-hint"), hint);
  $("af-hint").classList.toggle("hidden", !hint);
  drawAfChart();
  drawAfRoi();
}

// riassunto di un modo: «live view · 2 passate · conferma con 3 scatti veri» (come in Configurazione)
// «Veloce|modo»: chiave a parte da «Veloce» della velocità del motore (vedi app.js)
document.querySelector("[data-af-mode=fast]").textContent = t("Veloce|modo").split("|")[0];

function afModeSummary(u) {
  if (!u) return "";
  const parts = [u.source === "shot" ? t("scatti veri") : t("live view"),
    u.passes > 1 ? t("{n} passate", { n: u.passes }) : t("1 passata")];
  if (u.source !== "shot" && u.confirm > 0) parts.push(t("conferma con {n} scatti veri", { n: u.confirm }));
  return parts.join(" · ");
}

// Corsa: prima di Avvia quella prevista attorno alla posizione attuale; durante e dopo, il tratto percorso. La barra
// va da −escursione massima a +escursione massima attorno alla partenza (oltre, l'autofocus si ferma da solo).
function renderTravel(a, f, mode) {
  const busyOrDone = a.start_pos != null && (a.busy || ["done", "failed", "error"].includes(a.state));
  const tr = (((a.modes || {})[mode]) || {}).travel || a.travel || {};
  const start = busyOrDone ? a.start_pos : f.position;
  const M = busyOrDone && a.max_travel ? a.max_travel : tr.max, P = tr.planned;
  const box = $("af-travel");
  box.classList.toggle("hidden", !(f.connected && start != null && M));
  if (!(f.connected && start != null && M)) return;
  const frac = (pos) => Math.max(0, Math.min(1, (pos - (start - M)) / (2 * M)));
  const place = (el, a0, b0) => { el.style.left = `${frac(a0) * 100}%`; el.style.width = `${Math.max(0, frac(b0) - frac(a0)) * 100}%`; };
  place($("af-bar-plan"), start - P, start + P);
  const seen = a.visited && a.visited.length === 2 && busyOrDone ? a.visited : null;
  $("af-bar-seen").classList.toggle("hidden", !seen);
  if (seen) place($("af-bar-seen"), seen[0], seen[1]);
  $("af-bar-now").style.left = `${frac(f.position) * 100}%`;
  const um = (lastState && lastState.um_per_step) || 0;
  const umTxt = (n) => (um ? ` (${fmtNum((n * um) / 1000, n * um >= 1000 ? 2 : 3)} mm)` : "");
  // verso il campione: con «decreasing» avvicinarsi al campione vuol dire passi decrescenti
  const toward = ((lastState && lastState.settings && lastState.settings.toward_specimen) || "decreasing") === "decreasing" ? -1 : 1;
  let text = busyOrDone && seen
    ? t("Percorso: da {a} a {b} · al massimo ± {m} passi{um} dalla partenza", { a: fmtNum(seen[0]), b: fmtNum(seen[1]), m: fmtNum(M), um: umTxt(M) })
    : t("Corsa prevista ± {p} passi{up} · al massimo ± {m}{um}", { p: fmtNum(P), up: umTxt(P), m: fmtNum(M), um: umTxt(M) });
  text += " · " + t("verso il campione fino a {pos}", { pos: fmtNum(start + toward * M) });
  setText($("af-travel-txt"), text);
}

function onAfState(st) {
  const prev = afState;
  afState = st.autofocus || null;
  const a = afState || {};
  const cfgSize = st.settings && st.settings.autofocus && st.settings.autofocus.roi_px;
  if (cfgSize && afRevSeen == null && !prev) setAfSize(cfgSize, false);
  // autofocus partito (anche da un'altra finestra): pannello aperto; con gli scatti veri si seguono gli scatti
  if (afRevSeen != null && a.rev > afRevSeen) {
    afPanelOpen = true;
    afView = null; afAnim = null;   // grafico nuovo: niente zoom dal grafico dell'autofocus precedente
    if (a.source === "shot") {
      setFollow(true);
      if (liveOn) setLiveView(false, { restore: false });
    }
  }
  if (a.rev != null) afRevSeen = a.rev;
  renderAf();
}

$("af-btn").onclick = () => (afPanelOpen ? closeAf() : openAf());
$("af-close").onclick = closeAf;
$("af-size").addEventListener("input", (e) => setAfSize(Number(e.target.value)));
for (const b of document.querySelectorAll("[data-af-mode]")) {
  b.onclick = () => afSaveSettings({ mode: b.dataset.afMode }).catch((e) => notice(e.message));
}
$("af-coarse-chip").onclick = () => {
  const cfg = (lastState && lastState.settings && lastState.settings.autofocus) || {};
  afSaveSettings({ coarse: !cfg.coarse }).catch((e) => notice(e.message));
};
$("af-start").onclick = async () => {
  const roi = afRoiRect();
  if (!roi) return;
  $("af-start").disabled = true;
  try {
    const v = (lastState && lastState.autofocus) || {}, src = (((v.modes || {})[v.mode] || {}).used || {}).source || "live";
    if (src === "shot") { setFollow(true); if (liveOn) setLiveView(false, { restore: false }); }
    await post("/api/autofocus/start", { roi });
  } catch (e) {
    notice(e.message);
  }
  renderAf();
};
$("af-stop").onclick = () => post("/api/autofocus/stop").catch((e) => notice(e.message));
const useAs = (mark) => {
  const pos = afState && afState.best;
  if (pos == null) return;
  if (!("BroadcastChannel" in window)) { notice(t("La finestra principale non è raggiungibile: imposta la posizione a mano")); return; }
  new BroadcastChannel("focus-stack").postMessage({ mark, position: pos });
  notice(mark === "start" ? t("Inizio della pila: {pos}", { pos: fmtNum(pos) }) : t("Fine della pila: {pos}", { pos: fmtNum(pos) }));
};
$("af-use-start").onclick = () => useAs("start");
$("af-use-end").onclick = () => useAs("end");
// valori al passaggio del mouse: il punto più vicino al puntatore (entro 14 unità del grafico)
$("af-chart").addEventListener("pointermove", (e) => {
  const g = afChartGeom, svg = $("af-chart");
  if (!g) return;
  const r = svg.getBoundingClientRect(), k = AF_W / r.width;
  const mx = (e.clientX - r.left) * k, my = (e.clientY - r.top) * k;
  let best = null, bestD = 14;
  g.pts.forEach((p, i) => { const d = Math.hypot(g.X(p.pos) - mx, g.Y(p.v) - my); if (d < bestD) { bestD = d; best = i; } });
  g.cps.forEach((p, i) => { const d = Math.hypot(g.X(p.pos) - mx, g.Yc(p.v) - my); if (d < bestD) { bestD = d; best = `c${i}`; } });
  const vy = g.ver ? (g.ver.shot && g.cps.length ? g.Yc(g.ver.v) : g.Y(g.ver.v)) : 0;
  if (g.ver && Math.hypot(g.X(g.ver.pos) - mx, vy - my) < bestD) best = "verify";
  if (best !== afHover) { afHover = best; drawAfChart(); }
});
$("af-chart").addEventListener("pointerleave", () => { if (afHover != null) { afHover = null; drawAfChart(); } });
// i clic sul pannello non spostano l'immagine
$("af-panel").addEventListener("pointerdown", (e) => e.stopPropagation());
$("af-panel").addEventListener("dblclick", (e) => e.stopPropagation());
$("af-panel").addEventListener("wheel", (e) => e.stopPropagation());

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
  drag = { x: e.clientX, y: e.clientY, tx: view.tx, ty: view.ty, moved: false };
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
  if (Math.hypot(e.clientX - drag.x, e.clientY - drag.y) > 4) drag.moved = true;
  view.tx = drag.tx + (e.clientX - drag.x);
  view.ty = drag.ty + (e.clientY - drag.y);
  view.mode = "free";
  apply();
});
const endDrag = () => { drag = null; stage.classList.remove("dragging"); };
stage.addEventListener("pointerup", (e) => {
  // modalità autofocus: un clic (senza trascinare) mette l'area sul punto
  if (drag && !drag.moved && afPanelOpen && !afBusy()) afPlace(e.clientX, e.clientY);
  endDrag();
});
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
  if (afPanelOpen) return;   // con l'autofocus aperto il clic sceglie l'area
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
  else if (k === "a" || k === "A") { if (!$("af-btn").disabled) $("af-btn").click(); }
  else if (k === "Escape" && afPanelOpen) closeAf();
  else if ((k === "[" || k === "]") && afPanelOpen && !afBusy()) setAfSize(afSizePx * (k === "]" ? 1.25 : 0.8));
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
