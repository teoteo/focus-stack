"use strict";
const $ = (id) => document.getElementById(id);
const $$ = (sel) => document.querySelectorAll(sel);
let S = null;              // ultimo stato dal server
let formLoaded = false;    // i campi vengono popolati dal server una sola volta
let camSettingsSig = "", presetSig = "", motorSig = "", lastShotId = null;
let jogSize = 100;

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
    throw new Error(typeof d === "string" ? d : Array.isArray(d) ? "Valore non valido" : res.statusText);
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
const fmtInt = (n) => (n == null ? "—" : Number(n).toLocaleString("it-IT"));
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
  return Math.abs(um) >= 1000 ? `${(um / 1000).toFixed(3)} mm` : `${um.toFixed(Math.abs(um) < 10 ? 2 : 1)} µm`;
};
const running = () => S && ["running", "paused", "stopping"].includes(S.sequence.state);
const towardSign = () => (S && S.settings.toward_specimen === "increasing" ? 1 : -1);

// ---------------- tema ----------------
function applyTheme(t) {
  document.documentElement.dataset.theme = t;
  document.querySelector('meta[name="theme-color"]').content = t === "light" ? "#eef1f5" : "#0d1117";
}
try { applyTheme(localStorage.getItem("fs-theme") || "dark"); } catch { applyTheme("dark"); }

// ---------------- WebSocket di stato ----------------
let serverStopped = false;
function connectWS() {
  const ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = (ev) => { S = JSON.parse(ev.data); render(); };
  ws.onopen = () => setDot("st-link", "on");
  ws.onclose = () => { setDot("st-link", ""); setTimeout(checkServer, 1500); };
}

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
      document.title = updatingApp ? "Focus Stack — aggiornamento" : "Focus Stack — server spento";
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
    $("alarm-text").textContent = "Il server in esecuzione è di una versione precedente: chiudi Focus Stack e riaprilo.";
    return;
  }
  if (!formLoaded) safe("form", () => loadForms(S.settings));

  // barra superiore
  setDot("st-focuser", f.connected ? (f.moving ? "busy" : "on") : "");
  setDot("st-camera", c.connected ? (c.busy ? "busy" : "on") : "");
  const hasTemp = f.connected && f.temperature != null;
  $("st-temp").classList.toggle("hidden", !hasTemp);
  if (hasTemp) $("st-temp").textContent = `${f.temperature.toFixed(1)} °C`;
  const alarm = S.alarm || (S.code_stale
    ? "Il codice dell'app è cambiato: chiudi Focus Stack e riaprilo, poi ricarica la pagina." : "");
  $("alarm").classList.toggle("hidden", !alarm);
  $("alarm-text").textContent = alarm;

  safe("focheggiatore", () => renderFocuser(f, run));
  safe("fotocamera", () => renderCamera(c, run));
  safe("sequenza", () => renderSequence(f, c, q, run));
  safe("ultimo scatto", renderLastShot);
  safe("configurazione", () => renderConfig(f));
  safe("preset", renderPresets);
  safe("registro", renderLog);
  safe("aggiornamenti", renderUpdates);
}

