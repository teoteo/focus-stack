"use strict";
const $ = (id) => document.getElementById(id);
const $$ = (sel) => document.querySelectorAll(sel);
let S = null;              // ultimo stato dal server
let formLoaded = false;    // i campi vengono popolati dal server una sola volta
let camSettingsSig = "", presetSig = "", motorSig = "", lastShotId = null;
let jogSize = 100, jogSizesSig = "";
const HOLD_DELAY = 400;     // ms: oltre, il pulsante tenuto premuto diventa movimento continuo

// ---------------- utilità ----------------
function toast(msg, err = false) {
  const t = $("toast");
  t.textContent = msg;
  t.className = "show" + (err ? " err" : "");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => (t.className = ""), err ? 5000 : 2200);
}

async function api(path, body, method = "POST") {
  const res = await fetch(path, {
    method, headers: { "Content-Type": "application/json", "X-FocusStack": "1" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  let data = null;
  try { data = await res.json(); } catch { /* risposta vuota */ }
  if (!res.ok) {
    const d = data && data.detail;
    throw new Error(typeof d === "string" ? d : Array.isArray(d) ? t("Valore non valido") : res.statusText);
  }
  return data;
}

async function act(btn, fn, okMsg) {
  if (btn) btn.disabled = true;
  try {
    const r = await fn();
    if (okMsg) toast(okMsg);
    return r;
  } catch (e) {
    toast(e.message, true);
  } finally {
    if (btn) btn.disabled = false;
  }
}

const num = (id) => Number($(id).value);
const optNum = (id) => ($(id).value.trim() === "" ? null : Number($(id).value));
// µm per pixel misurati (Ottica › Scala sul campione): campo di testo, accetta "0,3912" e "0.3912".
// null se vuoto, NaN se non è un numero maggiore di zero
function pxMeasured() {
  const raw = $("o-pxcal").value.trim();
  if (!raw) return null;
  const v = /^[0-9]*[.,]?[0-9]+$/.test(raw) ? Number(raw.replace(",", ".")) : NaN;
  return v > 0 ? v : NaN;
}
const fmtInt = (n) => (n == null ? "—" : Number(n).toLocaleString(LOCALE));
const fmtTime = (s) => {
  if (s == null || !isFinite(s)) return "—";
  s = Math.round(s);
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
  return h ? `${h}h ${String(m).padStart(2, "0")}m` : m ? `${m}m ${String(r).padStart(2, "0")}s` : `${r}s`;
};
const umPerStep = () => (S && S.um_per_step) || 0;
const fmtUm = (steps) => {
  const um = steps * umPerStep();
  if (!umPerStep()) return "";
  return Math.abs(um) >= 1000 ? `${fmtNum(um / 1000, 3)} mm` : `${fmtNum(um, Math.abs(um) < 10 ? 2 : 1)} µm`;
};
const running = () => S && ["running", "paused", "stopping"].includes(S.sequence.state);
const towardSign = () => (S && S.settings.toward_specimen === "increasing" ? 1 : -1);

// ---------------- tema ----------------
function applyTheme(t) {
  document.documentElement.dataset.theme = t;
  document.querySelector('meta[name="theme-color"]').content = t === "light" ? "#eef1f5" : "#0d1117";
  if (window.FSNative) FSNative.theme(t);
}
try { applyTheme(localStorage.getItem("fs-theme") || "dark"); } catch { applyTheme("dark"); }

// ---------------- WebSocket di stato ----------------
let serverStopped = false, wsConn = null, wsSeq = 0;
const wsWaiting = new Map();
function connectWS() {
  const ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = (ev) => {
    const data = JSON.parse(ev.data);
    if (data && "reply" in data) { const done = wsWaiting.get(data.reply); if (done) done(data); return; }
    S = data;
    // «Ferma live» premuto in un'altra finestra
    if (liveStopRev != null && data.live_stop_rev > liveStopRev && liveOn) setLive(false);
    liveStopRev = data.live_stop_rev ?? liveStopRev;
    // scatto di prova con il live acceso: si mostra lo scatto; il live riparte quando si muove il focheggiatore
    const park = data.live_park || {};
    if (liveParkRev != null && park.rev > liveParkRev && liveOn) {
      setLive(false);
      liveResume = { pos: park.pos };
      toast(t("Scatto di prova: il live view riparte quando muovi il focheggiatore"));
    }
    liveParkRev = park.rev ?? liveParkRev;
    render();
  };
  ws.onopen = () => { wsConn = ws; setDot("st-link", "on"); };
  ws.onclose = () => {
    if (wsConn === ws) wsConn = null;
    for (const done of wsWaiting.values()) done({ error: t("Connessione con il server interrotta") });
    setDot("st-link", ""); setTimeout(checkServer, 1500);
  };
}

// Comando sulla WebSocket di stato (risposta con lo stesso id); null se non è aperta. Il tieni premuto passa da
// qui: le richieste fetch possono restare in coda dietro i flussi del live view (Safari: 6 connessioni per host).
function wsCall(msg) {
  if (!wsConn || wsConn.readyState !== WebSocket.OPEN) return null;
  const id = ++wsSeq;
  wsConn.send(JSON.stringify({ ...msg, id }));
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => wsWaiting.get(id)({ error: t("Il server non risponde") }), 5000);
    wsWaiting.set(id, (r) => {
      clearTimeout(timer); wsWaiting.delete(id);
      if (r.error) reject(new Error(r.error)); else resolve(r);
    });
  });
}
const holdCall = (body) => wsCall({ type: "hold", ...body }) || api("/api/focuser/hold", body);

// Se il server non risponde più (app Focus Stack chiusa) mostra la schermata "server spento";
// quando torna disponibile (app riaperta) ricarica la pagina.
async function checkServer() {
  try {
    await fetch("/api/state", { cache: "no-store" });
    if (serverStopped) location.reload();
    else connectWS();
  } catch {
    if (!serverStopped) {
      serverStopped = true;
      if (viewerWin && !viewerWin.closed) viewerWin.close();
      document.title = updatingApp ? t("Focus Stack — aggiornamento") : t("Focus Stack — server spento");
      $("shutdown-screen").classList.remove("hidden");
    }
    setTimeout(checkServer, 2000);
  }
}

const setDot = (id, cls) => ($(id).className = "dot-label " + cls);
const setChip = (id, text, cls = "") => { const c = $(id); c.textContent = text; c.className = "chip " + cls; };

// ---------------- rendering ----------------
// Ogni sezione viene disegnata separatamente: un errore in una non blocca le altre.
function safe(name, fn) {
  try { fn(); } catch (e) { console.error(`[FocusStack] render ${name}:`, e); }
}

function render() {
  const f = S.focuser, c = S.camera, q = S.sequence, run = running();
  if (!S.settings.mechanics || !("bounds" in f || !f.connected)) {
    // server avviato con una versione precedente del codice
    $("alarm").classList.remove("hidden");
    $("alarm-text").textContent = t("Il server in esecuzione è di una versione precedente: chiudi Focus Stack e riaprilo.");
    return;
  }
  // lingua cambiata (anche da un'altra finestra): ricarica per avere testi e numeri nella lingua nuova
  if (S.language && S.language !== LANG) { location.reload(); return; }
  if (!formLoaded) safe("form", () => loadForms(S.settings));

  // barra superiore
  setDot("st-focuser", f.connected ? (f.moving ? "busy" : "on") : "");
  setDot("st-camera", c.connected ? (c.busy ? "busy" : "on") : "");
  const hasTemp = f.connected && f.temperature != null;
  $("st-temp").classList.toggle("hidden", !hasTemp);
  if (hasTemp) $("st-temp").textContent = `${fmtNum(f.temperature, 1)} °C`;
  const alarm = S.alarm || (S.code_stale
    ? t("Il codice dell'app è cambiato: chiudi Focus Stack e riaprilo, poi ricarica la pagina.") : "");
  $("alarm").classList.toggle("hidden", !alarm);
  $("alarm-text").textContent = alarm;

  safe("focheggiatore", () => renderFocuser(f, run));
  const calBusy = !!(S.calibration && S.calibration.busy);   // calibrazione o esposizione automatica in corso
  safe("fotocamera", () => renderCamera(c, run || calBusy));
  safe("sequenza", () => renderSequence(f, c, q, run));
  safe("ultimo scatto", renderLastShot);
  safe("live view", () => renderLive(c, run || calBusy));
  safe("calibrazione", () => renderCalibration(c, run));
  safe("configurazione", () => renderConfig(f));
  safe("iphone", renderRemote);
  safe("preset", renderPresets);
  safe("profili ottici", renderOpticsProfiles);
  safe("registro", renderLog);
  safe("aggiornamenti", renderUpdates);
}

// ---------------- aggiornamenti (app da GitHub, firmware incluso nell'app) ----------------
function renderUpdates() {
  const a = S.app || {}, fw = S.firmware_update || {}, f = S.focuser;
  const ver = a.version ?? "?";
  $("up-app").textContent = a.available ? t("{v} → disponibile {latest}", { v: ver, latest: a.latest })
    : a.error ? t("{v} (controllo non riuscito: verifica la connessione a internet)", { v: ver })
    : a.latest ? t("{v} (aggiornata)", { v: ver }) : ver;
  // Note della versione su GitHub: della nuova se c'è un aggiornamento, altrimenti di quella installata
  const notesVer = a.available ? a.latest : ver !== "sviluppo" && ver !== "?" ? ver : null;
  const notes = $("up-notes");
  notes.classList.toggle("hidden", !notesVer);
  if (notesVer) {
    notes.href = `https://github.com/teoteo/focus-stack/releases/tag/v${notesVer}`;
    notes.textContent = a.available ? t("Novità della versione {v}", { v: notesVer }) : t("Note della versione {v}", { v: notesVer });
  }
  const fwAvail = fw.bundled ? " → " + t("disponibile build {b}", { b: fw.bundled }) : "";
  let fwText;
  if (!f.connected || f.simulated) fwText = t("collega il focheggiatore per controllarlo");
  else if (fw.installed == null) fwText = t("originale myFocuserPro2 {fw}", { fw: f.firmware ?? "" }) + fwAvail;
  else fwText = t("build {b}", { b: fw.installed }) + (fw.available ? fwAvail : " " + t("(aggiornato)"));
  $("up-fw").textContent = fwText;
  $("fw-update").disabled = !fw.available || fw.busy || running();
  $("fw-progress-box").classList.toggle("hidden", !fw.busy && !fw.error);
  $("fw-progress").style.width = `${Math.round((fw.progress || 0) * 100)}%`;
  $("fw-phase").textContent = fw.error ? t("Errore: {e}", { e: fw.error }) : fw.busy ? `${fw.phase}… ${Math.round((fw.progress || 0) * 100)}%` : "";

  // Aggiornamento dell'app: la barra in alto e il pulsante qui sotto seguono la stessa regola.
  // Se c'è una versione nuova restano SEMPRE visibili: cambia solo cosa dicono (disponibile,
  // installazione in corso, installazione non riuscita), così l'avviso non sparisce mai in silenzio.
  const app = appUpdateView(a);
  const inst = $("up-install");
  inst.classList.toggle("hidden", !app);
  if (app) {
    inst.textContent = app.label;
    inst.disabled = app.disabled;
    inst.onclick = app.action;
  }

  // barra in alto: prima l'app, poi il firmware
  const bar = $("update-bar"), btn = $("update-btn");
  if (app) {
    $("update-text").textContent = app.text;
    btn.textContent = app.label;
    btn.disabled = app.disabled;
    btn.onclick = app.action;
    bar.classList.remove("hidden");
  } else if (fw.available && !fw.busy) {
    $("update-text").textContent = t("È disponibile un aggiornamento del firmware del focheggiatore (build {b}).", { b: fw.bundled });
    btn.textContent = t("Vai agli aggiornamenti");
    btn.disabled = false;
    btn.onclick = () => switchTab("config");
    bar.classList.remove("hidden");
  } else bar.classList.add("hidden");
}

// Cosa mostrare per l'aggiornamento dell'app (null = niente da proporre)
function appUpdateView(a) {
  if (!a.available) return null;
  const github = () => window.open("https://github.com/teoteo/focus-stack/releases/latest");
  if (a.installing && a.progress != null) {
    return { text: t("Scaricamento di Focus Stack {latest}: {p}%", { latest: a.latest, p: Math.floor(a.progress * 100) }),
      label: t("Installazione in corso…"), disabled: true, action: null };
  }
  if (a.installing || updatingApp) {
    return { text: t("Installazione di Focus Stack {latest} in corso: l'app si chiude e si riapre da sola…", { latest: a.latest }),
      label: t("Installazione in corso…"), disabled: true, action: null };
  }
  const label = a.can_install ? (a.install_error ? t("Riprova") : t("Aggiorna e riavvia")) : t("Scarica da GitHub");
  return {
    text: a.install_error || t("È disponibile Focus Stack {latest} (installata {v}).", { latest: a.latest, v: a.version }),
    label, disabled: false, action: a.can_install ? installAppUpdate : github,
  };
}

let updatingApp = false;
async function installAppUpdate() {
  if (running()) return toast(t("Attendi la fine della sequenza"), true);
  if (!confirm(t("Installare Focus Stack {v}?", { v: S.app.latest }) + "\n\n" +
    t("L'app si chiude e si riapre da sola; focheggiatore e fotocamera andranno ricollegati."))) return;
  $("update-btn").disabled = true;
  try {
    await api("/api/app/update");
  } catch (e) {
    $("update-btn").disabled = false;
    return toast(e.message, true);
  }
  updatingApp = true;
  $("shutdown-title").textContent = t("Aggiornamento in corso…");
  $("shutdown-text").textContent = t("Focus Stack si chiude, installa la nuova versione e si riapre da solo. Questa pagina si ricaricherà.");
  $("shutdown-hint").textContent = "";
  $("shutdown-screen").classList.remove("hidden");
}

async function updateFirmware() {
  const fw = S.firmware_update;
  if (!confirm(t("Aggiornare il firmware del focheggiatore alla build {b}?", { b: fw.bundled }) + "\n\n" +
    t("Durante l'aggiornamento (circa 20 secondi) non scollegare il cavo USB. Le impostazioni del focheggiatore restano."))) return;
  try { await api("/api/firmware/update"); } catch (e) { toast(e.message, true); }
}

function renderFocuser(f, run) {
  setChip("f-chip", !f.connected ? t("Disconnesso") : f.moving ? t("In movimento") : t("Fermo"),
    !f.connected ? "" : f.moving ? "busy" : "ok");
  $("f-connect-box").classList.toggle("hidden", f.connected);
  $("f-connected-line").classList.toggle("hidden", !f.connected);
  if (f.connected) {
    $("f-info").textContent = t("{port} · firmware {fw} · max {max}",
      { port: f.simulated ? t("Simulatore") : f.port, fw: f.firmware ?? "?", max: fmtInt(f.max_step) });
  }
  $("f-pos").textContent = f.connected ? fmtInt(f.position) : "—";
  $("f-pos-um").innerHTML = f.connected && umPerStep() ? fmtUm(f.position) : "&nbsp;";

  const [lo, hi] = f.connected ? f.bounds : [S.settings.limit_min, S.settings.limit_max];
  $("f-limits").textContent = `${fmtInt(lo)} – ${hi == null ? "∞" : fmtInt(hi)}`;
  if (f.connected && hi != null) {
    const towardDist = towardSign() < 0 ? f.position - lo : hi - f.position;
    $("f-range-left").textContent = t("verso il campione: {n} passi", { n: fmtInt(towardDist) }) + (umPerStep() ? " · " + fmtUm(towardDist) : "");
  } else $("f-range-left").innerHTML = "&nbsp;";

  renderRail(f, lo, hi);

  renderJogSizes();
  const away = towardSign() < 0 ? "+" : "−", toward = towardSign() < 0 ? "−" : "+";
  // riscritte solo se cambiano: in WebKit cambiare il testo di un pulsante mentre è premuto può far perdere
  // il rilascio (e il movimento continuo non si fermava più)
  const awayTxt = `${t("Allontana")}  ${away}${fmtInt(jogSize)}`, towardTxt = `${t("Avvicina")}  ${toward}${fmtInt(jogSize)}`;
  if ($("jog-away-label").textContent !== awayTxt) $("jog-away-label").textContent = awayTxt;
  if ($("jog-toward-label").textContent !== towardTxt) $("jog-toward-label").textContent = towardTxt;
  $("jog-um").innerHTML = umPerStep() ? t("{n} passi = {um}", { n: fmtInt(jogSize), um: fmtUm(jogSize) }) : "&nbsp;";

  const dis = !f.connected || run;
  ["jog-away", "jog-toward", "f-goto"].forEach((id) => ($(id).disabled = dis));
  updateGotoBtn();
  $("f-halt").disabled = !f.connected;
}

