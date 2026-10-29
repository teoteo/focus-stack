"""Deutscher Text der Anleitung. Kein Modul zum Importieren: genera_guida.py führt ihn mit exec() in einem
Namensraum aus, der die gemeinsamen Helfer und Zahlen bereits enthält (fig, frac, table, num, diagram, VERSION,
ICON, IMG, UA, UB, GEAR17, um_step, dof, OBJ, APP). Der Text füllt die Liste H mit den HTML-Abschnitten.
"""
# ruff: noqa: F821  (die Namen kommen aus genera_guida.py)

META = {
    "lang": "de",
    "title": "Focus Stack — Bedienungsanleitung",
    "footer": "Bedienungsanleitung",
    "pdf": "Focus Stack Anleitung.pdf",
}


def ui(s):
    """Deutscher Name eines App-Befehls: genau die Beschriftung der App (der italienische Text ist der Schlüssel)."""
    return APP.get(s, s)


DIAGRAM_LABELS = {
    "motor": "Motor", "gearbox": "Getriebe", "pulleys": "Riemen / Zahnräder", "knob": "Feintrieb", "stage": "Objekttisch",
    "motor1": "Schritte/Umdr.", "motor2": "× Mikroschritt",
    "gearbox1": "(falls vorhanden)", "gearbox2": "z. B. 26,85 : 1",
    "pulleys1": "Zähne Abtrieb", "pulleys2": "÷ Zähne Antrieb",
    "knob1": "µm pro Umdrehung", "knob2": "des Knopfes",
    "stage1": "bewegt sich", "stage2": "in µm",
    "ratio": "Gesamtuntersetzung = Getriebe × Riemen",
    "steps": "Motorschritte pro Knopfumdrehung = Schritte/Umdr. × Mikroschritt × Untersetzung",
}

# Tabelle der Schärfentiefe (Objektivnamen in der Sprache der Anleitung)
OBJ_NAMES = ["4× / 0,10", "10× / 0,25", "20× / 0,40", "40× / 0,65", "60× / 0,85", "100× / 1,25 Öl"]
dof_rows = []
for name, (mag, na) in zip(OBJ_NAMES, OBJ):
    d = dof(na, mag, 3.9)
    s = d * 0.7
    dof_rows.append([name, num(d), num(s), str(max(1, round(s / UA))), str(max(1, round(s / UB)))])
dof_note = ("Bei Ölimmersionsobjektiven unterschätzt die Formel der App (Brechzahl n = 1, Luft) die Schärfentiefe; "
            "die berechnete Schrittweite liegt also auf der sicheren Seite.")

H = []
add = H.append

add(f"""
<section class="cover">
  <div class="icon">{ICON}</div>
  <h1 class="title">Focus Stack</h1>
  <div class="sub">Bedienungsanleitung<br>Motorisierter Fokussierer und Kamera für Focus-Stacking am Mikroskop</div>
  <div class="shot-c"><img src="{IMG}/sessione.png" alt=""></div>
  <div class="meta"><span>App-Version {VERSION}</span><span>Oktober 2026</span></div>
</section>
""")

add("""
<h1 style="break-before:auto">Inhalt</h1>
<div class="toc"><ol>
<li><span>1</span>Was ist Focus Stack?<em>Funktionsweise, was Sie brauchen</em></li>
<li><span>2</span>Installation, Start und Updates</li>
<li><span>3</span>Die Oberfläche im Überblick<em>die drei Bereiche und die obere Leiste</em></li>
<li><span>4</span>Fokussierer und Kamera verbinden<em>Einstellungen der Nikon D5600 und anderer Kameras</em></li>
<li><span>5</span>Der Fokussierer: Position, Bewegungen, STOP</li>
<li><span>6</span>Kamera, Testaufnahme und Live-View</li>
<li><span>7</span>Die Stacking-Serie</li>
<li><span>8</span>Der Betrachter</li>
<li><span>9</span>Sicherheitsgrenzen</li>
<li><span>10</span>Mechanik einrichten: die Berechnungen<em>Auflösung in µm pro Schritt, Kontrollmessung, Verfahrweg, Geschwindigkeit, Spiel</em></li>
<li><span>11</span>Die Schrittweite der Serie wählen<em>Schärfentiefe, Anzahl der Aufnahmen, Dauer</em></li>
<li><span>12</span>Motor, manuelle Steuerung, Updates, Temperatur</li>
<li><span>13</span>Eine typische Sitzung, Schritt für Schritt</li>
<li><span>14</span>Wenn etwas nicht funktioniert</li>
<li><span>15</span>Tastaturkurzbefehle</li>
</ol></div>
""")

# 1
add(f"""
<h1><span class="n">1</span>Was ist Focus Stack?</h1>
<p class="lead">Mit Focus Stack steuert Ihr Mac einen motorisierten Fokussierer am Feintrieb des Mikroskops und eine
per USB angeschlossene Kamera. Die App führt automatisch Serien nach dem Muster <b>bewegen → warten →
auslösen</b> aus: Dutzende Fotos in verschiedenen Fokusebenen, bereit zum Verrechnen zu einem durchgehend
scharfen Bild mit <b>Helicon Focus</b> (oder einem ähnlichen Programm).</p>
<h2>Funktionsweise</h2>
<p>Die App Focus Stack startet auf dem Mac ein kleines Programm (den <i>Server</i>), das mit dem Fokussierer
(einer Arduino-Platine mit der Firmware myFocuserPro2) und mit der Kamera kommuniziert. Die Oberfläche öffnet
sich in <b>Safari</b> unter <code>http://localhost:8765</code> und ist nur von diesem Mac aus erreichbar.</p>
<ul>
<li>Der <b>Fokussierer</b> dreht den Fokussierknopf mit einem Schrittmotor. Jeder <i>Schritt</i> des Motors
  bewegt den Objekttisch (oder das Objektiv) um den Bruchteil eines Mikrometers; wie viel genau, berechnet die
  <b>Mechanik-Konfiguration</b> (Kapitel 10).</li>
<li>Die <b>Kamera</b> wird über dasselbe Protokoll gesteuert, das auch die Programme der Hersteller verwenden:
  Belichtungszeit, ISO, Format, Auslösung, Übertragen der Fotos und Live-View.</li>
<li>Die <b>Hardwaretasten</b> des Fokussierers funktionieren auch bei geöffneter App weiter.</li>
</ul>
<h2>Was Sie brauchen</h2>
<ul>
<li>Einen Mac mit macOS 13 oder neuer (Intel) bzw. macOS 14 oder neuer (Apple Silicon), mit Safari.</li>
<li>Den Fokussierer, angeschlossen mit seinem USB-Kabel und mit Strom versorgt (12 V).</li>
<li>Eine Kamera von Nikon, Canon oder Sony mit USB-Kabel. Als Beispiel dient in dieser Anleitung eine <b>Nikon D5600</b>.</li>
<li>Einen Adapter, der das Mikroskopbild auf den Sensor projiziert (Fototubus, T2-Adapter oder Ähnliches).</li>
</ul>
<div class="box tip"><span class="t">Ohne Hardware</span>In den Karten „{ui("Focheggiatore")}“ und „{ui("Fotocamera")}“
gibt es das Kästchen <span class="ui">{ui("Simulatore")}</span>: Damit können Sie die ganze App ausprobieren, ohne
etwas anzuschließen. Die Bildschirmfotos dieser Anleitung sind so entstanden.</div>
""")