// ---------------- aggiornamenti (app da GitHub, firmware incluso nell'app) ----------------
function renderUpdates() {
  const a = S.app || {}, fw = S.firmware_update || {}, f = S.focuser;
  $("up-app").textContent = a.available ? `${a.version} → disponibile ${a.latest}`
    : a.error ? `${a.version ?? "?"} (controllo non riuscito: verifica la connessione a internet)`
    : `${a.version ?? "?"}${a.latest ? " (aggiornata)" : ""}`;
  let fwText;
  if (!f.connected || f.simulated) fwText = "collega il focheggiatore per controllarlo";
  else if (fw.installed == null) fwText = `originale myFocuserPro2 ${f.firmware ?? ""}${fw.bundled ? ` → disponibile build ${fw.bundled}` : ""}`;
  else fwText = `build ${fw.installed}${fw.available ? ` → disponibile build ${fw.bundled}` : " (aggiornato)"}`;
  $("up-fw").textContent = fwText;
  $("fw-update").disabled = !fw.available || fw.busy || running();
  $("fw-progress-box").classList.toggle("hidden", !fw.busy && !fw.error);
  $("fw-progress").style.width = `${Math.round((fw.progress || 0) * 100)}%`;
  $("fw-phase").textContent = fw.error ? `Errore: ${fw.error}` : fw.busy ? `${fw.phase}… ${Math.round((fw.progress || 0) * 100)}%` : "";

  // barra in alto: prima l'app, poi il firmware
  const bar = $("update-bar"), btn = $("update-btn");
  if (a.available && !a.installing) {
    $("update-text").textContent = `È disponibile Focus Stack ${a.latest} (installata ${a.version}).`;
    btn.textContent = a.can_install ? "Aggiorna e riavvia" : "Scarica da GitHub";
    btn.onclick = a.can_install ? installAppUpdate : () => window.open("https://github.com/teoteo/focus-stack/releases/latest");
    bar.classList.remove("hidden");
  } else if (fw.available && !fw.busy) {
    $("update-text").textContent = `È disponibile un aggiornamento del firmware del focheggiatore (build ${fw.bundled}).`;
    btn.textContent = "Vai agli aggiornamenti";
    btn.onclick = () => switchTab("config");
    bar.classList.remove("hidden");
  } else bar.classList.add("hidden");
}

let updatingApp = false;
async function installAppUpdate() {
  if (running()) return toast("Attendi la fine della sequenza", true);
  if (!confirm(`Installare Focus Stack ${S.app.latest}?\n\nL'app si chiude e si riapre da sola; focheggiatore e fotocamera andranno ricollegati.`)) return;
  $("update-btn").disabled = true;
  try {
    await api("/api/app/update");
  } catch (e) {
    $("update-btn").disabled = false;
    return toast(e.message, true);
  }
  updatingApp = true;
  $("shutdown-title").textContent = "Aggiornamento in corso…";
  $("shutdown-text").textContent = "Focus Stack si chiude, installa la nuova versione e si riapre da solo. Questa pagina si ricaricherà.";
  $("shutdown-hint").textContent = "";
  $("shutdown-screen").classList.remove("hidden");
}

async function updateFirmware() {
  const fw = S.firmware_update;
  if (!confirm(`Aggiornare il firmware del focheggiatore alla build ${fw.bundled}?\n\nDurante l'aggiornamento (circa 20 secondi) non scollegare il cavo USB. Le impostazioni del focheggiatore restano.`)) return;
  try { await api("/api/firmware/update"); } catch (e) { toast(e.message, true); }
}

function renderFocuser(f, run) {
  setChip("f-chip", !f.connected ? "Disconnesso" : f.moving ? "In movimento" : "Fermo",
    !f.connected ? "" : f.moving ? "busy" : "ok");
  $("f-connect-box").classList.toggle("hidden", f.connected);
  $("f-connected-line").classList.toggle("hidden", !f.connected);
  if (f.connected) {
    $("f-info").textContent = `${f.simulated ? "Simulatore" : f.port} · firmware ${f.firmware ?? "?"} · max ${fmtInt(f.max_step)}`;
  }
  $("f-pos").textContent = f.connected ? fmtInt(f.position) : "—";
  $("f-pos-um").innerHTML = f.connected && umPerStep() ? fmtUm(f.position) : "&nbsp;";

  const [lo, hi] = f.connected ? f.bounds : [S.settings.limit_min, S.settings.limit_max];
  $("f-limits").textContent = `${fmtInt(lo)} – ${hi == null ? "∞" : fmtInt(hi)}`;
  if (f.connected && hi != null) {
    const towardDist = towardSign() < 0 ? f.position - lo : hi - f.position;
    $("f-range-left").textContent = `verso il campione: ${fmtInt(towardDist)} passi${umPerStep() ? " · " + fmtUm(towardDist) : ""}`;
  } else $("f-range-left").innerHTML = "&nbsp;";

  renderRail(f, lo, hi);

  const away = towardSign() < 0 ? "+" : "−", toward = towardSign() < 0 ? "−" : "+";
  $("jog-away-label").textContent = `Allontana  ${away}${fmtInt(jogSize)}`;
  $("jog-toward-label").textContent = `Avvicina  ${toward}${fmtInt(jogSize)}`;
  $("jog-um").innerHTML = umPerStep() ? `${fmtInt(jogSize)} passi = ${fmtUm(jogSize)}` : "&nbsp;";

  const dis = !f.connected || run;
  ["jog-away", "jog-toward", "f-goto-btn", "f-goto"].forEach((id) => ($(id).disabled = dis));
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
  $("rail-lo").textContent = `min ${fmtInt(lo)}`;
  $("rail-hi").textContent = hi == null ? "max firmware" : `max ${fmtInt(hi)}`;
  $("rail-dir").textContent = towardSign() < 0 ? "◀ campione" : "campione ▶";
}

