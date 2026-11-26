"""English text of the guide. Not a module to import: genera_guida.py runs it with exec() in a
namespace that already holds the shared helpers and numbers (fig, frac, table, num, diagram, VERSION,
ICON, IMG, UA, UB, GEAR17, um_step, dof, OBJ). The text fills the list H with the HTML sections.
"""
# ruff: noqa: F821  (names come from genera_guida.py)

META = {
    "lang": "en",
    "title": "Focus Stack — User Guide",
    "footer": "User Guide",
    "pdf": "EN Focus Stack - Guide.pdf",
}

# Names of the app's commands and labels, keyed by the Italian text (= the app's translation keys).
# To be aligned with the app's real English strings (web/lang/en-*.json) once they are final.
UI = {
    "Sessione": "Session",
    "Ottica": "Optics",
    "Configurazione": "Configuration",
    "Registro": "Log",
    "Esporta": "Export",
    "Analisi del sensore": "Sensor analysis",
    "Sensore": "Sensor",
    "Prepara": "Prepare",
    "Tappo": "Cap",
    "Risultato": "Result",
    "Ho messo il tappo: scatta i dark": "The cap is on: shoot the darks",
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
    "Visualizzatore": "Viewer",
    "Inizio": "Start",
    "Fine": "End",
    "⌖ qui": "⌖ here",
    "qui": "here",
    "Usa posizione attuale": "Use current position",
    "Passo (passi motore)": "Step (motor steps)",
    "Numero di scatti": "Number of shots",
    "Salva in": "Save to",
    "Scegli…": "Choose…",
    "Apri": "Open",
    "Tempi, gioco e scatti per posizione": "Timing, backlash and shots per position",
    "Scatti per posizione": "Shots per position",
    "Ottica e filtro (profilo)": "Optics and filter (profile)",
    "Modifica": "Edit",
    "Profilo da modificare": "Profile to edit",
    "— nuovo profilo —": "— new profile —",
    "Salva come nuovo profilo…": "Save as new profile…",
    "Elimina profilo": "Delete profile",
    "Salva profilo": "Save profile",
    "Obiettivo": "Objective",
    "Ingrandimento dell'obiettivo": "Objective magnification",
    "Cambio d'ingrandimento intermedio": "Intermediate magnification changer",
    "Adattatore / oculare di proiezione": "Camera adapter / projection eyepiece",
    "Immersione": "Immersion",
    "Filtro": "Filter",
    "Non indicato": "Not specified",
    "Nessun filtro": "No filter",
    "Filtro montato": "Filter fitted",
    "Illuminazione": "Illumination",
    "Note": "Notes",
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
    "Apri nel Finder": "Open in the Finder",
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
    "Motore (firmware)": "Motor (firmware)",
    "Microstep": "Microstep",
    "Velocità": "Speed",
    "Alimentazione bobine motore": "Motor coil power",
    "Sempre quando connesso": "Always while connected",
    "Alimentazione bobine motore › Sempre quando connesso": "Motor coil power › Always while connected",
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
    "Pixel del sensore (pixel pitch in µm)": "Sensor pixel (pixel pitch in µm)",
    "Sovrapposizione (%)": "Overlap (%)",
    "Usa come passo della sequenza": "Use as sequence step",
    "Focus Stack è chiuso": "Focus Stack is closed",
    "Live view interrotto: …": "Live view stopped: …",
    # 1.1.0
    "Calibrazione": "Calibration",
    "Nome della pila": "Stack name",
    "＋ Nuova pila": "＋ New stack",
    "Suono sul Mac a fine sequenza": "Sound on the Mac when the sequence ends",
    "Tipo di ottica": "Optics type",
    "Microscopio": "Microscope",
    "Macro fotografica": "Photographic macro",
    "Cerca nel database": "Search the database",
    "＋ Aggiungi al mio elenco": "＋ Add to my list",
    "Marca": "Make",
    "Modello": "Model",
    "Focale (mm)": "Focal length (mm)",
    "Diaframma più aperto (f/)": "Widest aperture (f/)",
    "Rapporto di riproduzione dell'obiettivo (×)": "Lens reproduction ratio (×)",
    "Diaframma impostato (f/)": "Aperture set (f/)",
    "Tubi di prolunga / soffietto (mm)": "Extension tubes / bellows (mm)",
    "Tubi di prolunga e lenti addizionali": "Extension tubes and close-up lenses",
    "µm per pixel sul campione, misurati": "µm per pixel on the specimen, measured",
    "Temperatura di colore (K)": "Colour temperature (K)",
    "Esposizione dei light": "Light exposure",
    "Misura su": "Measure on",
    "Luci (99,5° percentile)": "Highlights (99.5th percentile)",
    "Media (livello medio)": "Mean (average level)",
    "Media": "Medium",
    "Livello obiettivo (% della saturazione)": "Target level (% of saturation)",
    "Calcola e imposta il tempo": "Compute and set the shutter speed",
    "Frame di calibrazione": "Calibration frames",
    "Tipo di frame": "Frame type",
    "Dark": "Darks",
    "Flat": "Flats",
    "Dark dei flat": "Flat darks",
    "Fotogrammi": "Frames",
    "Livello dei flat (% della saturazione)": "Flat level (% of saturation)",
    "▶ Scatta i frame": "▶ Take the frames",
    "Interrompi": "Abort",
    "Libreria di calibrazione": "Calibration library",
    "Avanzamento da smartphone": "Smartphone progress",
    "Mostra l'avanzamento sulla rete locale": "Show progress on the local network",
    "Nuovo link": "New link",
    "Avvisami con un suono a fine sequenza": "Alert me with a sound when the sequence ends",
    "Mostra l'ultimo scatto": "Show the last shot",
    "Aggiorna l'ultimo scatto": "Refresh the last shot",
    "Svuota": "Clear",
    "Ispettore": "Inspector",
    "Bruciati e neri": "Burnt and black",
    "Evidenzia sull'immagine": "Mark on the image",
    "Sotto il puntatore:": "Under the pointer:",
    "Motore": "Motor",
    "Alimentale comunque durante la sequenza": "Power them anyway during the sequence",
    "Anche quando viene disconnesso o si spegne l'applicazione": "Also when disconnected or when the app quits",
    "Tratto massimo per comando (passi)": "Maximum segment per command (steps)",
}


def ui(s):
    """English name of an app command (the Italian text is the key)."""
    return UI.get(s, s)


# nome dell'opzione con l'apostrofo: in una costante, perché Python 3.11 non accetta virgolette annidate nelle f-string
COIL_HOLD = "Anche quando viene disconnesso o si spegne l'applicazione"


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

# schema «Come li usa la fusione» (7.6): etichette dello SVG, testo semplice (&lt; per <)
CALIB_LABELS = {
    "col_dark": 'MASTER DARK',
    "col_stack": 'SUBJECT STACK',
    "col_flat": 'MASTER FLAT',
    "dark": 'Darks · N shots',
    "dark1": 'cap on, same ISO and shutter',
    "mean": 'pixel-by-pixel average',
    "D": 'D: master dark',
    "flat": 'Flats · N shots',
    "flat1": 'even field, same optics',
    "flat_mean": 'average − flat darks',
    "norm": '÷ its own average',
    "F": 'F: normalised flat',
    "F1": '&lt; 1 at the edges and on dust',
    "frame": 'Each frame I',
    "frame1": 'RAW, linear light',
    "fusion": 'alignment and fusion',
    "note1": 'Without darks the subtraction is skipped,',
    "note2": 'without flats the division.',
}

