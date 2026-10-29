"""English text of the guide. Not a module to import: genera_guida.py runs it with exec() in a
namespace that already holds the shared helpers and numbers (fig, frac, table, num, diagram, VERSION,
ICON, IMG, UA, UB, GEAR17, um_step, dof, OBJ). The text fills the list H with the HTML sections.
"""
# ruff: noqa: F821  (names come from genera_guida.py)

META = {
    "lang": "en",
    "title": "Focus Stack — User Guide",
    "footer": "User Guide",
    "pdf": "Focus Stack Guide.pdf",
}

# Names of the app's commands and labels, keyed by the Italian text (= the app's translation keys).
# To be aligned with the app's real English strings (web/lang/en-*.json) once they are final.
UI = {
    "Sessione": "Session",
    "Configurazione": "Configuration",
    "Registro": "Log",
    "Simulatore": "Simulator",
    "Connetti": "Connect",
    "Disconnetti": "Disconnect",
    "Rileva": "Detect cameras",
    "Rilevamento automatico": "Automatic detection",
    "Esci": "Quit",
    "Aggiorna e riavvia": "Update and restart",
    "Aggiornamenti": "Updates",
    "Controlla ora": "Check now",
    "Aggiorna firmware": "Update firmware",
    "Allontana": "Away",
    "Avvicina": "Closer",
    "Vai alla posizione": "Go to position",
    "Vai": "Go",
    "Comandi manuali": "Manual controls",
    "Fine corsa": "Limits",
    "Fine corsa di sicurezza": "Safety limits",
    "Fine corsa inferiore": "Lower limit",
    "Fine corsa superiore": "Upper limit",
    "Verso il campione (si avvicina) con": "Toward the specimen (closer) with",
    "⌖ Usa posizione attuale": "⌖ Use current position",
    "Salva fine corsa": "Save limits",
    "Imposta qui lo zero": "Set zero here",
    "Scrivi il massimo nel firmware": "Write maximum to firmware",
    "Tempo di posa": "Shutter speed",
    "Diaframma": "Aperture",
    "Formato": "Format",
    "Destinazione": "Destination",
    "Posa B (secondi)": "Bulb (seconds)",
    "Ritardo specchio (reflex)": "Mirror delay (DSLR)",
    "Rileggi": "Reload",
    "◉ Scatto di prova": "◉ Test shot",
    "Ultimo scatto": "Latest shot",
    "● Live": "● Live",
    "■ Ferma live": "■ Stop live",
    "Apri visualizzatore ↗": "Open viewer ↗",
    "Inizio": "Start",
    "Fine": "End",
    "⌖ qui": "⌖ here",
    "Passo (passi motore)": "Step (motor steps)",
    "Numero di scatti": "Number of shots",
    "Salva in": "Save to",
    "Scegli…": "Choose…",
    "Apri": "Open",
    "Tempi, gioco e nome della sessione": "Timing, backlash and session name",
    "Attesa dopo il movimento (ms)": "Settle time after moving (ms)",
    "Pausa dopo lo scatto (ms)": "Pause after the shot (ms)",
    "Compensazione gioco (passi)": "Backlash compensation (steps)",
    "Modalità di scatto": "Capture mode",
    "Scarica sul Mac": "Download to the Mac",
    "Solo sulla scheda": "Memory card only",
    "Solo trigger (veloce)": "Trigger only (fast)",
    "Nome sessione": "Session name",
    "Torna all'inizio a fine sequenza": "Return to the start when the sequence ends",
    "Preset…": "Preset…",
    "Salva preset": "Save preset",
    "▶ Avvia sequenza": "▶ Start sequence",
    "❚❚ Pausa": "❚❚ Pause",
    "Riprendi": "Resume",
    "■ Interrompi": "■ Abort",
    "Apri in Helicon Focus": "Open in Helicon Focus",
    "Adatta": "Fit",
    "Reset": "Reset",
    "Segui ultimo": "Follow latest",
    "Blocca vista": "Lock view",
    "Finder": "Finder",
    "Calcola dalla meccanica": "Calculate from mechanics",
    "Inserisci µm/passo": "Enter µm/step",
    "Passi motore per giro": "Motor steps per revolution",
    "Microstep (dal firmware)": "Microstep (from firmware)",
    "Rapporto di riduzione": "Gear ratio",
    "Automatica (lingua del sistema)": "Automatic (system language)",
    "Lingua": "Language",
    "Corsa per giro manopola (µm)": "Travel per knob turn (µm)",
    "µm per passo": "µm per step",
    "Salva meccanica": "Save mechanics",
    "Motore (firmware)": "Motor (firmware)",
    "Microstep": "Microstep",
    "Velocità": "Speed",
    "Bobine alimentate a motore fermo": "Keep coils powered when idle",
    "Inverti verso di rotazione": "Reverse rotation",
    "Compensa il gioco IN": "Compensate backlash IN",
    "Compensa il gioco OUT": "Compensate backlash OUT",
    "Gioco IN (passi)": "Backlash IN (steps)",
    "Gioco OUT (passi)": "Backlash OUT (steps)",
    "Tieni premuto per muovere senza fermarti": "Hold down to keep moving",
    "Temperatura": "Temperature",
    "Profondità di campo": "Depth of field",
    "Apertura numerica (NA)": "Numerical aperture (NA)",
    "Ingrandimento sul sensore": "Magnification on the sensor",
    "Pixel del sensore (µm)": "Sensor pixel (µm)",
    "Sovrapposizione (%)": "Overlap (%)",
    "Usa come passo della sequenza": "Use as sequence step",
    "Focus Stack è chiuso": "Focus Stack is closed",
    "Live view interrotto: …": "Live view stopped: …",
}


def ui(s):
    """English name of an app command (the Italian text is the key)."""
    return UI.get(s, s)


DIAGRAM_LABELS = {
    "motor": "Motor", "gearbox": "Gearbox", "pulleys": "Pulleys / gears", "knob": "Fine focus", "stage": "Stage",
    "motor1": "steps per rev", "motor2": "× microstep",
    "gearbox1": "(if any)", "gearbox2": "e.g. 26.85 : 1",
    "pulleys1": "driven teeth", "pulleys2": "÷ driving teeth",
    "knob1": "µm per turn", "knob2": "of the knob",
    "stage1": "moves", "stage2": "in µm",
    "ratio": "total gear ratio = gearbox × pulleys",
    "steps": "motor steps per knob turn = steps/rev × microstep × ratio",
}

# depth-of-field table (objective names in the guide's language)
OBJ_NAMES = ["4× / 0.10", "10× / 0.25", "20× / 0.40", "40× / 0.65", "60× / 0.85", "100× / 1.25 oil"]
dof_rows = []
for name, (mag, na) in zip(OBJ_NAMES, OBJ):
    d = dof(na, mag, 3.9)
    s = d * 0.7
    dof_rows.append([name, num(d), num(s), str(max(1, round(s / UA))), str(max(1, round(s / UB)))])