const CAM_FIELDS = { shutterspeed: "c-shutter", iso: "c-iso", aperture: "c-aperture", imageformat: "c-format", capturetarget: "c-target" };

function renderCamera(c, run) {
  $("gp-missing").classList.toggle("hidden", S.gphoto);
  setChip("c-chip", !c.connected ? "Disconnessa" : c.busy ? "Scatto…" : "Pronta", !c.connected ? "" : c.busy ? "busy" : "ok");
  $("c-connect-box").classList.toggle("hidden", c.connected);
  $("c-connected-line").classList.toggle("hidden", !c.connected);
  if (c.connected) $("c-info").textContent = c.model + (c.simulated ? " (simulata)" : "");
  ["c-reload", "c-test"].forEach((id) => ($(id).disabled = !c.connected || run || c.busy));

  const settings = (c.connected && c.settings) || {};
  const sig = JSON.stringify(settings);
  if (sig === camSettingsSig) return;
  camSettingsSig = sig;
  for (const [name, id] of Object.entries(CAM_FIELDS)) {
    const sel = $(id), s = settings[name];
    sel.innerHTML = "";
    if (!s) { sel.add(new Option(c.connected ? "non disponibile" : "—", "")); sel.disabled = true; continue; }
    const choices = s.choices.length ? [...s.choices] : [s.current];
    if (!choices.includes(s.current)) choices.unshift(s.current);
    for (const ch of choices) sel.add(new Option(ch, ch, false, ch === s.current));
    sel.disabled = s.readonly || !s.choices.length;
  }
  updateSummary();
}

function renderSequence(f, c, q, run) {
  const labels = { idle: "Pronta", running: "In corso", paused: "In pausa", stopping: "Arresto…", done: "Completata", error: "Errore" };
  setChip("s-chip", labels[q.state] || q.state,
    { running: "busy", paused: "busy", stopping: "busy", done: "ok", error: "bad" }[q.state] || "");
  const bothOk = f.connected && c.connected;
  $("s-start-btn").disabled = run || !bothOk;
  $("s-start-btn").title = bothOk ? "" : "Connetti focheggiatore e fotocamera";
  $("s-pause-btn").disabled = !run || q.state === "stopping";
  $("s-pause-btn").innerHTML = q.state === "paused" ? "▶&nbsp; Riprendi" : "❚❚&nbsp; Pausa";
  $("s-stop-btn").disabled = !run;
  $$("[data-mark]").forEach((b) => (b.disabled = !f.connected || run));
  $("s-helicon").disabled = !q.folder || run;
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
  $("s-eta").textContent = run && q.eta_s != null ? `restano ~${fmtTime(q.eta_s)}` : "";
  $("s-bar").style.width = `${q.total ? (q.index / q.total) * 100 : 0}%`;
  let txt = "";
  if (run && q.current_target != null) txt = `Posizione ${fmtInt(q.current_target)}`;
  if (q.message) txt += (txt ? " · " : "") + q.message;
  if (q.folder && !run) txt += (txt ? " · " : "") + q.folder;
  $("s-progress").textContent = txt;
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
    if (shot.kind === "sequence") parts.push(`<span>scatto <b>${shot.index}</b></span>`);
    if (shot.position != null) parts.push(`<span>posizione <b>${fmtInt(shot.position)}</b></span>`);
    if (shot.temperature != null) parts.push(`<span><b>${shot.temperature.toFixed(1)}</b> °C</span>`);
    parts.push(`<span>${shot.time}</span>`);
    $("last-meta").innerHTML = parts.join("");
  }
}