# grafico d'esempio dell'analisi del sensore (7.6)
SENSOR_LABELS = {
    "title_dr": 'Dynamic range (stops)',
    "title_rn": 'Read noise (electrons)',
    "unreliable": 'not reliable',
    "stops": 'stops',
    "dcg1": 'dual gain:',
    "dcg2": 'from 3.0 to 1.2 e-',
    "dec": '.',
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
  <div class="shot-c"><img src="{IMG}/sessione.jpg" alt=""></div>
  <div class="meta"><span>App version {VERSION}</span><span>November 2026</span></div>
</section>
""")

add("""
<h1 style="break-before:auto">Contents</h1>
<div class="toc"><ol>
<li><span>1</span>What Focus Stack is<em>how it works, what you need</em></li>
<li><span>2</span>Installing, starting and updating</li>
<li><span>3</span>The interface at a glance<em>the five tabs, the top bar and the guide</em></li>
<li><span>4</span>Connecting the focuser and the camera<em>settings for the Nikon D5600 and other cameras</em></li>
<li><span>5</span>The focuser: position, moves, STOP<em>continuous movement in segments, the stage that doesn't advance</em></li>
<li><span>6</span>Camera, test shot and live view</li>
<li><span>7</span>The stacking sequence<em>optics profiles, photographic macro, several shots per position, the stack files,
calibration (darks, flats, exposure), smartphone progress</em></li>
<li><span>8</span>The viewer<em>zoom, live view, autofocus on a point, Inspector</em></li>
<li><span>9</span>Safety limits</li>
<li><span>10</span>Mechanical setup: the calculations<em>resolution in µm per step, verification, travel, speed, backlash</em></li>
<li><span>11</span>Choosing the sequence step<em>depth of field, number of shots, duration</em></li>
<li><span>12</span>Motor, manual controls, autofocus, updates, temperature</li>
<li><span>13</span>A typical session, step by step</li>
<li><span>14</span>Troubleshooting</li>
<li><span>15</span>Keyboard shortcuts</li>
</ol></div>
""")

# 1
add(f"""
<h1><span class="n">1</span>What Focus Stack is</h1>
<p class="lead">Focus Stack lets your Mac drive a motorized focuser, fitted to the microscope's fine focus or to a
macro rail, and a camera connected over USB. It runs <b>move → wait → shoot</b> sequences automatically: dozens of photos at
different focus positions, ready to be merged into one fully sharp image with <b>Helicon Focus</b> (or a
similar program).</p>
<h2>How it works</h2>
<p>The Focus Stack app starts a small program on the Mac (the <i>server</i>) that talks to the focuser (an
Arduino board running the myFocuserPro2 firmware) and to the camera. The interface opens in the <b>app's
window</b>: it is a web page served at <code>http://localhost:8765</code>, reachable only from this Mac (it can also be
opened in a browser).</p>
<ul>
<li>The <b>focuser</b> turns the focus knob with a stepper motor. Each motor <i>step</i> moves the stage (or the
  objective) by a fraction of a micrometre; how much is worked out by the <b>mechanical setup</b> (chapter 10).</li>
<li>The <b>camera</b> is controlled with the same protocol the manufacturers' programs use: shutter speed,
  ISO, format, release, photo download and live view.</li>
<li>The focuser's <b>physical buttons</b> keep working while the app is open.</li>
</ul>
<h2>What you need</h2>
<ul>
<li>A Mac with macOS 13 or later (Intel) or macOS 14 or later (Apple Silicon).</li>
<li>A <b>myFocuserPro2</b> focuser (DRV8825 driver version) or an <b>Ardufocus</b> (rev1 board with DRV8825),
  connected with its USB cable and powered (12 V).</li>
<li>A Nikon, Canon or Sony camera with its USB cable. This guide uses a <b>Nikon D5600</b> as the example.</li>
<li>On the microscope, an adapter that projects the image onto the sensor (photo tube, T2 adapter or similar). For
  <b>photographic macro</b>, a macro lens (with any tubes or close-up lenses) and a rail driven by the
  focuser.</li>
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
<li>When it starts, Focus Stack opens its window and stays in the Dock. Closing the window (<kbd>⌘W</kbd>)
  only hides it: the app keeps running and clicking the Dock icon brings it back. The viewer and the guide open
  in separate windows; links to external sites open in the browser.</li>
<li>To quit: <kbd>⌘Q</kbd> on the app, or <span class="ui">{ui("Esci")}</span> from the Dock icon's menu.
  If a sequence is running, the app asks for confirmation, stops it and halts the motor.</li>
<li>During a stack or a calibration series the Dock icon shows a <b>progress bar</b>. When it finishes, or stops
  because of an error, while you are using another app you get a <b>notification</b>: the first time macOS asks
  for permission.</li>
</ul>
<h2>Updates</h2>
<p>At start-up, and then every 6 hours, the app checks for a new version. If there is one, a bar with
<span class="ui">{ui("Aggiorna e riavvia")}</span> appears at the top: the app downloads the new version, quits and
reopens by itself. You can run the same check by hand in
<span class="ui">{ui("Configurazione")} › {ui("Aggiornamenti")} › {ui("Controlla ora")}</span>.</p>
<p>The <b>focuser firmware</b> is updated from the app too (chapter 12): when the board's firmware is older than
the one bundled with the app, the same bar tells you. It is worth installing: build 5, for example,
makes the movement continuous without pauses and stops the motor by itself if the Mac stops communicating (chapter 12).</p>
<h2>Language</h2>
<p>The app speaks Italian, English, French, German and Spanish. With <span class="ui">{ui("Automatica (lingua del sistema)")}</span> it follows the
language of macOS, falling back to English for other languages; you can force a language in
<span class="ui">{ui("Configurazione")} › {ui("Lingua")}</span>. The choice applies to the interface, messages and log, and
this guide exists in the same languages.</p>
""")

# 3
add(f"""
<h1><span class="n">3</span>The interface at a glance</h1>
<p>The page has five tabs, chosen at the top:</p>
<ul>
<li><b>{ui("Sessione")}</b>: the work at the microscope. Focuser, sequence, camera and latest shot.</li>
<li><b>{ui("Ottica")}</b>: the <b>profiles</b> for objective, filter and illumination, for the microscope or for
  photographic macro, which are recorded in the data of every stack, and the depth-of-field calculator
  (chapters 7.2, 7.3 and 11).</li>
<li><b>{ui("Calibrazione")}</b>: the light exposure and the calibration frames (darks, flats, flat darks) for the
  fusion software (chapter 7.6).</li>
<li><b>{ui("Configurazione")}</b>: limits, mechanics, manual controls, motor, smartphone progress, language,
  updates and temperature. Set up once, then rarely touched.</li>
<li><b>{ui("Registro")}</b>: a timestamped list of everything that happened in the session. The first place to look
  when something goes wrong.</li>