# 2
add(f"""
<h1><span class="n">2</span>Installation, Start und Updates</h1>
<h2>Erste Installation</h2>
<ol class="steps">
<li>Laden Sie <code>FocusStack-&lt;Version&gt;.zip</code> von
  <b>github.com/teoteo/focus-stack/releases</b> und öffnen Sie die Datei: Die App <b>Focus Stack</b> erscheint.</li>
<li>Ziehen Sie Focus Stack in den Ordner <b>Programme</b>, bevor Sie die App öffnen.</li>
<li>Öffnen Sie die App. macOS meldet, dass der Entwickler nicht überprüft werden kann, weil die App nicht von
  Apple signiert ist. Öffnen Sie <b>Systemeinstellungen › Datenschutz &amp; Sicherheit</b>, scrollen Sie nach unten
  und klicken Sie auf <b>Dennoch öffnen</b>. Das ist nur beim ersten Mal nötig.</li>
</ol>
<p>Die App enthält bereits alles, was sie braucht: Sie müssen nichts weiter installieren.</p>
<h2>Starten und beenden</h2>
<ul>
<li>Beim Start öffnet Focus Stack seine Seite in Safari und bleibt im Dock. Ein Klick auf das Symbol im Dock holt
  die Seite wieder in den Vordergrund.</li>
<li>Zum Beenden: <kbd>⌘Q</kbd> in der App oder <span class="ui">Beenden</span> im Menü des Dock-Symbols.
  Läuft gerade eine Serie, fragt die App nach, bricht sie ab und hält den Motor an.</li>
<li>Das Schließen von Safari beendet die App <b>nicht</b>. Bleibt die Seite offen, zeigt sie „{ui("Focus Stack è chiuso")}“
  an und lädt sich von selbst neu, sobald Sie die App wieder öffnen.</li>
</ul>
<h2>Updates</h2>
<p>Beim Start und danach alle 6 Stunden prüft die App, ob es eine neue Version gibt. Wenn ja, erscheint oben eine
Leiste mit <span class="ui">{ui("Aggiorna e riavvia")}</span>: Die App lädt die neue Version, beendet sich und öffnet
sich von selbst wieder. Dieselbe Prüfung können Sie von Hand unter
<span class="ui">{ui("Configurazione")} › {ui("Aggiornamenti")} › {ui("Controlla ora")}</span> starten.</p>
<p>Auch die <b>Firmware des Fokussierers</b> wird über die App aktualisiert (Kapitel 12): Ist die Firmware auf der
Platine älter als die in der App enthaltene, weist dieselbe Leiste darauf hin.</p>
<h2>Sprache</h2>
<p>Die App spricht Italienisch, Englisch, Französisch, Deutsch und Spanisch. Mit <span class="ui">{ui("Automatica (lingua del sistema)")}</span>
folgt sie der Sprache von macOS und verwendet für andere Sprachen Englisch; unter
<span class="ui">{ui("Configurazione")} › {ui("Lingua")}</span> können Sie eine feste Sprache wählen. Die Auswahl gilt für
Oberfläche, Meldungen und Protokoll, und diese Anleitung gibt es in denselben Sprachen.</p>
""")

# 3
add(f"""
<h1><span class="n">3</span>Die Oberfläche im Überblick</h1>
<p>Die Seite hat drei Bereiche, die Sie oben auswählen:</p>
<ul>
<li><b>{ui("Sessione")}</b>: die Arbeit am Mikroskop. Fokussierer, Serie, Kamera und letzte Aufnahme.</li>
<li><b>{ui("Configurazione")}</b>: Grenzen, Mechanik, manuelle Steuerung, Motor, Updates, Temperatur und der
  Schärfentiefe-Rechner. Wird einmal eingestellt und danach nur selten angefasst.</li>
<li><b>{ui("Registro")}</b>: eine Liste mit Uhrzeit von allem, was in der Sitzung passiert ist. Hier sollten Sie als
  Erstes nachsehen, wenn etwas nicht funktioniert.</li>
</ul>
{fig("sessione", layout="full", caption=f"Der Bereich {ui('Sessione')}: links der Fokussierer, in der Mitte die Serie, rechts Kamera und letzte Aufnahme.")}
<h2>Obere Leiste</h2>
{fig("barra-superiore", [
    f"<b>Bereiche</b> {ui('Sessione')}, {ui('Configurazione')} und {ui('Registro')}.",
    f"<b>Verbindungsstatus</b>: {ui('Server')}, {ui('Focheggiatore')} und {ui('Fotocamera')}. Grün = verbunden, grau = getrennt, rot = Fehler.",
    "<b>Temperatur</b>, gemessen vom Fühler des Fokussierers.",
    "<b>Design</b>, dunkel oder hell. Das dunkle Design ermüdet bei langen Sitzungen am Mikroskop weniger.",
], layout="full below-marks", anchors={1: "b", 2: "b", 3: "b", 4: "b"})}
<p>Unter der Leiste können zwei Streifen erscheinen: ein blauer für <b>Updates</b> und ein roter <b>Alarm</b>, zum
Beispiel wenn die Hardwaretasten den Fokussierer über eine Grenze hinaus bewegen.</p>
""")

# 4
add(f"""
<h1><span class="n">4</span>Fokussierer und Kamera verbinden</h1>
<h2>{ui("Focheggiatore")}</h2>
{fig("connessione-focheggiatore", [
    "<b>Serieller Port</b> des Fokussierers, meist <code>/dev/cu.usbserial-…</code> oder <code>/dev/cu.wchusbserial…</code>; der Name ändert sich mit der USB-Buchse am Mac.",
    "<b>Portliste aktualisieren</b> nach dem Anschließen des Kabels.",
    f"<b>{ui('Simulatore')}</b>: simulierter Fokussierer zum Ausprobieren.",
    f"<b>{ui('Connetti')}</b>. Beim Öffnen des Ports startet der Arduino neu: Das dauert 2–3 Sekunden.",
], layout="side narrow")}
<h2>{ui("Fotocamera")}</h2>
{fig("connessione-fotocamera", [
    f"<b>Kamera</b>: <i>{ui('Rilevamento automatico')}</i> lassen oder das gefundene Modell wählen.",
    f"<b>{ui('Rileva fotocamere')}</b>: sucht angeschlossene Kameras.",
    f"<b>{ui('Simulatore')}</b>: simulierte Kamera, die Testbilder erzeugt.",
    f"<b>{ui('Connetti')}</b>. Vorher beendet die App die macOS-Dienste, die die Kamera belegen.",
], layout="side narrow")}
<h3>Einstellungen an der Kamera</h3>
{table(["Kamera", "Was einstellen"], [
    ["<b>Nikon D5600</b> und andere Nikon", "Moduswahlrad auf <b>M</b> (manuell). Im Wiedergabemenü die <b>Bildkontrolle</b> ausschalten. SnapBridge/WLAN und Bluetooth ausschalten, sie können die Verbindung belegen. Speicherkarte eingelegt lassen, Akku geladen (oder Netzadapter EH-5/EP-5A)."],
    ["Canon", f"Modus <b>M</b>. Die Aufnahme landet je nach <i>{ui('Destinazione')}</i> im Kameraspeicher oder auf der Karte. Für die Spiegelverzögerung im Menü die <b>Spiegelverriegelung</b> aktivieren."],
    ["Sony", "USB-Menü › <b>PC Remote</b>; Modus <b>M</b>. Für Live-View muss die Kamera dies im Modus PC Remote erlauben."],
])}
<div class="box warn"><span class="t">Wenn sich die Kamera nicht verbindet</span>macOS versucht, die Kamera zu
übernehmen, sobald Sie sie anschließen. Die App beendet diesen Dienst selbst; reicht das nicht, beenden Sie
<b>Fotos</b>, <b>Vorschau</b>, <b>Digitale Bilder</b>, NX Studio und EOS Utility und versuchen Sie es erneut. Oft hilft
es, das Kabel bei eingeschalteter Kamera ab- und wieder anzustecken.</div>
""")