function renderConfig(f) {
  const lo = S.settings.limit_min, hi = S.settings.limit_max;
  setChip("lim-chip", hi == null ? "Superiore = max firmware" : `${fmtInt(lo)} – ${fmtInt(hi)}`, hi == null ? "busy" : "ok");
  $$("[data-limit-here], #lim-zero, #lim-fw, #mo-reload").forEach((b) => (b.disabled = !f.connected || running()));
  $("lim-fw-info").textContent = f.connected ? `Max attuale nel firmware: ${fmtInt(f.max_step)}` : "";

  // motore
  const motor = (f.connected && f.motor) || {};
  const sig = JSON.stringify(motor) + f.connected;
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
    $("mo-bl-in").textContent = "backlash_in_steps" in motor ? `${motor.backlash_in_steps} passi` : "";
    $("mo-bl-out").textContent = "backlash_out_steps" in motor ? `${motor.backlash_out_steps} passi` : "";
    $("m-micro").value = motor.step_mode ? (motor.step_mode === 1 ? "passo intero" : `1/${motor.step_mode}`) : "1 (non letto)";
    updateMechResult();
  }

  // temperatura
  const hist = S.temp_history || [];
  const hasProbe = f.connected && f.temperature != null;
  $("t-value").textContent = hasProbe ? `${f.temperature.toFixed(2)} °C` : f.connected ? "Sonda assente" : "—";
  if (hist.length > 1) {
    const mn = Math.min(...hist), mx = Math.max(...hist);
    setChip("t-chip", `${mn.toFixed(1)} – ${mx.toFixed(1)} °C`, mx - mn > 1 ? "busy" : "ok");
    $("t-spark").innerHTML = sparkline(hist, 300, 70);
  } else setChip("t-chip", hasProbe ? "in raccolta…" : "—");
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
  $("c-bulb").value = q.bulb_s || 0;
  if (cfg.focuser_port) $("f-port").dataset.saved = cfg.focuser_port;
  loadLimitForm(cfg);
  const m = cfg.mechanics;
  $("m-spr").value = m.motor_steps_per_rev; $("m-gear").value = m.gear_ratio; $("m-umrev").value = m.um_per_knob_rev;
  $("m-umstep").value = cfg.um_per_step;
  setMechMode(m.mode);
  syncCount();
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
    return_to_start: $("s-return").checked, capture_mode: $("s-mode").value,
    session_name: $("s-name").value.trim() || "stack", output_root: (S && S.settings.output_root) || "",
    bulb_s: num("c-bulb"),
  };
}

function shotCount(p = formParams()) {
  const span = Math.abs(p.end - p.start), step = Math.max(1, Math.abs(p.step));
  return Math.floor(span / step) + 1 + (span % step ? 1 : 0);
}
const syncCount = () => ($("s-count").value = shotCount());

function shutterSeconds() {
  const v = $("c-shutter").value || "";
  if (/^\d+\/\d+$/.test(v)) { const [a, b] = v.split("/").map(Number); return a / b; }
  const n = parseFloat(v);
  return isFinite(n) ? n : 0;
}