</ul>
{fig("sessione", layout="full", caption="The Session tab: focuser on the left, sequence in the middle, camera and latest shot on the right.")}
<h2>Top bar</h2>
{fig("barra-superiore", [
    f"<b>Tabs</b> {ui('Sessione')}, {ui('Ottica')}, {ui('Calibrazione')}, {ui('Configurazione')} and {ui('Registro')}.",
    "<b>Connection status</b>: Server, Focuser and Camera. Green = connected, grey = disconnected, red = error.",
    "<b>Temperature</b> read by the focuser's probe.",
    "<b>?</b> opens this <b>guide</b> at the chapter for the open tab.",
    "<b>Theme</b>, dark or light. The dark theme is easier on the eyes during long sessions at the microscope.",
], layout="full below-marks", anchors={1: "b", 2: "b", 3: "b", 4: "b", 5: "b"})}
<p>Two strips can appear below the bar: a blue one for <b>updates</b> and a red <b>alarm</b> one, for example
when the physical buttons take the focuser past a limit.</p>
<div class="box tip"><span class="t">The guide inside the app</span>Besides the <b>?</b> at the top, almost every card
has a small <b>?</b> next to its title: it opens this guide right at the part that explains that card. The guide has
a table of contents and a search (<kbd>/</kbd> key) and always opens in the same window.</div>
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
<p>When it opens, the app <b>reconnects by itself</b> to the focuser and the camera used last time, if they are
connected to the Mac: you only need to have connected them once with <b>{ui('Connetti')}</b>. The focuser reconnects only if
it is the same USB adapter (another device with the same port name is left alone), and connecting does not move the
motor. If a connection fails a line is left in the log, and <b>{ui('Connetti')}</b> works as always.</p>
<h3>Settings on the camera</h3>
{table(["Camera", "What to set"], [
    ["<b>Nikon D5600</b> and other Nikons", "Mode dial on <b>M</b> (manual). In the playback menu turn <b>image review</b> off. Turn off SnapBridge/Wi-Fi and Bluetooth, which can tie up the connection. Keep a memory card inserted and the battery charged (or use the EH-5/EP-5A power adapter)."],
    ["Canon", "Mode <b>M</b>. The shot goes to the camera's memory or to the card depending on <i>Destination</i>. For the mirror delay, enable <b>mirror lock-up</b> in the menu."],
    ["Sony", "USB menu › <b>PC Remote</b>; mode <b>M</b>. To download the photos to the Mac set the destination to <b>PC Only</b> (MENU › Setup › PC Remote Settings › Still Img. Save Dest.). For live view the camera must allow it in PC Remote."],
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
    f"<b>{ui('Allontana')} / {ui('Avvicina')}</b>: a click moves by the chosen step size. Hold the button and the motor keeps moving, in segments (chapter 12), and when you let go it slows down and stops.",
    f"<b>{ui('Vai alla posizione')}</b>: type a number of steps and click {ui('Vai')}.",
    "<b>STOP</b>: stops the motor and any running sequence at once. Keyboard: <kbd>Esc</kbd>. After STOP the motor stays still until you press a button again.",
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
<div class="box tip"><span class="t">Keyboard</span><kbd>↑</kbd> moves away, <kbd>↓</kbd> moves closer: a tap makes one
step, holding the key down moves continuously until you release it (like the buttons). <kbd>⇧</kbd> with an arrow multiplies the step by 10, the number keys <kbd>1</kbd> <kbd>2</kbd>
<kbd>3</kbd>… choose the step size, <kbd>Esc</kbd> is STOP. They work in the {ui('Sessione')} tab, even while
you watch the live view.</div>
<div class="box warn"><span class="t">Physical buttons</span>The buttons on the focuser drive the motor without
going through the app. The app watches them and, if the position leaves the limits, sends STOP and shows an
alarm; for full protection read chapter 9. Pressing them during a sequence pauses the sequence.</div>
<div class="box warn"><span class="t">If the stage doesn't advance with small steps</span>With <span class="ui">{ui('Alimentazione bobine motore › Sempre quando connesso')}</span>
turned off ({ui('Configurazione')} › Motor) the motor loses, at every stop, the force that holds it in position: the
load (weight of the camera, a spring, the belt) can pull it back. The step counter advances, but the stage stays where it
is and a whole stack ends up on the same plane. During the sequence the app powers the coils by itself (chapter 12); for
manual moves of a few steps turn them on, or check in live view that the image really moves.</div>
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
<p>With <b>Sony</b> cameras, shutter speed and ISO change in steps, as if turning the dial: a distant value can take
a few seconds. For the <b>A6400</b> the ISO menu goes up to 102400, the highest value it accepts. If the camera does not
accept a value within 12 seconds, the app tells you: unplug and replug the USB cable, or switch the camera off and on.</p>
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
    "Status: <b>LIVE</b>, or <b>SHOOTING…</b> during a test shot.",
    "Camera model. Double-click the image for full screen.",
], layout="stack")}
</div>
<p>Live view runs at up to 15 frames per second and is the easiest way to find the start and end of the
sequence while you move the focuser with the keyboard. When the sequence starts, live view stays on
while the focuser goes back to the start position, so you can watch it; once there it pauses (the mirror has to come
down and the camera has to shoot normally) and it closes at the first shot: the frame goes back to showing the latest
shot, in the viewer too. When the stack is done, turn it back on with <span class="ui">{ui('● Live')}</span>. On DSLRs
the mirror stays up while live view is on. Live view turned on from the main window also starts in the viewer, if it
is open; <span class="ui">{ui('■ Ferma live')}</span> turns it off in both windows. With <span class="ui">{ui('◉ Scatto di prova')}</span>
while live view is on, the frame shows the shot and live view restarts by itself as soon as you move the focuser, from the
app or with its own buttons.</p>
<div class="box tip"><span class="t">For precise focusing</span>Open live view in the <b>viewer</b>: you can zoom
to 100% and beyond and pan to the detail you care about (chapter 8).</div>
""")

# 7
add(f"""
<h1><span class="n">7</span>The stacking sequence</h1>
<h2 style="margin-top:0">7.1 Setting up the sequence</h2>
{fig("sequenza", [
    "<b>Status</b>: Ready, Running, Paused, Completed, Error.",
    f"<b>{ui('Nome della pila')}</b>: photos go into a <code>name_date-time</code> subfolder, named <code>name_0001</code>, <code>name_0002</code>…",
    f"<b>{ui('＋ Nuova pila')}</b>: once a stack is finished, prepares the next one (the status goes back to Ready). Even with the same name, every stack goes into a new folder.",
    f"<b>{ui('Inizio')}</b> and <b>{ui('Fine')}</b> in steps. <span class='ui'>⌖ {ui('qui')}</span> copies the current position.",
    "<b>Step</b> between one shot and the next, in motor steps (chapter 11).",
    f"<b>Number of shots</b>. If you change {ui('Inizio')}, {ui('Fine')} or Step, the number of shots is recalculated; if you change the number of shots, the step is recalculated. When the step changes on its own it turns orange and shows <span class='ui'>↺ was …</span>: one click undoes the change.",
    "<b>Settle time after move</b>: time for vibrations to die down before the shot (1–3 s on a microscope).",
    f"<b>{ui('Ottica e filtro (profilo)')}</b>: the objective, filter and illumination profile to record in the stack's data (7.2). <span class='ui'>{ui('Modifica')}</span> opens it in the {ui('Ottica')} tab. Without a profile the stack is recorded as “no filter”.",
    "<b>Summary</b>: shots, travel in steps and in µm, step in µm and estimated duration. One click on the summary (▶ on the right) also shows the optics profile used and the calibration that will be linked to the stack. If the sequence goes beyond the limits a red warning appears and the sequence won't start.",
    f"<b>{ui('Salva in')}</b>: the photo folder. <span class='ui'>{ui('Scegli…')}</span> opens the Finder panel, <span class='ui'>{ui('Apri')}</span> shows it in the Finder.",
    f"<b>{ui('Scatti per posizione')}</b>: how many photos to take at each position (default 1). With several shots the fusion software can average them and reduce noise (7.4).",
    "<b>Pause after shot</b>: time to write to the card and recharge the flash.",
    "<b>Backlash compensation</b>: before the first shot the motor backs off by this many steps and then moves forward, so every shot is reached from the same direction.",
    f"<b>{ui('Modalità di scatto')}</b>: <i>{ui('Scarica sul Mac')}</i> (recommended), <i>{ui('Solo sulla scheda')}</i>, <i>{ui('Solo trigger (veloce)')}</i> (faster: set the destination to card).",
    "<b>Return to start</b> when the sequence ends.",
    f"<b>{ui('Suono sul Mac a fine sequenza')}</b>: a bright sound if the stack completed, a low one if it stopped because of an error or paused by itself.",
    "<b>Presets</b>: save and recall the sequence settings, for example one per objective.",
    "<b>Progress</b>: shots taken, time left, position.",
    f"<b>Start</b>, <b>Pause</b>/<b>{ui('Riprendi')}</b> and <b>Abort</b>.",
    f"<b>{ui('Apri nel Finder')}</b>: when the sequence ends, opens the stack folder, with the photos, <code>sequence.json</code> and <code>sequence.txt</code> (7.5).",
])}
<p>Shots per position, pause after shot, backlash, capture mode, return to start and sound are in the collapsible
<span class="ui">{ui('Tempi, gioco e scatti per posizione')}</span> section. If the motor coils are off and the app
does not power them during the sequence, an orange warning appears below it (chapter 12).</p>
<h2>While the sequence runs</h2>
{fig("sequenza-in-corso", [
    "The status turns to <b>Running</b> (amber).",
    "Shots taken out of the total, estimated time left and current position. On the travel bar the ticks of the shots already taken change colour.",
    "<b>Pause</b> holds after the current shot; <b>Abort</b> ends the sequence. The focuser's <b>STOP</b> also halts the motor at once.",
], layout="side narrow")}
<ul>
<li>If you press the focuser's <b>physical buttons</b>, the sequence pauses; when resumed it goes back to the right
  position and repeats the shot.</li>
<li><b>If a shot fails</b> the app tries again after 3 s; after the second error it reconnects the camera by itself and
  tries once more. If that is not enough, the sequence <b>pauses</b> (it does not stop) and the message says what to
  check: sort out the camera (battery, cable, card) and click <span class="ui">{ui('Riprendi')}</span>. The app
  reconnects the camera, goes back to the same position and repeats the shot; the photos continue in the same folder.</li>
<li><b>The Mac does not go to sleep</b> while the sequence runs: sleep would suspend USB and the camera would
  disappear halfway through the stack. The display can still turn off. Note: closing the lid of a laptop without an
  external monitor puts the Mac to sleep anyway.</li>
<li>If the motor coils are off when idle, the app powers them for the whole stack and turns them off again after the
  return to the start (chapter 12).</li>
<li>The sequence fields are locked while the sequence runs.</li>
<li>Every new photo appears in Latest shot and in the viewer. To follow the stack away from the Mac there is
  smartphone progress (7.7).</li>
</ul>