# 5
add(f"""
<h1><span class="n">5</span>Der Fokussierer: Position, Bewegungen, STOP</h1>
{fig("focheggiatore", [
    f"<b>Status</b>: {ui('Fermo')}, {ui('In movimento')}, {ui('Disconnesso')}.",
    f"<b>Verbindung</b>: Port, Firmware-Version und Firmware-Maximum (die höchste zulässige Position). <span class='ui'>{ui('Disconnetti')}</span> gibt den Port frei.",
    "<b>Position</b> in Motorschritten und darunter in Millimetern oder Mikrometern (sobald die Mechanik konfiguriert ist).",
    "Eingestellte <b>Grenzen</b> und der verbleibende Abstand in Richtung Präparat bis zur Grenze.",
    "<b>Verfahrbalken</b>: siehe die Abbildung unten.",
    f"<b>Schrittgröße</b> der Tasten {ui('Allontana')}/{ui('Avvicina')}: 1, 10, 100 … Schritte. Die verfügbaren Größen wählen Sie unter {ui('Configurazione')} › {ui('Comandi manuali')}.",
    "Dieselbe Bewegung <b>in Mikrometern</b>.",
    f"<b>{ui('Allontana')} / {ui('Avvicina')}</b>: Ein Klick bewegt um die gewählte Schrittgröße. Halten Sie die Taste gedrückt, fährt der Motor ohne anzuhalten weiter und bremst beim Loslassen bis zum Stillstand ab.",
    f"<b>Zu Position fahren</b>: Geben Sie eine Schrittzahl ein und klicken Sie auf {ui('Vai')}.",
    "<b>STOP</b>: hält den Motor und eine laufende Serie sofort an. Tastatur: <kbd>Esc</kbd>.",
])}
<h2>Der Verfahrbalken</h2>
{fig("binario", [
    "<b>Rot schraffierte Zonen</b>: außerhalb der Grenzen, gesperrt.",
    "<b>Blaues Band</b>: der Bereich der Serie, mit einer Markierung pro Aufnahme.",
    "<b>Weiße Linie</b>: die aktuelle Position.",
], layout="side narrow")}
<p>Unter dem Balken: die untere Grenze, der Pfeil, der anzeigt, <b>auf welcher Seite das Präparat liegt</b>, und die
obere Grenze. „{ui('Avvicina')}“ bewegt immer in Richtung Präparat, egal in welche Richtung die Zahlen laufen: Das
stellen Sie unter {ui('Configurazione')} › {ui('Fine corsa')} ein (Kapitel 9).</p>
<div class="box tip"><span class="t">Tastatur</span><kbd>↑</kbd> fährt weg, <kbd>↓</kbd> fährt näher,
<kbd>⇧</kbd> zusammen mit einem Pfeil multipliziert den Schritt mit 10, die Zifferntasten <kbd>1</kbd> <kbd>2</kbd>
<kbd>3</kbd> … wählen die Schrittgröße, <kbd>Esc</kbd> ist STOP. Die Tasten funktionieren im Bereich {ui('Sessione')},
auch während Sie das Live-View betrachten.</div>
<div class="box warn"><span class="t">Hardwaretasten</span>Die Tasten am Fokussierer bewegen den Motor an der App
vorbei. Die App überwacht sie und sendet STOP und einen Alarm, wenn die Position die Grenzen verlässt; für einen
vollständigen Schutz lesen Sie Kapitel 9. Drücken Sie sie während einer Serie, wird die Serie pausiert.</div>
""")

# 6
add(f"""
<h1><span class="n">6</span>Kamera, Testaufnahme und Live-View</h1>
{fig("fotocamera", [
    f"<b>Status</b>: {ui('Pronta')}, {ui('Scatto…')}, {ui('Disconnessa')}.",
    f"Verbundenes <b>Modell</b> und <span class='ui'>{ui('Disconnetti')}</span>.",
    f"<b>{ui('Tempo di posa')}</b> und <b>ISO</b>.",
    f"<b>{ui('Diaframma')}</b> und <b>{ui('Formato')}</b> (RAW, JPEG …). Am Mikroskop, ohne Objektiv an der Kamera, gibt es meist keine Blende.",
    f"<b>{ui('Destinazione')}</b>: Kameraspeicher oder Karte.",
    f"<b>{ui('Posa B (secondi)')}</b>: 0 verwendet die Belichtungszeit; ein Wert über 0 löst eine vom Mac gesteuerte Bulb-Belichtung aus, für Zeiten über 30 s.",
    f"<b>{ui('Ritardo specchio (reflex)')}</b>, 0,5 bis 2,5 s: Wartezeit zwischen Hochklappen des Spiegels und Belichtung, damit Vibrationen abklingen. Bei der Nikon D5600 verwendet die App die <i>Belichtungsverzögerung</i> der Kamera.",
    f"<b>{ui('Rileggi')}</b>: liest die Einstellungen aus der Kamera. Nach jeder Änderung liest die App den Wert zurück, den die Kamera tatsächlich übernommen hat.",
    f"<b>{ui('◉ Scatto di prova')}</b>: ein Foto an der aktuellen Position, das in „{ui('Ultimo scatto')}“ und im Betrachter erscheint.",
])}
<h2>{ui('Ultimo scatto')} und Live-View</h2>
<div class="two">
{fig("ultimo-scatto", [
    f"<b>{ui('● Live')}</b>: zeigt das Livebild der Kamera.",
    f"<b>{ui('Apri visualizzatore ↗')}</b>: öffnet den Betrachter in einem eigenen Fenster (Kapitel 8).",
    f"<b>{ui('Ultimo scatto')}</b>: Ein Klick öffnet sie im Betrachter.",
    "Dateiname, Position und Temperatur zum Zeitpunkt der Aufnahme.",
], layout="stack")}
{fig("live", [
    f"<b>{ui('■ Ferma live')}</b> schaltet das Live-View aus.",
    f"Status: <b>{ui('LIVE')}</b>, <b>{ui('SCATTO…')}</b> während einer Testaufnahme, <b>{ui('IN PAUSA')}</b> während der Serie.",
    "Kameramodell. Doppelklick auf das Bild: Vollbild.",
], layout="stack")}
</div>
<p>Das Live-View liefert bis zu 15 Bilder pro Sekunde und ist der bequemste Weg, Anfang und Ende der Serie zu finden,
während Sie den Fokussierer mit der Tastatur bewegen. Während der Serie wird es ausgeschaltet (der Spiegel muss
herunterklappen und die Kamera normal auslösen) und startet am Ende von selbst wieder. Bei Spiegelreflexkameras bleibt
der Spiegel hochgeklappt, solange das Live-View eingeschaltet ist.</p>
<div class="box tip"><span class="t">Für präzises Fokussieren</span>Öffnen Sie das Live-View im <b>Betrachter</b>: Dort
können Sie auf 100 % und mehr vergrößern und zum gewünschten Detail verschieben (Kapitel 8).</div>
""")

# 7
TORNA = ui("Torna all'inizio a fine sequenza")
add(f"""
<h1><span class="n">7</span>Die Stacking-Serie</h1>
{fig("sequenza", [
    f"<b>Status</b>: {ui('Pronta')}, {ui('In corso')}, {ui('In pausa')}, {ui('Completata')}, {ui('Errore')}.",
    f"<b>{ui('Inizio')}</b> und <b>{ui('Fine')}</b> in Schritten. <span class='ui'>{ui('⌖ qui')}</span> übernimmt die aktuelle Position.",
    "<b>Schrittweite</b> zwischen zwei Aufnahmen, in Motorschritten (Kapitel 11).",
    f"<b>{ui('Numero di scatti')}</b>: mit der Schrittweite gekoppelt; ändern Sie einen Wert, wird der andere neu berechnet.",
    "<b>Übersicht</b>: Aufnahmen, Bereich in Schritten und µm, Schrittweite in µm, geschätzte Dauer. Liegt die Serie außerhalb der Grenzen, erscheint ein roter Hinweis und sie startet nicht.",
    f"<b>{ui('Salva in')}</b>: der Ordner für die Fotos. <span class='ui'>{ui('Scegli…')}</span> öffnet das Finder-Fenster, <span class='ui'>{ui('Apri')}</span> zeigt ihn im Finder.",
    "<b>Wartezeit nach Bewegung</b>: zum Abklingen der Vibrationen vor der Aufnahme (1–3 s am Mikroskop). <b>Pause nach Aufnahme</b>: zum Schreiben auf die Karte und Laden des Blitzes.",
    "<b>Spielausgleich</b>: Vor der ersten Aufnahme fährt der Motor so viele Schritte zurück und wieder vor, damit jede Aufnahme aus derselben Richtung angefahren wird.",
    f"<b>{ui('Modalità di scatto')}</b>: <i>{ui('Scarica sul Mac')}</i> (empfohlen), <i>{ui('Solo sulla scheda')}</i>, <i>Nur auslösen</i> (schneller: Speicherziel auf Karte).",
    "<b>Sitzungsname</b>: Unterordner <code>Name_Datum-Uhrzeit</code>, Dateien <code>Name_0001</code>, <code>Name_0002</code> …",
    f"<b>{TORNA}</b>.",
    f"<b>{ui('Preset')}</b>: speichert und lädt die Einstellungen der Serie, z. B. eines pro Objektiv.",
    "<b>Fortschritt</b>: erstellte Aufnahmen, verbleibende Zeit, Position.",
    f"<b>{ui('▶ Avvia sequenza')}</b>, <b>{ui('❚❚ Pausa')}</b>/<b>{ui('Riprendi')}</b> und <b>{ui('■ Interrompi')}</b>.",
    f"<b>{ui('Apri in Helicon Focus')}</b>: lädt nach der Serie alle Fotos in Helicon Focus.",
])}
<p>Die Einstellungen für Zeiten und Spiel befinden sich im einklappbaren Abschnitt
<span class="ui">{ui('Tempi, gioco e nome della sessione')}</span>. Im Fotoordner speichert die App außerdem
<code>sequence.json</code> mit den verwendeten Parametern sowie Position und Temperatur jeder Aufnahme.</p>
<h2>Während die Serie läuft</h2>
{fig("sequenza-in-corso", [
    f"Der Status wechselt zu <b>{ui('In corso')}</b> (bernsteinfarben).",
    "Erstellte Aufnahmen von insgesamt, geschätzte Restzeit und aktuelle Position. Auf dem Verfahrbalken ändern die Markierungen der erstellten Aufnahmen ihre Farbe.",
    f"<b>{ui('❚❚ Pausa')}</b> hält nach der laufenden Aufnahme an; <b>{ui('■ Interrompi')}</b> beendet die Serie. Das <b>STOP</b> des Fokussierers hält zusätzlich sofort den Motor an.",
], layout="side narrow")}
<ul>
<li>Wenn Sie die <b>Hardwaretasten</b> des Fokussierers drücken, wird die Serie pausiert; beim Fortsetzen fährt sie
  zurück an die richtige Position und wiederholt die Aufnahme.</li>
<li>Die Felder der Serie sind gesperrt, solange die Serie läuft.</li>
<li>Jedes neue Foto erscheint in „{ui('Ultimo scatto')}“ und im Betrachter.</li>
</ul>
""")