dof_note = ("for oil-immersion objectives the app's formula (index n = 1, air) underestimates the depth of field, "
            "so the computed step errs on the safe side.")

H = []
add = H.append

add(f"""
<section class="cover">
  <div class="icon">{ICON}</div>
  <h1 class="title">Focus Stack</h1>
  <div class="sub">User Guide<br>motorized focuser and camera for focus stacking on the microscope</div>
  <div class="shot-c"><img src="{IMG}/sessione.png" alt=""></div>
  <div class="meta"><span>App version {VERSION}</span><span>October 2026</span></div>
</section>
""")

add("""
<h1 style="break-before:auto">Contents</h1>
<div class="toc"><ol>
<li><span>1</span>What Focus Stack is<em>how it works, what you need</em></li>
<li><span>2</span>Installing, starting and updating</li>
<li><span>3</span>The interface at a glance<em>the three tabs and the top bar</em></li>
<li><span>4</span>Connecting the focuser and the camera<em>settings for the Nikon D5600 and other cameras</em></li>
<li><span>5</span>The focuser: position, moves, STOP</li>
<li><span>6</span>Camera, test shot and live view</li>
<li><span>7</span>The stacking sequence</li>
<li><span>8</span>The viewer</li>
<li><span>9</span>Safety limits</li>
<li><span>10</span>Mechanical setup: the calculations<em>resolution in µm per step, verification, travel, speed, backlash</em></li>
<li><span>11</span>Choosing the sequence step<em>depth of field, number of shots, duration</em></li>
<li><span>12</span>Motor, manual controls, updates, temperature</li>
<li><span>13</span>A typical session, step by step</li>
<li><span>14</span>Troubleshooting</li>
<li><span>15</span>Keyboard shortcuts</li>
</ol></div>
""")

# 1
add(f"""
<h1><span class="n">1</span>What Focus Stack is</h1>
<p class="lead">Focus Stack lets your Mac drive a motorized focuser fitted to the microscope's fine focus and a
camera connected over USB. It runs <b>move → wait → shoot</b> sequences automatically: dozens of photos at
different focus positions, ready to be merged into one fully sharp image with <b>Helicon Focus</b> (or a
similar program).</p>
<h2>How it works</h2>
<p>The Focus Stack app starts a small program on the Mac (the <i>server</i>) that talks to the focuser (an
Arduino board running the myFocuserPro2 firmware) and to the camera. The interface opens in <b>Safari</b> at
<code>http://localhost:8765</code> and can only be reached from this Mac.</p>
<ul>
<li>The <b>focuser</b> turns the focus knob with a stepper motor. Each motor <i>step</i> moves the stage (or the
  objective) by a fraction of a micrometre; how much is worked out by the <b>mechanical setup</b> (chapter 10).</li>
<li>The <b>camera</b> is controlled with the same protocol the manufacturers' programs use: shutter speed,
  ISO, format, release, photo download and live view.</li>
<li>The focuser's <b>physical buttons</b> keep working while the app is open.</li>
</ul>
<h2>What you need</h2>
<ul>
<li>A Mac with macOS 13 or later (Intel) or macOS 14 or later (Apple Silicon), with Safari.</li>
<li>A <b>myFocuserPro2</b> focuser (DRV8825 driver version) or an <b>Ardufocus</b> (rev1 board with DRV8825),
  connected with its USB cable and powered (12 V).</li>
<li>A Nikon, Canon or Sony camera with its USB cable. This guide uses a <b>Nikon D5600</b> as the example.</li>
<li>An adapter that projects the microscope image onto the sensor (photo tube, T2 adapter or similar).</li>
</ul>
<div class="box warn"><span class="t">Supported focusers</span>Focus Stack works with <b>myFocuserPro2</b> and
<b>Ardufocus</b> boards, running the firmware bundled with the app. A myFocuserPro2 with its original firmware connects
straight away and the app offers to update it with one click. An Ardufocus with its original firmware (Moonlite protocol)
is not recognised: the first time, the Focus Stack firmware must be loaded by hand (instructions in the README at
github.com/teoteo/focus-stack); after that, the Ardufocus is updated from the app too.</div>
<div class="box tip"><span class="t">No hardware?</span>The Focuser and Camera cards have a
<span class="ui">{ui("Simulatore")}</span> box: it lets you try the whole app without connecting anything.
The screenshots in this guide were made that way.</div>
""")

# 2
add(f"""
<h1><span class="n">2</span>Installing, starting and updating</h1>
<h2>First installation</h2>
<ol class="steps">
<li>Download <code>FocusStack-&lt;version&gt;.zip</code> from
  <b>github.com/teoteo/focus-stack/releases</b> and open it: the <b>Focus Stack</b> app appears.</li>
<li>Drag Focus Stack into the <b>Applications</b> folder before opening it.</li>
<li>Open it. macOS warns that it cannot verify the developer, because the app is not signed by Apple.
  Open <b>System Settings › Privacy &amp; Security</b>, scroll down and click <b>Open Anyway</b>.
  This is only needed the first time.</li>
</ol>
<p>The app already contains everything it needs: there is nothing else to install.</p>
<h2>Starting and quitting</h2>
<ul>
<li>When it starts, Focus Stack opens its page in Safari and stays in the Dock. Clicking the Dock icon brings
  the page back to the front.</li>
<li>To quit: <kbd>⌘Q</kbd> on the app, or <span class="ui">{ui("Esci")}</span> from the Dock icon's menu.
  If a sequence is running, the app asks for confirmation, stops it and halts the motor.</li>
<li>Closing Safari does <b>not</b> quit the app. If the page stays open it shows “{ui("Focus Stack è chiuso")}” and
  reloads by itself when you reopen the app.</li>
</ul>
<h2>Updates</h2>
<p>At start-up, and then every 6 hours, the app checks for a new version. If there is one, a bar with
<span class="ui">{ui("Aggiorna e riavvia")}</span> appears at the top: the app downloads the new version, quits and
reopens by itself. You can run the same check by hand in
<span class="ui">{ui("Configurazione")} › {ui("Aggiornamenti")} › {ui("Controlla ora")}</span>.</p>
<p>The <b>focuser firmware</b> is updated from the app too (chapter 12): when the board's firmware is older than
the one bundled with the app, the same bar tells you.</p>
<h2>Language</h2>
<p>The app speaks Italian, English, French, German and Spanish. With <span class="ui">{ui("Automatica (lingua del sistema)")}</span> it follows the
language of macOS, falling back to English for other languages; you can force a language in
<span class="ui">{ui("Configurazione")} › {ui("Lingua")}</span>. The choice applies to the interface, messages and log, and
this guide exists in the same languages.</p>
""")