<h2>7.2 Optics and filter: the profiles</h2>
<p>The fusion software works better when it knows what the photos were taken with: given the magnification and the
sensor pixel it can produce the depth map and the 3D view in real micrometres. These data are saved in the
<b>{ui('Ottica')}</b> tab as named <b>profiles</b>, one for each combination of objective, filter and illumination
(for example “10× GFP”, “4× brightfield”), and chosen in the sequence (number 8 in the figure above). Each profile is
of type <b>{ui('Microscopio')}</b> or <b>{ui('Macro fotografica')}</b> (7.3). The figure shows a microscope profile: a
10× objective with an Optovar 1.6× magnification changer and the camera on a T2 adapter with no lens.</p>
{fig("ottica", [
    f"<b>{ui('Profilo da modificare')}</b>: choose one to load its values; <i>{ui('— nuovo profilo —')}</i> starts from an empty form.",
    "<b>Save as new profile…</b>, in the bar that appears at the top: asks for a name and saves a copy, leaving the original profile as it was.",
    f"<b>{ui('Elimina profilo')}</b>, after a confirmation. <b>Rename…</b> changes the name also in the sequence and in the flats of the calibration library.",
    f"<b>{ui('Tipo di ottica')}</b>, the two tabs at the top of the {ui('Ottica')} panel, which change the fields below: <i>{ui('Microscopio')}</i> (objective with engraved magnification and NA) or <i>{ui('Macro fotografica')}</i> (photographic lens, tubes and close-up lenses, 7.3).",
    "<b>Sensor pixel</b> (pixel pitch) in µm. Nikon D5600: <b>3.9 µm</b> (23.5 mm ÷ 6,000 pixels). It is in the camera's specifications, on <b>digicamdb.com</b> (photo cameras) or in the sensor database of <b>AstroBin</b> (dedicated cameras, searching for example IMX571).",
    f"<b>{ui('Adattatore / oculare di proiezione')}</b> between the microscope and the camera: name and factor, for example a 0.5× or 0.63× C-mount adapter, a 2.5× photo eyepiece, a T2 adapter with no lens 1×. Empty = 1×.",
    "<b>" + ui("Cambio d'ingrandimento intermedio") + "</b>, if the microscope stand has one: name and factor, for example <i>Optovar</i> 1.25×, 1.6× or 2×. Empty = 1×.",
    f"<b>{ui('Obiettivo')}</b>: any name, for example as engraved on the objective.",
    "<b>" + ui("Ingrandimento dell'obiettivo") + "</b>: the first number engraved on the objective (<b>10</b>×/0.25).",
    f"<b>{ui('Apertura numerica (NA)')}</b>: the second number engraved on the objective (10×/<b>0.25</b>).",
    f"<b>{ui('Immersione')}</b>: air, water, oil, glycerol or silicone.",
    "<b>µm per pixel on the specimen, measured</b> with a stage micrometer: if present, it takes precedence over the calculation.",
    f"<b>{ui('Ingrandimento sul sensore')}</b> = objective × intermediate changer × adapter (here 10 × 1.6 × 1 = 16×) and <b>scale on the specimen</b>: the measured value, or sensor pixel ÷ magnification. With a measurement you also see the <b>real magnification</b> (sensor pixel ÷ measured µm per pixel), which includes what the chain leaves out, such as the sensor distance or the photo tube; if the deviation is large, the factor <i>suggested by the measurement</i> appears next to the adapter: one click writes it into the field.",
    f"<b>{ui('Filtro')}</b>: <i>{ui('Non indicato')}</i> (unknown), <i>{ui('Nessun filtro')}</i> or <i>{ui('Filtro montato')}</i>.",
    "Filter <b>name</b> and <b>type</b>: band pass, long pass, short pass, neutral density, polarizer, other.",
    "<b>Centre</b> and <b>bandwidth</b> in nm for a band pass; for long pass and short pass, the cut-off wavelength.",
    f"<b>{ui('Illuminazione')}</b> (free text, with suggestions), <b>intensity</b> in % and <b>colour temperature</b> in K (for example 4000 K for a neutral light).",
    f"Free <b>{ui('Note')}</b>, recorded in the stack's data.",
    "<b>Save profile</b>, in the <i>Unsaved changes</i> bar that appears at the top as soon as you change a value, with <b>Cancel</b> (back to the saved profile): overwrites the chosen profile; if it is a new one, asks for a name.",
    "The open <b>profile</b>; amber if there are unsaved changes.",
    "<b>Index</b> of the sections, with search: a click takes you to the section. With Microscope or Macro it shows only the sections of that type.",
    "<b>Summary</b>, always in view while you type: magnification on the sensor, scale on the sample (measured or calculated, with the deviation), depth of field and recommended step.",
], layout="full")}
<p>An empty field means “not specified” and is not written. If you choose no profile in the sequence, the stack is
recorded as taken <b>without a filter</b> and with no optical data. The same NA, magnification and pixel values are
also used by the depth-of-field calculator (chapter 11). Remember to change profile when you change objective or
filter: the sequence summary always shows what will be recorded.</p>

<h2>7.3 Photographic macro</h2>
<p>With the <span class="ui">{ui('Macro fotografica')}</span> type the profile describes a photographic lens instead of a
microscope objective. From it the app works out the magnification on the sensor, the effective aperture and an
equivalent NA, which are used for the scale in µm and for the depth of field exactly as on the microscope.</p>
{fig("ottica-macro", [
    f"<b>{ui('Macro fotografica')}</b>: shows the photographic lens fields instead of the microscope ones.",
    f"<b>{ui('Cerca nel database')}</b>: type part of the name (for example “90 macro”) and choose the lens. The database is that of <b>Lensfun</b> (1,162 lenses), plus a few dedicated macro lenses that Lensfun lacks (Canon MP-E 65, Laowa 25/90/100, OM 90) and your personal list.",
    f"<b>{ui('Marca')}</b> and <b>{ui('Modello')}</b>: filled in by the search, or typed by hand.",
    "<b>Focal length</b> and <b>widest aperture</b>. With a zoom, enter the focal length used.",
    f"<b>{ui('＋ Aggiungi al mio elenco')}</b>: saves a lens the database doesn't have, so you can find it again when searching.",
    "<b>Lens reproduction ratio</b>, read from its scale at the focus distance used: 1 = 1:1, 0.5 = 1:2, 0 = focused at infinity.",
    "<b>Aperture set</b> on the lens.",
    "<b>Extension tubes / bellows</b>: the total length added between lens and camera, in mm.",
    "<b>Close-up lenses</b> in front of the lens (Raynox and the like), up to 3, with their power in dioptres.",
    "<b>Result</b>: magnification on the sensor, effective aperture, equivalent NA and scale on the specimen in µm per pixel.",
], layout="full")}
<p>The calculations are the usual ones for close-up photographic optics, with <i>f</i> = focal length, <i>m₀</i> = lens
ratio, <i>e</i> = tubes in mm, <i>D</i> = dioptres of the close-up lenses and <i>N</i> = aperture set:</p>
<div class="formula">m₁ = m₀ + {frac("e", "f")} &nbsp;&nbsp;&nbsp; magnification m = m₁ + {frac("ΣD", "1000")} · f · (1 + m₁)
<span class="lbl">effective aperture = N · (1 + m₁) &nbsp;·&nbsp; equivalent NA = {frac("m", "2 · N · (1 + m₁)")}</span></div>
<div class="calc">Example: 90 mm macro lens at 1:2 (m₀ = 0.5), f/8, no tubes, +8 dioptre close-up lens
m₁ = 0.5 + 0 = 0.5
m  = 0.5 + 8 ÷ 1000 × 90 × (1 + 0.5) = 0.5 + 1.08 = <b>1.58×</b>
effective aperture = 8 × 1.5 = <b>f/12</b>      equivalent NA = 1.58 ÷ (2 × 8 × 1.5) = <b>0.066</b>
with a 3.9 µm sensor: 3.9 ÷ 1.58 = <b>2.47 µm per pixel</b> on the specimen</div>
<p>As on the microscope, a value measured with a millimetre ruler (field <span class="ui">{ui('µm per pixel sul campione, misurati')}</span>)
takes precedence over the calculation, which with close-up lenses is only an estimate. In macro the depth of field is
often tens or hundreds of µm: if one step of the rail turns out longer than the recommended step, the
{ui('Ottica')} tab says so and suggests a suitable microstep (chapter 10.2).</p>

<h2>7.4 Several shots per position</h2>
<p>With <span class="ui">{ui('Scatti per posizione')}</span> above 1 the camera shoots several times at each position,
without moving the motor in between: the settle time against vibrations applies only after a move, and between the
shots there is only the pause after the shot. The fusion software averages them: with 4 shots the noise is halved.
The files are named <code>stack_0001_1</code>, <code>stack_0001_2</code>…; with a single shot they stay
<code>stack_0001</code>, <code>stack_0002</code>… The summary shows positions × shots and the correct duration.</p>

<h2>7.5 The stack files</h2>
<p>In the stack folder, next to the photos, the app writes two files. It rewrites them after every shot, so they are
valid even if the sequence is aborted. The photos themselves are never modified.</p>
<ul>
<li><code>sequence.json</code>: all the data for the <b>fusion software</b>: position of every shot in steps and in µm,
  time, temperature, guide, camera, optics profile (microscope or macro), filter, illumination and the matching
  calibration sets (7.6). The format is described in <code>docs/sequence-json.md</code> on GitHub.</li>
<li><code>sequence.txt</code>: a <b>human-readable summary</b>, in the app's language. For example:</li>
</ul>
<div class="calc long">{SEQ_TXT}</div>