# 8
add(f"""
<h1><span class="n">8</span>Der Betrachter</h1>
<p>Sie öffnen ihn mit <span class="ui">{ui('Apri visualizzatore ↗')}</span> oder mit einem Klick auf die letzte
Aufnahme. Er ist ein eigenes Fenster, das Sie auf einen zweiten Monitor schieben können. Er zeigt die Fotos in voller
Auflösung (auch RAW-Dateien, die direkt umgewandelt werden) mit Zoom und Verschieben sowie das Live-View der Kamera.</p>
{fig("visualizzatore", [
    "<b>◀ ▶</b> vorherige und nächste Aufnahme (Pfeiltasten <kbd>←</kbd> <kbd>→</kbd>).",
    "Dateiname; Nummer der Aufnahme, Art, Position, Temperatur und Uhrzeit.",
    f"<b>{ui('● Live')}</b> (<kbd>L</kbd>): das Live-View im selben Fenster, mit Zoom und Verschieben.",
    "<b>Zoom</b> − und + (<kbd>−</kbd> <kbd>+</kbd>) und die Vergrößerungsstufe.",
    f"<b>{ui('Adatta')}</b> (<kbd>0</kbd>), <b>100 %</b> (<kbd>1</kbd>: ein Sensorpixel = ein Bildschirmpixel), <b>{ui('Reset')}</b> (<kbd>R</kbd>).",
    f"<b>{ui('Segui ultimo')}</b> (<kbd>U</kbd>): zeigt jede neue Aufnahme automatisch an.",
    f"<b>{ui('Blocca vista')}</b> (<kbd>K</kbd>): behält Zoom und Position beim Wechsel der Aufnahme bei, um die Schärfe an derselben Stelle zu vergleichen.",
    f"<b>{ui('Finder')}</b>: zeigt die Datei im Finder.",
    "<b>Vollbild</b> (<kbd>F</kbd>).",
    f"<b>Miniaturen</b>: Ein Klick öffnet die Aufnahme. <i>{ui('P')}</i> = Testaufnahme, die Zahlen sind die Aufnahmen der Serie.",
], layout="full", anchors={n: "b" for n in range(1, 10)})}
<p>Mit der Maus: Ziehen verschiebt das Bild, das Scrollrad (oder Aufziehen auf dem Trackpad) zoomt um den Zeiger herum,
ein Doppelklick wechselt zwischen „Einpassen“ und 100 %. Über 150 % bleiben die Pixel scharf, ohne Weichzeichnung.</p>
{fig("visualizzatore-live", [
    f"<b>{ui('■ Ferma live')}</b> kehrt zu den Fotos zurück; auch ◀ ▶ oder ein Klick auf eine Miniatur verlassen das Live-View.",
    f"Live-Status: {ui('LIVE')}, {ui('SCATTO…')}, {ui('IN PAUSA')} während der Serie.",
], layout="full", anchors={1: "b"}, caption="Das Live-View im Betrachter, hier mit dem Simulator im Fokus (das Schachbrett ist scharf). Bei 100 % hat das Live-View die Auflösung der Kameravorschau, also weniger als die Fotos.")}
""")

# 9
add(f"""
<h1><span class="n">9</span>Sicherheitsgrenzen</h1>
<p class="lead">Die Grenzen verhindern, dass das Objektiv den Objektträger berührt oder die Mechanik auf Anschlag
fährt. Richten Sie sie als Erstes ein, in aller Ruhe.</p>
{fig("fine-corsa", [
    f"<b>{ui('Fine corsa inferiore')}</b> in Schritten; <span class='ui'>{ui('⌖ Usa posizione attuale')}</span> übernimmt sie aus der Position des Fokussierers.",
    f"<b>{ui('Fine corsa superiore')}</b>. Leer = das Firmware-Maximum.",
    f"<b>{ui('Verso il campione (si avvicina) con')}</b>: ob die Schrittzahl bei Annäherung an das Präparat sinkt oder steigt. Damit werden {ui('Avvicina')}/{ui('Allontana')} richtig beschriftet.",
    f"<b>{ui('Salva fine corsa')}</b>.",
    f"<b>{ui('Imposta qui lo zero')}</b>: Die aktuelle Position wird zu 0; Grenzen und Serie werden entsprechend verschoben.",
    f"<b>{ui('Scrivi il massimo nel firmware')}</b>: Die obere Grenze wird zur Grenze der Firmware.",
], layout="full")}
<h2>Was schützt wovor?</h2>
<ul>
<li><b>Von der App gesteuerte Bewegungen</b> (Gehe zu, {ui('Allontana')}/{ui('Avvicina')}, Serie, Spielausgleich):
  Die App prüft sie, <i>bevor</i> sie den Motor bewegt. Die Dauerbewegung hält an der Grenze an; eine Serie, die die
  Grenzen überschreiten würde, startet nicht.</li>
<li><b>Hardwaretasten</b>: Die App liest die Position alle 0,2–0,5 s; verlässt sie die Grenzen, sendet die App STOP und
  zeigt den Alarm. Zwischen zwei Abfragen kann der Motor die Grenze jedoch um einige Dutzend Schritte überschreiten.</li>
</ul>
<h2>Empfohlener Schutz: Grenzen in der Firmware</h2>
<p>Die Firmware wendet ihre Grenzen auch auf die Hardwaretasten an: Sie fährt nie unter 0 und nie über ihr
Maximum.</p>
<ol class="steps">
<li>Bringen Sie den Objekttisch mit einem Trockenobjektiv und ohne Objektträger, oder mit großer Vorsicht, in die
  Position, die dem <b>Präparat am nächsten und noch sicher</b> ist, und klicken Sie auf <span class="ui">{ui('Imposta qui lo zero')}</span>.</li>
<li>Bringen Sie den Objekttisch in die entfernteste sinnvolle Position, klicken Sie bei der oberen Grenze auf
  <span class="ui">{ui('⌖ Usa posizione attuale')}</span>, dann auf <span class="ui">{ui('Salva fine corsa')}</span> und
  <span class="ui">{ui('Scrivi il massimo nel firmware')}</span>.</li>
<li>Prüfen Sie einmal von Hand und langsam mit den Hardwaretasten, ob der Fokussierer wirklich bei 0 und beim
  Maximum anhält.</li>
</ol>
<div class="box danger"><span class="t">{ui('Attenzione')}</span>Die Grenze „Richtung Präparat“ hängt vom Objektiv und
von der Dicke des Objektträgers ab: Bei einem Objektiv mit kurzem Arbeitsabstand (40×, 100×) beträgt der Spielraum nur
wenige Zehntelmillimeter. Prüfen Sie die Grenzen bei jedem Objektivwechsel erneut, ebenso nach einer Änderung des
<b>Mikroschritts</b>, die den Maßstab der Positionen ändert.</div>
""")