function updateSummary() {
  if (!formLoaded || !S) return;
  const p = formParams(), n = shotCount(p), span = Math.abs(p.end - p.start);
  const perShot = (p.settle_ms + p.post_shot_ms) / 1000 + (p.bulb_s || shutterSeconds()) + 1.5 + p.step / 400;
  let html = `<b>${n}</b> scatti · escursione <b>${fmtInt(span)}</b> passi`;
  if (umPerStep()) html += ` = <b>${fmtUm(span)}</b> · passo <b>${fmtUm(p.step)}</b>`;
  html += `<br>Durata stimata <b>~${fmtTime(n * perShot)}</b>`;
  // controllo fine corsa lato interfaccia (il server ricontrolla comunque)
  const [lo, hi] = S.focuser.connected ? S.focuser.bounds : [S.settings.limit_min, S.settings.limit_max];
  const dir = p.end >= p.start ? 1 : -1;
  const approach = p.backlash > 0 ? p.start - dir * p.backlash : null;
  const out = [p.start, p.end, approach].filter((v) => v != null && (v < lo || (hi != null && v > hi)));
  if (out.length) html += `<span class="bad-text">⚠ La sequenza${approach != null && out.includes(approach) ? " (con la compensazione del gioco)" : ""} esce dai fine corsa ${fmtInt(lo)} – ${hi == null ? "∞" : fmtInt(hi)}</span>`;
  if (p.capture_mode === "trigger") html += `<span class="warn-text">In modalità trigger imposta la destinazione su scheda.</span>`;
  $("s-summary").innerHTML = html;
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
  if (!(u > 0)) { $("m-result").textContent = "Inserisci valori validi"; return; }
  $("m-result").innerHTML = `Risoluzione: <b>${u.toFixed(4)} µm/passo</b> · 1 µm = <b>${(1 / u).toFixed(2)}</b> passi · 1000 passi = <b>${(u * 1000).toFixed(1)} µm</b>`;
}

// ---------------- profondità di campo ----------------
// Formula di Berek/Shillaber: DOF = λ·n/NA² + n·e/(M·NA)
function dof() {
  const na = num("d-na"), mag = num("d-mag"), px = num("d-px"), ov = num("d-ov") / 100;
  if (!(na > 0 && mag > 0)) { $("d-result").textContent = "Inserisci NA e ingrandimento"; return 0; }
  const d = (0.55 * 1.0) / (na * na) + (1.0 * px) / (mag * na);
  const step = d * (1 - ov), um = umPerStep();
  $("d-result").innerHTML = `Profondità di campo ≈ <b>${d.toFixed(2)} µm</b> · passo consigliato <b>${step.toFixed(2)} µm</b>`
    + (um ? ` = <b>${Math.max(1, Math.round(step / um))} passi</b>` : " · configura la meccanica per convertirlo in passi");
  return step;
}

// ---------------- visualizzatore ----------------
let viewerWin = null;
function openViewer(shotId) {
  const url = "/viewer.html" + (shotId != null ? `#${shotId}` : "");
  if (viewerWin && !viewerWin.closed) {
    viewerWin.location.hash = shotId != null ? String(shotId) : "";
    viewerWin.focus();
    return;
  }
  viewerWin = window.open(url, "focusstack-viewer", "width=1280,height=900");
  if (!viewerWin) location.href = url; // finestre popup bloccate
}