<h2>7.6 Calibration: exposure, darks and flats</h2>
<p>The <b>{ui('Calibrazione')}</b> tab prepares what the fusion software needs to correct the photos: a correct
shutter speed for the stack and the <b>calibration frames</b>. Levels are measured on the <b>real RAW files</b>, with
no colour conversion, by <i>fs-rawstat</i>, a small program bundled with the app and based on LibRaw; burnt-out pixels
are detected channel by channel. With the simulator the levels are only an estimate.</p>
<h3>{ui('Esposizione dei light')}</h3>
{fig("calibrazione-esposizione", [
    f"<b>{ui('Misura su')}</b>: <i>{ui('Luci (99,5° percentile)')}</i> (the 99.5th percentile, i.e. the brightest parts) or <i>{ui('Media (livello medio)')}</i>.",
    "<b>Target level</b> as a % of sensor saturation, for example 85% on the highlights.",
    f"<b>{ui('Calcola e imposta il tempo')}</b>: the app takes a few test shots, measures the RAWs and sets the shutter speed, preferring speeds with no burnt-out pixels. ISO and aperture stay as set.",
    "<b>Result</b>: chosen shutter speed, measured level and burnt-out pixels.",
], layout="side")}
<p>Bring the focuser to the middle of the stack and turn on the illumination as for the sequence. The exposure is
computed <b>once, before the stack</b>: changing it from one plane to the next would make the brightness of the frames
differ.</p>
<h3>{ui('Frame di calibrazione')}</h3>
{fig("calibrazione-frame", [
    f"<b>Type</b>: <i>{ui('Dark')}</i> (cap on the lens, same ISO and shutter speed as the lights: thermal noise and hot pixels), <i>{ui('Flat')}</i> (evenly lit field, same optics and aperture: vignetting and dust) or <i>{ui('Dark dei flat')}</i> (cap on, same ISO and shutter speed as the flats).",
    f"<b>{ui('Fotogrammi')}</b> to take, for example 16.",
    "<b>Flat level</b> as a % of saturation, for example 50%: the app finds the shutter speed.",
    "<b>Progress</b>: frames taken and measured level.",
    f"<b>{ui('▶ Scatta i frame')}</b> and <b>{ui('Interrompi')}</b>.",
], layout="side")}
<ul>
<li><b>{ui('Dark')}</b>: cap on the lens and viewfinder eyepiece covered, same ISO and shutter speed (or bulb time) as the
  lights, ideally at the same temperature.</li>
<li><b>{ui('Flat')}</b>: evenly lit field (an empty slide, a diffuser), with the same optics profile and the same
  aperture as the stack: they correct vignetting and dust only if the optics are the same.</li>
<li><b>{ui('Dark dei flat')}</b>: right after the flats, with the cap on: the app uses the ISO and shutter speed of the
  most recent flats by itself.</li>
</ul>
<h3>How fusion uses them</h3>
<p>Focus Stack shoots the frames and lists them in the stack's <code>sequence.json</code>; the correction is done by the
fusion software (for example Focus Fusion) on every frame, before aligning it. The dark is <b>subtracted</b>: it removes
thermal noise and hot pixels. The flat <b>divides</b>: it gives back the light that vignetting and dust shadows had
taken away.</p>
{calib_diagram(CALIB_LABELS)}
{fig("calibrazione-esempio", [
    '<b>Normalised flat</b> F, with boosted contrast: the corners get 70% of the light of the centre, and every dot is a speck of dust on the sensor.',
    '<b>One frame of the stack</b> as it is: the background darkens towards the corners (64% of the centre) and the same dust spot shows on the background (box enlarged 4×).',
    '<b>The same frame corrected</b>, (I − D) ÷ F, with the same rendering: corners at 94% of the centre and the spot gone.',
], layout="full", caption='A pencil: Sony A6400 with the 70-350 mm at 350 mm, +8 dioptre close-up lens, f/20, ISO 400, 1/20 s; 10 flats, 10 darks and 10 flat darks.')}
<h3>The {ui('Libreria di calibrazione').lower()}</h3>
{fig("calibrazione-libreria", [
    f"Library <b>folder</b>: <code>_calibrazione</code> inside the stacks folder. <span class='ui'>{ui('Apri nel Finder')}</span> shows it.",
    "<b>Matching sets</b> for a stack started now, with the current camera and settings.",
    "<b>Table of sets</b>: type, date, camera, ISO, shutter speed, optics profile, frames, mean level and temperature. <span class='ui'>Delete</span> moves the set to the Mac's Trash (recoverable from the Finder). With the boxes in front of the type you can pick several (the one in the header selects them all) and delete them together with <span class='ui'>Delete selected</span>: to be safe, you have to type the word DELETE.",
], layout="full")}
<p>Each set has its own folder with the frames and a <code>calibration.json</code> (format in
<code>docs/calibration-json.md</code>). When a stack starts, <code>sequence.json</code> lists the most recent matching
sets: for darks the same camera, ISO and shutter speed; for flats the same optics profile as well. The frames are not
copied. It is the same library used by <b>Focus Fusion</b>, which saves its “masters” next to them.</p>

<p>On the right, the <b>summary</b> stays in view while you work in the tab.</p>
{fig("calibrazione-riepilogo", [
    "<b>For the next stack</b>: for darks, flats and flat darks, ✓ with the date of the set that would be used, or <i>missing</i> in orange. If a set is missing, an orange dot also appears next to <i>Library</i> in the index.",
    "Current probe <b>temperature</b>.",
    "The <b>last 60 minutes</b>: compare it with the temperature of the darks in the table.",
    f"<b>{ui('Sensore')}</b>: expected dynamic range at the current ISO, with the chart (recommended ISO values in green, the current one circled). It appears after the sensor analysis.",
], layout="side narrow")}

<h3>{ui('Analisi del sensore')}</h3>
<p>Once per camera, <b>{ui('Calibrazione')} › {ui('Sensore')} › {ui('Analisi del sensore')}</b> measures how the sensor
behaves at every ISO: <b>gain</b> (how many electrons one RAW unit is worth), <b>read noise</b>, <b>full well</b> (how
much light a pixel collects before it saturates) and <b>dynamic range</b> in stops. For 19 ISO values it takes about
20 minutes.</p>
<ol>
<li><b>{ui('Prepara')}</b>: the lit diffuser in front of the lens, as for flats; camera in RAW and manual focus. Choose the
  ISO range (100 to 6400 in thirds of a stop is a good start) and the shots per ISO (2 are enough).</li>
<li><b>Flat</b>: for each ISO the app finds the exposure for a 50% flat and shoots. ISO values the camera refuses are struck through.</li>
<li><b>{ui('Tappo')}</b>: the app stops and asks you to put the cap on; then press <i>{ui('Ho messo il tappo: scatta i dark')}</i>.</li>
<li><b>Dark</b>: same ISO values and exposures, in the dark.</li>
<li><b>{ui('Risultato')}</b>: two charts, dynamic range and read noise per ISO, and the recommended ISO values.</li>
</ol>
{fig("calibrazione-sensore", [
    "The procedure's <b>steps</b>: the current one in blue, the finished ones ticked.",
    '<b>Charts</b> of dynamic range and read noise per ISO: recommended ISO values in green, the ISO set on the camera circled, grey band and dashed line for ISO values that are not reliable.',
    '<b>Recommended</b>, <b>Recommended in low light</b> and <b>Best avoided</b>, each with the reason.',
    "<b>Table</b>: for each ISO the flats' exposure, the range, the noise, the full well and the gain.",
    '<b>Export CSV</b> saves the table in Downloads; <b>Redo the analysis</b> starts again from the preparation.',
], layout="full")}
<figure class="shot">{sensor_chart(SENSOR_LABELS)}<figcaption>Sensor analysis of a Sony A6400: 19 ISO values from 100 to 102400, 2 flats and 2 darks each. ISO 400 circled.</figcaption></figure>
<p>How to read it, with a Sony A6400 as the example. ISO 100 has the widest range, 13.3 stops, because it collects the most
light. At ISO 400 the sensor switches to a second gain and read noise drops from 3 to 1.2 electrons: 12.9 stops with
exposures four times shorter. Above that, noise no longer falls and every doubling of ISO costs one stop: if light is
short, stay at 400 and brighten later. ISO 160 to 320 give less range than ISO 400 with longer exposures: best avoided.
Above 3200 the camera already filters noise in the RAW, and those values are marked as not reliable.</p>
<p>The result is saved as the camera's <b>sensor profile</b>, in <code>_calibrazione/_sensore</code>. The Calibration
summary and the sequence summary (once its details are opened) show the expected dynamic range at the current ISO, with the point on the chart; every
stack writes the values for its ISO into its <code>sequence.json</code> (<code>"sensor"</code>), which Focus Fusion can use.
The analysis frames live in the same folder, outside the library of sets, and are never chosen for a stack. Redo the
analysis if you change camera or update its firmware.</p>