# 10 — Mechanik
add(f"""
<h1><span class="n">10</span>Mechanik einrichten: die Berechnungen</h1>
<p class="lead">Die App rechnet in <b>Motorschritten</b>. Um Ihnen Bewegungen, Bereiche und Schrittweiten der Serie in
<b>Mikrometern</b> anzuzeigen und die richtige Schrittweite aus der Schärfentiefe zu berechnen, muss sie wissen, wie
viele Mikrometer ein Schritt ausmacht. Diese Zahl heißt <b>Auflösung</b> (µm/Schritt) und hängt davon ab, wie der Motor
mit dem Feintrieb gekoppelt ist.</p>
{fig("meccanica", [
    f"<b>Modus</b>: <i>{ui('Calcola dalla meccanica')}</i> (aus den Daten darunter) oder <i>{ui('Inserisci µm/passo')}</i> (ein gemessener Wert).",
    f"<b>{ui('Passi motore per giro')}</b>: 200 bei einem 1,8°-Motor, 400 bei einem 0,9°-Motor.",
    f"<b>{ui('Microstep (dal firmware)')}</b>: wird aus der Firmware gelesen und hier nicht geändert (siehe {ui('Motore (firmware)')}).",
    f"<b>{ui('Rapporto di riduzione')}</b>: wie viele Umdrehungen der Motor für eine Umdrehung des Knopfes macht.",
    f"<b>{ui('Corsa per giro manopola (µm)')}</b>: um wie viele µm sich der Objekttisch pro Umdrehung des Feintriebknopfes bewegt.",
    "<b>Ergebnis</b>: µm pro Schritt, Schritte pro µm, µm pro 1.000 Schritte.",
    f"<b>{ui('Salva meccanica')}</b>.",
])}
<h2>10.1 Der Antriebsstrang</h2>
<p>Vom Motor bis zum Objekttisch durchläuft die Bewegung mehrere Stufen, und jede multipliziert oder teilt:</p>
{diagram(DIAGRAM_LABELS)}
<div class="formula">
  Auflösung (µm/Schritt) = {frac("Weg pro Knopfumdrehung (µm)", "Schritte/Umdr. × Mikroschritt × Untersetzung")}
  <span class="lbl">Genau das berechnet die App bei „{ui('Calcola dalla meccanica')}“.</span>
</div>
<h2>10.2 Die vier Zahlen im Einzelnen</h2>
<h3>Motorschritte pro Umdrehung</h3>
<p>Sie ergeben sich aus dem Schrittwinkel auf dem Typenschild oder im Datenblatt des Motors:</p>
<div class="formula">Schritte pro Umdrehung = {frac("360°", "Schrittwinkel")}
<span class="lbl">1,8° → 200 Schritte · 0,9° → 400 Schritte · 7,5° → 48 Schritte</span></div>
<p>Der NEMA 14 OMC 14HM11-0404S des Fokussierers myFocuserPro2 hat 0,9°: <b>400</b>. Der NEMA 17
17HS13-0404S-PG27 mit Getriebe hat 1,8°: <b>200</b>; das Getriebe gehört in die Untersetzung (unten), nicht hierher.</p>
<h3>Mikroschritt</h3>
<p>Der Treiber kann jeden Schritt in 2, 4, 8, 16 oder 32 Mikroschritte teilen. Bei 1/8-Mikroschritt braucht eine
Motorumdrehung 8-mal so viele Schritte und die Auflösung wird 8-mal feiner (dafür sinkt das Drehmoment pro Mikroschritt,
und die Höchstgeschwindigkeit in µm/s fällt auf ein Achtel).</p>
<ul>
<li><b>myFocuserPro2</b>: Der Mikroschritt wird von der Firmware eingestellt und unter {ui('Configurazione')} ›
  {ui('Motore (firmware)')} geändert. Die App liest ihn und verwendet ihn selbstständig in der Berechnung.</li>
<li><b>Ardufocus</b>: Der Mikroschritt ist auf der Platine festgelegt (Jumper oder Verdrahtung des Treibers), die
  Firmware steuert ihn nicht. Stellen Sie unter {ui('Configurazione')} › {ui('Motore (firmware)')} <b>denselben Wert wie
  auf der Platine</b> ein, sonst ist die Berechnung um genau diesen Faktor falsch. Wenn Sie ihn nicht kennen, messen
  Sie ihn (10.4).</li>
</ul>
<h3>Untersetzung</h3>
<p>Das ist die Zahl der Motorumdrehungen für <b>eine</b> Umdrehung des Knopfes. Alle Stufen werden miteinander
multipliziert:</p>
<div class="formula">Untersetzung = Getriebe × {frac("Zähne der Riemenscheibe am Knopf", "Zähne der Riemenscheibe am Motor")}
<span class="lbl">bei Reibrädern oder O-Ringen: statt der Zähne die Durchmesser</span></div>
<ul>
<li><b>Direkte Kopplung</b> (Motor auf der Knopfachse, ohne Getriebe): Untersetzung 1.</li>
<li><b>Zahnriemen</b> von einer GT2-Riemenscheibe mit 20 Zähnen am Motor auf eine mit 60 Zähnen am Knopf: 60 ÷ 20 = <b>3</b>.</li>
<li><b>Planetengetriebe</b>: die auf dem Motor angegebene Untersetzung. Das PG27 des 17HS13 hat 26 103/121 = 26 + 103 ÷ 121
  = <b>26,851</b> (nicht genau 27: Verwenden Sie den genauen Wert). Bei direkter Kopplung ist die Untersetzung 26,851; mit
  einem Riemen 20 → 40 Zähne wird sie zu 26,851 × 2 = 53,70.</li>
</ul>
<h3>Weg pro Knopfumdrehung</h3>
<p>Wie weit sich der Objekttisch (oder der Tubus, bei Mikroskopen, die das Objektiv bewegen) pro Umdrehung des vom Motor
angetriebenen Knopfes bewegt, meist des <b>Feintriebs</b>. Viele Mikroskope haben 100 µm pro Umdrehung, manche 200 µm oder
andere Werte. Am sichersten finden Sie es heraus, indem Sie die Teilstriche am Knopf zählen:</p>
<div class="formula">Weg pro Umdrehung = Anzahl der Teilstriche am Knopf × µm pro Teilstrich
<span class="lbl">Beispiel: 100 Teilstriche zu 1 µm = 100 µm pro Umdrehung · 50 Teilstriche zu 2 µm = 100 µm pro Umdrehung</span></div>
<p>Der Wert pro Teilstrich ist oft auf dem Knopf oder dem Mikroskopstativ eingraviert („1 µm“, „2 µm“) oder im Handbuch
angegeben. Treibt der Motor den <b>Grobtrieb</b> statt des Feintriebs an, beträgt der Weg pro Umdrehung mehrere
Millimeter: Die Auflösung ist dann viel gröber und muss sorgfältig überprüft werden.</p>

<h2>10.3 Rechenbeispiele</h2>
<h3>Beispiel A: myFocuserPro2 mit NEMA 14 und Riemen</h3>
<div class="calc">Motor 0,9°               → Schritte/Umdr. = 360 ÷ 0,9 = 400
Mikroschritt             → 1 (Vollschritt)
Riemen 20 → 60 Zähne     → Untersetzung = 60 ÷ 20 = 3
Feintrieb                → 100 µm pro Umdrehung

Schritte pro Knopfumdrehung = 400 × 1 × 3 = 1.200
Auflösung = 100 ÷ 1.200 = <b>{num(UA, 4)} µm/Schritt</b>   (12 Schritte = 1 µm; 1.000 Schritte = {num(UA * 1000, 1)} µm)</div>
<p>Mit dieser Konfiguration wurden die Bildschirmfotos dieser Anleitung erstellt. Bei 1/8-Mikroschritt ergäbe derselbe
Fokussierer 100 ÷ (400 × 8 × 3) = <b>{num(um_step(100, 400, 8, 3), 4)} µm/Schritt</b>.</p>
<h3>Beispiel B: Ardufocus mit NEMA 17 und Getriebe PG27</h3>
<div class="calc">Motor 1,8°               → Schritte/Umdr. = 200
Mikroschritt (Platine)   → 1
Getriebe 26 103/121      → 26,851, direkt mit dem Knopf gekoppelt
Feintrieb                → 100 µm pro Umdrehung

Schritte pro Knopfumdrehung = 200 × 1 × 26,851 = {num(200 * GEAR17, 0)}
Auflösung = 100 ÷ {num(200 * GEAR17, 0)} = <b>{num(UB, 4)} µm/Schritt</b>   (1 µm = {num(1 / UB, 1)} Schritte)</div>
<p>Das Getriebe macht die Auflösung etwa 4,5-mal feiner als in Beispiel A und liefert viel mehr Drehmoment, für dieselbe
Bewegung sind aber viel mehr Schritte nötig: Deshalb erlaubt die App Schrittgrößen bis 100.000 Schritte (Kapitel 12).</p>

<h2>10.4 Mit einer Messung überprüfen</h2>
<p>Die Berechnung stimmt, wenn alle Daten richtig sind und nichts rutscht (lockerer Riemen, Riemenscheibe, die sich auf
der Achse dreht). Eine Kontrolle lohnt sich immer und ist unverzichtbar, wenn Sie eine der Zahlen nicht kennen.</p>
<h3>Mit den Teilstrichen des Feintriebs</h3>
<ol class="steps">
<li>Fahren Sie immer aus derselben Richtung an (um das Spiel auszuschließen): Fahren Sie einige hundert Schritte in eine
  Richtung und notieren Sie dann den Teilstrich des Knopfes, der auf der Indexmarke steht.</li>
<li>Fahren Sie mit <span class="ui">Zu Position fahren</span> um eine große Schrittzahl <b>N</b> in dieselbe Richtung, sodass
  sich der Knopf mindestens eine halbe Umdrehung dreht (Beispiel A: N = 1.000; Beispiel B: N = 5.000).</li>
<li>Zählen Sie die zurückgelegten Teilstriche <b>T</b> und multiplizieren Sie mit den µm pro Teilstrich.</li>
</ol>
<div class="formula">gemessene Auflösung = {frac("T × µm pro Teilstrich", "N")}</div>
<div class="calc">Beispiel A: N = 1.000 Schritte, der Knopf rückt um 83 Teilstriche zu 1 µm vor
Auflösung = 83 × 1 ÷ 1.000 = <b>0,083 µm/Schritt</b>   (berechnet waren {num(UA, 4)}: passt)</div>
<h3>Mit einer Messuhr</h3>
<p>Eine Messuhr mit 0,01 oder 0,001 mm Ablesegenauigkeit, die auf dem Objekttisch aufliegt, misst die Bewegung direkt.
Fahren Sie N Schritte (immer aus derselben Richtung) und teilen Sie die Bewegung in µm durch N. Je größer N, desto
genauer das Ergebnis.</p>
<h3>Wenn die Messung nicht passt</h3>
<ul>
<li>Abweichung um den Faktor 2, 4, 8, 16: Der <b>Mikroschritt</b> ist nicht der, den Sie annehmen (typisch beim Ardufocus).</li>
<li>Abweichung um genau den Faktor 2: Ein 0,9°-Motor wurde für einen 1,8°-Motor gehalten oder umgekehrt.</li>
<li>Unregelmäßige Abweichung, die sich von Messung zu Messung ändert: Etwas <b>rutscht</b> (Riemen, Madenschraube der
  Riemenscheibe) oder der Motor <b>verliert Schritte</b> (Geschwindigkeit zu hoch, Strom zu niedrig).</li>
<li>Sind die mechanischen Daten unsicher, die Messung aber wiederholbar, wählen Sie
  <span class="ui">{ui('Inserisci µm/passo')}</span> und geben Sie den gemessenen Wert ein.</li>
</ul>
{fig("meccanica-manuale", [
    f"<b>{ui('Inserisci µm/passo')}</b>: um einen gemessenen Wert zu verwenden.",
    f"Gemessene <b>{ui('µm per passo')}</b>.",
    "Das Ergebnis wird während der Eingabe aktualisiert.",
], layout="side narrow")}

<h2>10.5 Weitere nützliche Werte</h2>
<h3>Nutzbarer Verfahrweg in Millimetern</h3>
<div class="calc">Verfahrweg (µm) = (obere Grenze − untere Grenze) × Auflösung
Beispiel A: (45.000 − 2.000) × {num(UA, 4)} = <b>{num(43000 * UA, 0)} µm ≈ {num(43000 * UA / 1000, 2)} mm</b></div>
<h3>Geschwindigkeit in µm pro Sekunde</h3>
<div class="calc">Geschwindigkeit (µm/s) = Schritte pro Sekunde × Auflösung
Beispiel A, Firmware mit 400 Schritten/s:   400 × {num(UA, 4)} ≈ <b>{num(400 * UA, 0)} µm/s</b>
Beispiel B, Firmware mit 2.000 Schritten/s: 2.000 × {num(UB, 4)} ≈ <b>{num(2000 * UB, 0)} µm/s</b></div>
<p>Daran sehen Sie, wie lange eine lange Bewegung dauert: 1 mm braucht in Beispiel A etwa {num(1000 / (400 * UA), 0)} Sekunden.</p>
<h3>Das Spiel in Schritten</h3>
<p>Wenn der Motor die Richtung umkehrt, bewegt sich der Knopf einige Schritte lang nicht: Das ist das <b>Spiel</b>
(Umkehrspiel) des Antriebs (Riemen, Zähne, Getriebe, Gewinde des Feintriebs). Es wird in Schritten ausgeglichen,
deshalb misst man es am besten in Schritten:</p>
<ol class="steps">
<li>Öffnen Sie das Live-View im Betrachter bei 100 % oder mehr, auf einem kleinen, kontrastreichen Detail.</li>
<li>Fahren Sie einige hundert Schritte in eine Richtung und kehren Sie dann mit der Schrittgröße 1 oder 10 um.</li>
<li>Zählen Sie die Schritte nach der Umkehr, bis sich das Bild zu bewegen beginnt: Das ist das Spiel. Wiederholen Sie
  das einige Male und nehmen Sie den höchsten Wert mit einer kleinen Reserve.</li>
</ol>
<p>Das angegebene Winkelspiel liefert die Größenordnung. Für das Getriebe PG27 ist höchstens 1° Spiel am Abtrieb
angegeben, also 1/360 einer Knopfumdrehung:</p>
<div class="calc">Spiel in Schritten = (1° ÷ 360°) × Schritte pro Knopfumdrehung = {num(200 * GEAR17, 0)} ÷ 360 ≈ <b>{num(200 * GEAR17 / 360, 0)} Schritte</b>
Spiel in µm        = (1° ÷ 360°) × 100 µm ≈ <b>{num(100 / 360, 2)} µm</b></div>
<p>Das Spiel von Riemen und Feintrieb kommt hinzu: Maßgeblich bleibt die Messung mit dem Live-View. Der Wert gehört dann
an <b>nur eine</b> von zwei Stellen: den <b>Spielausgleich der Serie</b> (Kapitel 7) oder das <b>Spiel IN/OUT der
Firmware</b> (Kapitel 12, höchstens 255 Schritte), nicht an beide.</p>
<h3>Wie fein die Auflösung sein muss</h3>
<p>Die Schrittweite der Serie (Kapitel 11) sollte mindestens etwa zehn Motorschritte betragen, damit das Runden auf ganze
Schritte kaum ins Gewicht fällt. Mit Beispiel A und einem 60×-Objektiv liegt die empfohlene Schrittweite bei etwa
7 Schritten: machbar, aber für sehr starke Objektive ist eine feinere Auflösung besser (Mikroschritt oder höhere
Untersetzung).</p>
""")