# 3
add(f"""
<h1><span class="n">3</span>The interface at a glance</h1>
<p>The page has three tabs, chosen at the top:</p>
<ul>
<li><b>{ui("Sessione")}</b>: the work at the microscope. Focuser, sequence, camera and latest shot.</li>
<li><b>{ui("Configurazione")}</b>: limits, mechanics, manual controls, motor, updates, temperature and the
  depth-of-field calculator. Set up once, then rarely touched.</li>
<li><b>{ui("Registro")}</b>: a timestamped list of everything that happened in the session. The first place to look
  when something goes wrong.</li>
</ul>
{fig("sessione", layout="full", caption="The Session tab: focuser on the left, sequence in the middle, camera and latest shot on the right.")}
<h2>Top bar</h2>
{fig("barra-superiore", [
    f"<b>Tabs</b> {ui('Sessione')}, {ui('Configurazione')} and {ui('Registro')}.",
    "<b>Connection status</b>: Server, Focuser and Camera. Green = connected, grey = disconnected, red = error.",
    "<b>Temperature</b> read by the focuser's probe.",
    "<b>Theme</b>, dark or light. The dark theme is easier on the eyes during long sessions at the microscope.",
], layout="full below-marks", anchors={1: "b", 2: "b", 3: "b", 4: "b"})}
<p>Two strips can appear below the bar: a blue one for <b>updates</b> and a red <b>alarm</b> one, for example
when the physical buttons take the focuser past a limit.</p>
""")

# 4
add(f"""
<h1><span class="n">4</span>Connecting the focuser and the camera</h1>
<h2>Focuser</h2>
{fig("connessione-focheggiatore", [
    "The focuser's <b>serial port</b>. It is usually called <code>/dev/cu.usbserial-…</code> or <code>/dev/cu.wchusbserial…</code>; the name changes if you use another USB socket on the Mac.",
    "<b>Refresh</b> the port list after plugging in the cable.",
    f"<b>{ui('Simulatore')}</b>: a fake focuser for trying out the app.",
    f"<b>{ui('Connetti')}</b>. Opening the port restarts the Arduino: connecting takes 2–3 seconds.",
], layout="side narrow")}
<h2>Camera</h2>
{fig("connessione-fotocamera", [
    f"<b>Camera</b>: leave <i>{ui('Rilevamento automatico')}</i> or pick the model that was found.",
    f"<b>{ui('Rileva')}</b> the connected cameras.",
    f"<b>{ui('Simulatore')}</b>: a fake camera that generates test images.",
    f"<b>{ui('Connetti')}</b>. Before connecting, the app closes the macOS services that grab the camera.",
], layout="side narrow")}
<h3>Settings on the camera</h3>
{table(["Camera", "What to set"], [
    ["<b>Nikon D5600</b> and other Nikons", "Mode dial on <b>M</b> (manual). In the playback menu turn <b>image review</b> off. Turn off SnapBridge/Wi-Fi and Bluetooth, which can tie up the connection. Keep a memory card inserted and the battery charged (or use the EH-5/EP-5A power adapter)."],
    ["Canon", "Mode <b>M</b>. The shot goes to the camera's memory or to the card depending on <i>Destination</i>. For the mirror delay, enable <b>mirror lock-up</b> in the menu."],
    ["Sony", "USB menu › <b>PC Remote</b>; mode <b>M</b>. For live view the camera must allow it in PC Remote."],
])}
<div class="box warn"><span class="t">If the camera won't connect</span>macOS tries to take over the camera as
soon as you plug it in. The app closes that service by itself; if that is not enough, quit <b>Photos</b>,
<b>Preview</b>, <b>Image Capture</b>, NX Studio and EOS Utility and try again. Unplugging and replugging the
cable with the camera switched on often helps.</div>
""")

# 5
add(f"""
<h1><span class="n">5</span>The focuser: position, moves, STOP</h1>
{fig("focheggiatore", [
    "<b>Status</b>: Idle, Moving, Disconnected.",
    f"<b>Connection</b>: port, firmware version and firmware maximum (the highest position allowed). <span class='ui'>{ui('Disconnetti')}</span> frees the port.",
    "<b>Position</b> in motor steps and, below it, in millimetres or micrometres (once the mechanics are set up).",
    "<b>Limits</b> currently set, and the distance left towards the specimen before the limit.",
    "<b>Travel bar</b>: see the figure below.",
    f"<b>Step size</b> of the {ui('Allontana')}/{ui('Avvicina')} buttons: 1, 10, 100… steps. The available sizes are chosen in {ui('Configurazione')} › {ui('Comandi manuali')}.",
    "The same move <b>in micrometres</b>.",
    f"<b>{ui('Allontana')} / {ui('Avvicina')}</b>: a click moves by the chosen step size. Hold the button and the motor keeps moving, then slows down and stops when you let go.",
    f"<b>{ui('Vai alla posizione')}</b>: type a number of steps and click {ui('Vai')}.",
    "<b>STOP</b>: stops the motor and any running sequence at once. Keyboard: <kbd>Esc</kbd>.",
])}
<h2>The travel bar</h2>
{fig("binario", [
    "<b>Red hatched zones</b>: outside the limits, off limits.",
    "<b>Blue band</b>: the sequence range, with a tick for each shot.",
    "<b>White line</b>: the current position.",
], layout="side narrow")}
<p>Under the bar: the lower limit, the arrow showing <b>which side the specimen is on</b>, and the upper limit.
“{ui('Avvicina')}” always moves towards the specimen, whichever way the numbers run: this is set in
{ui('Configurazione')} › {ui('Fine corsa')} (chapter 9).</p>
<div class="box tip"><span class="t">Keyboard</span><kbd>↑</kbd> moves away, <kbd>↓</kbd> moves closer,
<kbd>⇧</kbd> with an arrow multiplies the step by 10, the number keys <kbd>1</kbd> <kbd>2</kbd>
<kbd>3</kbd>… choose the step size, <kbd>Esc</kbd> is STOP. They work in the {ui('Sessione')} tab, even while
you watch the live view.</div>
<div class="box warn"><span class="t">Physical buttons</span>The buttons on the focuser drive the motor without
going through the app. The app watches them and, if the position leaves the limits, sends STOP and shows an
alarm; for full protection read chapter 9. Pressing them during a sequence pauses the sequence.</div>
""")