<h2>7.7 {ui('Avanzamento da smartphone')}</h2>
<p>To follow a long stack away from the Mac, turn on a <b>read-only</b> page on the local network in
<span class="ui">{ui('Configurazione')} › {ui('Avanzamento da smartphone')}</span>.</p>
{fig("smartphone", [
    "<b>" + ui("Mostra l'avanzamento sulla rete locale") + "</b>: turns the page on (it stays off until you enable it).",
    "<b>QR code</b>: scan it with the smartphone's camera; the phone must be on the same Wi-Fi network as the Mac.",
    f"<b>{ui('Nuovo link')}</b>: changes the link's code; the old one stops working.",
], layout="side")}
{fig("smartphone-pagina", [
    "Stack name, status, shots taken, time left and expected end time.",
    f"<b>{ui('Avvisami con un suono a fine sequenza')}</b>: the smartphone plays a sound (and vibrates on Android) when the stack finishes, stops because of an error or pauses by itself; while the sound is on the screen stays on.",
    "<b>Show / Refresh the last shot</b>: the latest photo, full width.",
    f"The latest shot: pinch, drag or double-tap to zoom. Zooming in loads a high-resolution detail; the zoom is kept when the next shot arrives, to compare the same area. <span class='ui'>{ui('Adatta')}</span> goes back to the whole image.",
], layout="side narrow", width="70%")}
<p>Nothing <b>can be controlled</b> from the page, and without the link's code nothing can be seen. The first time,
macOS asks whether to allow incoming connections: answer <b>Allow</b>. For the sound, keep the page open in the
foreground: while the sound is on, the page keeps the screen on. If the phone locks anyway, set auto-lock to
<b>Never</b> while you wait (iPhone: Settings › Display &amp; Brightness › Auto-Lock): a locked phone suspends web pages
and the sound does not arrive.</p>
""")

# 8
add(f"""
<h1><span class="n">8</span>The viewer</h1>
<p>Open it with <span class="ui">{ui('Apri visualizzatore ↗')}</span> or by clicking the latest shot. It is a separate
window: with two monitors it opens full screen on the other one by itself (you can turn this off in
<span class="ui">{ui('Configurazione')} › {ui('Visualizzatore')}</span>). It shows the photos at full resolution (RAW files too, converted on the
fly) with zoom and pan, and the camera's live view.</p>
{fig("visualizzatore", [
    "<b>◀ ▶</b> previous and next shot (arrow keys <kbd>←</kbd> <kbd>→</kbd>).",
    "<b>Stack counter</b>: during the sequence the last shot taken out of the total (for example 75/115, <i>running</i>), then <i>completed</i>; with test shots, how many there are. Next to it the file name and, below, shot number, position, temperature and time. During the stack a blue line along the top edge of the window shows the progress.",
    "<b>● Live</b> (<kbd>L</kbd>): live view in the same window, with zoom and pan.",
    "<b>Zoom</b> − and + (<kbd>−</kbd> <kbd>+</kbd>) and the zoom level.",
    f"<b>{ui('Adatta')}</b> (<kbd>0</kbd>), <b>100%</b> (<kbd>1</kbd>: one sensor pixel = one screen pixel), <b>{ui('Reset')}</b> (<kbd>R</kbd>).",
    f"<b>{ui('Segui ultimo')}</b> (<kbd>U</kbd>): shows every new shot automatically. Like the next two buttons it is an icon, highlighted when on; it is on when the viewer opens.",
    f"<b>{ui('Blocca vista')}</b> (<kbd>K</kbd>): keeps zoom and position when you change shot, to compare focus at the same spot. On when the viewer opens.",
    "<b>Composition guides</b> (<kbd>G</kbd>): each click switches between thirds, a cross at the centre, thirds and centre, none. 1-pixel lines that follow zoom and panning; they also work in live view.",
    f"<b>{ui('Ispettore')}</b> (<kbd>I</kbd>): histograms, burnt-out and black pixels, values under the pointer (see below). Open when the viewer opens.",
    "<b>Full screen</b> (<kbd>F</kbd>).",
    "<b>?</b>: this guide, at the viewer chapter.",
    "<b>Thumbnails</b>: click to open a shot. <i>P</i> = test shot, <i>C</i> = calibration frame, <i>E</i> = exposure photo, <i>AF</i> = autofocus shots, numbers are the sequence shots. The strip shows only the current or last sequence: it empties when a sequence starts, and the first test shot taken afterwards starts a new one. The files stay in the folder.",
    f"<b>{ui('Svuota')}</b>, at the bottom right of the thumbnail strip when there are shots: starts over. The shots leave the viewer and the sequence goes back to Ready; the files stay in the folder.",
], layout="full", anchors={n: "bb" if n in (7, 9, 11) else "b" for n in range(1, 12)})}
<p>With the mouse: drag to pan, scroll wheel (or pinch on the trackpad) to zoom around the pointer, double-click to
switch between “fit” and 100%. Above 150% the pixels stay crisp, without blurring.</p>
{fig("visualizzatore-live", [
    f"<b>{ui('■ Ferma live')}</b> goes back to the photos; ◀ ▶ or clicking a thumbnail also leaves live view.",
    "Live status: LIVE, SHOOTING…, PAUSED during the sequence.",
], layout="full", anchors={1: "b"}, caption="Live view in the viewer, here with the simulator in focus (the checkerboard is sharp). At 100% the live view has the resolution of the camera's preview, lower than that of the photos.")}
<h2>Autofocus on a point</h2>
<p>The autofocus finds by itself the focuser position where a chosen detail is sharpest: a marker, a hair, the edge of
a structure. It is useful, for example, to set the start or the end of the stack precisely.</p>
<ol class="steps">
<li>Press <span class="ui">⌖ Autofocus</span> (<kbd>A</kbd> key) and click the detail: a blue square appears, the
  measured area. Change its side with the <b>Area</b> slider or with <kbd>[</kbd> <kbd>]</kbd>; another click moves the
  square. Dragging and zoom work as usual.</li>
<li>Choose the <b>mode</b> (Fast, Precise or Real shots) and check the <b>travel</b>: the bar and the line below show
  how far the focuser will move and how close it will get to the specimen. Then press <span class="ui">Start</span>: the
  focuser moves in the same direction as the stack and the sharpness curve grows one point at a time.</li>
<li>At the end the focuser goes back to the sharpest position: it first goes past it by the <b>overshoot</b> and
  arrives in the same direction as the scan, so the backlash of the mechanics does not shift the focus. Then it takes a
  <b>check shot</b>, the green diamond on the chart. In the row below, <span class="ui">Use the focus as</span>
  <span class="ui">stack start</span> or <span class="ui">stack end</span> writes the position into the sequence, in the main window.</li>
</ol>
{fig("visualizzatore-autofocus", [
    "<b>⌖ Autofocus</b> (<kbd>A</kbd>): opens the panel; clicking the image chooses the area. <kbd>Esc</kbd> closes it.",
    "<b>Measured area</b>: dashed while the autofocus runs. It stays on the same spot when you change shot or switch to live view.",
    "<b>Mode</b>: <i>Fast</i>, <i>Precise</i> (default) or <i>Real shots</i>; below, what it will do. <b>Wide search</b> turns it on for when the whole image is blurred. <b>Area</b>: side of the square in sensor pixels. The <b>travel bar</b> runs from − to + the maximum excursion around the start: in light colour the planned travel, darker the path already covered, the line is the current position.",
    "<b>Sharpness curve</b>: one point per measurement, the focuser position across; below, the step. Earlier passes stay fainter under the current one, and the chart zooms in on the area of the fine pass. The orange squares are the real confirmation shots, the green line the chosen position, the green diamond the check shot. Hover over a point to read its position and sharpness (in % of the maximum).",
    "<b>Status</b>: pass, current shot and position, then the result with the check and the peak width, or the reason why no focus was found.",
    "<b>Run again</b> and, below, <b>Use the focus as stack start / stack end</b>, as long as the focuser stays on the position found. <b>Run again</b> repeats the autofocus; clicking another point moves the area without closing the panel. While measuring there is <b>Stop</b>.",
], layout="full", anchors={6: "r"})}
<p>At every shot the app measures how sharp the edges inside the area are (the brightness gradient, divided by the
mean brightness, so the exposure does not count). Far from focus the curve is flat; close to it, it rises into a narrow
peak. The app fits a curve to the points around the maximum, so the position found can also fall between two shots.
The pass stops by itself as soon as the peak is passed; if the peak lies beyond the last shot it goes on, if it lies
before the first it restarts further back. With RAW files it measures the JPEG preview inside the file: in tests on
real stacks it gives the same focus as the developed RAW.</p>
<div class="box tip"><span class="t">Choosing the area</span>A contrasty detail, all at the same depth. If the area holds
two things at different focus (the leg and the body of an insect) the curve has two peaks and the app says so in
orange: make the area smaller, on the detail you care about. On a uniform background there is nothing to measure and
the autofocus stops with a message.</div>
<h3>The modes</h3>
<p><b>Live view</b> is faster, but its frame is small and compressed, and noisy in low light; <b>real shots</b> measure
the photo as it will be in the stack, but take a few seconds each. The modes combine the two:</p>
<ul>
<li><b>Fast</b>: live view only, one pass. For finding the focus and for trials.</li>
<li><b>Precise</b> (default): two live view passes, then <b>3 real confirmation shots</b> around the focus found. The
  focus is recalculated on these shots (if the sharpest is at the edge, one or two more are added) and the check shot is
  a real shot too. This is the mode for setting the start or end of a stack.</li>