# 11 — Schrittweite der Serie
add(f"""
<h1><span class="n">11</span>Die Schrittweite der Serie wählen</h1>
<p class="lead">Jedes Foto ist nur in einer dünnen Schicht des Präparats scharf, der <b>Schärfentiefe</b>. Damit nach dem
Stacking alles scharf ist, darf sich der Fokus zwischen zwei Aufnahmen nicht weiter als diese Schicht verschieben, mit
etwas Überlappung.</p>
{fig("profondita", [
    f"<b>{ui('Apertura numerica (NA)')}</b>: die zweite auf dem Objektiv eingravierte Zahl (10×/<b>0,25</b>).",
    f"<b>{ui('Ingrandimento sul sensore')}</b>: Objektivvergrößerung × Faktor des Kameraadapters.",
    f"<b>{ui('Pixel del sensore (µm)')}</b>. Nikon D5600: <b>3,9 µm</b> (23,5 mm ÷ 6.000 Pixel).",
    f"<b>{ui('Sovrapposizione (%)')}</b> zwischen einer scharfen Schicht und der nächsten; 20–30 % ist ein guter Wert.",
    "<b>Ergebnis</b>: Schärfentiefe, empfohlene Schrittweite in µm und in Motorschritten.",
    f"<b>{ui('Usa come passo della sequenza')}</b>: übernimmt den Wert in Schritten in das Feld Schrittweite der Serie.",
])}
<h2>11.1 Die Formel</h2>
<p>Die App verwendet die Formel nach Berek, die in der Mikroskopie am weitesten verbreitet ist:</p>
<div class="formula">Schärfentiefe (µm) = {frac("λ · n", "NA²")} + {frac("n · e", "M · NA")}
<span class="lbl">λ = Wellenlänge = 0,55 µm (grünes Licht) · n = Brechzahl des Mediums zwischen Objektiv und Objektträger = 1 (Luft) ·
e = Pixelgröße des Sensors (µm) · M = Vergrößerung auf dem Sensor</span></div>
<p>Der erste Term ist die Grenze der Optik (Beugung), der zweite die des Sensors. Dann:</p>
<div class="formula">Schrittweite (µm) = Schärfentiefe × (1 − Überlappung) &nbsp;&nbsp;&nbsp; Schrittweite (Motorschritte) = {frac("Schrittweite (µm)", "Auflösung (µm/Schritt)")}</div>
<h3>Rechenbeispiel: Objektiv 10×/0,25, Nikon D5600, Adapter 1×</h3>
<div class="calc">erster Term    = 0,55 × 1 ÷ 0,25²       = 0,55 ÷ 0,0625 = 8,80 µm
zweiter Term   = 1 × 3,9 ÷ (10 × 0,25)  = 3,9 ÷ 2,5     = 1,56 µm
Schärfentiefe  = 8,80 + 1,56 = <b>10,36 µm</b>
Schrittweite bei 30 % Überlappung = 10,36 × 0,70 = <b>7,25 µm</b>
in Schritten, Beispiel A: 7,25 ÷ {num(UA, 4)} = 87,0 → <b>87 Schritte</b>   Beispiel B: 7,25 ÷ {num(UB, 4)} → <b>{max(1, round(dof(.25, 10, 3.9) * .7 / UB))} Schritte</b></div>
<h3>Typische Werte (D5600, Adapter 1×, Überlappung 30 %)</h3>
{table(["Objektiv", "Schärfentiefe (µm)", "Schrittweite (µm)", "Schritte, Beispiel A", "Schritte, Beispiel B"], dof_rows, right=(1, 2, 3, 4))}
<p style="font-size:9pt;color:#5a6b80">Beispiel A = {num(UA, 4)} µm/Schritt; Beispiel B = {num(UB, 4)} µm/Schritt (Abschnitt 10.3). Hinweis: {dof_note}</p>
<div class="box tip"><span class="t">Der Kameraadapter</span>Hat der Adapter einen anderen Faktor als 1 (zum Beispiel
0,5× oder 2,5×), multiplizieren Sie die Objektivvergrößerung mit diesem Faktor: 10× mit Adapter 0,5× = 5 auf dem Sensor.
Nur der zweite Term der Formel ändert sich, und der fällt bei schwachen Objektiven am stärksten ins Gewicht.</div>

<h2>11.2 Anfang, Ende und Anzahl der Aufnahmen</h2>
<ol class="steps">
<li>Schalten Sie das Live-View ein (am besten im Betrachter, vergrößert) und stellen Sie den Fokus <b>knapp über</b> den
  höchsten Teil des Objekts, der scharf werden soll: Klicken Sie neben <b>{ui('Inizio')}</b> auf <span class="ui">{ui('⌖ qui')}</span>.</li>
<li>Fahren Sie bis <b>knapp unter</b> den tiefsten Teil und klicken Sie neben <b>{ui('Fine')}</b> auf <span class="ui">{ui('⌖ qui')}</span>.</li>
<li>Geben Sie die Schrittweite ein (oder verwenden Sie <span class="ui">{ui('Usa come passo della sequenza')}</span>): Die App
  berechnet die Anzahl der Aufnahmen.</li>
</ol>
<div class="formula">Anzahl der Aufnahmen = {frac("|Ende − Anfang|", "Schrittweite")} + 1
<span class="lbl">abgerundet, plus eine letzte Aufnahme genau am Ende, wenn die Division nicht aufgeht</span></div>
<div class="calc">Beispiel: Anfang 24.000, Ende 26.000, Schrittweite 87
2.000 ÷ 87 = 22,99 → 22 + 1 = 23, plus die letzte Aufnahme bei 26.000 = <b>24 Aufnahmen</b>
Bereich = 2.000 × {num(UA, 4)} = <b>{num(2000 * UA, 1)} µm</b></div>
<p>Umgekehrt: Wenn Sie die <b>Anzahl der Aufnahmen</b> eingeben, berechnet die App die Schrittweite neu: Schrittweite =
Bereich ÷ (Aufnahmen − 1), gerundet auf ganze Schritte.</p>
<h2>11.3 Geschätzte Dauer</h2>
<p>Für jede Aufnahme addiert die App:</p>
<div class="formula">Wartezeit nach Bewegung + Pause nach Aufnahme + Spiegelverzögerung + Belichtungszeit + 1,5 s + {frac("Schrittweite", "400")} s</div>
<p>Dabei ist 1,5 s eine Schätzung der Zeit für Auslösung und Übertragung und Schrittweite ÷ 400 die Fahrzeit. Mit dem
Beispiel (1,5 s + 0,5 s + 0 + 1/60 s + 1,5 s + 0,22 s ≈ 3,7 s pro Aufnahme × 24 Aufnahmen) beträgt die Dauer etwa
<b>anderthalb Minuten</b>, wie auf dem Bildschirmfoto in Kapitel 7. Während die Serie läuft, wird die Schätzung mit den
tatsächlichen Zeiten aktualisiert.</p>
<div class="box warn"><span class="t">Die Wartezeit nach der Bewegung ist wichtig</span>Ein Mikroskop schwingt nach jeder
Bewegung eine Weile nach. Wenn Fotos verwackelt oder „doppelt“ aussehen, erhöhen Sie die Wartezeit (2–3 s) und bei
Spiegelreflexkameras die Spiegelverzögerung, bevor Sie nach anderen Ursachen suchen.</div>
""")