# 6
add(f"""
<h1><span class="n">6</span>Camera, test shot and live view</h1>
{fig("fotocamera", [
    "<b>Status</b>: Ready, Shooting…, Disconnected.",
    f"Connected <b>model</b> and <span class='ui'>{ui('Disconnetti')}</span>.",
    f"<b>{ui('Tempo di posa')}</b> and <b>ISO</b>.",
    f"<b>{ui('Diaframma')}</b> and <b>{ui('Formato')}</b> (RAW, JPEG…). On a microscope, with no lens on the camera, there is usually no aperture.",
    f"<b>{ui('Destinazione')}</b>: camera memory or card.",
    "<b>Bulb</b> in seconds: 0 uses the shutter speed; a value above 0 makes a bulb exposure timed by the Mac, for exposures longer than 30 s.",
    "<b>Mirror delay</b> (DSLR), 0.5 to 2.5 s: wait between mirror lift and exposure, to let vibrations die down. On the Nikon D5600 the app uses the camera's own <i>exposure delay</i>.",
    f"<b>{ui('Rileggi')}</b> the settings from the camera. After every change the app reads back the value the camera actually accepted.",
    "<b>Test shot</b>: one photo at the current position, shown in Latest shot and in the viewer.",
])}
<h2>Latest shot and live view</h2>
<div class="two">
{fig("ultimo-scatto", [
    "<b>● Live</b>: shows the camera's live image.",
    "<b>Open viewer</b> in a separate window (chapter 8).",
    "<b>Latest shot</b>: click it to open it in the viewer.",
    "File name, position and temperature at the time of the shot.",
], layout="stack")}
{fig("live", [
    f"<b>{ui('■ Ferma live')}</b> turns the live view off.",
    "Status: <b>LIVE</b>, <b>SHOOTING…</b> during a test shot, <b>PAUSED</b> during the sequence.",
    "Camera model. Double-click the image for full screen.",
], layout="stack")}
</div>
<p>Live view runs at up to 15 frames per second and is the easiest way to find the start and end of the
sequence while you move the focuser with the keyboard. It is switched off during the sequence (the mirror has to
come down and the camera has to shoot normally) and comes back by itself at the end. On DSLRs the mirror stays up
while live view is on.</p>
<div class="box tip"><span class="t">For precise focusing</span>Open live view in the <b>viewer</b>: you can zoom
to 100% and beyond and pan to the detail you care about (chapter 8).</div>
""")

# 7
add(f"""
<h1><span class="n">7</span>The stacking sequence</h1>
{fig("sequenza", [
    "<b>Status</b>: Ready, Running, Paused, Completed, Error.",
    f"<b>{ui('Inizio')}</b> and <b>{ui('Fine')}</b> in steps. <span class='ui'>{ui('⌖ qui')}</span> copies the current position.",
    "<b>Step</b> between one shot and the next, in motor steps (chapter 11).",
    "<b>Number of shots</b>. It is linked to the step: change one and the other is recalculated.",
    "<b>Summary</b>: shots, travel in steps and in µm, step in µm, estimated duration. If the sequence goes beyond the limits a red warning appears and the sequence won't start.",
    f"<b>{ui('Salva in')}</b>: the photo folder. <span class='ui'>{ui('Scegli…')}</span> opens the Finder panel, <span class='ui'>{ui('Apri')}</span> shows it in the Finder.",
    "<b>Settle time after move</b>: time for vibrations to die down before the shot (1–3 s on a microscope). <b>Pause after shot</b>: time to write to the card and recharge the flash.",
    "<b>Backlash compensation</b>: before the first shot the motor backs off by this many steps and then moves forward, so every shot is reached from the same direction.",
    f"<b>{ui('Modalità di scatto')}</b>: <i>{ui('Scarica sul Mac')}</i> (recommended), <i>{ui('Solo sulla scheda')}</i>, <i>{ui('Solo trigger (veloce)')}</i> (faster: set the destination to card).",
    "<b>Session name</b>: photos go into a <code>name_date-time</code> subfolder, named <code>name_0001</code>, <code>name_0002</code>…",
    "<b>Return to start</b> when the sequence ends.",
    "<b>Presets</b>: save and recall the sequence settings, for example one per objective.",
    "<b>Progress</b>: shots taken, time left, position.",
    f"<b>Start</b>, <b>Pause</b>/<b>{ui('Riprendi')}</b> and <b>Abort</b>.",
    f"<b>{ui('Apri in Helicon Focus')}</b>: when the sequence ends, loads all the photos into Helicon Focus.",
])}
<p>Timing and backlash settings are in the collapsible <span class="ui">{ui('Tempi, gioco e nome della sessione')}</span>
section. In the photo folder the app also saves <code>sequence.json</code>, with the parameters used and the
position and temperature of every shot.</p>
<h2>While the sequence runs</h2>
{fig("sequenza-in-corso", [
    "The status turns to <b>Running</b> (amber).",
    "Shots taken out of the total, estimated time left and current position. On the travel bar the ticks of the shots already taken change colour.",
    "<b>Pause</b> holds after the current shot; <b>Abort</b> ends the sequence. The focuser's <b>STOP</b> also halts the motor at once.",
], layout="side narrow")}
<ul>
<li>If you press the focuser's <b>physical buttons</b>, the sequence pauses; when resumed it goes back to the right
  position and repeats the shot.</li>
<li>The sequence fields are locked while the sequence runs.</li>
<li>Every new photo appears in Latest shot and in the viewer.</li>
</ul>
""")

# 8
add(f"""
<h1><span class="n">8</span>The viewer</h1>
<p>Open it with <span class="ui">{ui('Apri visualizzatore ↗')}</span> or by clicking the latest shot. It is a separate
window you can move to a second monitor. It shows the photos at full resolution (RAW files too, converted on the
fly) with zoom and pan, and the camera's live view.</p>
{fig("visualizzatore", [
    "<b>◀ ▶</b> previous and next shot (arrow keys <kbd>←</kbd> <kbd>→</kbd>).",
    "File name; shot number, type, position, temperature and time.",
    "<b>● Live</b> (<kbd>L</kbd>): live view in the same window, with zoom and pan.",
    "<b>Zoom</b> − and + (<kbd>−</kbd> <kbd>+</kbd>) and the zoom level.",
    f"<b>{ui('Adatta')}</b> (<kbd>0</kbd>), <b>100%</b> (<kbd>1</kbd>: one sensor pixel = one screen pixel), <b>{ui('Reset')}</b> (<kbd>R</kbd>).",
    f"<b>{ui('Segui ultimo')}</b> (<kbd>U</kbd>): shows every new shot automatically.",
    f"<b>{ui('Blocca vista')}</b> (<kbd>K</kbd>): keeps zoom and position when you change shot, to compare focus at the same spot.",
    "<b>Finder</b>: shows the file in the Finder.",
    "<b>Full screen</b> (<kbd>F</kbd>).",
    "<b>Thumbnails</b>: click to open a shot. <i>P</i> = test shot, numbers are the sequence shots.",
], layout="full", anchors={n: "b" for n in range(1, 10)})}
<p>With the mouse: drag to pan, scroll wheel (or pinch on the trackpad) to zoom around the pointer, double-click to
switch between “fit” and 100%. Above 150% the pixels stay crisp, without blurring.</p>
{fig("visualizzatore-live", [
    f"<b>{ui('■ Ferma live')}</b> goes back to the photos; ◀ ▶ or clicking a thumbnail also leaves live view.",
    "Live status: LIVE, SHOOTING…, PAUSED during the sequence.",
], layout="full", anchors={1: "b"}, caption="Live view in the viewer, here with the simulator in focus (the checkerboard is sharp). At 100% the live view has the resolution of the camera's preview, lower than that of the photos.")}
""")