<li><b>Real shots</b>: the whole scan with real shots. The most certain and the slowest.</li>
</ul>
<p>Each mode remembers its own settings (step, shots per pass, passes, images, confirmation shots), which you change
in <span class="ui">Configuration › Autofocus</span>.</p>
<p>With real shots (<i>Precise</i> and <i>Real shots</i>) live view turns off before the first shot, as for a
test shot, and stays off until the autofocus ends: the camera does not keep switching between live view and shooting.
It restarts by itself when you move the focuser. If the camera disconnects during a shot, the app retries and
reconnects it; if disconnections keep happening, check the power supply: a dummy battery that cannot handle the peak
of the shot drops the camera from USB.</p>
<div class="box warn"><span class="t">Maximum excursion: it protects the subject</span>The autofocus never moves further
from the starting position than the <b>maximum excursion</b> (± steps, in the travel bar). If the pass would have to
extend beyond it, because the focus is further than expected, it stops and says so instead of carrying on towards the
specimen. The calculated value covers the planned travel with a margin; lower it if the specimen is close to the
objective.</div>
<div class="box warn"><span class="t">Low check: backlash</span>If the check shot is much less sharp than the peak of the
curve (below 80 %), the app says so in orange: usually the backlash of the mechanics is larger than the overshoot.
Increase it in <span class="ui">Configuration › Autofocus</span>; it starts from the sequence's backlash compensation,
but at least one peak width.</div>
<p>All the values are in <span class="ui">Configuration › Autofocus</span>, chapter 12.</p>
<h2>{ui('Ispettore')}</h2>
<p>The <span class="ui">{ui('Ispettore')}</span> panel (<kbd>I</kbd> key) checks the exposure of a photo with the same
rules as Focus Fusion. It is read-only: it does not modify the photos. It also works on live view, updated every half
second.</p>
{fig("ispettore", [
    "<b>" + ui("Bruciati e neri") + "</b> pixels: percentage and rules used. <span class='ui'>" + ui("Evidenzia sull'immagine") + "</span> marks burnt-out pixels in red and black ones in blue; the two buttons show or hide them separately.",
    "<b>Histograms</b> of red, green, blue and luminance. With the pointer over a level you can read how many pixels it has.",
    f"<b>{ui('Sotto il puntatore:').rstrip(':')}</b>: the R, G, B values and the luminance of the pixel under the mouse.",
], layout="full")}
<p>With RAW photos the {ui('Ispettore')} works on the converted preview; for the exact sensor level use
<span class="ui">{ui('Esposizione dei light')}</span> (7.6), which measures the real RAW files.</p>
""")

# 9
add(f"""
<h1><span class="n">9</span>Safety limits</h1>
<p class="lead">The limits stop the objective from touching the slide and the mechanics from hitting their end
stops. Set them first, calmly.</p>
<p>The <b>Settings</b> tab is a single page, divided into the groups Focuser, App and System. The Optics and
Calibration tabs are built the same way.</p>
{fig("configurazione", [
    "<b>Search</b>: type part of a name (for example “backlash”) and only the rows that contain it remain.",
    "<b>Index</b>: a click takes you to the section; the highlighted entry follows the scrolling. A dot marks unsaved changes or an available update.",
    "<b>Section title</b>; the <b>?</b> opens the guide at that point.",
    "<b>Details</b>: the longer explanations, closed at first.",
    "<b>Summary</b>, always in view: resolution, usable travel, firmware, app version and smartphone progress.",
], layout="full")}
<p>Almost everything is saved as soon as you change a value: the motor settings go straight to the firmware, the
mechanics and the other options to the app's settings. The limits, below, are the exception.</p>
{fig("fine-corsa", [
    f"<b>{ui('Fine corsa inferiore')}</b> in steps; <span class='ui'>⌖ {ui('Usa posizione attuale')}</span> takes it from the focuser's position.",
    f"<b>{ui('Fine corsa superiore')}</b>. Empty = the firmware maximum.",
    f"<b>Towards the specimen</b>: whether the step count goes down or up as you approach the specimen. It is used to label {ui('Avvicina')}/{ui('Allontana')} correctly.",
    "<b>Save limits</b>, in the <i>Unsaved changes</i> bar that appears when you change a value; <b>Cancel</b> goes back to the saved values. It is the only part of the Settings that is not saved automatically.",
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
<li>Bring the stage to the farthest useful position, click <span class="ui">⌖ {ui('Usa posizione attuale')}</span>
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
    "<b>Result</b>: µm per step, steps per µm, µm per 1000 steps. Changes are saved automatically.",
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
<p>The calculator is at the bottom of the <b>{ui('Ottica')}</b> tab, in the <b>Tools</b> group (the result also appears in the summary on the right), and uses the numerical aperture, the magnification on
the sensor (objective × intermediate changer × adapter) and the sensor pixel of the open profile (chapter 7.2).</p>
{fig("profondita", [
    "<b>Overlap</b> between one sharp layer and the next; 20–30% is a good value.",
    "<b>Result</b>: depth of field, recommended step in µm and in motor steps.",
    f"<b>{ui('Usa come passo della sequenza')}</b>: copies the value in steps into the sequence's Step field.",
], layout="side narrow")}
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
<div class="box tip"><span class="t">Optovar, adapters and projection eyepieces</span>In the optics profile (chapter 7.2)
enter the factor of the intermediate magnification changer and that of the camera adapter or projection eyepiece: the
app multiplies them by the objective magnification. For example 10× with an Optovar 1.6× and a 0.63× adapter =
10 × 1.6 × 0.63 ≈ 10.1× on the sensor. Only the second term of the formula changes, and it matters most with low-power
objectives. For an exact scale in µm, measure the µm per pixel with a stage micrometer: the factors marked on the
accessories are nominal.</div>

<h2>11.2 Start, end and number of shots</h2>
<ol class="steps">
<li>Turn on live view (preferably in the viewer, zoomed in) and bring the focus <b>just above</b> the highest part
  of the subject you want sharp: click <span class="ui">⌖ {ui('qui')}</span> next to <b>{ui('Inizio')}</b>.</li>
<li>Go down to <b>just below</b> the lowest part and click <span class="ui">⌖ {ui('qui')}</span> next to <b>{ui('Fine')}</b>.</li>
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
<h1><span class="n">12</span>Motor, manual controls, autofocus, updates, temperature</h1>
<h2>{ui('Motore (firmware)')}</h2>
{fig("motore", [
    "<b>Microstep</b>: full step, 1/2 … 1/32 (see 10.2). Changing it changes the scale of the positions: check the limits again afterwards.",
    "Firmware <b>speed</b>: slow, medium, fast. With the myFocuserPro2 and firmware build 7 the maximum speed of moves is 80, 200 and 400 steps per second; every move starts at 40 steps per second and accelerates.",
    f"<b>{ui('Alimentazione bobine motore')}</b>: with <b>{ui('Sempre quando connesso')}</b> the motor holds its position when idle, but runs warm. <b>{ui(COIL_HOLD)}</b> (off at first; only with the first one on): if you leave it off, the coils switch off when you disconnect the focuser or quit the app, so the motor doesn't stay warm for hours; the first move switches them back on. Turn it on if the weight can make a vertical slide sink. Needs firmware build 8.",
    f"<b>{ui('Alimentale comunque durante la sequenza')}</b> (appears when the coils are off; on by default): the coils are powered when the stack starts and turned off again after the return to the start.",
    f"<b>{ui('Inverti verso di rotazione')}</b>.",
    "<b>Compensate backlash IN / OUT</b>: at every reversal towards lower (IN) or higher (OUT) positions the firmware adds extra steps without counting them, physical buttons included.",
    "<b>Backlash IN / OUT</b> in steps, 0 to 255 (see 10.5).",
    f"<b>{ui('Rileggi')}</b> the values from the firmware.",
])}
<div class="box warn"><span class="t">Coils off: the stage may not advance</span>With no current when idle, at every
stop the load can pull the stage back, and with microstepping the motor also falls back to the nearest full step: the
counter advances but the stage doesn't. That is why, with the coils off, the app turns them on during the sequence
(number 4) and an orange warning reminds you if you untick the option. If the motor runs too hot, lower the current on
the driver instead of turning the coils off.</div>
<h2>{ui('Comandi manuali')}</h2>
{fig("comandi-manuali", [
    f"<b>Step sizes</b> of the {ui('Allontana')}/{ui('Avvicina')} buttons: in powers of ten up to 1,000, 10,000 or 100,000 steps. A gearbox needs large step sizes.",
    f"<b>{ui('Tieni premuto per muovere senza fermarti')}</b>: on release the motor slows down and stops; it stops anyway at the limit and, if the page stops responding, after about a second.",
    f"<b>{ui('Tratto massimo per comando (passi)').replace(' (steps)', '')}</b>: while you hold the button, the motor never goes more than one segment (500 steps by default) beyond the page's last confirmation that the button is still held down.",
], layout="side")}
<p>Continuous movement works this way for safety: if communication breaks off (network, frozen app, cable) the motor
travels at most one segment. With <b>firmware build 5</b> each confirmation moves the target one segment further and the
motor never stops; with older firmware it advances one segment at a time, with a short pause between one segment and the
next (short segments are safer but jerkier). From <b>build 4</b> there is extra protection: during continuous movement
the focuser stops by itself if it receives no commands from the Mac for 1.5 s. <span class="ui">{ui('Vai')}</span>, single-click buttons and the sequence, on the other hand,
always reach their destination, even if the move takes many seconds.</p>
<h2>Autofocus</h2>
<p>Settings of the autofocus on a point (chapter 8): first the mode and its settings, then those shared by all
modes. Empty fields use the default value, shown in grey inside the field; steps and shots are calculated from the
<b>peak width</b>, the range of steps over which sharpness stays above half its maximum.</p>
{fig("autofocus-config", [
    "<b>Mode</b> used by the viewer, with a summary of what it does. It can also be chosen in the panel.",
    "<b>Mode settings</b>: images (live view or real shots), step and shots of the fine pass, passes. Empty = the mode's default or calculated from the peak width. <b>Restore the mode</b> goes back to the initial values.",
    "<b>Confirm with real shots</b> (live view only): how many real shots around the focus found; 0 = no confirmation.",
    "<b>Wide search</b> if the whole image is blurred, with its range (± steps) and step, one peak width: a few widely spaced shots.",
    "<b>Maximum excursion ±</b> from the starting position: beyond it, the autofocus stops. Below, settle time after moving and <b>backlash overshoot</b>.",
    "<b>Peak width</b> used for the calculations and where it comes from. <b>Forget the measurement</b> goes back to the estimate.",
], layout="side", anchors={2: "r", 4: "r"})}
<p>The first time, the peak width is estimated from the depth of field of the optics profile chosen in the sequence and
from the mechanics (µm per step); without a profile, from the travel between the limits. After each successful
autofocus the app saves the measured width for that profile and uses it from then on. The first estimate is rough: if
the peak is wider than expected the pass extends by itself, if it is narrower it repeats the measurement with a finer
step. The <b>backlash overshoot</b> is how far the focuser goes past a position before returning to it: it must exceed
the backlash of the mechanics. <span class="ui">Restore calculated values</span> clears the shared fields typed by
hand. If the wide search is off and the focus is far away, the autofocus stops and suggests turning it on.</p>
<h2>{ui('Aggiornamenti')}</h2>
{fig("aggiornamenti", [
    "<b>App</b> version and the result of the last check.",
    "<b>Firmware</b> version on the focuser.",
    f"<b>{ui('Aggiorna firmware')}</b>: about 20 seconds; the focuser's settings are kept. Don't unplug the cable; if something goes wrong, just repeat it. Build 5 makes the movement continuous while the button is held down; from build 4 there is the automatic stop if the Mac stops communicating. Build 7 starts moves more gently (40 steps per second) and halves the slow speed of the myFocuserPro2.",
    f"<b>{ui('Controlla ora')}</b> for app updates.",
], layout="side")}
<p>The app picks the right firmware for the board by itself (myFocuserPro2 or Ardufocus). The <b>Ardufocus</b> does
not restart over the USB cable: during the update the app asks you to press the board's <b>reset button</b>.</p>
<p>The board saves position and settings to its permanent memory only about ten seconds after the last move. So as
not to lose the position, the app has it saved immediately whenever it closes the connection ({ui('Disconnetti')},
quitting the app, update).</p>
<h2>{ui('Temperatura')}</h2>
<p>The current probe temperature is in the top bar. The graph of the last 60 minutes is in the summary of the
<b>Calibration</b> tab (chapter 7.6), next to the darks. The temperature of every shot is saved in
<code>sequence.json</code> and summarised in <code>sequence.txt</code>: useful because focus drifts with thermal
expansion.</p>
""")

# 13
add(f"""
<h1><span class="n">13</span>A typical session, step by step</h1>
<h2>Once (or whenever the mechanics change)</h2>
<ol class="steps">
<li><b>Mechanics</b>: enter the data and check the resolution with a measurement (chapter 10).</li>
<li><b>Specimen direction</b> and <b>limits</b>, with the limits written to the firmware (chapter 9).</li>
<li><b>Backlash</b>: measure it with live view and choose where to compensate it (sequence or firmware).</li>
<li><b>Motor</b>: check the coils (chapter 12) and, if the app offers it, update the firmware.</li>
<li><b>Optics profiles</b>: in the {ui('Ottica')} tab, save a profile for each combination of objective, filter and
  illumination, on the microscope or in macro (chapters 7.2 and 7.3).</li>
<li><b>Presets</b>: for each objective, work out the step from the depth of field and save a preset; the preset
  also remembers the optics profile.</li>
</ol>
<h2>Every session</h2>
<ol class="steps">
<li>Switch on the focuser and the camera (mode M), plug in the cables and open Focus Stack.</li>
<li>The focuser and the camera connect by themselves; if they don't, press <b>{ui('Connetti')}</b> in the {ui('Sessione')} tab.</li>
<li>Set shutter speed, ISO and format; take a <b>test shot</b> and check it in the viewer at 100%.</li>
<li>Choose the objective's <b>preset</b> (or the step) and check the <b>optics profile</b> in the sequence.</li>
<li>Using <b>live view</b> and the keyboard, find the <b>end</b> and the <b>start</b> of the sequence and click ⌖ {ui('qui')}.</li>
<li>If you need them, prepare the <b>darks</b> and <b>flats</b> and compute the light exposure (chapter 7.6).</li>
<li>Check the summary: number of shots, travel, duration, no red warning.</li>
<li><b>{ui('▶ Avvia sequenza')}</b>. Don't touch the microscope: vibrations spoil the shots. To follow it from a
  distance, use smartphone progress (chapter 7.7).</li>
<li>When the sequence ends, click <b>{ui('Apri nel Finder')}</b> and open the folder in the fusion software.</li>
</ol>
""")

# 14
add(f"""<h1><span class="n">14</span>Troubleshooting</h1>
<p>The <b>{ui('Registro')}</b> (the last tab) lists every connection, move, shot and error with its time: when something
goes wrong, read it first. At the top you can search for words and show only warnings (⚠) and errors (✖). If you
report a problem, press <b>{ui('Esporta')}</b>: the log is saved as a text file in the Downloads folder, with the app
and firmware versions and the focuser and camera details, without the key of the smartphone link or your user name.
Attach that file to your report.</p>
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
    ["The whole stack is on the same plane: the stage doesn't advance", f"The motor coils are off and the load pulls the stage back at every stop (chapter 12): leave <i>{ui('Alimentale comunque durante la sequenza')}</i> on. Try a small move while watching live view."],
    ["The sequence paused by itself", f"The shot failed even after reconnecting the camera. Read the message, check battery, cable and card, then click <i>{ui('Riprendi')}</i>: the shot is repeated from the same position."],
    ["The camera disappears halfway through the stack", "Usually the Mac went to sleep and suspended USB. During the sequence the app prevents this, but not if you close the lid of a laptop without an external monitor. Also check the camera battery."],
    ["The smartphone won't open the progress page", f"The phone must be on the same Wi-Fi network as the Mac; the first time, macOS asks to allow incoming connections (answer Allow). After <i>{ui('Nuovo link')}</i> the old code no longer works."],
]))