# 12
add(f"""
<h1><span class="n">12</span>Motor, manuelle Steuerung, Updates, Temperatur</h1>
<h2>{ui('Motore (firmware)')}</h2>
{fig("motore", [
    f"<b>{ui('Microstep')}</b>: {ui('Passo intero')}, 1/2 … 1/32 (siehe 10.2). Eine Änderung ändert den Maßstab der Positionen: Prüfen Sie danach die Grenzen erneut.",
    f"<b>{ui('Velocità')}</b> der Firmware: {ui('Lenta')}, {ui('Media')}, {ui('Veloce')}.",
    f"<b>{ui('Bobine alimentate a motore fermo')}</b>: Der Motor hält seine Position, wird aber warm.",
    f"<b>{ui('Inverti verso di rotazione')}</b>.",
    f"<b>{ui('Compensa il gioco IN')} / OUT</b>: Bei jeder Umkehr zu niedrigeren (IN) oder höheren (OUT) Positionen fährt die Firmware zusätzliche Schritte, ohne sie zu zählen, auch bei den Hardwaretasten.",
    "<b>Spiel IN / OUT</b> in Schritten, 0 bis 255 (siehe 10.5).",
    f"<b>{ui('Rileggi')}</b>: liest die Werte aus der Firmware.",
])}
<h2>{ui('Comandi manuali')}</h2>
{fig("comandi-manuali", [
    f"<b>Schrittgrößen</b> der Tasten {ui('Allontana')}/{ui('Avvicina')}: in Zehnerpotenzen bis 1.000, 10.000 oder 100.000 Schritte. Ein Getriebe braucht große Schrittgrößen.",
    f"<b>{ui('Tieni premuto per muovere senza fermarti')}</b>: Beim Loslassen bremst der Motor ab und hält an; er hält in jedem Fall an der Grenze an und, falls die Seite nicht mehr reagiert, nach etwa einer Sekunde.",
], layout="side")}
<h2>{ui('Aggiornamenti')}</h2>
{fig("aggiornamenti", [
    "Version der <b>App</b> und Ergebnis der letzten Prüfung.",
    "Version der <b>Firmware</b> auf dem Fokussierer.",
    f"<b>{ui('Aggiorna firmware')}</b>: etwa 20 Sekunden; die Einstellungen des Fokussierers bleiben erhalten. Ziehen Sie das Kabel nicht ab; falls etwas schiefgeht, wiederholen Sie den Vorgang einfach.",
    f"<b>{ui('Controlla ora')}</b>: sucht nach Updates der App.",
], layout="side")}
<p>Die App wählt selbst die passende Firmware für die Platine (myFocuserPro2 oder Ardufocus). Der <b>Ardufocus</b> startet
über das USB-Kabel nicht neu: Während der Aktualisierung fordert die App Sie auf, die <b>Reset-Taste</b> der Platine zu
drücken.</p>
<h2>{ui('Temperatura')}</h2>
{fig("temperatura", [
    "Aktuelle Temperatur des Fühlers.",
    "Verlauf der letzten 60 Minuten. Die Temperatur jeder Aufnahme wird in <code>sequence.json</code> gespeichert: nützlich, weil sich der Fokus durch Wärmeausdehnung verschiebt.",
], layout="side")}
""")