# 9
add(f"""
<h1><span class="n">9</span>Safety limits</h1>
<p class="lead">The limits stop the objective from touching the slide and the mechanics from hitting their end
stops. Set them first, calmly.</p>
{fig("fine-corsa", [
    f"<b>{ui('Fine corsa inferiore')}</b> in steps; <span class='ui'>{ui('⌖ Usa posizione attuale')}</span> takes it from the focuser's position.",
    f"<b>{ui('Fine corsa superiore')}</b>. Empty = the firmware maximum.",
    f"<b>Towards the specimen</b>: whether the step count goes down or up as you approach the specimen. It is used to label {ui('Avvicina')}/{ui('Allontana')} correctly.",
    f"<b>{ui('Salva fine corsa')}</b>.",
    f"<b>{ui('Imposta qui lo zero')}</b>: the current position becomes 0; limits and sequence are shifted accordingly.",
    f"<b>{ui('Scrivi il massimo nel firmware')}</b>: the upper limit becomes the firmware's limit.",
], layout="full")}
<h2>What protects what</h2>
<ul>
<li><b>Moves commanded by the app</b> (go to, {ui('Allontana')}/{ui('Avvicina')}, sequence, backlash compensation):
  the app checks them <i>before</i> moving the motor. Continuous movement stops at the limit; a sequence that would
  go beyond the limits does not start.</li>
<li><b>Physical buttons</b>: the app reads the position every 0.2–0.5 s; if it leaves the limits, it sends STOP and
  shows the alarm. Between two readings, though, the motor can overshoot the limit by a few dozen steps.</li>
</ul>
<h2>Recommended protection: limits in the firmware</h2>
<p>The firmware applies its limits to the physical buttons as well: it never goes below 0 and never above its
maximum.</p>
<ol class="steps">
<li>With a dry objective and no slide, or with great care, bring the stage to the position <b>closest to the
  specimen that is still safe</b> and click <span class="ui">{ui('Imposta qui lo zero')}</span>.</li>
<li>Bring the stage to the farthest useful position, click <span class="ui">{ui('⌖ Usa posizione attuale')}</span>
  on the upper limit, then <span class="ui">{ui('Salva fine corsa')}</span> and <span class="ui">{ui('Scrivi il massimo nel firmware')}</span>.</li>
<li>Check once, by hand and slowly with the physical buttons, that the focuser really stops at 0 and at the
  maximum.</li>
</ol>
<div class="box danger"><span class="t">Warning</span>The limit “towards the specimen” depends on the objective and
the slide thickness: with a short-working-distance objective (40×, 100×) the margin is a few tenths of a millimetre.
Check the limits again whenever you change objective, and after changing the <b>microstep</b>, which changes the
scale of the positions.</div>
""")