// ---------------- eventi ----------------
async function refreshPorts() {
  try {
    const ports = await api("/api/ports", undefined, "GET");
    const sel = $("f-port"), saved = sel.dataset.saved || (S && S.settings.focuser_port);
    sel.innerHTML = "";
    if (!ports.length) sel.add(new Option("Nessuna porta USB trovata", ""));
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
  if (!cams.length) { sel.add(new Option("Nessuna fotocamera trovata", "")); toast("Nessuna fotocamera rilevata", true); return; }
  for (const c of cams) sel.add(new Option(`${c.model} (${c.port})`, JSON.stringify(c)));
}

function jog(sign) {
  if (!S || !S.focuser.connected || running()) return;
  api("/api/focuser/jog", { delta: sign * jogSize })
    .then((r) => r && r.clamped && toast("Fermato al fine corsa"))
    .catch((e) => toast(e.message, true));
}

function setJogSize(size) {
  jogSize = size;
  $$("#jog-size button").forEach((b) => b.setAttribute("aria-checked", Number(b.dataset.size) === size));
  try { localStorage.setItem("fs-jog", String(size)); } catch { /* opzionale */ }
  if (S) render();
}

function switchTab(name) {
  $$(".tabs button").forEach((b) => b.setAttribute("aria-selected", b.dataset.tab === name));
  $$(".view").forEach((v) => v.classList.toggle("hidden", v.id !== `view-${name}`));
  if (name === "log" && S) { renderLog(); $("log").scrollTop = $("log").scrollHeight; }
  try { localStorage.setItem("fs-tab", name); } catch { /* opzionale */ }
}

function bind() {
  $$(".tabs button").forEach((b) => (b.onclick = () => switchTab(b.dataset.tab)));
  $("fw-update").onclick = updateFirmware;
  $("up-check").onclick = () => api("/api/app/check").then((a) => toast(a.error || (a.available ? `Disponibile la versione ${a.latest}` : "Nessun aggiornamento"), !!a.error)).catch((e) => toast(e.message, true));
  $("theme-btn").onclick = () => {
    const t = document.documentElement.dataset.theme === "dark" ? "light" : "dark";
    applyTheme(t);
    try { localStorage.setItem("fs-theme", t); } catch { /* opzionale */ }
  };

  // focheggiatore
  $("f-refresh").onclick = refreshPorts;
  $("f-connect").onclick = (e) => act(e.target, () => api("/api/focuser/connect", { port: $("f-port").value, simulate: $("f-sim").checked }));
  $("f-disconnect").onclick = (e) => act(e.target, () => api("/api/focuser/disconnect"));
  $$("#jog-size button").forEach((b) => (b.onclick = () => setJogSize(Number(b.dataset.size))));
  $("jog-away").onclick = () => jog(-towardSign());
  $("jog-toward").onclick = () => jog(towardSign());
  $("f-goto-btn").onclick = (e) => act(e.target, () => api("/api/focuser/move", { position: num("f-goto") }));
  $("f-goto").onkeydown = (e) => { if (e.key === "Enter") $("f-goto-btn").click(); };
  $("f-halt").onclick = () => act(null, () => api("/api/focuser/halt"), "Stop");

  // fotocamera
  $("c-detect").onclick = detectCameras;
  $("c-connect").onclick = (e) => act(e.target, () => {
    let sel = {};
    try { sel = JSON.parse($("c-model").value || "{}"); } catch { /* automatico */ }
    return api("/api/camera/connect", { model: sel.model || "", port: sel.port || "", simulate: $("c-sim").checked });
  });
  $("c-disconnect").onclick = (e) => act(e.target, () => api("/api/camera/disconnect"));
  for (const [name, id] of Object.entries(CAM_FIELDS)) {
    $(id).onchange = (e) => act(e.target, async () => {
      await api("/api/camera/settings", { name, value: e.target.value });
      camSettingsSig = ""; // ridisegna con il valore effettivamente accettato dalla fotocamera
    });
  }
  $("c-reload").onclick = (e) => act(e.target, () => api("/api/camera/settings/reload"));
  $("c-test").onclick = (e) => act(e.target, () => api("/api/camera/test", { bulb_s: num("c-bulb") }), "Scatto completato");

  // ultimo scatto / visualizzatore
  $("last-thumb").onclick = () => S && S.last_shot && openViewer(S.last_shot.id);
  $("v-open").onclick = () => openViewer(S && S.last_shot ? S.last_shot.id : null);

  // sequenza
  $$("[data-mark]").forEach((b) => (b.onclick = () => {
    $(b.dataset.mark === "start" ? "s-start" : "s-end").value = S.focuser.position;
    syncCount(); updateSummary();
  }));
  ["s-start", "s-end", "s-step"].forEach((id) => $(id).addEventListener("input", () => { syncCount(); updateSummary(); }));
  $("s-count").addEventListener("change", () => {
    const n = Math.max(2, num("s-count")), span = Math.abs(num("s-end") - num("s-start"));
    $("s-step").value = Math.max(1, Math.round(span / (n - 1)));
    syncCount(); updateSummary();
  });
  ["s-settle", "s-post", "s-backlash", "s-mode", "c-bulb", "c-shutter"].forEach((id) => $(id).addEventListener("input", updateSummary));
  $("s-start-btn").onclick = (e) => act(e.target, () => api("/api/sequence/start", formParams()), "Sequenza avviata");
  $("s-pause-btn").onclick = (e) => act(e.target, () => api(S.sequence.state === "paused" ? "/api/sequence/resume" : "/api/sequence/pause"));
  $("s-stop-btn").onclick = (e) => act(e.target, () => api("/api/sequence/stop"));
  $("s-open").onclick = () => act(null, () => api("/api/open-folder"));
  $("s-root-choose").onclick = (e) => act(e.target, async () => {
    toast("Scegli la cartella nella finestra del Finder…");
    const r = await api("/api/choose-folder");
    if (r && r.path) { S.settings.output_root = r.path; toast("Cartella di salvataggio aggiornata"); }
  });
  $("s-helicon").onclick = (e) => act(e.target, () => api("/api/open-helicon"));

  // preset
  $("s-preset").onchange = () => {
    const p = S.settings.presets[$("s-preset").value];
    if (!p) return;
    const map = { start: "s-start", end: "s-end", step: "s-step", settle_ms: "s-settle", post_shot_ms: "s-post",
      backlash: "s-backlash", capture_mode: "s-mode", session_name: "s-name", bulb_s: "c-bulb" };
    for (const [k, id] of Object.entries(map)) if (p[k] !== undefined) $(id).value = p[k];
    if (p.return_to_start !== undefined) $("s-return").checked = p.return_to_start;
    syncCount(); updateSummary();
  };
  $("s-preset-save").onclick = () => {
    const name = window.prompt("Nome del preset (es. obiettivo 10×)", $("s-preset").value || "");
    if (!name) return;
    const { output_root, ...data } = formParams();
    act(null, async () => { S.settings.presets = await api("/api/presets/save", { name, data }); presetSig = ""; renderPresets(); }, "Preset salvato");
  };
  $("s-preset-del").onclick = () => {
    const name = $("s-preset").value;
    if (!name) return;
    act(null, async () => { S.settings.presets = await api("/api/presets/delete", { name }); presetSig = ""; renderPresets(); }, "Preset eliminato");
  };

  // fine corsa
  $$("[data-limit-here]").forEach((b) => (b.onclick = () => {
    $(b.dataset.limitHere === "min" ? "lim-min" : "lim-max").value = S.focuser.position;
    toast("Valore copiato: premi Salva fine corsa per applicarlo");
  }));
  $("lim-save").onclick = (e) => act(e.target, () => api("/api/limits", {
    limit_min: num("lim-min"), limit_max: optNum("lim-max"), toward_specimen: $("lim-dir").value,
  }), "Fine corsa salvati");
  $("lim-zero").onclick = (e) => {
    if (!confirm(`La posizione attuale (${fmtInt(S.focuser.position)}) diventerà 0. Fine corsa e sequenza verranno traslati di conseguenza. Continuare?`)) return;
    act(e.target, async () => {
      await api("/api/limits/zero-here");
      const st = await api("/api/state", undefined, "GET");
      loadLimitForm(st.settings);
      $("s-start").value = st.settings.sequence.start; $("s-end").value = st.settings.sequence.end;
    }, "Zero impostato");
  };
  $("lim-fw").onclick = (e) => {
    const v = optNum("lim-max");
    if (v == null) return toast("Imposta prima il fine corsa superiore", true);
    if (!confirm(`Scrivere ${fmtInt(v)} come massimo nel firmware? Anche i pulsanti fisici non potranno superarlo.`)) return;
    act(e.target, async () => {
      const f = await api("/api/focuser/maxstep", { position: v });
      if (f.max_step !== v) throw new Error(`Il firmware ha mantenuto ${fmtInt(f.max_step)}: potrebbe avere un minimo ammesso`);
      await api("/api/limits", { limit_min: num("lim-min"), limit_max: v, toward_specimen: $("lim-dir").value });
    }, "Massimo scritto nel firmware");
  };

  // meccanica
  $$("#mech-mode button").forEach((b) => (b.onclick = () => setMechMode(b.dataset.mode)));
  ["m-spr", "m-gear", "m-umrev", "m-umstep"].forEach((id) => $(id).addEventListener("input", updateMechResult));
  $("m-save").onclick = (e) => act(e.target, () => api("/api/mechanics", {
    mode: mechMode, motor_steps_per_rev: num("m-spr"), gear_ratio: num("m-gear"), um_per_knob_rev: num("m-umrev"),
    um_per_step: mechMode === "manual" ? num("m-umstep") : null,
  }), "Meccanica salvata");

  // motore
  $("mo-reload").onclick = (e) => act(e.target, () => api("/api/focuser/motor/reload"));
  for (const name of ["step_mode", "speed"]) {
    $(`mo-${name}`).onchange = (e) => {
      if (name === "step_mode" && !confirm("Cambiare il microstep cambia la scala delle posizioni e dei fine corsa. Continuare?")) {
        motorSig = ""; return;
      }
      act(e.target, () => api("/api/focuser/motor", { name, value: Number(e.target.value) }), "Impostazione inviata");
    };
  }
  for (const name of ["coil_power", "reverse", "backlash_in_enabled", "backlash_out_enabled"]) {
    $(`mo-${name}`).onchange = (e) => act(e.target, () => api("/api/focuser/motor", { name, value: e.target.checked }), "Impostazione inviata");
  }

  // profondità di campo
  ["d-na", "d-mag", "d-px", "d-ov"].forEach((id) => $(id).addEventListener("input", dof));
  $("d-apply").onclick = () => {
    if (!umPerStep()) return toast("Configura prima la meccanica (µm per passo)", true);
    $("s-step").value = Math.max(1, Math.round(dof() / umPerStep()));
    syncCount(); updateSummary();
    switchTab("session");
    toast("Passo della sequenza aggiornato");
  };

  // tastiera
  document.addEventListener("keydown", (e) => {
    if (["INPUT", "SELECT", "TEXTAREA"].includes(document.activeElement.tagName) || e.metaKey || e.ctrlKey) return;
    if (e.key === "Escape") { api("/api/focuser/halt").catch(() => {}); toast("Stop"); return; }
    if (["1", "2", "3", "4"].includes(e.key)) { setJogSize([1, 10, 100, 1000][Number(e.key) - 1]); return; }
    if (e.key === "ArrowUp" || e.key === "ArrowDown") {
      e.preventDefault();
      const away = e.key === "ArrowUp";
      const sign = away ? -towardSign() : towardSign();
      const prev = jogSize;
      if (e.shiftKey) jogSize = Math.min(prev * 10, 10000);
      jog(sign);
      jogSize = prev;
    }
  });
}

function renderPresets() {
  const presets = (S && S.settings.presets) || {};
  const sig = Object.keys(presets).join("|");
  if (sig === presetSig) return;
  presetSig = sig;
  const sel = $("s-preset"), cur = sel.value;
  sel.innerHTML = '<option value="">Preset…</option>';
  for (const name of Object.keys(presets).sort()) sel.add(new Option(name, name, false, name === cur));
}

bind();
try {
  setJogSize(Number(localStorage.getItem("fs-jog")) || 100);
  const hashTab = location.hash.slice(1);
  switchTab(["session", "config", "log"].includes(hashTab) ? hashTab : localStorage.getItem("fs-tab") || "session");
} catch { setJogSize(100); }
refreshPorts();
connectWS();
if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