# 13
add(f"""
<h1><span class="n">13</span>Eine typische Sitzung, Schritt für Schritt</h1>
<h2>Einmalig (oder wenn sich die Mechanik ändert)</h2>
<ol class="steps">
<li><b>Mechanik</b>: Geben Sie die Daten ein und prüfen Sie die Auflösung mit einer Messung (Kapitel 10).</li>
<li><b>Richtung des Präparats</b> und <b>Grenzen</b>, mit den in die Firmware geschriebenen Grenzen (Kapitel 9).</li>
<li><b>Spiel</b>: Messen Sie es mit dem Live-View und entscheiden Sie, wo es ausgeglichen wird (Serie oder Firmware).</li>
<li><b>Presets</b>: Berechnen Sie für jedes Objektiv die Schrittweite aus der Schärfentiefe und speichern Sie ein Preset.</li>
</ol>
<h2>Bei jeder Sitzung</h2>
<ol class="steps">
<li>Schalten Sie Fokussierer und Kamera ein (Modus M), schließen Sie die Kabel an und öffnen Sie Focus Stack.</li>
<li>Verbinden Sie Fokussierer und Kamera im Bereich {ui('Sessione')}.</li>
<li>Stellen Sie Belichtungszeit, ISO und Format ein; machen Sie eine <b>Testaufnahme</b> und prüfen Sie sie im Betrachter bei 100 %.</li>
<li>Wählen Sie das <b>Preset</b> des Objektivs (oder die Schrittweite).</li>
<li>Suchen Sie mit dem <b>Live-View</b> und der Tastatur <b>Ende</b> und <b>Anfang</b> der Serie und klicken Sie jeweils auf {ui('⌖ qui')}.</li>
<li>Prüfen Sie die Übersicht: Anzahl der Aufnahmen, Bereich, Dauer, kein roter Hinweis.</li>
<li><b>{ui('▶ Avvia sequenza')}</b>. Berühren Sie das Mikroskop nicht: Vibrationen verderben die Aufnahmen.</li>
<li>Klicken Sie nach Ende der Serie auf <b>{ui('Apri in Helicon Focus')}</b>.</li>
</ol>
""")

# 14
add(f"""<h1><span class="n">14</span>Wenn etwas nicht funktioniert</h1>
<p>Das <b>{ui('Registro')}</b> (dritter Bereich) listet jede Verbindung, Bewegung, Aufnahme und jeden Fehler mit Uhrzeit
auf: Wenn etwas nicht funktioniert, lesen Sie es zuerst.</p>
""")
add(table(["Problem", "Was tun"], [
    ["Die Kamera verbindet sich nicht", "Beenden Sie Fotos, Vorschau, Digitale Bilder, NX Studio und EOS Utility; ziehen Sie das Kabel bei eingeschalteter Kamera ab und stecken Sie es wieder an; prüfen Sie, ob sie im Modus M ist und WLAN/SnapBridge ausgeschaltet sind."],
    ["Das Live-View startet nicht (Nikon D5600)", f"Moduswahlrad auf <b>M</b> (Motivprogramme können das Live-View über USB sperren), Karte eingelegt, Akku geladen, Bildkontrolle aus. Die genaue Meldung erscheint unten und im <b>{ui('Registro')}</b> („Live-View unterbrochen: …“): Darauf sollten Sie zuerst schauen. Prüfen Sie auch, ob Sie die neueste Version der App haben."],
    ["Das Live-View ist mit zwei offenen Fenstern langsam", "Aktualisieren Sie die App: Seit Version 1.0.6 erhalten Hauptfenster und Betrachter jedes Einzelbild."],
    ["Der Fokussierer erscheint nicht in der Portliste", "Klicken Sie nach dem Anschließen des Kabels auf ⟳; probieren Sie eine andere USB-Buchse oder ein anderes Kabel (manche Kabel laden nur)."],
    ["Der Motor brummt, dreht sich aber nicht, oder verliert Schritte", "Geschwindigkeit zu hoch für die Last oder Treiberstrom zu niedrig; prüfen Sie auch, ob die Riemenscheibe auf der Achse rutscht."],
    ["Die Abstände in µm stimmen nicht", "Wiederholen Sie die Messung aus Abschnitt 10.4; beim Ardufocus prüfen Sie den Mikroschritt."],
    ["Roter Alarm „außerhalb der Grenzen“", f"Eine Hardwaretaste hat den Fokussierer über eine Grenze hinaus bewegt. Bringen Sie die Position mit {ui('Allontana')}/{ui('Avvicina')} zurück in die Grenzen; um das zu verhindern, schreiben Sie die Grenzen in die Firmware (Kapitel 9)."],
    ["Die Serie startet nicht", "Lesen Sie den roten Hinweis in der Übersicht: Meist überschreitet die Serie, einschließlich Spielausgleich, die Grenzen."],
    ["Verwackelte oder doppelte Fotos", "Erhöhen Sie die Wartezeit nach der Bewegung und die Spiegelverzögerung; verwenden Sie Bulb oder den lautlosen Verschluss, wenn die Kamera das erlaubt."],
    [f"„{ui('Focus Stack è chiuso')}“ auf der Seite", "Die App wurde beendet: Öffnen Sie sie wieder, dann lädt sich die Seite von selbst neu."],
]))

# 15
add(f"""<h1><span class="n">15</span>Tastaturkurzbefehle</h1>
<div class="two">
<div class="keep"><h2 style="margin-top:0">Bereich {ui('Sessione')}</h2>
<table><tbody>
<tr><td><kbd>↑</kbd></td><td>Objektiv vom Präparat wegfahren</td></tr>
<tr><td><kbd>↓</kbd></td><td>Objektiv näher an das Präparat fahren</td></tr>
<tr><td><kbd>⇧</kbd> + <kbd>↑</kbd>/<kbd>↓</kbd></td><td>Schritt × 10</td></tr>
<tr><td><kbd>1</kbd> <kbd>2</kbd> <kbd>3</kbd> …</td><td>Schrittgröße: 1, 10, 100 …</td></tr>
<tr><td><kbd>Esc</kbd></td><td>STOP</td></tr>
</tbody></table></div>
<div class="keep"><h2 style="margin-top:0">{ui('Visualizzatore')}</h2>
<table><tbody>
<tr><td><kbd>←</kbd> <kbd>→</kbd></td><td>vorherige / nächste Aufnahme</td></tr>
<tr><td><kbd>L</kbd></td><td>Live-View ein / aus</td></tr>
<tr><td><kbd>−</kbd> <kbd>+</kbd></td><td>Zoom</td></tr>
<tr><td><kbd>0</kbd> oder <kbd>R</kbd></td><td>an Fenster anpassen</td></tr>
<tr><td><kbd>1</kbd></td><td>100 %</td></tr>
<tr><td><kbd>U</kbd></td><td>neueste folgen</td></tr>
<tr><td><kbd>K</kbd></td><td>Ansicht sperren</td></tr>
<tr><td><kbd>F</kbd></td><td>Vollbild</td></tr>
</tbody></table></div>
</div>
<p style="margin-top:8mm;color:#5a6b80;font-size:9pt">Focus Stack ist freie Software (MIT-Lizenz) ·
github.com/teoteo/focus-stack · Die Firmware basiert auf myFocuserPro2 von Robert Brown (MIT-Lizenz).</p>
""")