# 10 — mechanics
add(f"""
<h1><span class="n">10</span>Mechanical setup: the calculations</h1>
<p class="lead">The app thinks in <b>motor steps</b>. To show you moves, travel and sequence steps in
<b>micrometres</b>, and to work out the right step from the depth of field, it needs to know how many micrometres
one step is worth. This number is the <b>resolution</b> (µm/step) and depends on how the motor is coupled to the
fine focus.</p>
{fig("meccanica", [
    f"<b>Mode</b>: <i>{ui('Calcola dalla meccanica')}</i> (from the data below) or <i>{ui('Inserisci µm/passo')}</i> (a measured value).",
    f"<b>{ui('Passi motore per giro')}</b>: 200 for a 1.8° motor, 400 for a 0.9° one.",
    "<b>Microstep</b>: read from the firmware, not edited here (see Motor).",
    f"<b>{ui('Rapporto di riduzione')}</b>: how many turns the motor makes for one turn of the knob.",
    "<b>Travel per knob turn</b>: how many µm the stage moves for each turn of the fine focus knob.",
    "<b>Result</b>: µm per step, steps per µm, µm per 1000 steps.",
    f"<b>{ui('Salva meccanica')}</b>.",
])}
<h2>10.1 The drive train</h2>
<p>From the motor to the stage the movement passes through a few stages, and each one multiplies or divides:</p>
{diagram(DIAGRAM_LABELS)}
<div class="formula">
  resolution (µm/step) = {frac("travel per knob turn (µm)", "steps per rev × microstep × gear ratio")}
  <span class="lbl">This is exactly what the app computes in “{ui('Calcola dalla meccanica')}”.</span>
</div>
<h2>10.2 The four numbers, one at a time</h2>
<h3>Motor steps per revolution</h3>
<p>It follows from the step angle printed on the motor's label or datasheet:</p>
<div class="formula">steps per rev = {frac("360°", "step angle")}
<span class="lbl">1.8° → 200 steps · 0.9° → 400 steps · 7.5° → 48 steps</span></div>
<p>The NEMA 14 OMC 14HM11-0404S on the myFocuserPro2 focuser is a 0.9° motor: <b>400</b>. The NEMA 17
17HS13-0404S-PG27 with gearbox is 1.8°: <b>200</b>, and the gearbox goes into the ratio (below), not here.</p>
<h3>Microstep</h3>
<p>The driver can split each step into 2, 4, 8, 16 or 32 microsteps. At 1/8 microstep one motor turn takes 8 times
as many steps and the resolution becomes 8 times finer (but the torque per microstep drops and the top speed in
µm/s falls by a factor of 8).</p>
<ul>
<li><b>myFocuserPro2</b>: the microstep is set by the firmware and changed in {ui('Configurazione')} › Motor. The app
  reads it and uses it in the calculation by itself.</li>
<li><b>Ardufocus</b>: the microstep is fixed on the board (driver jumpers or wiring) and the firmware does not control
  it. Set <b>the same value as the board</b> in {ui('Configurazione')} › Motor, otherwise the calculation is off by
  that factor. If you don't know it, measure it (10.4).</li>
</ul>
<h3>Gear ratio</h3>
<p>It is the number of motor turns for <b>one</b> turn of the knob. All the stages are multiplied together:</p>
<div class="formula">ratio = gearbox × {frac("teeth of the pulley on the knob", "teeth of the pulley on the motor")}
<span class="lbl">with friction wheels or O-rings: use the diameters instead of the teeth</span></div>
<ul>
<li><b>Direct coupling</b> (motor on the knob shaft, no gearbox): ratio 1.</li>
<li><b>Toothed belt</b> from a 20-tooth GT2 pulley on the motor to a 60-tooth one on the knob: 60 ÷ 20 = <b>3</b>.</li>
<li><b>Planetary gearbox</b>: the ratio printed on the motor. The PG27 on the 17HS13 is 26 103/121 = 26 + 103 ÷ 121
  = <b>26.851</b> (not exactly 27: use the precise value). With direct coupling the ratio is 26.851; with a
  20 → 40 tooth belt it becomes 26.851 × 2 = 53.70.</li>
</ul>
<h3>Travel per knob turn</h3>
<p>How far the stage (or the tube, on microscopes that move the objective) travels for each turn of the knob the
motor drives, usually the <b>fine focus</b>. Many microscopes have 100 µm per turn, some 200 µm or other values.
The safest way to find out is to count the graduations on the knob:</p>
<div class="formula">travel per turn = number of graduations on the knob × µm per graduation
<span class="lbl">example: 100 graduations of 1 µm = 100 µm per turn · 50 graduations of 2 µm = 100 µm per turn</span></div>
<p>The value per graduation is often engraved on the knob or the microscope body (“1 µm”, “2 µm”) or given in the
manual. If the motor drives the <b>coarse focus</b> instead of the fine focus, the travel per turn is several
millimetres: the resolution is much coarser and must be checked carefully.</p>

<h2>10.3 Worked examples</h2>
<h3>Example A: myFocuserPro2 with NEMA 14 and belt</h3>
<div class="calc">motor 0.9°               → steps per rev = 360 ÷ 0.9 = 400
microstep                → 1 (full step)
pulleys 20 → 60 teeth    → ratio = 60 ÷ 20 = 3
fine focus               → 100 µm per turn

steps per knob turn = 400 × 1 × 3 = 1,200
resolution = 100 ÷ 1,200 = <b>{num(UA, 4)} µm/step</b>   (12 steps = 1 µm; 1,000 steps = {num(UA * 1000, 1)} µm)</div>
<p>This is the setup used for the screenshots in this guide. At 1/8 microstep the same focuser would give
100 ÷ (400 × 8 × 3) = <b>{num(um_step(100, 400, 8, 3), 4)} µm/step</b>.</p>
<h3>Example B: Ardufocus with NEMA 17 and PG27 gearbox</h3>
<div class="calc">motor 1.8°               → steps per rev = 200
microstep (on the board) → 1
gearbox 26 103/121       → 26.851, coupled directly to the knob
fine focus               → 100 µm per turn

steps per knob turn = 200 × 1 × 26.851 = {num(200 * GEAR17, 0)}
resolution = 100 ÷ {num(200 * GEAR17, 0)} = <b>{num(UB, 4)} µm/step</b>   (1 µm = {num(1 / UB, 1)} steps)</div>
<p>The gearbox makes the resolution about 4.5 times finer than example A and gives much more torque, but many more
steps are needed for the same move: that is why the app allows step sizes up to 100,000 steps (chapter 12).</p>

<h2>10.4 Checking with a measurement</h2>
<p>The calculation holds if all the data are right and nothing slips (a loose belt, a pulley turning on its shaft).
A check is always worthwhile, and essential if you don't know one of the numbers.</p>
<h3>With the fine-focus graduations</h3>
<ol class="steps">
<li>Always approach from the same direction (to rule out backlash): move a few hundred steps one way, then note
  the knob graduation lined up with the index mark.</li>
<li>With <span class="ui">{ui('Vai alla posizione')}</span> move by a large number of steps <b>N</b>, in the same
  direction, so that the knob turns at least half a turn (example A: N = 1,000; example B: N = 5,000).</li>
<li>Count the graduations travelled, <b>T</b>, and multiply by the µm per graduation.</li>
</ol>
<div class="formula">measured resolution = {frac("T × µm per graduation", "N")}</div>
<div class="calc">Example A: N = 1,000 steps, the knob advances 83 graduations of 1 µm
resolution = 83 × 1 ÷ 1,000 = <b>0.083 µm/step</b>   (the calculation gave {num(UA, 4)}: it matches)</div>
<h3>With a dial gauge</h3>
<p>A dial indicator reading to 0.01 or 0.001 mm resting on the stage measures the movement directly. Move N steps
(always from the same direction) and divide the movement in µm by N. The larger N, the more precise the result.</p>
<h3>If the measurement doesn't match</h3>
<ul>
<li>Off by a factor of 2, 4, 8, 16: the <b>microstep</b> is not what you think (typical of the Ardufocus).</li>
<li>Off by exactly 2: a 0.9° motor taken for a 1.8° one, or vice versa.</li>
<li>Off irregularly, changing from one measurement to the next: something <b>slips</b> (belt, pulley set screw) or
  the motor <b>skips steps</b> (speed too high, current too low).</li>
<li>If the mechanical data are uncertain but the measurement is repeatable, choose
  <span class="ui">{ui('Inserisci µm/passo')}</span> and enter the measured value.</li>
</ul>
{fig("meccanica-manuale", [
    f"<b>{ui('Inserisci µm/passo')}</b>: to use a measured value.",
    "Measured <b>µm per step</b>.",
    "The result updates as you type.",
], layout="side narrow")}

<h2>10.5 Other useful figures</h2>
<h3>Usable travel in millimetres</h3>
<div class="calc">travel (µm) = (upper limit − lower limit) × resolution
example A: (45,000 − 2,000) × {num(UA, 4)} = <b>{num(43000 * UA, 0)} µm ≈ {num(43000 * UA / 1000, 2)} mm</b></div>
<h3>Speed in µm per second</h3>
<div class="calc">speed (µm/s) = steps per second × resolution
example A, firmware at 400 steps/s:   400 × {num(UA, 4)} ≈ <b>{num(400 * UA, 0)} µm/s</b>
example B, firmware at 2,000 steps/s: 2,000 × {num(UB, 4)} ≈ <b>{num(2000 * UB, 0)} µm/s</b></div>
<p>This tells you how long a long move takes: 1 mm in example A takes about {num(1000 / (400 * UA), 0)} seconds.</p>
<h3>Backlash in steps</h3>
<p>When the motor reverses, the knob doesn't move for a few steps: that is the <b>backlash</b> of the drive train
(belt, teeth, gearbox, fine-focus thread). It is compensated in steps, so it is best measured in steps:</p>
<ol class="steps">
<li>Open live view in the viewer at 100% or more, on a small, high-contrast detail.</li>
<li>Move a few hundred steps one way, then reverse with a step size of 1 or 10.</li>
<li>Count the steps after the reversal before the image starts to move: that is the backlash. Repeat a few times
  and take the highest value, with a small margin.</li>
</ol>
<p>The rated angular backlash gives an order of magnitude. The PG27 gearbox is rated at no more than 1° of backlash
at the output, i.e. 1/360 of a knob turn:</p>
<div class="calc">backlash in steps = (1° ÷ 360°) × steps per knob turn = {num(200 * GEAR17, 0)} ÷ 360 ≈ <b>{num(200 * GEAR17 / 360, 0)} steps</b>
backlash in µm    = (1° ÷ 360°) × 100 µm ≈ <b>{num(100 / 360, 2)} µm</b></div>
<p>Belt and fine-focus backlash add to this: the live-view measurement is still the figure to trust. The value then
goes in <b>only one</b> of two places: the <b>sequence's compensation</b> (chapter 7) or the
<b>firmware's backlash IN/OUT</b> (chapter 12, at most 255 steps), not both.</p>
<h3>How fine the resolution needs to be</h3>
<p>The sequence step (chapter 11) should be worth at least ten or so motor steps, so that rounding to whole steps
matters little. With example A and a 60× objective the recommended step is about 7 steps: workable, but for very
strong objectives a finer resolution (microstep or higher reduction) is better.</p>
""")