function renderRail(f, lo, hi) {
  const seqA = num("s-start"), seqB = num("s-end");
  const pts = [lo, hi ?? lo, seqA, seqB];
  if (f.connected) pts.push(f.position);
  let min = Math.min(...pts), max = Math.max(...pts);
  const pad = Math.max(1, (max - min) * 0.08);
  min -= pad; max += pad;
  const pct = (v) => `${((v - min) / (max - min)) * 100}%`;
  $("rail-forb-l").style.width = pct(lo);
  $("rail-forb-r").style.width = hi == null ? "0" : `${100 - parseFloat(pct(hi))}%`;
  const a = Math.min(seqA, seqB), b = Math.max(seqA, seqB);
  $("rail-seq").style.left = pct(a);
  $("rail-seq").style.width = `${parseFloat(pct(b)) - parseFloat(pct(a))}%`;
  $("rail-pos").style.display = f.connected ? "" : "none";
  if (f.connected) $("rail-pos").style.left = pct(f.position);

  // tacche degli scatti (solo se non troppe)
  const step = Math.max(1, Math.abs(num("s-step")));
  const n = shotCount();
  const key = `${a}:${b}:${step}:${min}:${max}:${S.sequence.index}`;
  const ticks = $("rail-ticks");
  if (ticks.dataset.key !== key) {
    ticks.dataset.key = key;
    ticks.innerHTML = "";
    if (n <= 150) {
      const dir = seqB >= seqA ? 1 : -1;
      for (let i = 0; i < n; i++) {
        const p = i === n - 1 ? seqB : seqA + dir * step * i;
        const t = document.createElement("i");
        t.style.left = pct(p);
        if (running() && i < S.sequence.index) t.className = "done";
        ticks.appendChild(t);
      }
    }
  }
  $("rail-lo").textContent = t("min {n}", { n: fmtInt(lo) });
  $("rail-hi").textContent = hi == null ? t("max firmware") : t("max {n}", { n: fmtInt(hi) });
  $("rail-dir").textContent = towardSign() < 0 ? t("◀ campione") : t("campione ▶");
}

const CAM_FIELDS = { shutterspeed: "c-shutter", iso: "c-iso", aperture: "c-aperture", imageformat: "c-format", capturetarget: "c-target" };

function renderCamera(c, run) {
  $("gp-missing").classList.toggle("hidden", S.gphoto);
  setChip("c-chip", !c.connected ? t("Disconnessa") : c.busy ? t("Scatto…") : t("Pronta"), !c.connected ? "" : c.busy ? "busy" : "ok");
  $("c-connect-box").classList.toggle("hidden", c.connected);
  $("c-connected-line").classList.toggle("hidden", !c.connected);
  if (c.connected) $("c-info").textContent = c.model;   // la fotocamera simulata si chiama già così
  ["c-reload", "c-test"].forEach((id) => ($(id).disabled = !c.connected || run || c.busy));
  $("c-mirror").disabled = run;
  renderMirrorHint();

  const settings = (c.connected && c.settings) || {};
  const sig = JSON.stringify(settings);
  if (sig === camSettingsSig) return;
  camSettingsSig = sig;
  for (const [name, id] of Object.entries(CAM_FIELDS)) {
    const sel = $(id), s = settings[name];
    sel.innerHTML = "";
    if (!s) { sel.add(new Option(c.connected ? t("non disponibile") : "—", "")); sel.disabled = true; continue; }
    const choices = s.choices.length ? [...s.choices] : [s.current];
    if (!choices.includes(s.current)) choices.unshift(s.current);
    for (const ch of choices) sel.add(new Option(ch, ch, false, ch === s.current));
    sel.disabled = s.readonly || !s.choices.length;
  }
  updateSummary();
}

const MIRROR_HINTS = {
  nikon: t("Nikon: l'app imposta il “ritardo di esposizione” della fotocamera al valore disponibile più vicino."),
  canon: t("Canon: attiva il “blocco dello specchio” nel menu della fotocamera (funzioni personalizzate). L'app solleva lo specchio, attende e poi scatta."),
  none: t("Questa fotocamera non ha un ritardo dello specchio controllabile da remoto: l'impostazione viene ignorata."),
};

function renderMirrorHint() {
  const c = S && S.camera, hint = $("c-mirror-hint");
  const show = !!(c && c.connected && num("c-mirror") > 0 && !c.simulated);
  hint.classList.toggle("hidden", !show);
  if (show) hint.textContent = MIRROR_HINTS[c.mirror_method] || MIRROR_HINTS.none;
}

function renderSequence(f, c, q, run) {
  const labels = { idle: t("Pronta"), running: t("In corso"), paused: t("In pausa"), stopping: t("Arresto…"), done: t("Completata"), error: t("Errore") };
  setChip("s-chip", labels[q.state] || q.state,
    { running: "busy", paused: "busy", stopping: "busy", done: "ok", error: "bad" }[q.state] || "");
  const bothOk = f.connected && c.connected;
  $("s-start-btn").disabled = run || !bothOk || !!(S.calibration && S.calibration.busy);
  $("s-start-btn").title = bothOk ? "" : t("Connetti focheggiatore e fotocamera");
  $("s-pause-btn").disabled = !run || q.state === "stopping";
  // solo se cambia: Safari annulla il clic se il testo del pulsante viene sostituito fra pressione e rilascio
  // (render ogni 250 ms: «Riprendi» a volte non arrivava al server)
  const pauseTxt = q.state === "paused" ? `▶\u00a0 ${t("Riprendi")}` : `❚❚\u00a0 ${t("Pausa")}`;
  if ($("s-pause-btn").textContent !== pauseTxt) $("s-pause-btn").textContent = pauseTxt;
  $("s-stop-btn").disabled = !run;
  // bobine spente: il carico può riportare indietro la slitta a ogni fermata (pila tutta sullo stesso piano)
  $("s-coil-warn").classList.toggle("hidden",
    !(f.connected && f.motor && f.motor.coil_power === false && S.settings.coil_during_sequence === false));
  $$("[data-mark]").forEach((b) => (b.disabled = !f.connected || run));
  $("s-finder").disabled = !q.folder || run;
  $$("#card-seq input, #card-seq select").forEach((el) => (el.disabled = run));

  const root = S.settings.output_root || "";
  const home = root.match(/^\/Users\/[^/]+/);
  const pretty = home ? "~" + root.slice(home[0].length) : root;
  // il carattere \u200e mantiene corretto l'ordine dei caratteri con direction: rtl
  $("s-root-label").textContent = "\u200e" + pretty + "\u200e";
  $("s-root-label").title = root;
  $("s-folder").classList.toggle("inactive", $("s-mode").value !== "download");
  $("s-root-choose").disabled = run;

  const total = q.total || shotCount();
  $("s-count-label").textContent = `${q.state === "idle" && !q.total ? 0 : q.index} / ${total}`;
  $("s-eta").textContent = run && q.eta_s != null ? t("restano ~{t}", { t: fmtTime(q.eta_s) }) : "";
  $("s-bar").style.width = `${q.total ? (q.index / q.total) * 100 : 0}%`;
  let txt = "";
  if (run && q.current_target != null) txt = t("Posizione {n}", { n: fmtInt(q.current_target) });
  if (q.message) txt += (txt ? " · " : "") + q.message;
  if (q.folder && !run) txt += (txt ? " · " : "") + q.folder;
  $("s-progress").textContent = txt;

  // nome della pila: dopo una pila finita (completata, interrotta o con errore) si prepara la successiva
  const finished = !run && (q.state !== "idle" || q.total > 0);
  $("s-new").classList.toggle("hidden", !finished);
  $("s-new").disabled = run;
  const safeName = (($("s-name").value.trim() || "stack").replace(/[^\p{L}\p{N}_-]/gu, "_"));
  const last = q.folder ? q.folder.split("/").pop() : "";
  $("s-name-hint").textContent = finished && last
    ? t("Ultima pila: {folder}. Con «Nuova pila» la prossima va in una cartella nuova, anche con lo stesso nome.", { folder: last })
    : t("Cartella: {name}_data-ora", { name: safeName });
}

function renderLastShot() {
  const shot = S.last_shot;
  const thumb = $("last-thumb");
  thumb.classList.toggle("empty", !shot);
  if (!shot) { $("last-meta").innerHTML = ""; return; }
  if (shot.key !== lastShotId) {
    lastShotId = shot.key;
    const img = $("last-img");
    // la conversione da RAW può richiedere un istante: riprova se l'immagine non è pronta
    let tries = 0;
    img.onerror = () => { if (tries++ < 5) setTimeout(() => (img.src = `/api/shots/${shot.id}/image?size=preview&v=${shot.key}&r=${tries}`), 800); };
    img.src = `/api/shots/${shot.id}/image?size=preview&v=${shot.key}`;
    const parts = [`<span><b>${shot.name}</b></span>`];
    if (shot.kind === "sequence") parts.push(`<span>${t("scatto <b>{n}</b>", { n: shotLabel(shot) })}</span>`);
    if (shot.position != null) parts.push(`<span>${t("posizione <b>{n}</b>", { n: fmtInt(shot.position) })}</span>`);
    if (shot.temperature != null) parts.push(`<span><b>${fmtNum(shot.temperature, 1)}</b> °C</span>`);
    parts.push(`<span>${shot.time}</span>`);
    $("last-meta").innerHTML = parts.join("");
  }
}

// ---------------- live view (stream MJPEG del server in un <img>) ----------------
let liveOn = false, liveStartedAt = 0;
let liveStopRev = null;   // ultimo valore visto di live_stop_rev (null fino al primo stato)
// live view messo da parte da uno scatto di prova: {pos} finché il focheggiatore non si muove, poi riparte
let liveParkRev = null, liveResume = null;

// canale fra la finestra principale e il visualizzatore (Safari 15.4+; senza, semplicemente non si parlano)
const windowLink = "BroadcastChannel" in window ? new BroadcastChannel("focus-stack") : null;

function setLive(on) {
  liveOn = on;
  liveResume = null;   // acceso o spento in qualsiasi altro modo: niente ripresa automatica
  liveStartedAt = Date.now();
  const img = $("live-img");
  // togliere src chiude la connessione: il server spegne il live view della fotocamera
  if (on) img.src = `/api/camera/live?t=${liveStartedAt}`;
  else img.removeAttribute("src");
  if (!on && (document.fullscreenElement || document.webkitFullscreenElement)) {
    (document.exitFullscreen || document.webkitExitFullscreen).call(document);
  }
  $("live-btn").setAttribute("aria-pressed", String(on));
  $("live-btn").textContent = on ? t("■ Ferma live") : t("● Live");
  $("last-title").textContent = on ? t("Live view") : t("Ultimo scatto");
  for (const id of ["last-thumb", "last-meta"]) $(id).classList.toggle("hidden", on);
  for (const id of ["live-box", "live-meta"]) $(id).classList.toggle("hidden", !on);
  if (S) renderLive(S.camera, running());
}

let liveShotsPrev = 0;
function renderLive(c, run) {
  $("live-btn").disabled = !c.connected;
  // primo scatto della sequenza: il live view si chiude e il riquadro torna a mostrare l'ultimo scatto.
  // Fino a lì resta acceso, per guardare la slitta che torna all'inizio.
  const q = S.sequence || {}, shots = run ? q.shots || 0 : 0;
  const firstShot = shots > 0 && liveShotsPrev === 0;
  liveShotsPrev = shots;
  if (firstShot && liveOn) { setLive(false); toast(t("Primo scatto della sequenza: live view chiuso, ora segue l'ultimo scatto")); return; }
  if (liveResume && !liveOn) {
    // dopo lo scatto di prova: il live riparte al primo movimento (pulsanti dell'app, tastiera o del focheggiatore)
    const f = S.focuser || {};
    if (!c.connected || run) liveResume = null;
    else if (f.connected && (f.moving || (liveResume.pos != null && f.position !== liveResume.pos))) setLive(true);
  }
  if (!liveOn) return;
  if (!c.connected) { setLive(false); return; }
  // l'errore di uno stream precedente può arrivare ancora per un attimo dopo il riavvio
  if (c.live_error && Date.now() - liveStartedAt > 2000) {
    setLive(false);
    toast(c.live_error, true);
    return;
  }
  const seqPaused = run && !q.live_ok;   // in pausa dall'arrivo al primo piano
  const badge = $("live-badge");
  badge.textContent = seqPaused ? t("IN PAUSA") : c.busy ? t("SCATTO…") : t("LIVE");
  badge.classList.toggle("paused", seqPaused || c.busy);
  $("live-meta").innerHTML = seqPaused
    ? `<span>${t("Live view in pausa durante la sequenza")}</span>`
    : `<span><b>${c.model}</b></span><span>${t("doppio clic: schermo intero")}</span>`;
}

function toggleLiveFullscreen() {
  const box = $("live-box");
  if (document.fullscreenElement || document.webkitFullscreenElement) {
    (document.exitFullscreen || document.webkitExitFullscreen).call(document);
  } else {
    (box.requestFullscreen || box.webkitRequestFullscreen).call(box);
  }
}

function renderConfig(f) {
  const lo = S.settings.limit_min, hi = S.settings.limit_max;
  setChip("lim-chip", hi == null ? t("Superiore = max firmware") : `${fmtInt(lo)} – ${fmtInt(hi)}`, hi == null ? "busy" : "ok");
  $$("[data-limit-here], #lim-zero, #lim-fw, #mo-reload").forEach((b) => (b.disabled = !f.connected || running()));
  $("lim-fw-info").textContent = f.connected ? t("Max attuale nel firmware: {n}", { n: fmtInt(f.max_step) }) : "";
  $("mo-offline").classList.toggle("hidden", !!f.connected);
  setChip("mo-chip", f.connected ? (f.simulated ? t("simulatore") : t("collegato")) : t("non collegato"), f.connected ? "ok" : "bad");
  updateLimDirty();
  renderSettingsSummary();

  // motore
  const motor = (f.connected && f.motor) || {};
  // l'opzione "bobine durante la sequenza" cambia gli avvisi: fa parte della firma
  const sig = JSON.stringify(motor) + f.connected + (S.settings.coil_during_sequence !== false);
  if (sig !== motorSig) {
    motorSig = sig;
    for (const name of ["step_mode", "speed"]) {
      const el = $(`mo-${name}`);
      el.disabled = !(name in motor);
      if (name in motor) el.value = String(motor[name]);
    }
    for (const name of ["coil_power", "reverse", "backlash_in_enabled", "backlash_out_enabled"]) {
      const el = $(`mo-${name}`);
      el.disabled = !(name in motor);
      el.checked = !!motor[name];
    }
    for (const name of ["backlash_in_steps", "backlash_out_steps"]) {
      const el = $(`mo-${name}`);
      el.disabled = !(name in motor);
      el.value = name in motor ? motor[name] : "";
    }
    const coilSeq = S.settings.coil_during_sequence !== false;
    $("opt-coil-seq-row").classList.toggle("hidden", motor.coil_power !== false);
    $("opt-coil-seq").checked = coilSeq;
    $("mo-coil-warn").classList.toggle("hidden", !(motor.coil_power === false && !coilSeq));
    $("m-micro").value = motor.step_mode ? (motor.step_mode === 1 ? t("passo intero") : `1/${motor.step_mode}`) : t("1 (non letto)");
    updateMechResult();
  }

  // temperatura
  const hist = S.temp_history || [];
  const hasProbe = f.connected && f.temperature != null;
  $("t-value").textContent = hasProbe ? `${fmtNum(f.temperature, 2)} °C` : f.connected ? t("Sonda assente") : "—";
  if (hist.length > 1) {
    const mn = Math.min(...hist), mx = Math.max(...hist);
    setChip("t-chip", `${fmtNum(mn, 1)} – ${fmtNum(mx, 1)} °C`, mx - mn > 1 ? "busy" : "ok");
    $("t-spark").innerHTML = sparkline(hist, 300, 70);
  } else setChip("t-chip", hasProbe ? t("in raccolta…") : "—");
}