# 15
add(f"""<h1><span class="n">15</span>Keyboard shortcuts</h1>
<div class="two">
<div class="keep"><h2 style="margin-top:0">{ui('Sessione')} tab</h2>
<table><tbody>
<tr><td><kbd>↑</kbd></td><td>move the objective away from the specimen</td></tr>
<tr><td><kbd>↓</kbd></td><td>move the objective closer to the specimen</td></tr>
<tr><td><kbd>↑</kbd>/<kbd>↓</kbd> held down</td><td>continuous movement until release</td></tr>
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
<tr><td><kbd>I</kbd></td><td>{ui('Ispettore')}</td></tr>
<tr><td><kbd>G</kbd></td><td>composition guides</td></tr>
<tr><td><kbd>A</kbd></td><td>autofocus: opens the panel, then click the detail</td></tr>
<tr><td><kbd>[</kbd> <kbd>]</kbd></td><td>smaller / larger autofocus area</td></tr>
<tr><td><kbd>Esc</kbd></td><td>closes the autofocus</td></tr>
<tr><td><kbd>F</kbd></td><td>full screen</td></tr>
</tbody></table></div>
</div>
<p style="margin-top:8mm;color:#5a6b80;font-size:9pt">Focus Stack is free software (MIT licence) ·
github.com/teoteo/focus-stack · The firmware is derived from myFocuserPro2 by Robert Brown (MIT licence).</p>
""")