# 11 — sequence step
add(f"""
<h1><span class="n">11</span>Choosing the sequence step</h1>
<p class="lead">Each photo is sharp only in a thin layer of the specimen, the <b>depth of field</b>. To have
everything in focus after stacking, the focus must not move more than that layer between one shot and the next,
with a little overlap.</p>
{fig("profondita", [
    f"<b>{ui('Apertura numerica (NA)')}</b>: the second number engraved on the objective (10×/<b>0.25</b>).",
    f"<b>{ui('Ingrandimento sul sensore')}</b>: objective magnification × the camera adapter's factor.",
    "<b>Sensor pixel</b> in µm. Nikon D5600: <b>3.9 µm</b> (23.5 mm ÷ 6,000 pixels).",
    "<b>Overlap</b> between one sharp layer and the next; 20–30% is a good value.",
    "<b>Result</b>: depth of field, recommended step in µm and in motor steps.",
    f"<b>{ui('Usa come passo della sequenza')}</b>: copies the value in steps into the sequence's Step field.",
])}
<h2>11.1 The formula</h2>
<p>The app uses Berek's formula, the most widely used in microscopy:</p>
<div class="formula">depth of field (µm) = {frac("λ · n", "NA²")} + {frac("n · e", "M · NA")}
<span class="lbl">λ = wavelength = 0.55 µm (green light) · n = refractive index between objective and slide = 1 (air) ·
e = sensor pixel size (µm) · M = magnification on the sensor</span></div>
<p>The first term is the optical limit (diffraction), the second the sensor's. Then:</p>
<div class="formula">step (µm) = depth of field × (1 − overlap) &nbsp;&nbsp;&nbsp; step (motor steps) = {frac("step (µm)", "resolution (µm/step)")}</div>
<h3>Worked example: 10×/0.25 objective, Nikon D5600, 1× adapter</h3>
<div class="calc">first term     = 0.55 × 1 ÷ 0.25²       = 0.55 ÷ 0.0625 = 8.80 µm
second term    = 1 × 3.9 ÷ (10 × 0.25)  = 3.9 ÷ 2.5     = 1.56 µm
depth of field = 8.80 + 1.56 = <b>10.36 µm</b>
step with 30% overlap = 10.36 × 0.70 = <b>7.25 µm</b>
in steps, example A: 7.25 ÷ {num(UA, 4)} = 87.0 → <b>87 steps</b>   example B: 7.25 ÷ {num(UB, 4)} → <b>{max(1, round(dof(.25, 10, 3.9) * .7 / UB))} steps</b></div>
<h3>Typical values (D5600, 1× adapter, 30% overlap)</h3>
{table(["Objective", "Depth of field (µm)", "Step (µm)", "Steps, example A", "Steps, example B"], dof_rows, right=(1, 2, 3, 4))}
<p style="font-size:9pt;color:#5a6b80">Example A = {num(UA, 4)} µm/step; example B = {num(UB, 4)} µm/step (section 10.3). Note: {dof_note}</p>
<div class="box tip"><span class="t">The camera adapter</span>If the adapter has a factor other than 1 (for example
0.5× or 2.5×), multiply the objective magnification by that factor: 10× with a 0.5× adapter = 5 on the sensor. Only
the second term of the formula changes, and it matters most with low-power objectives.</div>

<h2>11.2 Start, end and number of shots</h2>
<ol class="steps">
<li>Turn on live view (preferably in the viewer, zoomed in) and bring the focus <b>just above</b> the highest part
  of the subject you want sharp: click <span class="ui">{ui('⌖ qui')}</span> next to <b>{ui('Inizio')}</b>.</li>
<li>Go down to <b>just below</b> the lowest part and click <span class="ui">{ui('⌖ qui')}</span> next to <b>{ui('Fine')}</b>.</li>
<li>Enter the step (or use <span class="ui">{ui('Usa come passo della sequenza')}</span>): the app works out the number of shots.</li>
</ol>
<div class="formula">number of shots = {frac("|end − start|", "step")} + 1
<span class="lbl">rounded down, plus one final shot exactly at the end if the division is not exact</span></div>
<div class="calc">example: start 24,000, end 26,000, step 87
2,000 ÷ 87 = 22.99 → 22 + 1 = 23, plus the final shot at 26,000 = <b>24 shots</b>
travel = 2,000 × {num(UA, 4)} = <b>{num(2000 * UA, 1)} µm</b></div>
<p>The other way round, if you enter the <b>number of shots</b>, the app recalculates the step: step = travel ÷
(shots − 1), rounded to a whole step.</p>
<h2>11.3 Estimated duration</h2>
<p>For each shot the app adds up:</p>
<div class="formula">settle time + pause after shot + mirror delay + shutter speed + 1.5 s + {frac("step", "400")} s</div>
<p>where 1.5 s is an estimate of the release and transfer time and step ÷ 400 the move time. With the example
(1.5 s + 0.5 s + 0 + 1/60 s + 1.5 s + 0.22 s ≈ 3.7 s per shot × 24 shots) the duration is about
<b>a minute and a half</b>, as in the screenshot in chapter 7. While the sequence runs, the estimate is updated with
the real timings.</p>
<div class="box warn"><span class="t">Settle time matters</span>A microscope keeps vibrating for a while after each
move. If photos come out blurred or “doubled”, increase the settle time (2–3 s) and, on DSLRs, the mirror delay,
before looking for other causes.</div>
""")