function sparkline(values, w, h) {
  let mn = Math.min(...values), mx = Math.max(...values);
  if (mx - mn < 0.2) { const m = (mx + mn) / 2; mn = m - 0.1; mx = m + 0.1; }
  const pts = values.map((v, i) => [(i / (values.length - 1)) * w, h - 4 - ((v - mn) / (mx - mn)) * (h - 8)]);
  const line = pts.map((p, i) => `${i ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join("");
  return `<path class="area" d="${line}L${w},${h}L0,${h}Z"/><path class="line" d="${line}"/>`;
}

function renderLog() {
  if ($("view-log").classList.contains("hidden")) return;
  const log = $("log");
  const atBottom = log.scrollTop + log.clientHeight >= log.scrollHeight - 8;
  const text = S.log.join("\n");
  if (log.textContent !== text) {
    log.textContent = text;
    if (atBottom) log.scrollTop = log.scrollHeight;
  }
}

// ---------------- form ----------------
function loadForms(cfg) {
  const q = cfg.sequence;
  $("s-start").value = q.start; $("s-end").value = q.end; $("s-step").value = q.step;
  $("s-settle").value = q.settle_ms; $("s-post").value = q.post_shot_ms; $("s-backlash").value = q.backlash;
  $("s-mode").value = q.capture_mode; $("s-name").value = q.session_name; $("s-return").checked = q.return_to_start;
  $("s-sound").checked = q.sound_on_end !== false;
  $("s-repeats").value = q.shots_per_position || 1;
  const cal = cfg.calibration || {};
  $("x-stat").value = cal.light_stat || "highlights";
  $("x-target").value = cal.light_target_pct ?? 85;
  $("k-count").value = cal.count ?? 16;
  $("k-target").value = cal.flat_target_pct ?? 50;
  renderOpticsProfiles();
  $("s-optics").value = opticsProfiles()[q.optics_profile] ? q.optics_profile : "";
  editProfile($("s-optics").value);
  $("c-bulb").value = q.bulb_s || 0;
  $("c-mirror").value = String(q.mirror_delay_ms || 0);
  $("lang-select").value = cfg.language || "auto";
  if (cfg.focuser_port) $("f-port").dataset.saved = cfg.focuser_port;
  loadLimitForm(cfg);
  const m = cfg.mechanics;
  $("m-spr").value = m.motor_steps_per_rev; $("m-gear").value = m.gear_ratio; $("m-umrev").value = m.um_per_knob_rev;
  $("m-umstep").value = cfg.um_per_step;
  setMechMode(m.mode);
  syncCount(); linkClear();
  formLoaded = true;
  updateSummary();
  dof();
}

function loadLimitForm(cfg) {
  $("lim-min").value = cfg.limit_min ?? 0;
  $("lim-max").value = cfg.limit_max ?? "";
  $("lim-dir").value = cfg.toward_specimen;
}

function formParams() {
  return {
    start: num("s-start"), end: num("s-end"), step: num("s-step"),
    settle_ms: num("s-settle"), post_shot_ms: num("s-post"), backlash: num("s-backlash"),
    return_to_start: $("s-return").checked, sound_on_end: $("s-sound").checked, capture_mode: $("s-mode").value,
    session_name: $("s-name").value.trim() || "stack", output_root: (S && S.settings.output_root) || "",
    bulb_s: num("c-bulb"), mirror_delay_ms: num("c-mirror"),
    shots_per_position: Math.max(1, Math.round(num("s-repeats") || 1)),
    optics_profile: $("s-optics").value,
  };
}

function shotCount(p = formParams()) {
  const span = Math.abs(p.end - p.start), step = Math.max(1, Math.abs(p.step));
  return Math.floor(span / step) + 1 + (span % step ? 1 : 0);
}
const syncCount = () => ($("s-count").value = shotCount());

// ---- campi collegati della pila: Inizio, Fine e Passo ricalcolano il Numero di scatti; il Numero di scatti
// ricalcola il Passo. Solo il Passo, se cambia da solo, si evidenzia con «↺ era X» (il numero di scatti che si
// aggiorna è atteso, il passo che cambia no): il pulsante annulla l'ultima modifica.
const LINKED = ["s-start", "s-end", "s-step", "s-count"];
const linkValues = () => Object.fromEntries(LINKED.map((id) => [id, $(id).value]));
let linkEdit = null;   // modifica in corso: { field, before: {id: valore}, closed }
let linkPrev = null;   // valori dei quattro campi dopo l'ultimo aggiornamento (l'evento input arriva a valore già cambiato)
function linkBegin(field) {
  if (linkEdit && linkEdit.field === field && !linkEdit.closed) return;
  linkEdit = { field, before: linkPrev || linkValues(), closed: false };
}
const linkDone = () => { linkPrev = linkValues(); };
function linkMark() {
  for (const id of LINKED) {
    const input = $(id), label = input.closest("label");
    const before = linkEdit && id === "s-step" && id !== linkEdit.field ? linkEdit.before[id] : "";
    const changed = before !== "" && before !== input.value;
    input.classList.toggle("auto-upd", changed);
    let chip = label.querySelector(".revert");
    if (!changed) { if (chip) chip.remove(); continue; }
    if (!chip) {
      // in fondo all'etichetta (posizionato in alto a destra): il primo controllo dell'etichetta resta il campo
      chip = document.createElement("button");
      chip.type = "button"; chip.className = "revert";
      chip.onclick = (e) => { e.preventDefault(); linkRestore(); };
      label.append(chip);
    }
    const txt = t("↺ era {v}", { v: before });
    if (chip.textContent !== txt) chip.textContent = txt;   // solo se cambia (Safari perde il clic)
    const field = $(linkEdit.field).closest("label").firstChild.nodeValue.trim();
    chip.title = t("Ricalcolato dopo la modifica di «{f}»: clic per tornare ai valori di prima", { f: field });
  }
}
function linkRestore() {
  if (!linkEdit) return;
  for (const id of LINKED) $(id).value = linkEdit.before[id];
  linkEdit = null;
  linkMark(); linkDone(); updateSummary();
}
function linkClear() {
  linkEdit = null;
  linkMark(); linkDone();
}

function shutterSeconds() {
  const v = $("c-shutter").value || "";
  if (/^\d+\/\d+$/.test(v)) { const [a, b] = v.split("/").map(Number); return a / b; }
  const n = parseFloat(v);
  return isFinite(n) ? n : 0;
}

let summaryOpen = false;   // riepilogo della pila aperto (profilo e calibrazione visibili)
function updateSummary() {
  if (!formLoaded || !S) return;
  const p = formParams(), n = shotCount(p), span = Math.abs(p.end - p.start), k = p.shots_per_position;
  const perShot = (p.post_shot_ms + p.mirror_delay_ms) / 1000 + (p.bulb_s || shutterSeconds()) + 1.5;
  const perPos = p.settle_ms / 1000 + p.step / 400 + k * perShot;
  let html = k > 1
    ? t("<b>{n}</b> posizioni × <b>{k}</b> = <b>{tot}</b> scatti · escursione <b>{span}</b> passi", { n, k, tot: fmtInt(n * k), span: fmtInt(span) })
    : t("<b>{n}</b> scatti · escursione <b>{span}</b> passi", { n, span: fmtInt(span) });
  if (umPerStep()) html += " " + t("= <b>{um}</b> · passo <b>{step}</b>", { um: fmtUm(span), step: fmtUm(p.step) });
  html += "<br>" + t("Durata stimata <b>~{t}</b>", { t: fmtTime(n * perPos) });
  // profilo ottico e calibrazione: a richiesta (si apre con un clic sul riepilogo; resta aperto fra un aggiornamento e l'altro)
  let more = `<span class="optics-line">${opticsSummary()}</span>`;
  if (p.capture_mode === "download") more += `<span class="optics-line">${calibrationSummary()}</span>`;
  html = `<details id="s-sum-more"${summaryOpen ? " open" : ""}><summary title="${t("Profilo ottico e calibrazione")}">${html}</summary>${more}</details>`;
  // controllo fine corsa lato interfaccia (il server ricontrolla comunque)
  const [lo, hi] = S.focuser.connected ? S.focuser.bounds : [S.settings.limit_min, S.settings.limit_max];
  const dir = p.end >= p.start ? 1 : -1;
  const approach = p.backlash > 0 ? p.start - dir * p.backlash : null;
  const out = [p.start, p.end, approach].filter((v) => v != null && (v < lo || (hi != null && v > hi)));
  const lim = { lo: fmtInt(lo), hi: hi == null ? "∞" : fmtInt(hi) };
  if (out.length) html += `<span class="bad-text">${approach != null && out.includes(approach)
    ? t("⚠ La sequenza (con la compensazione del gioco) esce dai fine corsa {lo} – {hi}", lim)
    : t("⚠ La sequenza esce dai fine corsa {lo} – {hi}", lim)}</span>`;
  if (p.capture_mode === "trigger") html += `<span class="warn-text">${t("In modalità trigger imposta la destinazione su scheda.")}</span>`;
  $("s-summary").innerHTML = html;
  // sequenza ferma e mai avviata: il contatore segue i campi (prima si aggiornava solo all'arrivo dello stato)
  const q = S.sequence || {};
  if (q.state === "idle" && !q.total) $("s-count-label").textContent = `0 / ${n}`;
}

// ---------------- meccanica ----------------
let mechMode = "manual";
function setMechMode(mode) {
  mechMode = mode;
  $$("#mech-mode button").forEach((b) => b.setAttribute("aria-checked", b.dataset.mode === mode));
  $("mech-computed").classList.toggle("hidden", mode !== "computed");
  $("mech-manual").classList.toggle("hidden", mode !== "manual");
  updateMechResult();
}
function mechUmPerStep() {
  if (mechMode === "manual") return num("m-umstep");
  const micro = (S && S.focuser.connected && S.focuser.motor && S.focuser.motor.step_mode) || 1;
  const d = num("m-spr") * micro * num("m-gear");
  return d > 0 ? num("m-umrev") / d : 0;
}
function updateMechResult() {
  const u = mechUmPerStep();
  if (!(u > 0)) { $("m-result").textContent = t("Inserisci valori validi"); return; }
  $("m-result").innerHTML = t("Risoluzione: <b>{u} µm/passo</b> · 1 µm = <b>{p}</b> passi · 1000 passi = <b>{k} µm</b>",
    { u: fmtNum(u, 4), p: fmtNum(1 / u, 2), k: fmtNum(u * 1000, 1) });
}

// ---------------- schede di impostazioni: barra dei fine corsa, riepilogo, indice e ricerca ----------------
// I fine corsa si salvano solo con «Salva fine corsa»: la barra compare quando i campi sono diversi da quelli salvati.
function limDirty() {
  if (!S) return false;
  const c = S.settings, max = $("lim-max").value.trim();
  return String(num("lim-min")) !== String(c.limit_min ?? 0)
    || (max === "" ? c.limit_max != null : Number(max) !== c.limit_max)
    || $("lim-dir").value !== c.toward_specimen;
}
function updateLimDirty() {
  const d = limDirty();
  $("lim-bar").classList.toggle("hidden", !d);
  $("lim-dot").classList.toggle("hidden", !d);
}

// riepilogo della Configurazione: i valori che derivano dalle impostazioni, sempre in vista
function renderSettingsSummary() {
  if (!S) return;
  const f = S.focuser || {}, c = S.settings, u = mechUmPerStep();
  $("sum-res").textContent = u > 0 ? t("{u} µm/passo", { u: fmtNum(u, 4) }) : "—";
  $("sum-res1k").textContent = u > 0 ? t("1000 passi = {k} µm", { k: fmtNum(u * 1000, 1) }) : t("Inserisci valori validi");
  const lo = c.limit_min ?? 0, hi = c.limit_max ?? (f.connected ? f.max_step : null);
  $("sum-run").textContent = hi != null ? t("{a} – {b} passi", { a: fmtInt(lo), b: fmtInt(hi) }) : "—";
  $("sum-runum").textContent = hi != null && u > 0 ? `= ${fmtNum((hi - lo) * u, 1)} µm` + (c.limit_max == null ? " " + t("(max firmware)") : "") : "";
  const fw = S.firmware_update || {};
  $("sum-fw").textContent = !f.connected ? "—" : f.simulated ? t("simulatore") : fw.installed != null ? t("build {b}", { b: fw.installed }) : (f.firmware || "myFocuserPro2");
  const fwx = $("sum-fwx");
  fwx.textContent = f.connected ? (fw.available ? t("disponibile build {b}", { b: fw.bundled }) : t("collegato")) : t("non collegato");
  fwx.className = f.connected ? (fw.available ? "sum-warn" : "sum-ok") : "";
  const a = S.app || {};
  $("sum-app").textContent = a.version ?? "—";
  const appx = $("sum-appx");
  appx.textContent = a.available ? t("disponibile {v}", { v: a.latest }) : a.latest ? t("aggiornata") : "";
  appx.className = a.available ? "sum-warn" : "";
  const r = S.remote || {}, want = !!(c.remote && c.remote.enabled);
  $("sum-phone").textContent = want && r.running ? t("attivo") : t("spento");
  let host = "";
  try { host = want && r.running && r.url ? new URL(r.url).host : ""; } catch { /* indirizzo non valido */ }
  $("sum-phonex").textContent = host;
  $("up-dot").classList.toggle("hidden", !a.available && !fw.available);
}

// indice: clic, sezione corrente durante lo scorrimento, ricerca fra le righe
function bindSettingsPage(viewId, navId, searchId, noneId) {
  const view = $(viewId), nav = $(navId), links = [...nav.querySelectorAll("a[href^='#']")];
  const target = (a) => document.getElementById(a.getAttribute("href").slice(1));
  const gone = (el) => !el || el.hidden || el.classList.contains("hidden") || getComputedStyle(el).display === "none";
  let hold = 0;
  links.forEach((a) => a.addEventListener("click", (e) => {
    e.preventDefault();
    const sec = target(a);
    if (gone(sec)) return;
    hold = Date.now() + 900;
    links.forEach((x) => x.classList.toggle("on", x === a));
    sec.scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  }));
  const spy = () => {
    if (view.classList.contains("hidden") || Date.now() < hold) return;
    const top = (parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--topbar-h")) || 62) + 40;
    let cur = null;
    for (const a of links) {
      if (gone(a) || gone(target(a))) continue;
      if (target(a).getBoundingClientRect().top <= top) cur = a;
    }
    cur = cur || links.find((a) => !gone(a));
    links.forEach((a) => a.classList.toggle("on", a === cur));
  };
  addEventListener("scroll", spy, { passive: true });
  view._spy = spy;
  const search = searchId && $(searchId);
  if (!search) return;
  search.addEventListener("input", () => {
    const q = search.value.trim().toLowerCase();
    let any = false;
    view.querySelectorAll(".set-sec").forEach((sec) => {
      sec.hidden = false;
      if (sec.classList.contains("hidden") || getComputedStyle(sec).display === "none") return;
      const title = sec.querySelector("h2").textContent.toLowerCase();
      let n = 0;
      sec.querySelectorAll(".set-row").forEach((r) => {
        if (r.id === "jog-chunk-row" || r.id === "opt-coil-seq-row") { if (r.classList.contains("hidden")) return; }
        const hit = !q || title.includes(q) || r.textContent.toLowerCase().includes(q);
        r.hidden = !hit; r.classList.toggle("set-hit", !!q && hit); if (hit) n++;
      });
      sec.querySelectorAll(".set-box > .result, .set-sub, .set-details, .set-note, .save-bar ~ .set-rows").forEach((h) => (h.hidden = !!q && !h.querySelector(".set-hit")));
      sec.hidden = !!q && n === 0;
      if (!sec.hidden) any = true;
    });
    // un gruppo senza sezioni trovate sparisce con il suo titolo
    view.querySelectorAll(".set-card").forEach((card) => {
      const empty = ![...card.querySelectorAll(".set-sec")].some((x) => !gone(x));
      card.hidden = empty;
      if (card.previousElementSibling && card.previousElementSibling.classList.contains("set-group")) card.previousElementSibling.hidden = empty;
      // la linea sopra la prima sezione visibile non serve
      let first = true;
      card.querySelectorAll(".set-sec").forEach((x) => { const vis = !gone(x); x.style.borderTop = vis && first ? "0" : ""; if (vis) first = false; });
    });
    $(noneId).classList.toggle("hidden", any);
    links.forEach((a) => { const sec = target(a); a.hidden = !!sec && !!sec.hidden; });
    spy();
  });
}

// altezza della barra in alto: indice e riepilogo restano appena sotto
function trackTopbar() {
  const set = () => document.documentElement.style.setProperty("--topbar-h", `${$$(".topbar")[0]?.offsetHeight || 62}px`);
  set(); addEventListener("resize", set);
}

// ---------------- avanzamento da smartphone ----------------
let remoteUrl = null;
function renderRemote() {
  const r = S.remote || {}, want = !!(S.settings.remote && S.settings.remote.enabled);
  $("r-enabled").checked = want;
  $("r-info").classList.toggle("hidden", !(r.running && r.url));
  $("r-error").textContent = want && !r.running && r.error ? r.error
    : want && r.running && !r.url ? t("Il Mac non sembra collegato a una rete locale.") : "";
  if (r.url && r.url !== remoteUrl) {      // il QR cambia solo con il link (nuovo codice o nuovo indirizzo)
    remoteUrl = r.url;
    $("r-url").textContent = r.url; $("r-url").href = r.url;
    $("r-qr").src = "/api/remote/qr.png?u=" + encodeURIComponent(r.url);
  }
}
function bindRemote() {
  // in caso di errore la casella torna allo stato salvato al prossimo aggiornamento (renderRemote)
  $("r-enabled").addEventListener("change", (e) => act(null, () => api("/api/remote", { enabled: e.target.checked })));
  $("r-new").onclick = () => {
    if (!confirm(t("Creare un nuovo link? Quello attuale smetterà di funzionare."))) return;
    act($("r-new"), () => api("/api/remote", { enabled: true, new_link: true }), t("Nuovo link creato"));
  };
}

// ---------------- profondità di campo ----------------
// Formula di Berek/Shillaber: DOF = λ·n/NA² + n·e/(M·NA)
// Macro: NA equivalente lato soggetto = m / (2 N (1 + m1)), calcolata dal diaframma (vedi macroNumbers)
let dofLast = null;   // ultimo calcolo della profondità di campo, per il riepilogo di Ottica
function dof() {
  dofLast = null;
  $("d-apply").disabled = true;   // senza profondità di campo (manca NA o ingrandimento) non c'è un passo da usare
  const o = opticsForm(), macro = o.kind === "macro";
  const na = macro ? macroNumbers(o).na : num("d-na"), mag = totalMag(o) || 0, px = num("d-px"), ov = num("d-ov") / 100;
  // pixel sul campione (e/M nella formula): quello misurato se c'è, altrimenti pixel del sensore ÷ ingrandimento
  const measured = o.pixel_size_um || 0;
  const pxSample = measured || (mag > 0 ? px / mag : 0);
  if (!(na > 0 && (mag > 0 || measured))) {
    $("d-result").textContent = macro ? t("Inserisci obiettivo, rapporto di riproduzione e diaframma") : t("Inserisci NA e ingrandimento");
    return 0;
  }
  const d = (0.55 * 1.0) / (na * na) + (1.0 * pxSample) / na;
  const step = d * (1 - ov), um = umPerStep();
  dofLast = { d, step, steps: um ? stepsFor(step, um) : null, ov: num("d-ov") };
  $("d-apply").disabled = false;
  let html = t("Profondità di campo ≈ <b>{d} µm</b> · passo consigliato <b>{s} µm</b>", { d: fmtNum(d, 2), s: fmtNum(step, 2) });
  if (measured) html += " " + t("(con i µm per pixel misurati)");
  if (!um) html += " · " + t("configura la meccanica per convertirlo in passi");
  else {
    const n = stepsFor(step, um);
    html += " = " + (n === 1 ? t("<b>1 passo</b>") : t("<b>{n} passi</b>", { n }));
    if (step < um) html += microstepAdvice(step, um);
  }
  $("d-result").innerHTML = html;
  return step;
}

// passi della slitta per il passo consigliato: mai più lungo del consigliato (la sovrapposizione resta), almeno 1
function stepsFor(step, um) {
  return Math.max(1, Math.floor(step / um + 1e-9));
}

// Un passo della slitta è più lungo del passo consigliato: tra gli scatti resterebbero zone sfocate.
// Suggerisce il microstep più grosso che dà almeno MIN_STEPS passi per il passo consigliato.
const MICROSTEPS = [1, 2, 4, 8, 16, 32];
const MIN_STEPS = 3;
function microstepAdvice(step, um) {
  let html = `<span class="warn-text">${t("Un passo della slitta ({u} µm) è più lungo del passo consigliato: tra uno scatto e l'altro resterebbero zone sfocate.",
    { u: fmtNum(um, 2) })}</span>`;
  const f = S && S.focuser;
  const micro = f && f.connected && f.motor && f.motor.step_mode;
  if (!micro) {   // scheda senza microstep leggibile: indica solo di quanto accorciare il passo
    return html + `<span class="muted">${t("Serve un passo almeno {k} volte più corto: microstep più fine o più riduzione meccanica.",
      { k: fmtNum(Math.ceil(MIN_STEPS * um / step), 0) })}</span>`;
  }
  const full = um * micro;   // µm per passo intero
  const pick = MICROSTEPS.find((m) => m > micro && step / (full / m) >= MIN_STEPS);
  if (!pick) {
    return html + `<span class="muted">${t("Anche con il microstep 1/32 il passo resta troppo lungo: serve più riduzione meccanica.")}</span>`;
  }
  const u2 = full / pick;
  let tip = t("Imposta il microstep a 1/{m} (Configurazione › Motore): {u} µm/passo, passo consigliato {n} passi.",
    { m: pick, u: fmtNum(u2, 3), n: stepsFor(step, u2) });
  if (mechMode === "manual") tip += " " + t("Poi scrivi {u} µm/passo in Configurazione meccanica: il valore inserito a mano non segue il microstep.", { u: fmtNum(u2, 3) });
  tip += " " + t("Con il microstep tieni attive le bobine alimentate a motore fermo.");
  return html + `<span class="muted">${tip}</span>`;
}

// ---------------- profili di ottica, filtro e illuminazione (finiscono in sequence.json) ----------------
// Il tab Ottica modifica i profili; la card Sequenza sceglie quale usare ("" = nessun filtro).
const shotLabel = (shot) => (shot.repeat ? `${shot.index}.${shot.repeat}` : shot.index);
let filterMode = "unknown", editingProfile = "", opticsSaved = "", profileSig = null;
const FILTER_TYPE_LABELS = () => ({ bandpass: t("Passa banda"), longpass: t("Long pass"), shortpass: t("Short pass"),
  neutral_density: t("Neutro (ND)"), polarizer: t("Polarizzatore"), other: t("Altro") });
// suggerimenti per il campo Illuminazione (testo libero)
const ILLUMINATION_SUGGESTIONS = () => [t("Campo chiaro (luce trasmessa)"), t("Luce riflessa"), t("LED ad anello"),
  t("Epifluorescenza"), t("Campo scuro"), t("Luce polarizzata")];
const opticsProfiles = () => (S && S.settings.optics_profiles) || {};
const BLANK_OPTICS = { kind: "microscope", dof_overlap: 30, filter_mode: "unknown", filter: { type: "bandpass" }, illumination: {} };
let opticsKind = "microscope";
const MAX_CLOSEUP = 3;
// lenti addizionali comuni (potenza in diottrie dalle schede dei produttori): suggerimenti del campo Nome
const CLOSEUP_PRESETS = { "Raynox DCR-250": 8, "Raynox DCR-150": 4.8, "Canon 500D": 2, "Canon 250D": 4,
  "Nikon 5T": 1.5, "Nikon 6T": 2.9, "Marumi Achromat Macro 330": 3, "Marumi Achromat Macro 200": 5 };

function setOpticsKind(kind) {
  opticsKind = kind === "macro" ? "macro" : "microscope";
  $("card-optics").dataset.kind = opticsKind;
  $("view-optics").dataset.kind = opticsKind;
  $$("#o-kind button").forEach((b) => b.setAttribute("aria-checked", b.dataset.kind === opticsKind));
}

// righe delle lenti addizionali (nome + diottrie)
function renderCloseups(list) {
  const box = $("m-closeups");
  box.innerHTML = "";
  for (const c of list) addCloseupRow(c);
  $("m-closeup-add").disabled = box.children.length >= MAX_CLOSEUP;
}
function addCloseupRow(c = {}) {
  const box = $("m-closeups");
  const row = document.createElement("div");
  row.className = "closeup-row";
  row.innerHTML = `<label>${t("Lente addizionale")}<input type="text" class="cu-name" list="m-closeup-list" autocomplete="off" placeholder="${t("es. Raynox DCR-250")}"></label>`
    + `<label>${t("Diottrie")}<input type="number" class="cu-d" step="0.1" min="0" placeholder="${t("es. 8")}"></label>`
    + `<button class="btn ghost small cu-del" title="${t("Togli questa lente")}" aria-label="${t("Togli questa lente")}">✕</button>`;
  row.querySelector(".cu-name").value = c.name || "";
  row.querySelector(".cu-d").value = c.diopters ?? "";
  row.querySelector(".cu-name").addEventListener("change", (e) => {
    const d = CLOSEUP_PRESETS[e.target.value.trim()], dIn = row.querySelector(".cu-d");
    if (d && !dIn.value) { dIn.value = d; updateOptics(); }
  });
  row.querySelector(".cu-del").onclick = () => { row.remove(); $("m-closeup-add").disabled = false; updateOptics(); };
  box.append(row);
  $("m-closeup-add").disabled = box.children.length >= MAX_CLOSEUP;
  return row;
}

function setFilterMode(mode) {
  filterMode = mode;
  $$("#o-filter-mode button").forEach((b) => b.setAttribute("aria-checked", b.dataset.fmode === mode));
  $("o-filter-fields").classList.toggle("hidden", mode !== "filter");
  const type = $("o-ftype").value;
  $$("#o-filter-fields .f-band").forEach((el) => el.classList.toggle("hidden", type !== "bandpass"));
  $$("#o-filter-fields .f-edge").forEach((el) => el.classList.toggle("hidden", type !== "longpass" && type !== "shortpass"));
}

function loadOptics(o) {
  const f = o.filter || {}, il = o.illumination || {};
  const set = (id, v) => ($(id).value = v == null ? "" : v);
  const inter = o.intermediate || {}, relay = o.relay || {};
  set("o-objective", o.objective); set("d-mag", o.objective_magnification ?? o.magnification); set("d-na", o.na);
  set("o-inter-name", inter.name); set("o-inter", inter.factor); set("o-relay-name", relay.name); set("o-relay", relay.factor);
  $("o-immersion").value = o.immersion || "";
  set("d-px", o.sensor_pixel_um); set("o-pxcal", o.pixel_size_um); set("d-ov", o.dof_overlap ?? 30);
  set("o-fname", f.name); $("o-ftype").value = f.type || "bandpass";
  set("o-fcenter", f.center_nm); set("o-fwidth", f.bandwidth_nm); set("o-fedge", f.edge_nm);
  set("o-illum", il.type); set("o-level", il.level_percent); set("o-cct", il.color_temp_k); set("o-notes", o.notes);
  setFilterMode(o.filter_mode || "unknown");
  const mc = o.macro || {}, lens = mc.lens || {};
  set("m-maker", lens.maker); set("m-model", lens.model); set("m-focal", lens.focal_mm); set("m-fmax", lens.max_aperture);
  lensSource = lens.source || "";
  set("m-mag", mc.lens_magnification); set("m-fnum", mc.f_number); set("m-ext", mc.extension_mm);
  $("m-search").value = "";
  renderCloseups(mc.closeup || []);
  setOpticsKind(o.kind);
}

// carica nell'editor un profilo ("" = nuovo profilo vuoto)
function editProfile(name) {
  editingProfile = opticsProfiles()[name] ? name : "";
  $("o-profile").value = editingProfile;
  loadOptics(opticsProfiles()[editingProfile] || BLANK_OPTICS);
  opticsSaved = JSON.stringify(opticsForm());
  updateOptics();
  dof();
}

function opticsForm() {
  const closeup = [...$$("#m-closeups .closeup-row")].map((r) => ({
    name: r.querySelector(".cu-name").value.trim(),
    diopters: r.querySelector(".cu-d").value.trim() === "" ? null : Number(r.querySelector(".cu-d").value) }));
  return {
    kind: opticsKind,
    macro: {
      lens: { maker: $("m-maker").value.trim(), model: $("m-model").value.trim(), focal_mm: optNum("m-focal"),
        max_aperture: optNum("m-fmax"), source: lensSource },
      lens_magnification: optNum("m-mag"), f_number: optNum("m-fnum"), extension_mm: optNum("m-ext"), closeup,
    },
    objective: $("o-objective").value.trim(), objective_magnification: optNum("d-mag"),
    intermediate: { name: $("o-inter-name").value.trim(), factor: optNum("o-inter") },
    relay: { name: $("o-relay-name").value.trim(), factor: optNum("o-relay") },
    na: optNum("d-na"),
    immersion: $("o-immersion").value, sensor_pixel_um: optNum("d-px"), pixel_size_um: Number.isNaN(pxMeasured()) ? null : pxMeasured(),
    dof_overlap: optNum("d-ov") ?? 30, filter_mode: filterMode,
    filter: { name: $("o-fname").value.trim(), type: $("o-ftype").value, center_nm: optNum("o-fcenter"),
      bandwidth_nm: optNum("o-fwidth"), edge_nm: optNum("o-fedge") },
    illumination: { type: $("o-illum").value.trim(), level_percent: optNum("o-level"), color_temp_k: optNum("o-cct") },
    notes: $("o-notes").value.trim(),
  };
}

// numero con i soli decimali che servono (40 · 1,6 · 0,63)
const fmtMag = (x) => fmtNum(x, Math.abs(x - Math.round(x)) < 1e-9 ? 0 : Math.abs(x * 10 - Math.round(x * 10)) < 1e-9 ? 1 : 2);

// Macro fotografica (lente sottile, stima; stessa formula di backend/optics.py):
// m1 = m0 + tubi / f · m = m1 + ΣD/1000 · f · (1 + m1) · diaframma effettivo N (1 + m1) · NA = m / (2 N (1 + m1))
function macroNumbers(o) {
  const mc = o.macro || {}, f = (mc.lens || {}).focal_mm, m0 = mc.lens_magnification, ext = mc.extension_mm || 0;
  const power = (mc.closeup || []).reduce((a, c) => a + (c.diopters > 0 ? c.diopters : 0), 0);
  if (m0 == null && !(ext || power)) return {};
  if ((ext || power) && !(f > 0)) return { needFocal: true };
  const m1 = (m0 || 0) + (ext ? ext / f : 0);
  const m = power ? m1 + (power / 1000) * f * (1 + m1) : m1;
  if (!(m > 0)) return {};
  const out = { magnification: m, lensSide: m1, power };
  if (mc.f_number > 0) { out.nEff = mc.f_number * (1 + m1); out.na = m / (2 * mc.f_number * (1 + m1)); }
  return out;
}

// ingrandimento sul sensore = obiettivo × cambio intermedio × adattatore (fattori vuoti = 1)
function totalMag(o) {
  if (o.kind === "macro") return macroNumbers(o).magnification || null;
  const obj = o.objective_magnification ?? o.magnification;
  if (!obj) return null;
  return obj * ((o.intermediate && o.intermediate.factor) || 1) * ((o.relay && o.relay.factor) || 1);
}

// ingrandimento reale sul sensore, dai µm per pixel misurati: pixel del sensore ÷ pixel sul campione.
// Contiene tutto quello che la catena non dice (distanza del sensore, tubo foto, tolleranze)
function measuredMag(o) {
  return o.pixel_size_um > 0 && o.sensor_pixel_um > 0 ? o.sensor_pixel_um / o.pixel_size_um : null;
}

// fattore dell'adattatore che fa tornare la catena (obiettivo × intermedio × adattatore) con la misura
function derivedRelay(o) {
  const real = measuredMag(o), obj = o.objective_magnification;
  if (o.kind === "macro" || !real || !obj) return null;
  return Math.round((real / (obj * ((o.intermediate && o.intermediate.factor) || 1))) * 1000) / 1000;
}

// testo breve di un profilo: obiettivo · totale sul sensore · NA · filtro
function opticsText(o) {
  const parts = [], total = totalMag(o), obj = o.objective_magnification ?? o.magnification, real = measuredMag(o);
  if (o.kind === "macro") {
    const lens = (o.macro || {}).lens || {}, mc = o.macro || {};
    const name = lensName(lens);
    parts.push(name || t("macro fotografica"));
    if (real) parts.push(t("{m}× sul sensore (misurato)", { m: fmtMag(real) }));
    else if (total) parts.push(t("≈ {m}× sul sensore", { m: fmtNum(total, 2) }));
    if (mc.f_number) parts.push(`f/${fmtNum(mc.f_number, 1)}`);
  } else {
    if (o.objective) parts.push(o.objective);
    else if (obj) parts.push(`${fmtNum(obj, 1)}×`);
    if (real) parts.push(t("{m}× sul sensore (misurato)", { m: fmtMag(real) }));
    else if (total && total !== obj) parts.push(t("{m}× sul sensore", { m: fmtMag(total) }));
    if (o.na) parts.push(`NA ${fmtNum(o.na, 2)}`);
  }
  const f = o.filter || {};
  if (o.filter_mode === "none") parts.push(t("nessun filtro"));
  else if (o.filter_mode === "filter") parts.push(t("filtro {name}", { name: f.name || FILTER_TYPE_LABELS()[f.type] || t("Altro") }));
  else parts.push(t("filtro non indicato"));
  return parts.join(" · ");
}

// riga nel riepilogo della sequenza: cosa finirà in sequence.json
function opticsSummary() {
  const name = $("s-optics").value, o = opticsProfiles()[name];
  if (!o) return t("Nessun profilo ottico: in sequence.json il filtro risulterà «nessuno»");
  return t("Profilo «{name}»: {txt}", { name: escapeHtml(name), txt: escapeHtml(opticsText(o)) });
}
const escapeHtml = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

let pxResultHtml = null;   // ultimo testo di Scala sul campione
function updateOptics() {
  const o = opticsForm(), total = totalMag(o), real = measuredMag(o);
  const limit = o.kind === "macro" ? 15 : 2;   // scarto accettabile fra misura e calcolo (macro: stima a lenti sottili)
  let txt = "";
  if (o.kind === "macro") {
    const mn = macroNumbers(o), mc = o.macro;
    if (mn.needFocal) txt = t("Indica la focale dell'obiettivo: tubi e lenti addizionali dipendono da quella") + "<br>";
    else if (total) {
      const steps = [];
      if (mc.extension_mm) steps.push(t("con i tubi {m}×", { m: fmtNum(mn.lensSide, 2) }));
      if (mn.power) steps.push(t("lenti +{d} D", { d: fmtNum(mn.power, 1) }));
      txt = t("Ingrandimento sul sensore ≈ <b>{m}×</b>", { m: fmtNum(total, 2) })
        + (steps.length ? ` (${t("obiettivo {m}×", { m: fmtNum(mc.lens_magnification || 0, 2) })} · ${steps.join(" · ")})` : "") + "<br>";
      if (mn.nEff) txt += t("Diaframma effettivo ≈ <b>f/{n}</b> · NA equivalente <b>{na}</b>", { n: fmtNum(mn.nEff, 1), na: fmtNum(mn.na, 3) }) + "<br>";
    }
    if (!mn.needFocal && !total) txt += t("Indica il rapporto di riproduzione dell'obiettivo (o tubi e lenti con la focale)") + "<br>";
  } else if (total) {
    const factors = [o.objective_magnification, o.intermediate.factor, o.relay.factor].filter((f) => f);
    // con la misura, il valore della catena è solo un confronto: quello reale è sotto, dalla misura
    txt = (real ? t("Ingrandimento dalla catena: {m}×", { m: fmtMag(total) }) : t("Ingrandimento sul sensore: <b>{m}×</b>", { m: fmtMag(total) }))
      + (factors.length > 1 ? ` (${factors.map(fmtMag).join(" × ")})` : "") + "<br>";
  }
  const calc = o.sensor_pixel_um && total ? o.sensor_pixel_um / total : 0;
  if (Number.isNaN(pxMeasured())) {
    $("o-pxcal").setAttribute("aria-invalid", "true");
    txt += `<span class="warn-text">${t("I µm per pixel misurati devono essere un numero maggiore di zero, per esempio 0,3912")}</span>`;
  } else $("o-pxcal").removeAttribute("aria-invalid");
  if (o.pixel_size_um && calc) {
    // scarto fra misurato e calcolato: oltre il 2 % (in macro oltre il 15 %, normale per la stima a lenti sottili)
    // di solito manca o è di troppo un fattore (Optovar, adattatore) o il pixel del sensore è sbagliato
    const diff = (o.pixel_size_um / calc - 1) * 100;
    const line = t("Sul campione: calcolato {c} · misurato <b>{m} µm/pixel</b> (scarto {d} %)",
      { c: fmtNum(calc, 4), m: fmtNum(o.pixel_size_um, 4), d: (diff > 0 ? "+" : "") + fmtNum(diff, 1) });
    txt += Math.abs(diff) > limit
      ? `${line}<span class="warn-text">${t("Scarto grande: controlla ingrandimenti, fattori intermedi (Optovar, adattatore) e pixel del sensore. Per i calcoli vale il valore misurato.")}</span>`
      : line;
  } else if (o.pixel_size_um) txt += t("Sul campione: <b>{v} µm/pixel</b> (misurato)", { v: fmtNum(o.pixel_size_um, 4) });
  else if (o.sensor_pixel_um && total)
    txt += t("Sul campione: <b>{v} µm/pixel</b> (pixel del sensore ÷ ingrandimento)", { v: fmtNum(o.sensor_pixel_um / total, 4) });
  else if (o.kind !== "macro" || total) txt += t("Indica ingrandimento e pixel del sensore per avere la scala in µm");
  if (real) {
    txt += `<span class="result-line">${t("Ingrandimento reale sul sensore, dalla misura: <b>{m}×</b>", { m: fmtMag(real) })}</span>`;
    // la catena non torna: propone il fattore dell'adattatore che la fa coincidere con la misura
    const relay = derivedRelay(o);
    if (relay && calc && Math.abs((o.pixel_size_um / calc - 1) * 100) > limit)
      txt += `<span class="result-line"><button type="button" class="btn ghost small" id="o-derive">${t("Ricava il fattore dalla misura")}</button>`
        + `<span class="muted">${t("l'adattatore diventa {f}×, così la catena coincide con la misura", { f: fmtNum(relay, 3) })}</span></span>`;
  }
  if (o.kind === "macro" && total && !o.pixel_size_um) txt += "<br>" + `<span class="hint">${t("Stima con lenti sottili: per misure esatte fotografa un righello o un micrometro e scrivi qui sotto i µm per pixel misurati.")}</span>`;
  // si riscrive solo se cambia: uscire dal campo (change) mentre si clicca «Ricava il fattore» non deve
  // sostituire il pulsante fra la pressione e il rilascio, altrimenti il clic va perso
  if (txt !== pxResultHtml) { $("o-pxresult").innerHTML = txt; pxResultHtml = txt; }
  const derive = $("o-derive");
  if (derive) derive.onclick = () => {
    const f = derivedRelay(opticsForm());
    if (!f) return;
    $("o-relay").value = f;
    updateOptics();
    toast(t("Adattatore a {f}×: salva il profilo per tenerlo", { f: fmtNum(f, 3) }));
  };
  dof();
  const dirty = JSON.stringify(o) !== opticsSaved;
  setChip("o-chip", editingProfile || t("Nuovo profilo"), editingProfile ? (dirty ? "busy" : "ok") : "");
  $("o-dirty").textContent = dirty ? t("Modifiche non salvate") : "";
  $("o-bar").classList.toggle("hidden", !dirty);
  $("o-dot").classList.toggle("hidden", !dirty);
  $("o-profile-del").disabled = !editingProfile;
  renderLensButtons();
  renderOpticsSummary(o, total, dirty);
}

// riepilogo di Ottica: profilo, ingrandimento, scala e profondità di campo, sempre in vista
function renderOpticsSummary(o, total, dirty) {
  $("osum-name").textContent = editingProfile || t("Nuovo profilo");
  const st = $("osum-state");
  st.textContent = dirty ? t("Modifiche non salvate") : editingProfile ? t("salvato") : "";
  st.className = dirty ? "sum-warn" : editingProfile ? "sum-ok" : "";
  // ingrandimento reale (dalla misura) se c'è; altrimenti quello della catena
  const real = measuredMag(o), limit = o.kind === "macro" ? 15 : 2, mx = $("osum-magx");
  $("osum-mag").textContent = real ? `${fmtMag(real)}×` : total ? `${fmtMag(total)}×` : "—";
  if (real) {
    const off = total && Math.abs((real / total - 1) * 100) > limit;
    mx.textContent = off ? t("dalla misura · catena {m}×", { m: fmtMag(total) }) : t("dalla misura");
    mx.className = off ? "sum-warn" : "sum-ok";
  } else {
    mx.textContent = o.kind === "macro" && total ? t("stima con lenti sottili") : "";
    mx.className = "";
  }
  const calc = o.sensor_pixel_um && total ? o.sensor_pixel_um / total : 0, meas = o.pixel_size_um || 0;
  $("osum-scale").textContent = meas || calc ? t("{v} µm/pixel", { v: fmtNum(meas || calc, 4) }) : "—";
  const sx = $("osum-scalex");
  if (meas && calc) {
    const diff = (meas / calc - 1) * 100, limit = o.kind === "macro" ? 15 : 2;
    sx.textContent = t("misurata · scarto {d} %", { d: (diff > 0 ? "+" : "") + fmtNum(diff, 1) });
    sx.className = Math.abs(diff) > limit ? "sum-warn" : "sum-ok";
  } else { sx.textContent = meas ? t("misurata") : calc ? t("calcolata") : ""; sx.className = ""; }
  const d = dofLast;
  $("osum-dof").textContent = d ? `${fmtNum(d.d, 2)} µm` : "—";
  $("osum-step").textContent = d ? `${fmtNum(d.step, 2)} µm` : "—";
  $("osum-steps").textContent = d ? (d.steps ? t("{n} passi del motore · sovrapposizione {o} %", { n: d.steps, o: fmtNum(d.ov, 0) }) : t("configura la meccanica per convertirlo in passi")) : "";
}

// riempie i due menu dei profili (editor e sequenza) solo quando l'elenco cambia
function renderOpticsProfiles() {
  const names = Object.keys(opticsProfiles()).sort((a, b) => a.localeCompare(b));
  const sig = names.join("|") + "#" + LANG;
  if (sig === profileSig) return;
  profileSig = sig;
  const fill = (sel, emptyLabel) => {
    const cur = sel.value;
    sel.innerHTML = "";
    sel.add(new Option(emptyLabel, ""));
    for (const n of names) sel.add(new Option(n, n));
    sel.value = names.includes(cur) ? cur : "";
  };
  fill($("o-profile"), t("— nuovo profilo —"));
  fill($("s-optics"), t("Nessun profilo (nessun filtro)"));
}

async function saveProfile(name) {
  if (Number.isNaN(pxMeasured())) throw new Error(t("I µm per pixel misurati devono essere un numero maggiore di zero, per esempio 0,3912"));
  const profiles = await api("/api/optics/profiles/save", { name, optics: opticsForm() });
  S.settings.optics_profiles = profiles;
  renderOpticsProfiles();
  editProfile(name);
  // primo profilo creato: lo propone subito anche per la sequenza
  if (!$("s-optics").value && Object.keys(opticsProfiles()).length === 1) $("s-optics").value = name;
  updateSummary();
}

function bindOptics() {
  const list = $("o-illum-list");
  for (const v of ILLUMINATION_SUGGESTIONS()) list.append(new Option(v, v));
  $$("#o-filter-mode button").forEach((b) => (b.onclick = () => { setFilterMode(b.dataset.fmode); updateOptics(); }));
  $("o-ftype").addEventListener("change", () => setFilterMode(filterMode));
  // delega: vale anche per le righe delle lenti addizionali create dopo
  for (const ev of ["input", "change"]) {
    $("card-optics").addEventListener(ev, (e) => {
      if (e.target.id === "o-profile" || e.target.id === "m-search") return;
      if (["m-maker", "m-model", "m-focal", "m-fmax"].includes(e.target.id) && ev === "input") lensSource = "";
      updateOptics();
    });
  }
  $$("#o-kind button").forEach((b) => (b.onclick = () => { setOpticsKind(b.dataset.kind); updateOptics(); }));
  for (const name of Object.keys(CLOSEUP_PRESETS)) $("m-closeup-list").append(new Option(`+${fmtNum(CLOSEUP_PRESETS[name], 1)} D`, name));
  $("m-closeup-add").onclick = () => { addCloseupRow().querySelector(".cu-name").focus(); };
  bindLensSearch();
  $("o-profile").onchange = (e) => {
    if ($("o-dirty").textContent && !window.confirm(t("Le modifiche non salvate andranno perse. Continuare?"))) {
      e.target.value = editingProfile;
      return;
    }
    editProfile(e.target.value);
  };
  $("o-undo").onclick = () => editProfile(editingProfile);
  $("o-save").onclick = (e) => {
    const name = editingProfile || (window.prompt(t("Nome del profilo (es. 10× GFP)"), "") || "").trim();
    if (name) act(e.target, () => saveProfile(name), t("Profilo salvato"));
  };
  $("o-profile-save").onclick = (e) => {
    const name = (window.prompt(t("Nome del nuovo profilo"), editingProfile) || "").trim();
    if (name) act(e.target, () => saveProfile(name), t("Profilo salvato"));
  };
  $("o-profile-del").onclick = (e) => {
    const name = editingProfile;
    if (!name || !window.confirm(t("Eliminare il profilo «{name}»?", { name }))) return;
    act(e.target, async () => {
      const profiles = await api("/api/optics/profiles/delete", { name });
      S.settings.optics_profiles = profiles;
      renderOpticsProfiles();
      editProfile("");
      updateSummary();
    }, t("Profilo eliminato"));
  };
  $("s-optics").addEventListener("change", updateSummary);
  $("s-optics-edit").onclick = () => {
    switchTab("optics");
    if (!$("o-dirty").textContent) editProfile($("s-optics").value);
  };
}

// ---------------- obiettivi fotografici: database Lensfun + elenco personale ----------------
// web/data/lenses-lensfun.json (CC BY-SA 3.0, generato da tools/lensfun_import.py) e
// web/data/lenses-extra.json (ottiche macro dedicate che Lensfun non ha) si caricano alla prima ricerca.
let lensSource = "", lensDb = null, lensDbLoading = null, lensHits = [], lensActive = -1;
const customLenses = () => (S && S.settings.custom_lenses) || [];
// marca + modello senza ripetere la marca («Nikon» + «Nikon AF-S …»), come lens_name in backend/optics.py
const lensName = (l) => {
  const maker = (l.maker || "").trim(), model = (l.model || "").trim();
  return maker && model.toLowerCase().startsWith(maker.toLowerCase()) ? model : [maker, model].filter(Boolean).join(" ");
};
const lensKey = (l) => `${(l.maker || "").toLowerCase()}|${(l.model || "").toLowerCase()}`;

function loadLensDb() {
  if (lensDb) return Promise.resolve(lensDb);
  lensDbLoading = lensDbLoading || Promise.all(["/data/lenses-lensfun.json", "/data/lenses-extra.json"].map((u) =>
    fetch(u).then((r) => (r.ok ? r.json() : { lenses: [] })).catch(() => ({ lenses: [] }))))
    .then(([lf, extra]) => {
      const norm = (l, source) => ({ maker: l.maker, model: l.model, mounts: l.mounts || [], focal: l.focal,
        f: l.f, mag: l.mag, macro: !!l.macro, source });
      lensDb = [...(extra.lenses || []).map((l) => norm(l, "extra")), ...(lf.lenses || []).map((l) => norm(l, "lensfun"))];
      $("m-db-hint").title = lf.count ? t("{n} obiettivi da Lensfun ({date})", { n: lf.count, date: lf.source_date || "" }) : "";
      return lensDb;
    });
  return lensDbLoading;
}

function allLenses() {
  const mine = customLenses().map((l) => ({ maker: l.maker, model: l.model, mounts: l.mounts || [],
    focal: [l.focal_mm, l.focal_mm], f: l.max_aperture, mag: l.max_magnification, macro: true, source: "custom" }));
  return [...mine, ...(lensDb || [])];
}

// tutte le parole devono comparire in marca, modello o attacco; prima i propri, poi i macro
function searchLenses(q) {
  const words = q.toLowerCase().replace(/[,]/g, ".").split(/\s+/).filter(Boolean);
  if (!words.length) return [];
  const hits = [];
  for (const l of allLenses()) {
    const hay = `${l.maker} ${l.model} ${l.mounts.join(" ")}`.toLowerCase();
    if (words.every((w) => hay.includes(w))) hits.push(l);
  }
  const rank = (l) => (l.source === "custom" ? 0 : l.macro ? 1 : 2);
  hits.sort((a, b) => rank(a) - rank(b) || a.maker.localeCompare(b.maker) || a.model.localeCompare(b.model));
  return hits.slice(0, 40);
}

function lensLine(l) {
  const [a, b] = l.focal || [];
  const parts = [a ? (b && b !== a ? `${fmtNum(a)}–${fmtNum(b)} mm` : `${fmtNum(a)} mm`) : ""];
  if (l.f) parts.push(`f/${fmtNum(l.f, 1)}`);
  if (l.mag) parts.push(t("fino a {m}×", { m: fmtNum(l.mag, 2) }));
  if (l.mounts.length) parts.push(l.mounts.slice(0, 3).join(", ") + (l.mounts.length > 3 ? "…" : ""));
  return parts.filter(Boolean).join(" · ");
}

function renderLensResults() {
  const ul = $("m-results"), q = $("m-search").value.trim();
  ul.innerHTML = "";
  if (!q) { ul.classList.add("hidden"); return; }
  if (!lensHits.length) {
    ul.innerHTML = `<li class="empty">${escapeHtml(t("Nessun obiettivo trovato: scrivilo nei campi qui sotto e aggiungilo al tuo elenco"))}</li>`;
  }
  lensHits.forEach((l, i) => {
    const li = document.createElement("li");
    li.setAttribute("role", "option");
    li.setAttribute("aria-selected", String(i === lensActive));
    const tags = (l.source === "custom" ? `<span class="tag">${escapeHtml(t("mio"))}</span>` : "")
      + (l.macro && l.source !== "custom" ? `<span class="tag macro">macro</span>` : "");
    li.innerHTML = `<b>${escapeHtml(lensName(l))}${tags}</b><span>${escapeHtml(lensLine(l))}</span>`;
    li.onmousedown = (e) => { e.preventDefault(); pickLens(l); };
    ul.append(li);
  });
  ul.classList.remove("hidden");
}

function pickLens(l) {
  const [a, b] = l.focal || [];
  $("m-maker").value = l.maker || "";
  $("m-model").value = l.model || "";
  $("m-focal").value = a ?? "";
  $("m-fmax").value = l.f ?? "";
  lensSource = l.source === "extra" ? "focus_stack" : l.source;
  let note = "";
  if (b && a && b !== a) note = t("Zoom {a}–{b} mm: correggi la focale con quella usata", { a: fmtNum(a), b: fmtNum(b) });
  if (l.mag) {
    if ($("m-mag").value === "") $("m-mag").value = l.mag;
    note = (note ? note + " · " : "") + t("Rapporto massimo dell'obiettivo: {m}×", { m: fmtNum(l.mag, 2) });
  } else if (!note) note = t("Indica sotto il rapporto di riproduzione usato (sulla scala dell'obiettivo)");
  $("m-lens-note").textContent = note;
  $("m-search").value = "";
  lensHits = []; lensActive = -1;
  renderLensResults();
  updateOptics();
}

function renderLensButtons() {
  const key = lensKey({ maker: $("m-maker").value.trim(), model: $("m-model").value.trim() });
  const mine = customLenses().some((l) => lensKey(l) === key);
  $("m-lens-del").classList.toggle("hidden", !mine);
  // il testo si riscrive solo se cambia: Safari annulla il clic se il testo del pulsante viene sostituito
  // fra pressione e rilascio (l'uscita dal campo Focale lancia "change" proprio in quel momento)
  const label = mine ? t("Aggiorna nel mio elenco") : t("＋ Aggiungi al mio elenco");
  if ($("m-lens-add").textContent !== label) $("m-lens-add").textContent = label;
  $("m-lens-add").disabled = !$("m-model").value.trim() || !(optNum("m-focal") > 0);
}

function bindLensSearch() {
  const input = $("m-search");
  input.addEventListener("focus", () => loadLensDb());
  input.addEventListener("input", async () => {
    await loadLensDb();
    lensHits = searchLenses(input.value); lensActive = lensHits.length ? 0 : -1;
    renderLensResults();
  });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      if (!lensHits.length) return;
      e.preventDefault();
      lensActive = (lensActive + (e.key === "ArrowDown" ? 1 : -1) + lensHits.length) % lensHits.length;
      renderLensResults();
      $("m-results").children[lensActive]?.scrollIntoView({ block: "nearest" });
    } else if (e.key === "Enter" && lensActive >= 0) { e.preventDefault(); pickLens(lensHits[lensActive]); }
    else if (e.key === "Escape") { input.value = ""; lensHits = []; renderLensResults(); }
  });
  input.addEventListener("blur", () => setTimeout(() => $("m-results").classList.add("hidden"), 150));
  for (const id of ["m-maker", "m-model", "m-focal"]) $(id).addEventListener("input", () => { $("m-lens-note").textContent = ""; renderLensButtons(); });
  $("m-lens-add").onclick = (e) => act(e.target, async () => {
    const lens = { maker: $("m-maker").value.trim(), model: $("m-model").value.trim(), focal_mm: optNum("m-focal"),
      max_aperture: optNum("m-fmax"), max_magnification: optNum("m-mag") };
    S.settings.custom_lenses = await api("/api/lenses/save", lens);
    lensSource = "custom";
    renderLensButtons(); updateOptics();
  }, t("Obiettivo salvato nel tuo elenco"));
  $("m-lens-del").onclick = (e) => {
    const name = lensName({ maker: $("m-maker").value, model: $("m-model").value });
    if (!window.confirm(t("Togliere «{name}» dal tuo elenco? I profili che lo usano restano invariati.", { name }))) return;
    act(e.target, async () => {
      S.settings.custom_lenses = await api("/api/lenses/delete", { maker: $("m-maker").value.trim(), model: $("m-model").value.trim() });
      if (lensSource === "custom") lensSource = "";
      renderLensButtons(); updateOptics();
    }, t("Obiettivo tolto dal tuo elenco"));
  };
}

// ---------------- calibrazione (dark, flat, dark dei flat) ed esposizione automatica ----------------
// La libreria sta in <cartella delle pile>/_calibrazione; il server sceglie i set adatti all'avvio di ogni pila.
let calibKind = "dark", calibView = null, calibSig = "", calibLoading = false, calibRunKey = null;
const CALIB_LABELS = () => ({ dark: t("Dark"), flat: t("Flat"), flat_dark: t("Dark dei flat") });
const CALIB_HINTS = () => ({
  dark: t("Tappo sull'obiettivo e oculare del mirino coperto. Stessi ISO, tempo di posa (o posa B) dei light, e possibilmente la stessa temperatura: imposta la fotocamera come per la pila."),
  flat: t("Campo illuminato in modo uniforme (diffusore, vetrino o cartoncino bianco fuori fuoco), con la stessa ottica, lo stesso diaframma e lo stesso profilo ottico dei light. Il tempo di posa si trova da solo."),
  flat_dark: t("Tappo sull'obiettivo. ISO e tempo di posa vengono presi dall'ultimo set di flat di questa fotocamera."),
});

function setCalibKind(kind) {
  calibKind = kind;
  $$("#k-kind button").forEach((b) => b.setAttribute("aria-checked", b.dataset.kind === kind));
  $("k-hint").textContent = CALIB_HINTS()[kind];
  $$("#card-calib .k-flat").forEach((el) => el.classList.toggle("hidden", kind !== "flat"));
  if (S) renderCalibration(S.camera, running());
}

// la libreria si rilegge quando cambiano fotocamera, ISO, tempo, profilo o lo stato della calibrazione
async function refreshCalibration(force = false) {
  if (!S || calibLoading) return;
  const c = S.camera, cur = (k) => (c.settings && c.settings[k] && c.settings[k].current) || "";
  const sig = [c.connected, c.model, cur("iso"), cur("shutterspeed"), cur("aperture"), S.settings.output_root,
    S.settings.sequence.optics_profile, $("s-optics").value, S.calibration && S.calibration.state, S.sequence.state].join("|");
  if (!force && sig === calibSig) return;
  calibSig = sig;
  calibLoading = true;
  try { calibView = await api("/api/calibration", undefined, "GET"); } catch { /* server non raggiungibile */ }
  calibLoading = false;
  renderLibrary();
  updateSummary();
}

const shortDate = (iso) => {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString(LOCALE, { day: "2-digit", month: "2-digit", year: "2-digit", hour: "2-digit", minute: "2-digit" });
};

function matchText(m) {
  if (!m) return t("Connetti la fotocamera per sapere quali set userebbe la prossima pila");
  const part = (key, label) => {
    const e = m[key];
    return e ? `${label} ✓ <span class="muted">(${escapeHtml(t("{n} fotogrammi", { n: e.frames }))} · ${escapeHtml(shortDate(e.created))})</span>`
      : `${label} —`;
  };
  return `${part("darks", t("Dark"))} · ${part("flats", t("Flat"))} · ${part("flat_darks", t("Dark dei flat"))}`;
}

// riga nel riepilogo della sequenza
function calibrationSummary() {
  if (!calibView || !calibView.match) return "";
  const m = calibView.match, n = ["darks", "flats", "flat_darks"].filter((k) => m[k]).length;
  return t("Calibrazione per questa pila: {txt}", { txt: matchText(m) }) + (n ? "" : " · " + t("nessun set adatto nella libreria"));
}

// riepilogo di Calibrazione: quali set userebbe la prossima pila
function renderCalibSummary(m) {
  const one = (key, id) => {
    const e = m && m[key], b = $(id), x = $(id + "x");
    b.textContent = !m ? "—" : e ? "✓ " + shortDate(e.created) : t("manca");
    b.className = !m ? "" : e ? "ok-t" : "warn-t";
    x.textContent = e ? t("{n} fotogrammi", { n: e.frames }) : !m ? t("connetti la fotocamera") : "";
  };
  one("darks", "ksum-dark"); one("flats", "ksum-flat"); one("flat_darks", "ksum-fdark");
  $("k-dot").classList.toggle("hidden", !m || (!!m.darks && !!m.flats));
}

function renderLibrary() {
  if (!calibView) return;
  $("k-root").textContent = t("Cartella: {path}", { path: calibView.root });
  $("k-match").innerHTML = t("Per la prossima pila, con le impostazioni attuali: {txt}", { txt: matchText(calibView.match) });
  renderCalibSummary(calibView.match);
  const tbody = $("k-table").querySelector("tbody");
  const rows = calibView.sets.map((s) => {
    const lv = s.mean_level_pct ? Math.max(...Object.values(s.mean_level_pct)) : null;
    const temp = s.temperature_c ? `${fmtNum(s.temperature_c.mean, 1)} °C` : "—";
    const state = s.state === "completed" ? "" : ` (${s.state === "interrupted" ? t("interrotto") : s.state === "running" ? t("in corso") : t("errore")})`;
    const cells = [CALIB_LABELS()[s.type] + state, shortDate(s.created), s.camera.model || "—", s.camera.iso || "—",
      s.bulb_s ? t("posa B {s} s", { s: fmtNum(s.bulb_s, 1) }) : s.camera.shutterspeed || "—",
      s.type === "flat" ? (s.optics_profile || t("nessuno")) : "—", s.frames, lv == null ? "—" : `${fmtNum(lv, 1)} %`, temp];
    const del = `<td><button class="btn ghost small" data-del="${escapeHtml(s.name)}" data-frames="${s.frames}" title="${escapeHtml(t("Sposta nel Cestino la cartella di questo set"))}">${escapeHtml(t("Elimina"))}</button></td>`;
    return `<tr title="${escapeHtml(s.path)}">${cells.map((v) => `<td>${escapeHtml(String(v))}</td>`).join("")}${del}</tr>`;
  });
  tbody.innerHTML = rows.length ? rows.join("")
    : `<tr class="empty"><td colspan="10">${escapeHtml(t("Nessun set di calibrazione: scatta dark e flat con la card qui sopra"))}</td></tr>`;
}

function renderCalibration(c, run) {
  const k = S.calibration || {}, busy = !!k.busy, cur = (key) => (c.settings && c.settings[key] && c.settings[key].current) || "—";
  refreshCalibration();
  const labels = { idle: t("Pronta"), exposing: t("Esposizione…"), running: t("In corso"), stopping: t("Arresto…"), done: t("Completata"), error: t("Errore") };
  const isExpo = k.state === "exposing" && !k.kind;
  // card esposizione dei light
  setChip("x-chip", isExpo ? labels.exposing : k.exposure && !k.kind ? (k.exposure.within_tolerance ? t("Fatto") : t("Approssimata")) : "—",
    isExpo ? "busy" : k.exposure && !k.kind ? (k.exposure.within_tolerance ? "ok" : "busy") : "");
  $("x-start").disabled = busy || run || !c.connected || !k.tool;
  $("x-stop").classList.toggle("hidden", !isExpo);
  if (!k.tool) $("x-result").textContent = t("Strumento di misura fs-rawstat mancante: python3 tools/rawstat/build.py");
  else if (!k.kind && (isExpo || k.exposure || k.state === "error")) {
    const hist = (k.history || []).map((h) => `${escapeHtml(h.shutter)} → ${fmtNum(h.level_pct, 1)} %`).join(" · ");
    $("x-result").innerHTML = `${escapeHtml(k.message || "")}${hist ? `<br><span class="muted">${hist}</span>` : ""}`
      + (k.exposure && k.exposure.linear === false ? `<br><span class="warn-text">${escapeHtml(t("Misura su JPEG: valori stimati. Con il RAW la misura è esatta."))}</span>` : "");
  }
  // card frame di calibrazione
  const mine = !!k.kind;
  // il tipo selezionato segue la calibrazione avviata (anche da un'altra finestra): mai «Dark» acceso mentre scatta flat
  const runKey = mine ? `${k.kind}|${k.folder || ""}|${k.total}` : "";
  if (runKey && runKey !== calibRunKey && k.kind !== calibKind) setCalibKind(k.kind);
  calibRunKey = runKey;
  setChip("k-chip", mine ? labels[k.state] || k.state : t("Pronta"),
    mine ? { exposing: "busy", running: "busy", stopping: "busy", done: "ok", error: "bad" }[k.state] || "" : "");
  const flat = calibView && calibView.flat;
  let info = t("Fotocamera: {model} · ISO {iso} · {sh} · {ap}", { model: c.connected ? c.model : t("non connessa"), iso: cur("iso"), sh: cur("shutterspeed"), ap: cur("aperture") });
  if (calibKind === "dark" && S.settings.sequence.bulb_s) info += " · " + t("posa B {s} s (come i light)", { s: fmtNum(S.settings.sequence.bulb_s, 1) });
  if (calibKind === "flat") {
    const prof = $("s-optics").value;
    info += "<br>" + (prof ? t("Profilo ottico: «{name}» (quello scelto nella card Sequenza)", { name: escapeHtml(prof) })
      : t("Nessun profilo ottico scelto nella card Sequenza: i flat varranno per le pile senza profilo"));
  }
  if (calibKind === "flat_dark") info += "<br>" + (flat
    ? t("Flat di riferimento: {date} · ISO {iso} · {sh}", { date: escapeHtml(shortDate(flat.created)), iso: escapeHtml(flat.camera.iso || "—"), sh: escapeHtml(flat.camera.shutterspeed || "—") })
    : `<span class="warn-text">${escapeHtml(t("Nessun set di flat per questa fotocamera: scatta prima i flat"))}</span>`);
  if (calibKind !== "flat" && !(S.settings.sequence.capture_mode === "download")) info += `<br><span class="warn-text">${escapeHtml(t("I frame vengono sempre scaricati sul Mac, nella libreria."))}</span>`;
  $("k-info").innerHTML = info;
  $("k-start").disabled = busy || run || !c.connected || !k.tool || (calibKind === "flat_dark" && !flat);
  $("k-stop").disabled = !busy || !mine;
  $$("#k-kind button, #k-count, #k-target, #k-table button[data-del]").forEach((el) => (el.disabled = busy || run));
  const total = mine ? k.total : num("k-count") || 0;
  $("k-count-label").textContent = `${mine ? k.index : 0} / ${total}`;
  $("k-bar").style.width = `${mine && k.total ? (k.index / k.total) * 100 : 0}%`;
  $("k-level").textContent = mine && k.level_pct != null ? t("livello {v} %", { v: fmtNum(k.level_pct, 1) }) : "";
  $("k-progress").textContent = mine ? [CALIB_LABELS()[k.kind], k.message, k.state !== "running" && k.folder ? k.folder : ""].filter(Boolean).join(" · ") : "";
}

function bindCalibration() {
  $$("#k-kind button").forEach((b) => (b.onclick = () => setCalibKind(b.dataset.kind)));
  setCalibKind("dark");
  $("k-start").onclick = (e) => {
    const capped = calibKind !== "flat";
    if (capped && !window.confirm(t("Metti il tappo sull'obiettivo e copri l'oculare del mirino, poi premi OK."))) return;
    if (!capped && !window.confirm(t("Illumina il campo in modo uniforme con la stessa ottica e lo stesso diaframma dei light, poi premi OK."))) return;
    act(e.target, () => api("/api/calibration/start", { kind: calibKind, count: Math.round(num("k-count") || 16), target_pct: num("k-target") || 50 }));
  };
  $("k-stop").onclick = (e) => act(e.target, () => api("/api/calibration/stop"));
  $("x-stop").onclick = (e) => act(e.target, () => api("/api/calibration/stop"));
  $("x-start").onclick = (e) => act(e.target, () => api("/api/exposure/auto", { target_pct: num("x-target") || 85, stat: $("x-stat").value }));
  $("k-open").onclick = (e) => act(e.target, () => api("/api/calibration/open"));
  // Elimina (delega: le righe della tabella si ricreano a ogni aggiornamento della libreria)
  $("k-table").addEventListener("click", (e) => {
    const b = e.target.closest("button[data-del]");
    if (!b) return;
    const name = b.dataset.del;
    if (!window.confirm(t("Spostare nel Cestino il set «{name}» ({n} fotogrammi)? Le pile che lo indicano nel loro sequence.json non lo troveranno più.", { name, n: b.dataset.frames }))) return;
    act(b, async () => { calibView = await api("/api/calibration/delete", { name }); renderLibrary(); updateSummary(); }, t("Set spostato nel Cestino"));
  });
  $("k-count").addEventListener("input", () => S && renderCalibration(S.camera, running()));
}

// ---------------- visualizzatore ----------------
let viewerWin = null;
function openViewer(shotId) {
  const url = "/viewer.html" + (shotId != null ? `#${shotId}` : "");
  // nell'app per Mac focus() non basta: il visualizzatore poteva restare nel Dock o su un'altra scrivania.
  // Lo riporta l'app (se il comando non c'è, app vecchia, resta focus())
  const front = () => window.FSNative && FSNative.focusViewer().catch(() => {});
  if (viewerWin && !viewerWin.closed) {
    viewerWin.location.hash = shotId != null ? String(shotId) : "";
    viewerWin.focus();
    front();
    return;
  }
  // window.open sincrono (dentro il clic): dopo un await la finestra verrebbe bloccata come popup
  viewerWin = window.open(url, "focusstack-viewer", "width=1280,height=900");
  if (!viewerWin) location.href = url; // finestre popup bloccate
  else front();   // pagina ricaricata: WebKit riusa il visualizzatore con lo stesso nome, ma non lo porta davanti
}

// ---------------- eventi ----------------
async function refreshPorts() {
  try {
    const ports = await api("/api/ports", undefined, "GET");
    const sel = $("f-port"), saved = sel.dataset.saved || (S && S.settings.focuser_port);
    sel.innerHTML = "";
    if (!ports.length) sel.add(new Option(t("Nessuna porta USB trovata"), ""));
    for (const p of ports) {
      const label = p.description && p.description !== "n/a" ? `${p.device} — ${p.description}` : p.device;
      sel.add(new Option(label, p.device, false, p.device === saved));
    }
  } catch (e) { toast(e.message, true); }
}

async function detectCameras() {
  const cams = await act($("c-detect"), () => api("/api/camera/detect"));
  if (!cams) return;
  const sel = $("c-model");
  sel.innerHTML = "";
  if (!cams.length) { sel.add(new Option(t("Nessuna fotocamera trovata"), "")); toast(t("Nessuna fotocamera rilevata"), true); return; }
  for (const c of cams) sel.add(new Option(`${c.model} (${c.port})`, JSON.stringify(c)));
}

// ampiezze per decine da 1 a jog_max (impostazione "Comandi manuali")
function jogSizes() {
  const max = (S && S.settings.jog_max) || 1000, out = [];
  for (let s = 1; s <= max; s *= 10) out.push(s);
  return out;
}

function renderJogSizes() {
  const sizes = jogSizes(), hold = !!(S && S.settings.jog_hold);
  // tratto del movimento continuo: aggiornato sempre (non dipende dalle ampiezze)
  const chunk = (S && S.settings.hold_chunk_steps) || 500;
  $("jog-chunk-row").classList.toggle("hidden", !hold);
  if (document.activeElement !== $("jog-chunk") && $("jog-chunk").value !== String(chunk)) $("jog-chunk").value = chunk;
  const chunkUm = umPerStep() ? t("{n} passi = {um}", { n: fmtInt(chunk), um: fmtUm(chunk) }) : "&nbsp;";
  if ($("jog-chunk-um").innerHTML !== chunkUm) $("jog-chunk-um").innerHTML = chunkUm;
  const sig = sizes.join(",") + (hold ? "h" : "");
  if (sig === jogSizesSig) return;
  jogSizesSig = sig;
  $("jog-size").innerHTML = sizes.map((s) =>
    `<button data-size="${s}" aria-checked="${s === jogSize}">${s >= 10000 ? s / 1000 + "k" : s}</button>`).join("");
  $$("#jog-size button").forEach((b) => (b.onclick = () => setJogSize(Number(b.dataset.size))));
  if (!sizes.includes(jogSize)) {
    jogSize = sizes.includes(100) ? 100 : sizes[sizes.length - 1];
    $$("#jog-size button").forEach((b) => b.setAttribute("aria-checked", Number(b.dataset.size) === jogSize));
  }
  $("jog-keys").innerHTML = t("Tastiera: ↑ ↓ muovi · ⇧ ×10 · 1–{n} ampiezza · <kbd>Esc</kbd> stop", { n: sizes.length }) +
    (hold ? "<br>" + t("Tieni premuto un pulsante per muovere senza fermarti") : "");
  $$("#jog-max button").forEach((b) => b.setAttribute("aria-checked", Number(b.dataset.max) === sizes[sizes.length - 1]));
  $("jog-hold").checked = hold;
}

// Pulsante Allontana/Avvicina: un tocco sposta di jogSize passi; tenuto premuto oltre HOLD_DELAY
// muove senza fermarsi fino al rilascio (se l'opzione è attiva). Durante il movimento la pagina
// conferma al server ogni 250 ms che il pulsante è ancora premuto.
// Pressione di Avvicina/Allontana, con il pulsante o con i tasti ↑/↓: breve = un colpo (tap), tenuta oltre
// HOLD_DELAY = movimento continuo (conferme ogni 250 ms) finché non si rilascia.
function jogPress(signFn, onHolding = () => {}) {
  let pressed = false, holding = false, timer = null, beat = null, tap = null;
  const stopHold = () => {
    clearInterval(beat); beat = null;
    onHolding(false);
    if (holding) { holding = false; holdCall({ direction: 0 }).catch(() => {}); }
  };
  // start = pulsante appena premuto; le conferme successive vengono rifiutate dal server dopo uno STOP
  const sendHold = (start) => holdCall({ direction: signFn(), start }).then((r) => {
    if (r && r.stopped) { pressed = false; stopHold(); }
  }).catch((e) => {
    pressed = false; stopHold(); toast(e.message, true);
  });
  const press = (tapFn) => {
    if (pressed) return;
    pressed = true; tap = tapFn;
    timer = setTimeout(() => {
      timer = null;
      if (!pressed || !(S && S.settings.jog_hold) || !S.focuser.connected || running()) return;
      holding = true;
      onHolding(true);
      sendHold(true);
      beat = setInterval(() => sendHold(false), 250);
    }, HOLD_DELAY);
  };
  const release = () => {
    if (!pressed) return;
    pressed = false;
    if (timer) { clearTimeout(timer); timer = null; }
    if (holding || beat) stopHold();
    else tap();
  };
  window.addEventListener("blur", release);
  document.addEventListener("visibilitychange", () => { if (document.hidden) release(); });
  return { press, release };
}

function bindJogButton(btn, signFn) {
  const p = jogPress(signFn, (on) => btn.classList.toggle("holding", on));
  btn.addEventListener("pointerdown", (e) => {
    if (btn.disabled || e.button !== 0) return;
    e.preventDefault();
    try { btn.setPointerCapture(e.pointerId); } catch { /* opzionale */ }
    p.press(() => jog(signFn()));
  });
  ["pointerup", "pointercancel", "lostpointercapture"].forEach((ev) => btn.addEventListener(ev, p.release));
  btn.addEventListener("click", (e) => { if (e.detail === 0) jog(signFn()); });  // Invio/spazio da tastiera
}

// posizione scritta nel campo "Vai alla posizione": null se vuoto o non è un intero ≥ 0
function gotoValue() {
  const raw = $("f-goto").value.trim();
  if (raw === "" || !/^\d+$/.test(raw)) return null;
  return Number(raw);
}

function updateGotoBtn() {
  const f = S && S.focuser;
  $("f-goto-btn").disabled = !(f && f.connected) || running() || gotoValue() == null;
}

function jog(sign) {
  if (!S || !S.focuser.connected || running()) return;
  api("/api/focuser/jog", { delta: sign * jogSize })
    .then((r) => r && r.clamped && toast(t("Fermato al fine corsa")))
    .catch((e) => toast(e.message, true));
}

function setJogSize(size) {
  jogSize = size;
  $$("#jog-size button").forEach((b) => b.setAttribute("aria-checked", Number(b.dataset.size) === size));
  try { localStorage.setItem("fs-jog", String(size)); } catch { /* opzionale */ }
  if (S) render();
}

// ---- guida HTML (web/guide/<lingua>.html, da docs/guida/genera_guida_web.py). «?» in alto apre il capitolo
// della scheda aperta, il «?» nel titolo delle card la sezione giusta. Le chiavi sono i nomi fissi di ALIASES nel
// generatore: se i capitoli cambiano numero si aggiorna solo lì.
const GUIDE_TABS = { session: "interfaccia", optics: "profili-ottici", calib: "calibrazione", config: "fine-corsa", log: "problemi" };
const GUIDE_CARDS = {
  "card-focuser": "focheggiatore", "card-seq": "sequenza", "card-camera": "fotocamera", "card-last": "live-view",
  "card-optics": "profili-ottici", "card-limits": "fine-corsa", "card-mech": "meccanica", "card-jog": "comandi-manuali",
  "card-motor": "motore", "card-lang": "lingua", "card-updates": "aggiornamenti", "card-temp": "temperatura",
  "card-expo": "calibrazione-esposizione", "card-calib": "calibrazione-frame", "card-library": "calibrazione-libreria",
  "card-remote": "smartphone",
};
const guideUrl = (key) => `/guide/${["it", "en", "fr", "de", "es"].includes(LANG) ? LANG : "en"}.html${key ? "#" + key : ""}`;
function setupGuideLinks() {
  for (const [id, key] of Object.entries(GUIDE_CARDS)) {
    const h2 = document.querySelector(`#${id} .card-head h2`);
    if (!h2 || h2.querySelector(".help")) continue;
    const a = document.createElement("a");
    a.className = "help"; a.href = guideUrl(key); a.target = "fs-guide"; a.textContent = "?";
    a.title = t("Apri la guida a questa parte"); a.setAttribute("aria-label", a.title);
    a.setAttribute("data-i18n-skip", "");
    h2.append(" ", a);   // dentro il titolo: chip e pulsanti della testata restano dove sono
  }
}

function switchTab(name) {
  $$(".tabs button").forEach((b) => b.setAttribute("aria-selected", b.dataset.tab === name));
  $$(".view").forEach((v) => v.classList.toggle("hidden", v.id !== `view-${name}`));
  if (name === "log" && S) { renderLog(); $("log").scrollTop = $("log").scrollHeight; }
  if (name === "calib" || name === "session") refreshCalibration(true);
  const view = $(`view-${name}`);
  if (view && view._spy) requestAnimationFrame(view._spy);
  $("guide-btn").href = guideUrl(GUIDE_TABS[name] || "");
  try { localStorage.setItem("fs-tab", name); } catch { /* opzionale */ }
}

function bind() {
  $$(".tabs button").forEach((b) => (b.onclick = () => switchTab(b.dataset.tab)));
  $("fw-update").onclick = updateFirmware;
  $("up-check").onclick = () => api("/api/app/check").then((a) => toast(a.error || (a.available ? t("Disponibile la versione {v}", { v: a.latest }) : t("Nessun aggiornamento")), !!a.error)).catch((e) => toast(e.message, true));
  $("theme-btn").onclick = () => {
    const t = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(t);
    try { localStorage.setItem("fs-theme", t); } catch { /* opzionale */ }
  };

  // focheggiatore
  $("f-refresh").onclick = refreshPorts;
  $("f-connect").onclick = (e) => act(e.target, () => api("/api/focuser/connect", { port: $("f-port").value, simulate: $("f-sim").checked }));
  $("f-disconnect").onclick = (e) => act(e.target, () => api("/api/focuser/disconnect"));
  bindJogButton($("jog-away"), () => -towardSign());
  bindJogButton($("jog-toward"), () => towardSign());
  $$("#jog-max button").forEach((b) => (b.onclick = () => act(null, async () => {
    S.settings = await api("/api/settings", { jog_max: Number(b.dataset.max) });
    render();
  }, t("Ampiezze aggiornate"))));
  if (window.FSNative) {            // solo nell'app per Mac: dove aprire il visualizzatore
    $("card-viewer").classList.remove("hidden");
    $("nav-viewer").classList.remove("hidden");
    FSNative.getPref("viewerOtherScreen").then((v) => { $("v-other-screen").checked = !!v; });
    $("v-other-screen").onchange = (e) => FSNative.setPref("viewerOtherScreen", e.target.checked);
  }
  $("jog-hold").onchange = (e) => act(null, async () => {
    S.settings = await api("/api/settings", { jog_hold: e.target.checked });
    render();
  });
  $("jog-chunk").onchange = (e) => act(null, async () => {
    S.settings = await api("/api/settings", { hold_chunk_steps: Math.round(Number(e.target.value)) });
    render();
  }, t("Tratto aggiornato"));
  $("opt-coil-seq").onchange = (e) => act(null, async () => {
    S.settings = await api("/api/settings", { coil_during_sequence: e.target.checked });
    render();
  });
  // "Vai" senza un numero valido resta disattivato: un campo vuoto vale 0 e mandava il motore a zero
  $("f-goto-btn").onclick = (e) => {
    const pos = gotoValue();
    if (pos == null) return;
    act(e.target, () => api("/api/focuser/move", { position: pos })).finally(updateGotoBtn);
  };
  $("f-goto").oninput = updateGotoBtn;
  $("f-goto").onkeydown = (e) => { if (e.key === "Enter") $("f-goto-btn").click(); };
  $("f-halt").onclick = () => act(null, () => api("/api/focuser/halt"), t("Stop"));

  // fotocamera
  $("c-detect").onclick = detectCameras;
  $("c-connect").onclick = (e) => act(e.target, () => {
    let sel = {};
    try { sel = JSON.parse($("c-model").value || "{}"); } catch { /* automatico */ }
    return api("/api/camera/connect", { model: sel.model || "", port: sel.port || "", simulate: $("c-sim").checked });
  });
  $("c-disconnect").onclick = (e) => act(e.target, () => api("/api/camera/disconnect"));
  // «Simulatore» e l'elenco si escludono: scegliere una fotocamera vera toglie la spunta (prima restava spuntata
  // da una prova precedente e si collegava di nuovo il simulatore); con la spunta l'elenco è grigio
  const syncSim = () => { $("c-model").disabled = $("c-sim").checked; $("c-detect").disabled = $("c-sim").checked; };
  $("c-model").addEventListener("change", () => { if ($("c-model").value) $("c-sim").checked = false; syncSim(); });
  $("c-sim").addEventListener("change", syncSim);
  for (const [name, id] of Object.entries(CAM_FIELDS)) {
    $(id).onchange = (e) => {
      // le Sony raggiungono il valore «a scatti»: se dopo 12 s non è arrivato, lo si dice invece di lasciare il menu grigio
      const value = e.target.value;
      const slow = setTimeout(() => toast(t("La fotocamera non ha ancora accettato {v}. Se resta bloccata, scollega e ricollega il cavo USB, oppure spegnila e riaccendila.", { v: value }), true), 12000);
      act(e.target, async () => {
        await api("/api/camera/settings", { name, value });
        camSettingsSig = ""; // ridisegna con il valore effettivamente accettato dalla fotocamera
      }).finally(() => clearTimeout(slow));
    };
  }
  $("c-reload").onclick = (e) => act(e.target, () => api("/api/camera/settings/reload"));
  $("c-test").onclick = async (e) => {
    const wasLive = liveOn;
    await act(e.target, () => api("/api/camera/test", { bulb_s: num("c-bulb"), mirror_delay_ms: num("c-mirror") }), t("Scatto completato"));
    // l'avviso del live messo da parte può arrivare (via WebSocket) prima di «Scatto completato», che lo coprirebbe
    if (wasLive && liveResume) toast(t("Scatto di prova: il live view riparte quando muovi il focheggiatore"));
  };

  // ultimo scatto / visualizzatore
  $("last-thumb").onclick = () => S && S.last_shot && openViewer(S.last_shot.id);
  // con il live view acceso il visualizzatore si apre sul live view (zoom e pan)
  $("v-open").onclick = () => openViewer(liveOn ? "live" : S && S.last_shot ? S.last_shot.id : null);
  $("live-btn").onclick = () => {
    // «Ferma live» la ferma anche nel visualizzatore (e viceversa): passa dal server, vedi live_stop_rev
    if (liveOn) api("/api/camera/live/stop").catch(() => {});
    setLive(!liveOn);
    // avviato a mano: parte anche nel visualizzatore, se è aperto (stessa origine, canale fra le finestre)
    if (liveOn && windowLink) windowLink.postMessage({ live: true });
  };
  $("live-box").ondblclick = toggleLiveFullscreen;

  // sequenza
  $$("[data-mark]").forEach((b) => (b.onclick = () => {
    const id = b.dataset.mark === "start" ? "s-start" : "s-end";
    linkBegin(id); linkEdit.closed = true;
    $(id).value = S.focuser.position;
    syncCount(); linkMark(); linkDone(); updateSummary();
  }));
  ["s-start", "s-end", "s-step"].forEach((id) => $(id).addEventListener("input", () => {
    linkBegin(id); syncCount(); linkMark(); linkDone(); updateSummary();
  }));
  $("s-count").addEventListener("change", () => {
    linkBegin("s-count");
    // per eccesso: con n-1 passi si copre tutta la corsa e gli scatti restano quelli scritti (per difetto ne
    // aggiungeva uno, per il resto della divisione)
    const n = Math.max(2, num("s-count")), span = Math.abs(num("s-end") - num("s-start"));
    $("s-step").value = Math.max(1, Math.ceil(span / (n - 1)));
    syncCount(); linkMark(); linkDone(); updateSummary();
  });
  $("s-summary").addEventListener("toggle", (e) => { if (e.target.id === "s-sum-more") summaryOpen = e.target.open; }, true);
  // una nuova modifica dello stesso campo, dopo esserne usciti, riparte dai valori di quel momento
  LINKED.forEach((id) => $(id).addEventListener("blur", () => { if (linkEdit && linkEdit.field === id) linkEdit.closed = true; }));
  ["s-settle", "s-post", "s-backlash", "s-mode", "s-repeats", "c-bulb", "c-shutter"].forEach((id) => $(id).addEventListener("input", updateSummary));
  $("c-mirror").addEventListener("change", () => { updateSummary(); renderMirrorHint(); });
  $("s-start-btn").onclick = (e) => { linkClear(); act(e.target, () => api("/api/sequence/start", formParams()), t("Sequenza avviata")); };
  $("s-pause-btn").onclick = (e) => act(e.target, () => api(S.sequence.state === "paused" ? "/api/sequence/resume" : "/api/sequence/pause"));
  $("s-stop-btn").onclick = (e) => act(e.target, () => api("/api/sequence/stop"));
  $("s-open").onclick = () => act(null, () => api("/api/open-folder"));
  $("s-root-choose").onclick = (e) => act(e.target, async () => {
    let r;
    if (window.FSNative) {          // app per Mac: finestra nativa attaccata alla finestra di Focus Stack
      const path = await FSNative.chooseFolder(S.settings.output_root, t("Cartella in cui salvare gli scatti"));
      if (!path) return;
      r = await api("/api/output-root", { path });
    } else {
      toast(t("Scegli la cartella nella finestra del Finder…"));
      r = await api("/api/choose-folder");
    }
    if (r && r.path) { S.settings.output_root = r.path; toast(t("Cartella di salvataggio aggiornata")); }
  });
  $("s-finder").onclick = (e) => act(e.target, () => api("/api/open-stack-folder"));
  $("s-new").onclick = (e) => act(e.target, async () => {
    await api("/api/sequence/reset");
    const name = $("s-name");
    name.focus();
    name.select();
  }, t("Pronta per una nuova pila: cambia il nome se serve"));
  $("s-name").addEventListener("input", () => S && renderSequence(S.focuser, S.camera, S.sequence, running()));
  $("s-name").addEventListener("keydown", (e) => { if (e.key === "Enter") e.target.blur(); });

  // preset
  $("s-preset").onchange = () => {
    const p = S.settings.presets[$("s-preset").value];
    if (!p) return;
    const map = { start: "s-start", end: "s-end", step: "s-step", settle_ms: "s-settle", post_shot_ms: "s-post",
      backlash: "s-backlash", capture_mode: "s-mode", session_name: "s-name", bulb_s: "c-bulb", mirror_delay_ms: "c-mirror",
      shots_per_position: "s-repeats", optics_profile: "s-optics" };
    for (const [k, id] of Object.entries(map)) if (p[k] !== undefined) $(id).value = p[k];
    if (p.return_to_start !== undefined) $("s-return").checked = p.return_to_start;
    if (p.sound_on_end !== undefined) $("s-sound").checked = p.sound_on_end;
    linkClear(); syncCount(); updateSummary();
  };
  $("s-preset-save").onclick = () => {
    const name = (window.prompt(t("Nome del preset (es. obiettivo 10×)"), $("s-preset").value || "") || "").trim();
    if (!name) return;
    // il nome proposto è quello del preset scelto: confermare prima di sostituirlo
    if (((S && S.settings.presets) || {})[name] && !window.confirm(t("Esiste già un preset «{name}»: sostituirlo con i valori attuali?", { name }))) return;
    const { output_root, ...data } = formParams();
    act(null, async () => {
      const r = await api("/api/presets/save", { name, data });
      S.settings.presets = r; presetSig = ""; renderPresets();
      $("s-preset").value = name;   // la tendina mostra il preset appena salvato
    }, t("Preset «{name}» salvato", { name }));
  };
  $("s-preset-del").onclick = () => {
    const name = $("s-preset").value;
    if (!name) return;
    act(null, async () => { const r = await api("/api/presets/delete", { name }); S.settings.presets = r; presetSig = ""; renderPresets(); }, t("Preset eliminato"));
  };

  // fine corsa
  $$("[data-limit-here]").forEach((b) => (b.onclick = () => {
    $(b.dataset.limitHere === "min" ? "lim-min" : "lim-max").value = S.focuser.position;
    updateLimDirty();
    toast(t("Valore copiato: premi Salva fine corsa per applicarlo"));
  }));
  $("lim-save").onclick = (e) => act(e.target, async () => {
    await api("/api/limits", { limit_min: num("lim-min"), limit_max: optNum("lim-max"), toward_specimen: $("lim-dir").value });
    const st = await api("/api/state", undefined, "GET");
    S.settings = st.settings; updateLimDirty(); renderSettingsSummary();
  }, t("Fine corsa salvati"));
  $("lim-undo").onclick = () => { loadLimitForm(S.settings); updateLimDirty(); };
  ["lim-min", "lim-max"].forEach((id) => $(id).addEventListener("input", updateLimDirty));
  $("lim-dir").addEventListener("change", updateLimDirty);
  $("lim-zero").onclick = (e) => {
    if (!confirm(t("La posizione attuale ({p}) diventerà 0. Fine corsa e sequenza verranno traslati di conseguenza. Continuare?", { p: fmtInt(S.focuser.position) }))) return;
    act(e.target, async () => {
      await api("/api/limits/zero-here");
      const st = await api("/api/state", undefined, "GET");
      loadLimitForm(st.settings);
      $("s-start").value = st.settings.sequence.start; $("s-end").value = st.settings.sequence.end;
      linkClear(); syncCount();
    }, t("Zero impostato"));
  };
  $("lim-fw").onclick = (e) => {
    const v = optNum("lim-max");
    if (v == null) return toast(t("Imposta prima il fine corsa superiore"), true);
    if (!confirm(t("Scrivere {v} come massimo nel firmware? Anche i pulsanti fisici non potranno superarlo.", { v: fmtInt(v) }))) return;
    act(e.target, async () => {
      const f = await api("/api/focuser/maxstep", { position: v });
      if (f.max_step !== v) throw new Error(t("Il firmware ha mantenuto {v}: potrebbe avere un minimo ammesso", { v: fmtInt(f.max_step) }));
      await api("/api/limits", { limit_min: num("lim-min"), limit_max: v, toward_specimen: $("lim-dir").value });
    }, t("Massimo scritto nel firmware"));
  };

  // meccanica
  // si salva da sola a ogni modifica, come le impostazioni del motore; con valori incompleti aspetta
  // (il risultato mostra già «Inserisci valori validi»)
  const saveMech = () => {
    if (!(mechUmPerStep() > 0)) return;
    act(null, () => api("/api/mechanics", {
      mode: mechMode, motor_steps_per_rev: num("m-spr"), gear_ratio: num("m-gear"), um_per_knob_rev: num("m-umrev"),
      um_per_step: mechMode === "manual" ? num("m-umstep") : null,
    }), t("Meccanica salvata"));
  };
  $$("#mech-mode button").forEach((b) => (b.onclick = () => { setMechMode(b.dataset.mode); saveMech(); }));
  ["m-spr", "m-gear", "m-umrev", "m-umstep"].forEach((id) => {
    $(id).addEventListener("input", () => { updateMechResult(); renderSettingsSummary(); });
    $(id).addEventListener("change", saveMech);
  });

  // motore
  $("mo-reload").onclick = (e) => act(e.target, () => api("/api/focuser/motor/reload"));
  for (const name of ["step_mode", "speed"]) {
    $(`mo-${name}`).onchange = (e) => {
      if (name === "step_mode" && !confirm(t("Cambiare il microstep cambia la scala delle posizioni e dei fine corsa. Continuare?"))) {
        motorSig = ""; return;
      }
      act(e.target, () => api("/api/focuser/motor", { name, value: Number(e.target.value) }), t("Impostazione inviata"));
    };
  }
  for (const name of ["coil_power", "reverse", "backlash_in_enabled", "backlash_out_enabled"]) {
    $(`mo-${name}`).onchange = (e) => act(e.target, () => api("/api/focuser/motor", { name, value: e.target.checked }), t("Impostazione inviata"));
  }
  for (const name of ["backlash_in_steps", "backlash_out_steps"]) {
    $(`mo-${name}`).onchange = (e) => {
      const v = Number(e.target.value);
      if (e.target.value.trim() === "" || !Number.isInteger(v) || v < 0 || v > 255) {
        toast(t("Il gioco del firmware va da 0 a 255 passi"), true); motorSig = ""; return;
      }
      act(e.target, () => api("/api/focuser/motor", { name, value: v }), t("Gioco salvato nel firmware"));
    };
  }

  // lingua: la sceglie il server (anche per messaggi e registro); la pagina si ricarica nella lingua nuova
  $("lang-select").onchange = (e) => act(e.target, async () => {
    await api("/api/settings", { language: e.target.value });
    location.reload();
  });

  // profondità di campo
  ["d-na", "d-mag", "d-px", "d-ov"].forEach((id) => $(id).addEventListener("input", dof));
  bindOptics();
  bindCalibration();
  bindRemote();
  $("d-apply").onclick = () => {
    if (!umPerStep()) return toast(t("Configura prima la meccanica (µm per passo)"), true);
    const step = dof();
    if (!(step > 0)) return toast($("d-result").textContent, true);   // mai 1 passo «per difetto»
    linkBegin("s-step"); linkEdit.closed = true;
    $("s-step").value = stepsFor(step, umPerStep());
    syncCount(); linkMark(); linkDone(); updateSummary();
    switchTab("session");
    toast(t("Passo della sequenza aggiornato"));
  };

  // tastiera
  const keyJog = {
    ArrowUp: jogPress(() => -towardSign(), (on) => $("jog-away").classList.toggle("holding", on)),
    ArrowDown: jogPress(() => towardSign(), (on) => $("jog-toward").classList.toggle("holding", on)),
  };
  document.addEventListener("keydown", (e) => {
    if (["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName) || e.metaKey || e.ctrlKey) return;
    if (e.key === "Escape") { api("/api/focuser/halt").catch(() => {}); toast(t("Stop")); return; }
    const sizes = jogSizes();
    if (/^[1-9]$/.test(e.key) && Number(e.key) <= sizes.length) { setJogSize(sizes[Number(e.key) - 1]); return; }
    if (e.key === "ArrowUp" || e.key === "ArrowDown") {
      e.preventDefault();
      const away = e.key === "ArrowUp";
      const sign = away ? -towardSign() : towardSign();
      const tap = () => {
        const prev = jogSize;
        if (e.shiftKey) jogSize = Math.min(prev * 10, sizes[sizes.length - 1] * 10);
        jog(sign);
        jogSize = prev;
      };
      // con "Tieni premuto per muovere" il tasto tenuto giù fa il movimento continuo, come i pulsanti (prima ogni
      // ripetizione del tasto mandava un colpo, ignorato dal firmware mentre il motore era ancora in moto: singhiozzo)
      if (S && S.settings.jog_hold) { if (!e.repeat) keyJog[e.key].press(tap); }
      else tap();
    }
  });
  document.addEventListener("keyup", (e) => { if (keyJog[e.key]) keyJog[e.key].release(); });
}

function renderPresets() {
  const presets = (S && S.settings.presets) || {};
  const sig = Object.keys(presets).join("|");
  if (sig === presetSig) return;
  presetSig = sig;
  const sel = $("s-preset"), cur = sel.value;
  sel.innerHTML = `<option value="">${t("Preset…")}</option>`;
  for (const name of Object.keys(presets).sort()) sel.add(new Option(name, name, false, name === cur));
}

bind();
setupGuideLinks();
trackTopbar();
bindSettingsPage("view-config", "cfg-nav", "cfg-search", "cfg-none");
bindSettingsPage("view-optics", "opt-nav", "opt-search", "opt-none");
bindSettingsPage("view-calib", "cal-nav", null, null);
try {
  setJogSize(Number(localStorage.getItem("fs-jog")) || 100);
  const hashTab = location.hash.slice(1);
  switchTab(["session", "optics", "calib", "config", "log"].includes(hashTab) ? hashTab : localStorage.getItem("fs-tab") || "session");
} catch { setJogSize(100); }
refreshPorts();
connectWS();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