# 12
add(f"""
<h1><span class="n">12</span>Motor, manual controls, updates, temperature</h1>
<h2>{ui('Motore (firmware)')}</h2>
{fig("motore", [
    "<b>Microstep</b>: full step, 1/2 … 1/32 (see 10.2). Changing it changes the scale of the positions: check the limits again afterwards.",
    "Firmware <b>speed</b>: slow, medium, fast.",
    f"<b>{ui('Bobine alimentate a motore fermo')}</b>: the motor holds its position, but runs warm.",
    f"<b>{ui('Inverti verso di rotazione')}</b>.",
    "<b>Compensate backlash IN / OUT</b>: at every reversal towards lower (IN) or higher (OUT) positions the firmware adds extra steps without counting them, physical buttons included.",
    "<b>Backlash IN / OUT</b> in steps, 0 to 255 (see 10.5).",
    f"<b>{ui('Rileggi')}</b> the values from the firmware.",
])}
<h2>{ui('Comandi manuali')}</h2>
{fig("comandi-manuali", [
    f"<b>Step sizes</b> of the {ui('Allontana')}/{ui('Avvicina')} buttons: in powers of ten up to 1,000, 10,000 or 100,000 steps. A gearbox needs large step sizes.",
    f"<b>{ui('Tieni premuto per muovere senza fermarti')}</b>: on release the motor slows down and stops; it stops anyway at the limit and, if the page stops responding, after about a second.",
], layout="side")}
<h2>{ui('Aggiornamenti')}</h2>
{fig("aggiornamenti", [
    "<b>App</b> version and the result of the last check.",
    "<b>Firmware</b> version on the focuser.",
    f"<b>{ui('Aggiorna firmware')}</b>: about 20 seconds; the focuser's settings are kept. Don't unplug the cable; if something goes wrong, just repeat it.",
    f"<b>{ui('Controlla ora')}</b> for app updates.",
], layout="side")}
<p>The app picks the right firmware for the board by itself (myFocuserPro2 or Ardufocus). The <b>Ardufocus</b> does
not restart over the USB cable: during the update the app asks you to press the board's <b>reset button</b>.</p>
<h2>{ui('Temperatura')}</h2>
{fig("temperatura", [
    "Current probe temperature.",
    "The last 60 minutes. The temperature of every shot is saved in <code>sequence.json</code>: useful because focus drifts with thermal expansion.",
], layout="side")}
""")

# 13
add(f"""
<h1><span class="n">13</span>A typical session, step by step</h1>
<h2>Once (or whenever the mechanics change)</h2>
<ol class="steps">
<li><b>Mechanics</b>: enter the data and check the resolution with a measurement (chapter 10).</li>
<li><b>Specimen direction</b> and <b>limits</b>, with the limits written to the firmware (chapter 9).</li>
<li><b>Backlash</b>: measure it with live view and choose where to compensate it (sequence or firmware).</li>
<li><b>Presets</b>: for each objective, work out the step from the depth of field and save a preset.</li>
</ol>
<h2>Every session</h2>
<ol class="steps">
<li>Switch on the focuser and the camera (mode M), plug in the cables and open Focus Stack.</li>
<li>Connect the focuser and the camera from the {ui('Sessione')} tab.</li>
<li>Set shutter speed, ISO and format; take a <b>test shot</b> and check it in the viewer at 100%.</li>
<li>Choose the objective's <b>preset</b> (or the step).</li>
<li>Using <b>live view</b> and the keyboard, find the <b>end</b> and the <b>start</b> of the sequence and click {ui('⌖ qui')}.</li>
<li>Check the summary: number of shots, travel, duration, no red warning.</li>
<li><b>{ui('▶ Avvia sequenza')}</b>. Don't touch the microscope: vibrations spoil the shots.</li>
<li>When the sequence ends, click <b>{ui('Apri in Helicon Focus')}</b>.</li>
</ol>
""")

# 14
add(f"""<h1><span class="n">14</span>Troubleshooting</h1>
<p>The <b>{ui('Registro')}</b> (third tab) lists every connection, move, shot and error with its time: when something
goes wrong, read it first.</p>
""")
add(table(["Problem", "What to do"], [
    ["The camera won't connect", "Quit Photos, Preview, Image Capture, NX Studio, EOS Utility; unplug and replug the cable with the camera on; make sure it is in mode M and that Wi-Fi/SnapBridge are off."],
    ["Live view won't start (Nikon D5600)", f"Mode dial on <b>M</b> (scene modes can block live view over USB), card inserted, battery charged, image review off. The exact message appears at the bottom and in the <b>{ui('Registro')}</b> (“{ui('Live view interrotto: …')}”): that is the first thing to look at. Also make sure you have the latest version of the app."],
    ["Live view is slow with two windows open", "Update the app: since version 1.0.6 the main window and the viewer both receive every frame."],
    ["The focuser doesn't appear among the ports", "Click ⟳ after plugging in the cable; try another USB socket or another cable (some cables only charge)."],
    ["The motor buzzes but doesn't turn, or skips steps", "Speed too high for the load or driver current too low; also check that the pulley isn't slipping on its shaft."],
    ["Distances in µm don't add up", "Repeat the measurement in section 10.4; on the Ardufocus check the microstep."],
    ["Red “outside the limits” alarm", f"A physical button took the focuser past a limit. Bring the position back inside the limits with {ui('Allontana')}/{ui('Avvicina')}; to prevent it, write the limits to the firmware (chapter 9)."],
    ["The sequence won't start", "Read the red warning in the summary: usually the sequence, including backlash compensation, goes beyond the limits."],
    ["Blurred or doubled photos", "Increase the settle time and the mirror delay; use bulb or the silent shutter if the camera allows it."],
    [f"“{ui('Focus Stack è chiuso')}” on the page", "The app has been closed: reopen it and the page reloads by itself."],
]))

# 15
add(f"""<h1><span class="n">15</span>Keyboard shortcuts</h1>
<div class="two">
<div class="keep"><h2 style="margin-top:0">{ui('Sessione')} tab</h2>
<table><tbody>
<tr><td><kbd>↑</kbd></td><td>move the objective away from the specimen</td></tr>
<tr><td><kbd>↓</kbd></td><td>move the objective closer to the specimen</td></tr>
<tr><td><kbd>⇧</kbd> + <kbd>↑</kbd>/<kbd>↓</kbd></td><td>step × 10</td></tr>
<tr><td><kbd>1</kbd> <kbd>2</kbd> <kbd>3</kbd> …</td><td>step size: 1, 10, 100 …</td></tr>
<tr><td><kbd>Esc</kbd></td><td>STOP</td></tr>
</tbody></table></div>
<div class="keep"><h2 style="margin-top:0">Viewer</h2>
<table><tbody>
<tr><td><kbd>←</kbd> <kbd>→</kbd></td><td>previous / next shot</td></tr>
<tr><td><kbd>L</kbd></td><td>live view on / off</td></tr>
<tr><td><kbd>−</kbd> <kbd>+</kbd></td><td>zoom</td></tr>
<tr><td><kbd>0</kbd> or <kbd>R</kbd></td><td>fit to window</td></tr>
<tr><td><kbd>1</kbd></td><td>100%</td></tr>
<tr><td><kbd>U</kbd></td><td>follow latest</td></tr>
<tr><td><kbd>K</kbd></td><td>lock view</td></tr>
<tr><td><kbd>F</kbd></td><td>full screen</td></tr>
</tbody></table></div>
</div>
<p style="margin-top:8mm;color:#5a6b80;font-size:9pt">Focus Stack is free software (MIT licence) ·
github.com/teoteo/focus-stack · The firmware is derived from myFocuserPro2 by Robert Brown (MIT licence).</p>
""")
