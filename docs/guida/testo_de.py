"""Deutscher Text der Anleitung. Kein Modul zum Importieren: genera_guida.py führt ihn mit exec() in einem
Namensraum aus, der die gemeinsamen Helfer und Zahlen bereits enthält (fig, frac, table, num, diagram, VERSION,
ICON, IMG, UA, UB, GEAR17, um_step, dof, OBJ, APP). Der Text füllt die Liste H mit den HTML-Abschnitten.
"""
# ruff: noqa: F821  (die Namen kommen aus genera_guida.py)

META = {
    "lang": "de",
    "title": "Focus Stack — Bedienungsanleitung",
    "footer": "Bedienungsanleitung",
    "pdf": "DE Focus Stack - Anleitung.pdf",
}


def ui(s):
    """Deutscher Name eines App-Befehls: genau die Beschriftung der App (der italienische Text ist der Schlüssel)."""
    return APP.get(s, s)


# nome dell'opzione con l'apostrofo: in una costante, perché Python 3.11 non accetta virgolette annidate nelle f-string
COIL_HOLD = "Anche quando viene disconnesso o si spegne l'applicazione"


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

# schema «Come li usa la fusione» (7.6): etichette dello SVG, testo semplice (&lt; per <)
CALIB_LABELS = {
    "col_dark": 'MASTER-DARK',
    "col_stack": 'STAPEL DES MOTIVS',
    "col_flat": 'MASTER-FLAT',
    "dark": 'Darks · N Aufnahmen',
    "dark1": 'Deckel, gleiche ISO und Zeit',
    "mean": 'Mittelwert Pixel für Pixel',
    "D": 'D: Master-Dark',
    "flat": 'Flats · N Aufnahmen',
    "flat1": 'gleichmäßig, gleiche Optik',
    "flat_mean": 'Mittelwert − Flat-Darks',
    "norm": '÷ eigener Mittelwert',
    "F": 'F: normiertes Flat',
    "F1": '&lt; 1 am Rand und auf Staub',
    "frame": 'Jedes Bild I',
    "frame1": 'RAW, lineares Licht',
    "fusion": 'Ausrichtung und Fusion',
    "note1": 'Ohne Darks entfällt die Subtraktion,',
    "note2": 'ohne Flats die Division.',
}

# grafico d'esempio dell'analisi del sensore (7.6)
SENSOR_LABELS = {
    "title_dr": 'Dynamikumfang (Blendenstufen)',
    "title_rn": 'Ausleserauschen (Elektronen)',
    "unreliable": 'nicht verlässlich',
    "stops": 'Stufen',
    "dcg1": 'doppelte Verstärkung:',
    "dcg2": 'von 3,0 auf 1,2 e-',
    "dec": ',',
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
  <div class="shot-c"><img src="{IMG}/sessione.jpg" alt=""></div>
  <div class="meta"><span>App-Version {VERSION}</span><span>November 2026</span></div>
</section>
""")

add("""
<h1 style="break-before:auto">Inhalt</h1>
<div class="toc"><ol>
<li><span>1</span>Was ist Focus Stack?<em>Funktionsweise, was Sie brauchen</em></li>
<li><span>2</span>Installation, Start und Updates</li>
<li><span>3</span>Die Oberfläche im Überblick<em>die fünf Bereiche, die obere Leiste und die Anleitung</em></li>
<li><span>4</span>Fokussierer und Kamera verbinden<em>Einstellungen der Nikon D5600 und anderer Kameras</em></li>
<li><span>5</span>Der Fokussierer: Position, Bewegungen, STOP<em>Dauerbewegung in Abschnitten, der Schlitten, der nicht vorrückt</em></li>
<li><span>6</span>Kamera, Testaufnahme und Live-View</li>
<li><span>7</span>Die Stacking-Serie<em>Optikprofile, Makrofotografie, mehrere Aufnahmen pro Position, die Dateien des Stapels,
Kalibrierung (Darks, Flats, Belichtung), Fortschritt auf dem Smartphone</em></li>
<li><span>8</span>Der Betrachter<em>Zoom, Live-View, Autofokus auf einen Punkt, Inspektor</em></li>
<li><span>9</span>Sicherheitsgrenzen</li>
<li><span>10</span>Mechanik einrichten: die Berechnungen<em>Auflösung in µm pro Schritt, Kontrollmessung, Verfahrweg, Geschwindigkeit, Spiel</em></li>
<li><span>11</span>Die Schrittweite der Serie wählen<em>Schärfentiefe, Anzahl der Aufnahmen, Dauer</em></li>
<li><span>12</span>Motor, manuelle Steuerung, Autofokus, Updates, Temperatur</li>
<li><span>13</span>Eine typische Sitzung, Schritt für Schritt</li>
<li><span>14</span>Wenn etwas nicht funktioniert</li>
<li><span>15</span>Tastaturkurzbefehle</li>
</ol></div>
""")

# 1
add(f"""
<h1><span class="n">1</span>Was ist Focus Stack?</h1>
<p class="lead">Mit Focus Stack steuert Ihr Mac einen motorisierten Fokussierer, montiert am Feintrieb des Mikroskops
oder an einem Makroschlitten, und eine per USB angeschlossene Kamera. Die App führt automatisch Serien nach dem Muster <b>bewegen → warten →
auslösen</b> aus: Dutzende Fotos in verschiedenen Fokusebenen, bereit zum Verrechnen zu einem durchgehend
scharfen Bild mit <b>Helicon Focus</b> (oder einem ähnlichen Programm).</p>
<h2>Funktionsweise</h2>
<p>Die App Focus Stack startet auf dem Mac ein kleines Programm (den <i>Server</i>), das mit dem Fokussierer
(einer Arduino-Platine mit der Firmware myFocuserPro2) und mit der Kamera kommuniziert. Die Oberfläche öffnet
sich im <b>Fenster der App</b>: Es ist eine Webseite unter <code>http://localhost:8765</code>, nur von diesem Mac aus
erreichbar (sie lässt sich auch in einem Browser öffnen).</p>
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
<li>Einen Mac mit macOS 13 oder neuer (Intel) bzw. macOS 14 oder neuer (Apple Silicon).</li>
<li>Einen Fokussierer <b>myFocuserPro2</b> (Version mit DRV8825-Treiber) oder <b>Ardufocus</b> (Platine rev1 mit
  DRV8825), angeschlossen mit seinem USB-Kabel und mit Strom versorgt (12 V).</li>
<li>Eine Kamera von Nikon, Canon oder Sony mit USB-Kabel. Als Beispiel dient in dieser Anleitung eine <b>Nikon D5600</b>.</li>
<li>Am Mikroskop einen Adapter, der das Bild auf den Sensor projiziert (Fototubus, T2-Adapter oder Ähnliches). In der
  <b>Makrofotografie</b> ein Makroobjektiv (gegebenenfalls mit Zwischenringen oder Nahlinsen) und einen Schlitten, den
  der Fokussierer bewegt.</li>
</ul>
<div class="box warn"><span class="t">Unterstützte Fokussierer</span>Focus Stack funktioniert mit den Platinen
<b>myFocuserPro2</b> und <b>Ardufocus</b> mit der Firmware, die der App beiliegt. Ein myFocuserPro2 mit Original-Firmware
lässt sich sofort verbinden, und die App bietet an, sie mit einem Klick zu aktualisieren. Ein Ardufocus mit
Original-Firmware (Moonlite-Protokoll) wird dagegen nicht erkannt: Beim ersten Mal muss die Focus-Stack-Firmware von Hand
geladen werden (Anleitung im README unter github.com/teoteo/focus-stack); danach wird auch der Ardufocus aus der App
aktualisiert.</div>
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
<li>Beim Start öffnet Focus Stack sein Fenster und bleibt im Dock. Das Schließen des Fensters (<kbd>⌘W</kbd>)
  blendet es nur aus: Die App läuft weiter, und ein Klick auf das Symbol im Dock holt es zurück. Betrachter und
  Anleitung öffnen sich in eigenen Fenstern; Links zu externen Websites öffnen sich im Browser.</li>
<li>Zum Beenden: <kbd>⌘Q</kbd> in der App oder <span class="ui">Beenden</span> im Menü des Dock-Symbols.
  Läuft gerade eine Serie, fragt die App nach, bricht sie ab und hält den Motor an.</li>
<li>Während eines Stapels oder einer Kalibrierungsserie zeigt das Dock-Symbol einen <b>Fortschrittsbalken</b>.
  Ist sie fertig oder durch einen Fehler angehalten, während Sie eine andere App verwenden, kommt eine
  <b>Mitteilung</b>: Beim ersten Mal fragt macOS nach der Erlaubnis.</li>
</ul>
<h2>Updates</h2>
<p>Beim Start und danach alle 6 Stunden prüft die App, ob es eine neue Version gibt. Wenn ja, erscheint oben eine
Leiste mit <span class="ui">{ui("Aggiorna e riavvia")}</span>: Die App lädt die neue Version, beendet sich und öffnet
sich von selbst wieder. Dieselbe Prüfung können Sie von Hand unter
<span class="ui">{ui("Configurazione")} › {ui("Aggiornamenti")} › {ui("Controlla ora")}</span> starten.</p>
<p>Auch die <b>Firmware des Fokussierers</b> wird über die App aktualisiert (Kapitel 12): Ist die Firmware auf der
Platine älter als die in der App enthaltene, weist dieselbe Leiste darauf hin. Die Installation lohnt sich: Build 5
zum Beispiel macht die Bewegung durchgehend ohne Pausen und hält den Motor selbstständig an, wenn der Mac nicht mehr
kommuniziert (Kapitel 12).</p>
<h2>Sprache</h2>
<p>Die App spricht Italienisch, Englisch, Französisch, Deutsch und Spanisch. Mit <span class="ui">{ui("Automatica (lingua del sistema)")}</span>
folgt sie der Sprache von macOS und verwendet für andere Sprachen Englisch; unter
<span class="ui">{ui("Configurazione")} › {ui("Lingua")}</span> können Sie eine feste Sprache wählen. Die Auswahl gilt für
Oberfläche, Meldungen und Protokoll, und diese Anleitung gibt es in denselben Sprachen.</p>
""")

# 3
add(f"""
<h1><span class="n">3</span>Die Oberfläche im Überblick</h1>
<p>Die Seite hat fünf Bereiche, die Sie oben auswählen:</p>
<ul>
<li><b>{ui("Sessione")}</b>: die Arbeit am Mikroskop. Fokussierer, Serie, Kamera und letzte Aufnahme.</li>
<li><b>{ui("Ottica")}</b>: die <b>Profile</b> für Objektiv, Filter und Beleuchtung, für das Mikroskop oder für die
  Makrofotografie, die in die Daten jedes Stapels geschrieben werden, und der Schärfentiefe-Rechner (Kapitel 7.2, 7.3
  und 11).</li>
<li><b>{ui("Calibrazione")}</b>: die Belichtung der Lights und die Kalibrierungsbilder (Darks, Flats, Flat-Darks) für
  die Fusionssoftware (Kapitel 7.6).</li>
<li><b>{ui("Configurazione")}</b>: Grenzen, Mechanik, manuelle Steuerung, Motor, Fortschritt auf dem Smartphone,
  Sprache, Updates und Temperatur. Wird einmal eingestellt und danach nur selten angefasst.</li>
<li><b>{ui("Registro")}</b>: eine Liste mit Uhrzeit von allem, was in der Sitzung passiert ist. Hier sollten Sie als
  Erstes nachsehen, wenn etwas nicht funktioniert.</li>
</ul>
{fig("sessione", layout="full", caption=f"Der Bereich {ui('Sessione')}: links der Fokussierer, in der Mitte die Serie, rechts Kamera und letzte Aufnahme.")}
<h2>Obere Leiste</h2>
{fig("barra-superiore", [
    f"<b>Bereiche</b> {ui('Sessione')}, {ui('Ottica')}, {ui('Calibrazione')}, {ui('Configurazione')} und {ui('Registro')}.",
    f"<b>Verbindungsstatus</b>: {ui('Server')}, {ui('Focheggiatore')} und {ui('Fotocamera')}. Grün = verbunden, grau = getrennt, rot = Fehler.",
    "<b>Temperatur</b>, gemessen vom Fühler des Fokussierers.",
    "<b>?</b> öffnet diese <b>Anleitung</b> beim Kapitel des geöffneten Bereichs.",
    "<b>Design</b>, dunkel oder hell. Das dunkle Design ermüdet bei langen Sitzungen am Mikroskop weniger.",
], layout="full below-marks", anchors={1: "b", 2: "b", 3: "b", 4: "b", 5: "b"})}
<p>Unter der Leiste können zwei Streifen erscheinen: ein blauer für <b>Updates</b> und ein roter <b>Alarm</b>, zum
Beispiel wenn die Hardwaretasten den Fokussierer über eine Grenze hinaus bewegen.</p>
<div class="box tip"><span class="t">Die Anleitung in der App</span>Neben dem <b>?</b> oben hat fast jede Karte ein kleines
<b>?</b> neben dem Titel: Es öffnet diese Anleitung direkt an der Stelle, die diese Karte erklärt. Die Anleitung hat ein
Inhaltsverzeichnis und eine Suche (Taste <kbd>/</kbd>) und öffnet sich immer im selben Fenster.</div>
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
<p>Beim Öffnen <b>verbindet sich die App von selbst wieder</b> mit dem zuletzt verwendeten Fokussierer und der zuletzt
verwendeten Kamera, sofern sie am Mac angeschlossen sind: Es genügt, sie einmal mit <b>{ui('Connetti')}</b> verbunden zu
haben. Der Fokussierer wird nur dann wieder verbunden, wenn es derselbe USB-Adapter ist (ein anderes Gerät mit demselben
Portnamen bleibt unberührt), und das Verbinden bewegt den Motor nicht. Schlägt eine Verbindung fehl, bleibt eine Zeile
im Protokoll, und <b>{ui('Connetti')}</b> funktioniert wie immer.</p>
<h3>Einstellungen an der Kamera</h3>
{table(["Kamera", "Was einstellen"], [
    ["<b>Nikon D5600</b> und andere Nikon", "Moduswahlrad auf <b>M</b> (manuell). Im Wiedergabemenü die <b>Bildkontrolle</b> ausschalten. SnapBridge/WLAN und Bluetooth ausschalten, sie können die Verbindung belegen. Speicherkarte eingelegt lassen, Akku geladen (oder Netzadapter EH-5/EP-5A)."],
    ["Canon", f"Modus <b>M</b>. Die Aufnahme landet je nach <i>{ui('Destinazione')}</i> im Kameraspeicher oder auf der Karte. Für die Spiegelverzögerung im Menü die <b>Spiegelverriegelung</b> aktivieren."],
    ["Sony", "USB-Menü › <b>PC Remote</b>; Modus <b>M</b>. Damit die Fotos auf den Mac geladen werden, stellen Sie das Speicherziel auf <b>Nur PC</b> (MENU › Einstellung › PC-Fernbedienungseinstellungen › Standbild-Speicherziel). Für Live-View muss die Kamera dies im Modus PC Remote erlauben."],
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
    f"<b>{ui('Allontana')} / {ui('Avvicina')}</b>: Ein Klick bewegt um die gewählte Schrittgröße. Halten Sie die Taste gedrückt, fährt der Motor in Abschnitten weiter (Kapitel 12) und bremst beim Loslassen bis zum Stillstand ab.",
    f"<b>Zu Position fahren</b>: Geben Sie eine Schrittzahl ein und klicken Sie auf {ui('Vai')}.",
    "<b>STOP</b>: hält den Motor und eine laufende Serie sofort an. Tastatur: <kbd>Esc</kbd>. Nach STOP bleibt der Motor stehen, bis Sie wieder eine Taste drücken.",
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
<div class="box tip"><span class="t">Tastatur</span><kbd>↑</kbd> fährt weg, <kbd>↓</kbd> fährt näher: Ein kurzer Druck macht einen
Schritt, eine gedrückt gehaltene Pfeiltaste bewegt durchgehend bis zum Loslassen (wie die Tasten auf der Seite). <kbd>⇧</kbd> zusammen mit einem Pfeil multipliziert den Schritt mit 10, die Zifferntasten <kbd>1</kbd> <kbd>2</kbd>
<kbd>3</kbd> … wählen die Schrittgröße, <kbd>Esc</kbd> ist STOP. Die Tasten funktionieren im Bereich {ui('Sessione')},
auch während Sie das Live-View betrachten.</div>
<div class="box warn"><span class="t">Hardwaretasten</span>Die Tasten am Fokussierer bewegen den Motor an der App
vorbei. Die App überwacht sie und sendet STOP und einen Alarm, wenn die Position die Grenzen verlässt; für einen
vollständigen Schutz lesen Sie Kapitel 9. Drücken Sie sie während einer Serie, wird die Serie pausiert.</div>
<div class="box warn"><span class="t">Wenn der Schlitten bei kleinen Schritten nicht vorrückt</span>Ist
<span class="ui">{ui('Alimentazione bobine motore › Sempre quando connesso')}</span> ausgeschaltet ({ui('Configurazione')} › {ui('Motore (firmware)')}),
verliert der Motor bei jedem Halt die Kraft, die ihn in Position hält: Die Last (Gewicht der Kamera, eine Feder, der
Riemen) kann ihn zurückdrehen. Der Schrittzähler läuft weiter, der Schlitten bleibt aber stehen, und ein ganzer Stapel
entsteht in derselben Ebene. Während der Serie bestromt die App die Spulen selbst (Kapitel 12); für Handbewegungen um
wenige Schritte schalten Sie sie ein oder prüfen Sie im Live-View, ob sich das Bild tatsächlich bewegt.</div>
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
<p>Bei <b>Sony</b>-Kameras ändern sich Belichtungszeit und ISO in Stufen, wie beim Drehen des Rads: Ein weit
entfernter Wert kann einige Sekunden dauern. Bei der <b>A6400</b> reicht das ISO-Menü bis 102400, dem höchsten Wert, den
sie annimmt. Übernimmt die Kamera einen Wert nicht innerhalb von 12 Sekunden, weist die App darauf hin: USB-Kabel ab- und
wieder anstecken oder die Kamera aus- und einschalten.</p>
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
    f"Status: <b>{ui('LIVE')}</b> oder <b>{ui('SCATTO…')}</b> während einer Testaufnahme.",
    "Kameramodell. Doppelklick auf das Bild: Vollbild.",
], layout="stack")}
</div>
<p>Das Live-View liefert bis zu 15 Bilder pro Sekunde und ist der bequemste Weg, Anfang und Ende der Serie zu finden,
während Sie den Fokussierer mit der Tastatur bewegen. Wenn die Serie startet, bleibt das Live-View an,
während der Fokussierer zur Startposition zurückfährt, damit Sie ihn beobachten können; dort angekommen pausiert es
(der Spiegel muss herunterklappen und die Kamera normal auslösen) und schließt sich bei der ersten Aufnahme: Das Feld
zeigt wieder die letzte Aufnahme, auch im Betrachter. Nach dem Stapel schalten Sie es mit
<span class="ui">{ui('● Live')}</span> wieder ein. Bei Spiegelreflexkameras bleibt der Spiegel hochgeklappt, solange
das Live-View eingeschaltet ist. Ein im Hauptfenster eingeschaltetes Live-View startet auch im Betrachter, wenn dieser
geöffnet ist; <span class="ui">{ui('■ Ferma live')}</span> schaltet es in beiden Fenstern aus. Mit <span class="ui">{ui('◉ Scatto di prova')}</span>
bei eingeschaltetem Live-View zeigt das Feld die Aufnahme, und das Live-View startet von selbst wieder, sobald Sie den
Fokussierer bewegen, in der App oder mit seinen Tasten.</p>
<div class="box tip"><span class="t">Für präzises Fokussieren</span>Öffnen Sie das Live-View im <b>Betrachter</b>: Dort
können Sie auf 100 % und mehr vergrößern und zum gewünschten Detail verschieben (Kapitel 8).</div>
""")

# 7
TORNA = ui("Torna all'inizio a fine sequenza")
ING_OBIETTIVO = ui("Ingrandimento dell'obiettivo")
CAMBIO_INTERMEDIO = ui("Cambio d'ingrandimento intermedio")
AVANZ_RETE = ui("Mostra l'avanzamento sulla rete locale")
MOSTRA_ULTIMO = ui("Mostra l'ultimo scatto")
AGGIORNA_ULTIMO = ui("Aggiorna l'ultimo scatto")
add(f"""
<h1><span class="n">7</span>Die Stacking-Serie</h1>
<h2 style="margin-top:0">7.1 Die Serie einstellen</h2>
{fig("sequenza", [
    f"<b>Status</b>: {ui('Pronta')}, {ui('In corso')}, {ui('In pausa')}, {ui('Completata')}, {ui('Errore')}.",
    f"<b>{ui('Nome della pila')}</b>: Unterordner <code>Name_Datum-Uhrzeit</code>, Dateien <code>Name_0001</code>, <code>Name_0002</code> …",
    f"<b>{ui('＋ Nuova pila')}</b>: bereitet nach einem Stapel den nächsten vor (der Status wird wieder {ui('Pronta')}). Auch mit demselben Namen kommt jeder Stapel in einen neuen Ordner.",
    f"<b>Ordner</b> des Stapels, unter dem Namen: <code>…/Name_Datum-Uhrzeit</code> im Speicherordner (beim Darüberfahren erscheint der ganze Pfad). <span class='ui'>{ui('Scegli…')}</span> ändert den Speicherordner über das Finder-Fenster, <span class='ui'>{ui('Apri')}</span> zeigt ihn im Finder.",
    f"<b>{ui('Inizio')}</b> und <b>{ui('Fine')}</b> in Schritten. <span class='ui'>⌖ {ui('qui')}</span> übernimmt die aktuelle Position.",
    "<b>Schrittweite</b> zwischen zwei Aufnahmen, in Motorschritten (Kapitel 11).",
    f"<b>{ui('Numero di scatti')}</b>. Ändern Sie {ui('Inizio')}, {ui('Fine')} oder die Schrittweite, wird die Anzahl der Aufnahmen neu berechnet; ändern Sie die Anzahl der Aufnahmen, wird die Schrittweite neu berechnet. Ändert sich die Schrittweite von selbst, wird sie orange und zeigt <span class='ui'>↺ war …</span>: Ein Klick macht die Änderung rückgängig.",
    "<b>Optik und Filter (Profil)</b>: das Profil aus Objektiv, Filter und Beleuchtung, das in die Daten des Stapels geschrieben wird (7.2). <span class='ui'>Bearbeiten</span> öffnet es im Reiter Optik, der von selbst zum hier gewählten Profil wechselt (wenn er keine ungespeicherten Änderungen hat). Ohne Profil wird der Stapel als „kein Filter“ gespeichert. Die Wahl eines Profils setzt auch den darin gespeicherten Stapelschritt (mit „↺ war …“ zum Zurückgehen) und, bei einem Makroprofil mit Blende, die Blende der Kamera; weichen Blende oder Schritt später ab, meldet es die Zusammenfassung.",
    "<b>Übersicht</b>: Aufnahmen, Bereich in Schritten und µm, Schrittweite in µm und geschätzte Dauer. Ein Klick auf die Übersicht (▶ rechts) zeigt auch das verwendete Optikprofil und die Kalibrierung, die mit dem Stapel verknüpft wird. Liegt die Serie außerhalb der Grenzen, erscheint ein roter Hinweis und sie startet nicht.",
    "<b>Wartezeit nach Bewegung</b>, im einklappbaren Abschnitt: zum Abklingen der Vibrationen vor der Aufnahme (1–3 s am Mikroskop).",
    f"<b>{ui('Scatti per posizione')}</b>: wie viele Fotos an jeder Position entstehen (Standard 1). Bei mehreren Aufnahmen kann die Fusionssoftware sie mitteln und so das Rauschen verringern (7.4).",
    "<b>Pause nach Aufnahme</b>: zum Schreiben auf die Karte und Laden des Blitzes.",
    "<b>Spielausgleich</b>: Vor der ersten Aufnahme fährt der Motor so viele Schritte zurück und wieder vor, damit jede Aufnahme aus derselben Richtung angefahren wird.",
    f"<b>{ui('Modalità di scatto')}</b>: <i>{ui('Scarica sul Mac')}</i> (empfohlen), <i>{ui('Solo sulla scheda')}</i>, <i>Nur auslösen</i> (schneller: Speicherziel auf Karte).",
    f"<b>{TORNA}</b>.",
    f"<b>{ui('Suono sul Mac a fine sequenza')}</b>: ein heller Ton, wenn der Stapel abgeschlossen ist, ein tiefer, wenn er wegen eines Fehlers angehalten wurde oder von selbst pausiert hat.",
    f"<b>{ui('Preset')}</b>: speichert und lädt die Einstellungen der Serie, z. B. eines pro Objektiv.",
    "<b>Fortschritt</b>: erstellte Aufnahmen von allen, Balken, verbleibende Zeit; während der Serie erscheinen darunter Position und Meldungen.",
    f"<b>{ui('▶ Avvia sequenza')}</b>, <b>{ui('❚❚ Pausa')}</b>/<b>{ui('Riprendi')}</b> und <b>{ui('■ Interrompi')}</b>.",
    f"<b>{ui('Apri')}</b>, neben dem Zähler nach der Serie: öffnet den Ordner des Stapels mit den Fotos, <code>sequence.json</code> und <code>sequence.txt</code> (7.5).",
])}
<p>Wartezeit nach Bewegung, Aufnahmen pro Position, Pause nach der Aufnahme, Spiel, Modus, Rückkehr zum Anfang und Ton befinden sich im
einklappbaren Abschnitt <span class="ui">{ui('Tempi, gioco e scatti per posizione')}</span>. Sind die Spulen des Motors
ausgeschaltet und bestromt die App sie während der Serie nicht, erscheint darunter ein orangefarbener Hinweis
(Kapitel 12).</p>
<h2>Während die Serie läuft</h2>
{fig("sequenza-in-corso", [
    f"Der Status wechselt zu <b>{ui('In corso')}</b> (bernsteinfarben).",
    "Erstellte Aufnahmen von insgesamt, geschätzte Restzeit und aktuelle Position. Auf dem Verfahrbalken ändern die Markierungen der erstellten Aufnahmen ihre Farbe.",
    f"<b>{ui('❚❚ Pausa')}</b> hält nach der laufenden Aufnahme an; <b>{ui('■ Interrompi')}</b> beendet die Serie. Das <b>STOP</b> des Fokussierers hält zusätzlich sofort den Motor an.",
], layout="side narrow")}
<ul>
<li>Wenn Sie die <b>Hardwaretasten</b> des Fokussierers drücken, wird die Serie pausiert; beim Fortsetzen fährt sie
  zurück an die richtige Position und wiederholt die Aufnahme.</li>
<li><b>Wenn eine Aufnahme fehlschlägt</b>, versucht es die App nach 3 s erneut; beim zweiten Fehler verbindet sie die
  Kamera selbstständig neu und versucht es noch einmal. Reicht das nicht, wird die Serie <b>pausiert</b> (nicht
  abgebrochen), und die Meldung sagt, was zu prüfen ist: Bringen Sie die Kamera in Ordnung (Akku, Kabel, Karte) und
  klicken Sie auf <span class="ui">{ui('Riprendi')}</span>. Die App verbindet die Kamera neu, fährt an dieselbe Position
  und wiederholt die Aufnahme; die Fotos landen weiter im selben Ordner.</li>
<li><b>Der Mac geht nicht in den Ruhezustand</b>, solange die Serie läuft: Der Ruhezustand würde USB anhalten, und die
  Kamera wäre mitten im Stapel verschwunden. Der Bildschirm darf sich trotzdem ausschalten. Achtung: Wenn Sie den Deckel
  eines Notebooks ohne externen Monitor schließen, geht der Mac trotzdem in den Ruhezustand.</li>
<li>Sind die Spulen des Motors im Stillstand ausgeschaltet, bestromt die App sie für den ganzen Stapel und schaltet sie
  nach der Rückkehr zum Anfang wieder aus (Kapitel 12).</li>
<li>Die Felder der Serie sind gesperrt, solange die Serie läuft.</li>
<li>Jedes neue Foto erscheint in „{ui('Ultimo scatto')}“ und im Betrachter. Um den Stapel fern vom Mac zu verfolgen,
  gibt es den Fortschritt auf dem Smartphone (7.7).</li>
</ul>

<h2>7.2 Optik und Filter: die Profile</h2>
<p>Die Fusionssoftware arbeitet besser, wenn sie weiß, womit die Fotos aufgenommen wurden: Mit der Vergrößerung und der
Pixelgröße des Sensors kann sie die Tiefenkarte und die 3D-Ansicht in echten Mikrometern liefern. Diese Daten speichern
Sie im Bereich <b>{ui('Ottica')}</b> als benannte <b>Profile</b>, eines für jede Kombination aus Objektiv, Filter und
Beleuchtung (zum Beispiel „10× GFP“, „4× Hellfeld“), und wählen sie in der Serie aus (Nummer 8 in der Abbildung oben).
Jedes Profil ist vom Typ <b>{ui('Microscopio')}</b> oder <b>{ui('Macro fotografica')}</b> (7.3). Die Abbildung zeigt ein
Profil für das Mikroskop: ein 10×-Objektiv mit dem Vergrößerungswechsler Optovar 1,6× und die Kamera an einem T2-Adapter
ohne Linsen.</p>
{fig("ottica", [
    f"<b>{ui('Profilo da modificare')}</b>: Wählen Sie es, um seine Werte zu laden; <i>{ui('— nuovo profilo —')}</i> beginnt mit einem leeren Formular.",
    f"<b>{ui('Salva come nuovo profilo…')}</b>, in der Leiste, die oben erscheint: fragt nach einem Namen und speichert eine Kopie; das Ausgangsprofil bleibt unverändert.",
    f"<b>{ui('Elimina profilo')}</b>, nach einer Rückfrage. <b>{ui('Rinomina…')}</b> ändert den Namen auch in der Serie und in den Flats der Kalibrierungsbibliothek.",
    f"<b>{ui('Tipo di ottica')}</b>, die zwei Reiter oben im Bereich {ui('Ottica')}, die die Felder darunter ändern: <i>{ui('Microscopio')}</i> (Objektiv mit eingravierter Vergrößerung und NA) oder <i>{ui('Macro fotografica')}</i> (Fotoobjektiv, Zwischenringe und Nahlinsen, 7.3).",
    f"<b>{ui('Pixel del sensore (pixel pitch in µm)')}</b>. Nikon D5600: <b>3,9 µm</b> (23,5 mm ÷ 6.000 Pixel). Er steht im Datenblatt der Kamera, auf <b>digicamdb.com</b> (Fotokameras) oder in der Sensordatenbank von <b>AstroBin</b> (dedizierte Kameras, zum Beispiel nach IMX571 suchen).",
    f"<b>{ui('Adattatore / oculare di proiezione')}</b> zwischen Mikroskop und Kamera: Name und Faktor, zum Beispiel ein C-Mount-Adapter 0,5× oder 0,63×, ein Fotookular 2,5×, ein T2-Adapter ohne Linsen 1×. Leer = 1×.",
    f"<b>{CAMBIO_INTERMEDIO}</b>, falls das Stativ einen hat: Name und Faktor, zum Beispiel <i>Optovar</i> 1,25×, 1,6× oder 2×. Leer = 1×.",
    f"<b>{ui('Obiettivo (nome)')}</b>: ein frei wählbarer Name, so wie er auf dem Objektiv eingraviert ist.",
    f"<b>{ING_OBIETTIVO}</b>: die erste auf dem Objektiv eingravierte Zahl (<b>10</b>×/0,25).",
    f"<b>{ui('Apertura numerica (NA)')}</b>: die zweite auf dem Objektiv eingravierte Zahl (10×/<b>0,25</b>).",
    f"<b>{ui('Immersione')}</b>: {ui('Aria (a secco)')}, {ui('Acqua')}, {ui('Olio')}, {ui('Glicerina')} oder {ui('Silicone')}.",
    f"<b>{ui('µm per pixel sul campione, misurati (facoltativo)')}</b> mit einem Objektmikrometer: Falls vorhanden, hat dieser Wert Vorrang vor der Berechnung.",
    f"<b>{ui('Ingrandimento sul sensore')}</b> = Objektiv × Zwischenvergrößerung × Adapter (hier 10 × 1,6 × 1 = 16×) und <b>Maßstab am Präparat</b>: der gemessene Wert oder Sensorpixel ÷ Vergrößerung. Mit einer Messung erscheint auch die <b>tatsächliche Vergrößerung</b> (Sensorpixel ÷ gemessene µm pro Pixel), die enthält, was die Kette nicht angibt, etwa den Sensorabstand oder den Fototubus; bei großer Abweichung erscheint neben dem Adapter der <i>aus der Messung vorgeschlagene</i> Faktor: Ein Klick trägt ihn ins Feld ein.",
    f"<b>{ui('Filtro')}</b>: <i>{ui('Non indicato')}</i> (unbekannt), <i>{ui('Nessun filtro')}</i> oder <i>{ui('Filtro montato')}</i>.",
    f"<b>{ui('Nome')}</b> und <b>{ui('Tipo')}</b> des Filters: {ui('Passa banda')}, {ui('Long pass')}, {ui('Short pass')}, {ui('Neutro (ND)')}, {ui('Polarizzatore')}, {ui('Altro')}.",
    f"<b>{ui('Centro (nm)')}</b> und <b>{ui('Larghezza di banda (nm)')}</b> bei einem Bandpass; bei Lang- und Kurzpass die Kantenwellenlänge.",
    f"<b>{ui('Illuminazione')}</b> (freier Text, mit Vorschlägen), <b>{ui('Intensità (%)')}</b> und <b>{ui('Temperatura di colore (K)')}</b> (zum Beispiel 4000 K für neutrales Licht).",
    f"Freie <b>{ui('Note')}</b>, die in die Daten des Stapels geschrieben werden.",
    f"<b>{ui('Salva profilo')}</b>, in der Leiste <i>{ui('Modifiche non salvate')}</i>, die oben erscheint, sobald Sie einen Wert ändern, zusammen mit <b>{ui('Annulla')}</b> (zurück zum gespeicherten Profil): überschreibt das gewählte Profil; bei einem neuen Profil fragt die App nach dem Namen.",
    "Das geöffnete <b>Profil</b>; bernsteinfarben, wenn es ungespeicherte Änderungen gibt.",
    "<b>Inhaltsverzeichnis</b> der Bereiche, mit Suche: Ein Klick springt zum Bereich. Mit Mikroskop oder Makro zeigt es nur die Bereiche dieser Art.",
    "<b>Übersicht</b>, beim Tippen immer sichtbar: Vergrößerung auf dem Sensor, Maßstab auf der Probe (gemessen oder berechnet, mit der Abweichung), Schärfentiefe und empfohlener Schritt.",
], layout="full")}
<p>Ein leeres Feld bedeutet „nicht angegeben“ und wird nicht geschrieben. Wählen Sie in der Serie kein Profil, wird der
Stapel als <b>ohne Filter</b> und ohne optische Daten vermerkt. Dieselben Werte für NA, Vergrößerung und Pixelgröße
verwendet auch der Schärfentiefe-Rechner (Kapitel 11). Denken Sie daran, das Profil zu wechseln, wenn Sie Objektiv oder
Filter wechseln: Die Übersicht der Serie zeigt immer an, was geschrieben wird.</p>

<h2>7.3 Makrofotografie</h2>
<p>Mit dem Typ <span class="ui">{ui('Macro fotografica')}</span> beschreibt das Profil ein Fotoobjektiv statt eines
Mikroskopobjektivs. Die App berechnet daraus die Vergrößerung auf dem Sensor, die effektive Blende und eine äquivalente NA,
die genau wie am Mikroskop für den Maßstab in µm und die Schärfentiefe verwendet werden.</p>
{fig("ottica-macro", [
    f"<b>{ui('Macro fotografica')}</b>: zeigt die Felder des Fotoobjektivs anstelle derer des Mikroskops.",
    f"<b>{ui('Cerca nel database')}</b>: Geben Sie einen Teil des Namens ein (zum Beispiel „90 macro“) und wählen Sie das Objektiv. Die Datenbank ist die von <b>Lensfun</b> (1.162 Objektive), ergänzt um einige spezielle Makroobjektive, die Lensfun nicht hat (Canon MP-E 65, Laowa 25/90/100, OM 90), und um Ihre persönliche Liste.",
    f"<b>{ui('Marca')}</b> und <b>{ui('Modello')}</b>: von der Suche ausgefüllt oder von Hand eingegeben.",
    "<b>Brennweite</b> und <b>größte Blendenöffnung</b>. Bei einem Zoom geben Sie die verwendete Brennweite an.",
    f"<b>{ui('＋ Aggiungi al mio elenco')}</b>: speichert ein Objektiv, das die Datenbank nicht kennt, damit die Suche es wiederfindet.",
    "<b>Abbildungsmaßstab des Objektivs</b>, abgelesen auf seiner Skala bei der verwendeten Entfernung: 1 = 1:1, 0,5 = 1:2, 0 = auf unendlich fokussiert.",
    "<b>Eingestellte Blende</b> am Objektiv.",
    "<b>Zwischenringe / Balgen</b>: die gesamte zwischen Objektiv und Kamera hinzugefügte Länge, in mm.",
    "<b>Nahlinsen</b> vor dem Objektiv (Raynox und ähnliche), bis zu 3, mit ihrer Brechkraft in Dioptrien.",
    "<b>Ergebnis</b>: Vergrößerung auf dem Sensor, effektive Blende, äquivalente NA und Maßstab am Präparat in µm pro Pixel.",
], layout="full")}
<p>Es sind die Formeln der fotografischen Nahoptik, mit <i>f</i> = Brennweite, <i>m₀</i> = Abbildungsmaßstab des
Objektivs, <i>e</i> = Zwischenringe in mm, <i>D</i> = Dioptrien der Nahlinsen und <i>N</i> = eingestellte Blende:</p>
<div class="formula">m₁ = m₀ + {frac("e", "f")} &nbsp;&nbsp;&nbsp; Vergrößerung m = m₁ + {frac("ΣD", "1000")} · f · (1 + m₁)
<span class="lbl">effektive Blende = N · (1 + m₁) &nbsp;·&nbsp; äquivalente NA = {frac("m", "2 · N · (1 + m₁)")}</span></div>
<div class="calc">Beispiel: Makroobjektiv 90 mm bei 1:2 (m₀ = 0,5), f/8, keine Zwischenringe, Nahlinse mit +8 Dioptrien
m₁ = 0,5 + 0 = 0,5
m  = 0,5 + 8 ÷ 1000 × 90 × (1 + 0,5) = 0,5 + 1,08 = <b>1,58×</b>
effektive Blende = 8 × 1,5 = <b>f/12</b>      äquivalente NA = 1,58 ÷ (2 × 8 × 1,5) = <b>0,066</b>
mit einem Sensor von 3,9 µm: 3,9 ÷ 1,58 = <b>2,47 µm pro Pixel</b> am Präparat</div>
<p>Wie am Mikroskop hat ein mit einem Millimeterlineal gemessener Wert (Feld <span class="ui">µm pro Pixel am Präparat,
gemessen</span>) Vorrang vor der Berechnung, die mit Nahlinsen nur eine Schätzung ist. In der Makrofotografie beträgt die
Schärfentiefe oft Dutzende oder Hunderte µm: Ist ein Schritt des Schlittens länger als die empfohlene Schrittweite, weist
der Bereich {ui('Ottica')} darauf hin und schlägt den passenden Mikroschritt vor (Kapitel 10.2).</p>

<h2>7.4 Mehrere Aufnahmen pro Position</h2>
<p>Ist <span class="ui">{ui('Scatti per posizione')}</span> größer als 1, löst die Kamera an jeder Position mehrmals aus,
ohne dass sich der Motor zwischen den Aufnahmen bewegt: Die Wartezeit gegen Vibrationen gibt es nur nach der Bewegung,
zwischen den Aufnahmen nur die Pause nach der Aufnahme. Die Fusionssoftware mittelt die Aufnahmen: Bei 4 Aufnahmen
halbiert sich das Rauschen. Die Dateien heißen <code>stack_0001_1</code>, <code>stack_0001_2</code> …; bei nur einer
Aufnahme bleibt es bei <code>stack_0001</code>, <code>stack_0002</code> … Die Übersicht zeigt Positionen × Aufnahmen
und die richtige Dauer.</p>

<h2>7.5 Die Dateien des Stapels</h2>
<p>Im Ordner des Stapels schreibt die App neben die Fotos zwei Dateien. Sie werden nach jeder Aufnahme neu geschrieben
und sind daher auch gültig, wenn die Serie abgebrochen wird. Die Fotos selbst werden nie verändert.</p>
<ul>
<li><code>sequence.json</code>: alle Daten für die <b>Fusionssoftware</b>: Position jeder Aufnahme in Schritten und µm,
  Uhrzeit, Temperatur, Führung, Kamera, Optikprofil (Mikroskop oder Makro), Filter, Beleuchtung und die passenden
  Kalibrierungssätze (7.6). Das Format ist in <code>docs/sequence-json.md</code> auf GitHub beschrieben.</li>
<li><code>sequence.txt</code>: eine <b>lesbare Übersicht</b> in der Sprache der App. Zum Beispiel:</li>
</ul>
<div class="calc long">{SEQ_TXT}</div>

<h2>7.6 Kalibrierung: Belichtung, Darks und Flats</h2>
<p>Der Bereich <b>{ui('Calibrazione')}</b> bereitet vor, was die Fusionssoftware zum Korrigieren der Fotos braucht: eine
passende Belichtungszeit für den Stapel und die <b>Kalibrierungsbilder</b>. Die Pegel werden an den <b>echten RAWs</b>
gemessen, ohne Farbumwandlung, mit <i>fs-rawstat</i>, einem kleinen, in der App enthaltenen Programm auf Basis von
LibRaw; ausgebrannte Pixel werden Kanal für Kanal erkannt. Mit dem Simulator sind die Pegel nur eine Schätzung.</p>
<h3>{ui('Esposizione dei light')}</h3>
{fig("calibrazione-esposizione", [
    f"<b>{ui('Misura su')}</b>: <i>{ui('Luci (99,5° percentile)')}</i> (die hellsten Bildteile) oder <i>{ui('Media (livello medio)')}</i>.",
    "<b>Zielpegel</b> in % der Sensorsättigung, zum Beispiel 85 % auf den Lichtern.",
    f"<b>{ui('Calcola e imposta il tempo')}</b>: Die App macht einige Testaufnahmen, misst die RAWs und stellt die Belichtungszeit ein, wobei sie Zeiten ohne ausgebrannte Pixel bevorzugt. ISO und Blende bleiben wie eingestellt.",
    "<b>Ergebnis</b>: gewählte Zeit, gemessener Pegel und ausgebrannte Pixel.",
], layout="side")}
<p>Fahren Sie den Fokussierer in die Mitte des Stapels und schalten Sie die Beleuchtung wie für die Serie ein. Die
Belichtung wird <b>einmal vor dem Stapel</b> berechnet: Sie zwischen den Ebenen zu ändern, würde die Helligkeit der
Bilder unterschiedlich machen.</p>
<h3>{ui('Frame di calibrazione')}</h3>
{fig("calibrazione-frame", [
    f"<b>{ui('Tipo di frame')}</b>: <i>{ui('Dark')}</i> (Objektivdeckel drauf, gleiche ISO und Zeit wie die Lights: thermisches Rauschen und Hotpixel), <i>{ui('Flat')}</i> (gleichmäßig beleuchtetes Feld, gleiche Optik und Blende: Vignettierung und Staub) oder <i>{ui('Dark dei flat')}</i> (Objektivdeckel, gleiche ISO und Zeit wie die Flats).",
    f"<b>{ui('Fotogrammi')}</b>, die aufgenommen werden, zum Beispiel 16.",
    "<b>Flat-Pegel</b> in % der Sättigung, zum Beispiel 50 %: Die Belichtungszeit findet die App selbst.",
    "<b>Fortschritt</b>: aufgenommene Bilder und gemessener Pegel.",
    f"<b>{ui('▶ Scatta i frame')}</b> und <b>{ui('■ Interrompi')}</b>.",
], layout="side")}
<ul>
<li><b>{ui('Dark')}</b>: Objektivdeckel drauf und Sucherokular abgedeckt, gleiche ISO und Belichtungszeit (oder Bulb) wie
  die Lights, möglichst bei derselben Temperatur.</li>
<li><b>{ui('Flat')}</b>: gleichmäßig beleuchtetes Feld (ein leerer Objektträger, ein Diffusor), mit demselben Optikprofil
  und derselben Blende wie der Stapel: Sie korrigieren Vignettierung und Staub nur, wenn die Optik dieselbe ist.</li>
<li><b>{ui('Dark dei flat')}</b>: direkt nach den Flats, mit Objektivdeckel: Die App übernimmt selbst ISO und Zeit der
  neuesten Flats.</li>
</ul>
<h3>Wie die Fusion sie verwendet</h3>
<p>Focus Stack nimmt die Frames auf und trägt sie in die <code>sequence.json</code> des Stapels ein; die Korrektur
übernimmt die Fusionssoftware (zum Beispiel Focus Fusion) an jedem Bild, bevor sie es ausrichtet. Das Dark wird
<b>abgezogen</b>: Es entfernt thermisches Rauschen und heiße Pixel. Durch das Flat wird <b>geteilt</b>: Es gibt das
Licht zurück, das Vignettierung und Staubschatten weggenommen hatten.</p>
{calib_diagram(CALIB_LABELS)}
{fig("calibrazione-esempio", [
    '<b>Normiertes Flat</b> F, mit verstärktem Kontrast: Die Ecken erhalten 70% des Lichts der Mitte, und jeder Punkt ist ein Staubkorn auf dem Sensor.',
    '<b>Ein Bild des Stapels</b> unverändert: Der Hintergrund wird zu den Ecken hin dunkler (64% der Mitte), und derselbe Staubfleck ist auf dem Hintergrund zu sehen (Ausschnitt 4× vergrößert).',
    '<b>Dasselbe Bild korrigiert</b>, (I − D) ÷ F, mit derselben Darstellung: Ecken bei 94% der Mitte, der Fleck ist verschwunden.',
], layout="full", caption='Ein Bleistift: Sony A6400 mit dem 70-350 mm bei 350 mm, Nahlinse +8 Dioptrien, f/20, ISO 400, 1/20 s; 10 Flats, 10 Darks und 10 Flat-Darks.')}
<h3>Die {ui('Libreria di calibrazione')}</h3>
{fig("calibrazione-libreria", [
    f"<b>Ordner</b> der Bibliothek: <code>_calibrazione</code> im Ordner der Stapel. <span class='ui'>{ui('Apri nel Finder')}</span> zeigt ihn an.",
    "<b>Passende Sätze</b> für einen Stapel, der jetzt gestartet würde, mit der aktuellen Kamera und den aktuellen Einstellungen.",
    "<b>Tabelle der Sätze</b>: Typ, Datum, Kamera, ISO, Zeit, Optikprofil, Bilder, mittlerer Pegel und Temperatur. <span class='ui'>Löschen</span> verschiebt den Satz in den Papierkorb des Mac (im Finder wiederherstellbar). Mit den Kästchen vor dem Typ wählen Sie mehrere aus (das Kästchen im Kopf wählt alle) und löschen sie zusammen mit <span class='ui'>Ausgewählte löschen</span>: Zur Sicherheit muss das Wort LÖSCHEN eingegeben werden.",
], layout="full")}
<p>Jeder Satz hat seinen eigenen Ordner mit den Bildern und einer <code>calibration.json</code> (Format in
<code>docs/calibration-json.md</code>). Beim Start eines Stapels verweist <code>sequence.json</code> auf die neuesten
passenden Sätze: für Darks gleiche Kamera, ISO und Zeit; für Flats zusätzlich dasselbe Optikprofil. Die Bilder werden
nicht kopiert. Es ist dieselbe Bibliothek, die <b>Focus Fusion</b> verwendet und in der es seine „Master“ ablegt.</p>
<p><b>Aufnahmen, die aus der Reihe fallen.</b> Ein Satz taugt nur, wenn sich seine Aufnahmen gleichen: ein Flat nach
erloschenem oder verändertem Licht oder ein Dark ohne Deckel verdirbt den Mittelwert. Während der Serie vergleicht die
App jede Aufnahme mit den bisherigen und meldet eine stark abweichende (Flats mehr als ±10 % vom Pegel der übrigen,
Darks mehr als einen Punkt heller) sofort in der Karte und im Protokoll, solange man noch anhalten kann. In der
Tabelle zeigt der Satz neben der Zahl der Aufnahmen ⚠ und wie viele (beim Darüberfahren welche); auch die Übersichten
weisen darauf hin. Besser den Satz neu aufnehmen: die Aufnahmen bleiben im Ordner, markiert in <code>calibration.json</code>.</p>

<p>Rechts bleibt die <b>Übersicht</b> sichtbar, während Sie im Bereich arbeiten.</p>
{fig("calibrazione-riepilogo", [
    f"<b>{ui('Per la prossima pila')}</b>: für Darks, Flats und Flat-Darks ein ✓ mit dem Datum des Satzes, der verwendet würde, oder <i>{ui('manca')}</i> in Orange. Fehlt ein Satz, erscheint auch neben <i>{ui('Libreria')}</i> im Inhaltsverzeichnis ein oranger Punkt.",
    "Aktuelle <b>Temperatur</b> des Fühlers.",
    "Verlauf der <b>letzten 60 Minuten</b>: Vergleichen Sie ihn mit der Temperatur der Darks in der Tabelle.",
    f"<b>{ui('Sensore')}</b>: erwarteter Dynamikumfang beim eingestellten ISO, mit dem Diagramm (empfohlene ISO-Werte grün, der aktuelle eingekreist). Erscheint nach der Sensoranalyse.",
], layout="side narrow")}

<h3>{ui('Analisi del sensore')}</h3>
<p>Einmal pro Kamera misst <b>{ui('Calibrazione')} › {ui('Sensore')} › {ui('Analisi del sensore')}</b>, wie sich der Sensor
bei jedem ISO verhält: <b>Verstärkung</b> (wie viele Elektronen eine RAW-Einheit wert ist), <b>Ausleserauschen</b>,
<b>Full-Well-Kapazität</b> (wie viel Licht ein Pixel sammelt, bevor er sättigt) und <b>Dynamikumfang</b> in
Blendenstufen. Für 19 ISO-Werte dauert es etwa 20 Minuten.</p>
<ol>
<li><b>{ui('Prepara')}</b>: vor dem Objektiv der beleuchtete Diffusor wie für die Flats; Kamera in RAW und manueller Fokus.
  Wählen Sie den ISO-Bereich (100 bis 6400 in Drittelstufen ist ein guter Anfang) und die Aufnahmen pro ISO (2 genügen).</li>
<li><b>Flat</b>: Für jeden ISO findet die App die Zeit für ein Flat bei 50% und nimmt auf. ISO-Werte, die die Kamera ablehnt, erscheinen durchgestrichen.</li>
<li><b>{ui('Tappo')}</b>: Die App hält an und bittet, den Objektivdeckel aufzusetzen; drücken Sie dann <i>{ui('Ho messo il tappo: scatta i dark')}</i>.</li>
<li><b>Dark</b>: gleiche ISO-Werte und Zeiten, im Dunkeln.</li>
<li><b>{ui('Risultato')}</b>: zwei Diagramme, Dynamikumfang und Ausleserauschen pro ISO, und die empfohlenen ISO-Werte.</li>
</ol>
{fig("calibrazione-sensore", [
    '<b>Schritte</b> des Ablaufs: der laufende blau, die erledigten mit Häkchen.',
    '<b>Diagramme</b> von Dynamikumfang und Ausleserauschen pro ISO: empfohlene ISO-Werte grün, der an der Kamera eingestellte ISO eingekreist, grauer Bereich und gestrichelte Linie für nicht verlässliche ISO-Werte.',
    '<b>Empfohlen</b>, <b>Empfohlen bei wenig Licht</b> und <b>Besser vermeiden</b>, jeweils mit Begründung.',
    '<b>Tabelle</b>: pro ISO die Zeit der Flats, der Umfang, das Rauschen, die Full-Well-Kapazität und die Verstärkung.',
    '<b>CSV exportieren</b> speichert die Tabelle in „Downloads“; <b>Analyse wiederholen</b> beginnt wieder bei der Vorbereitung.',
], layout="full")}
<figure class="shot">{sensor_chart(SENSOR_LABELS)}<figcaption>Sensoranalyse einer Sony A6400: 19 ISO-Werte von 100 bis 102400, je 2 Flats und 2 Darks. ISO 400 eingekreist.</figcaption></figure>
<p>So liest man es, am Beispiel einer Sony A6400. ISO 100 hat den größten Umfang, 13,3 Blendenstufen, weil er das meiste Licht
sammelt. Bei ISO 400 schaltet der Sensor auf eine zweite Verstärkung, und das Ausleserauschen sinkt von 3 auf
1,2 Elektronen: 12,9 Blendenstufen mit viermal kürzeren Zeiten. Darüber sinkt das Rauschen nicht mehr, und jede
Verdopplung des ISO kostet eine Blendenstufe: Fehlt Licht, bleiben Sie bei 400 und hellen später auf. ISO 160 bis 320
geben weniger Umfang als ISO 400 bei längeren Zeiten: besser vermeiden. Über 3200 filtert die Kamera das Rauschen schon im
RAW, und diese Werte sind als nicht verlässlich markiert.</p>
<p>Das Ergebnis wird als <b>Sensorprofil</b> der Kamera in <code>_calibrazione/_sensore</code> gespeichert. Die Übersicht der
Kalibrierung und die der Serie (wenn man ihre Details öffnet) zeigen den erwarteten Dynamikumfang beim eingestellten ISO, mit dem Punkt im Diagramm;
jeder Stapel schreibt die Werte seines ISO in seine <code>sequence.json</code> (<code>"sensor"</code>), die Focus Fusion
nutzen kann. Die Bilder der Analyse liegen im selben Ordner, außerhalb der Bibliothek der Sätze, und werden nie für einen
Stapel gewählt. Wiederholen Sie die Analyse, wenn Sie die Kamera wechseln oder ihre Firmware aktualisieren.</p>

<h2>7.7 {ui('Avanzamento da smartphone')}</h2>
<p>Um einen langen Stapel fern vom Mac zu verfolgen, schalten Sie unter
<span class="ui">{ui('Configurazione')} › {ui('Avanzamento da smartphone')}</span> eine <b>schreibgeschützte</b> Seite im
lokalen Netzwerk ein.</p>
{fig("smartphone", [
    f"<b>{AVANZ_RETE}</b>: schaltet die Seite ein (sie ist aus, bis Sie sie aktivieren).",
    "<b>QR-Code</b>: Scannen Sie ihn mit der Kamera des Smartphones, das im selben WLAN wie der Mac sein muss.",
    f"<b>{ui('Nuovo link')}</b>: ändert den Code des Links; der alte funktioniert nicht mehr.",
], layout="side")}
{fig("smartphone-pagina", [
    "Name des Stapels, Status, erstellte Aufnahmen, verbleibende Zeit und voraussichtliche Endzeit.",
    f"<b>{ui('Avvisami con un suono a fine sequenza')}</b>: Das Smartphone gibt einen Ton aus (und vibriert unter Android), wenn der Stapel fertig ist, wegen eines Fehlers anhält oder von selbst pausiert; solange der Ton aktiv ist, bleibt der Bildschirm an.",
    f"<b>{MOSTRA_ULTIMO} / {AGGIORNA_ULTIMO}</b>: das letzte Foto in voller Breite.",
    f"Die letzte Aufnahme: mit zwei Fingern aufziehen, ziehen oder doppelt tippen zum Vergrößern. Beim Vergrößern wird ein hochaufgelöster Ausschnitt geladen; der Zoom bleibt beim Wechsel zur nächsten Aufnahme erhalten, um dieselbe Stelle zu vergleichen. <span class='ui'>{ui('Adatta')}</span> kehrt zum ganzen Bild zurück.",
], layout="side narrow", width="70%")}
<p>Über die Seite <b>lässt sich nichts steuern</b>, und ohne den Code im Link wird nichts angezeigt. Beim ersten Mal fragt
macOS, ob eingehende Verbindungen erlaubt werden sollen: Antworten Sie <b>Erlauben</b>. Für den Ton lassen Sie die Seite
im Vordergrund geöffnet: Solange der Ton aktiv ist, lässt die Seite den Bildschirm eingeschaltet. Sperrt sich das Telefon trotzdem,
stellen Sie die automatische Sperre während des Wartens auf <b>Nie</b> (iPhone: Einstellungen › Anzeige &amp; Helligkeit ›
Automatische Sperre): Ein gesperrtes Telefon hält Webseiten an, und der Ton kommt nicht an.</p>
""")

# 8
EVIDENZIA = ui("Evidenzia sull'immagine")
add(f"""
<h1><span class="n">8</span>Der Betrachter</h1>
<p>Sie öffnen ihn mit <span class="ui">{ui('Apri visualizzatore ↗')}</span> oder mit einem Klick auf die letzte
Aufnahme. Er ist ein eigenes Fenster: Bei zwei Monitoren öffnet er sich von selbst im Vollbild auf dem anderen
(abschaltbar unter <span class="ui">{ui('Configurazione')} › {ui('Visualizzatore')}</span>). Er zeigt die Fotos in voller
Auflösung (auch RAW-Dateien, die direkt umgewandelt werden) mit Zoom und Verschieben sowie das Live-View der Kamera.</p>
{fig("visualizzatore", [
    "<b>◀ ▶</b> vorherige und nächste Aufnahme (Pfeiltasten <kbd>←</kbd> <kbd>→</kbd>).",
    "<b>Zähler des Stapels</b>: während der Serie die zuletzt gemachte Aufnahme von der Gesamtzahl (zum Beispiel 75/115, <i>läuft</i>), danach <i>abgeschlossen</i>; bei Testaufnahmen ihre Anzahl. Daneben der Dateiname und darunter Nummer der Aufnahme, Position, Temperatur und Uhrzeit. Während des Stapels zeigt eine blaue Linie am oberen Fensterrand den Fortschritt.",
    f"<b>{ui('● Live')}</b> (<kbd>L</kbd>): das Live-View im selben Fenster, mit Zoom und Verschieben.",
    "<b>Zoom</b> − und + (<kbd>−</kbd> <kbd>+</kbd>) und die Vergrößerungsstufe.",
    f"<b>{ui('Adatta')}</b> (<kbd>0</kbd>), <b>100 %</b> (<kbd>1</kbd>: ein Sensorpixel = ein Bildschirmpixel), <b>{ui('Reset')}</b> (<kbd>R</kbd>).",
    f"<b>{ui('Segui ultimo')}</b> (<kbd>U</kbd>): zeigt jede neue Aufnahme automatisch an. Wie die beiden folgenden Schaltflächen ist es ein Symbol, hervorgehoben, wenn es aktiv ist; beim Öffnen ist es aktiv.",
    f"<b>{ui('Blocca vista')}</b> (<kbd>K</kbd>): behält Zoom und Position beim Wechsel der Aufnahme bei, um die Schärfe an derselben Stelle zu vergleichen. Beim Öffnen aktiv.",
    "<b>Kompositionshilfen</b> (<kbd>G</kbd>): jeder Klick wechselt zwischen Drittel, Kreuz in der Mitte, Drittel und Mitte, keine. Linien von 1 Pixel, die Zoom und Verschieben folgen; sie funktionieren auch im Live-View.",
    "<b>Inspektor</b> (<kbd>I</kbd>): scharfe Bereiche, Zebra und Falschfarben, Histogramm, Wellenform, Werte unter dem Zeiger, gespiegelte Ansicht oder nur ein Kanal (siehe unten). Beim Öffnen des Betrachters geöffnet.",
    "<b>Vollbild</b> (<kbd>F</kbd>).",
    "<b>?</b>: diese Anleitung, beim Kapitel über den Betrachter.",
    f"<b>Miniaturen</b>: Ein Klick öffnet die Aufnahme. <i>{ui('P')}</i> = Testaufnahme, <i>{ui('C')}</i> = Kalibrierungsbild, <i>{ui('E')}</i> = Foto für die Belichtung, <i>AF</i> = Autofokus-Aufnahmen, die Zahlen sind die Aufnahmen der Serie. Der Streifen zeigt nur die laufende oder die letzte Serie: Er leert sich beim Start einer Serie, und die erste Testaufnahme danach beginnt einen neuen. Die Dateien bleiben im Ordner.",
    f"<b>{ui('Svuota')}</b>, unten rechts im Miniaturstreifen, wenn Aufnahmen vorhanden sind: neu beginnen. Die Aufnahmen verschwinden aus dem Betrachter und die Serie ist wieder {ui('Pronta')}; die Dateien bleiben im Ordner.",
], layout="full", anchors={n: "bb" if n in (7, 9, 11) else "b" for n in range(1, 12)})}
<p>Mit der Maus: Ziehen verschiebt das Bild, das Scrollrad (oder Aufziehen auf dem Trackpad) zoomt um den Zeiger herum,
ein Doppelklick wechselt zwischen „Einpassen“ und 100 %. Über 150 % bleiben die Pixel scharf, ohne Weichzeichnung.</p>
{fig("visualizzatore-live", [
    f"<b>{ui('■ Ferma live')}</b> kehrt zu den Fotos zurück; auch ◀ ▶ oder ein Klick auf eine Miniatur verlassen das Live-View.",
    f"Live-Status: {ui('LIVE')}, {ui('SCATTO…')}, {ui('IN PAUSA')} während der Serie.",
], layout="full", anchors={1: "b"}, caption="Das Live-View im Betrachter, hier mit dem Simulator im Fokus (das Schachbrett ist scharf). Bei 100 % hat das Live-View die Auflösung der Kameravorschau, also weniger als die Fotos.")}
<h2>Autofokus auf einen Punkt</h2>
<p>Der Autofokus findet selbst die Position des Fokussierers, an der ein gewähltes Detail am schärfsten ist: eine
Markierung, ein Haar, der Rand einer Struktur. Damit lassen sich zum Beispiel Anfang oder Ende des Stapels genau
festlegen.</p>
<ol class="steps">
<li><span class="ui">⌖ Autofokus</span> drücken (Taste <kbd>A</kbd>) und auf das Detail klicken: Ein blaues Quadrat
  erscheint, der gemessene Bereich. Die Seitenlänge ändert sich mit dem Regler <b>Bereich</b> oder mit <kbd>[</kbd>
  <kbd>]</kbd>; ein weiterer Klick verschiebt das Quadrat. Ziehen und Zoom funktionieren wie immer.</li>
<li>Den <b>Modus</b> wählen (Schnell, Präzise oder Echte Aufnahmen) und den <b>Weg</b> prüfen: Balken und Zeile darunter
  zeigen, wie weit sich der Fokussierer bewegt und wie nahe er dem Objekt kommt. Dann <span class="ui">Starten</span>
  drücken: Der Fokussierer fährt in dieselbe Richtung wie der Stapel, und die Schärfekurve wächst Punkt für Punkt.</li>
<li>Am Ende kehrt der Fokussierer zur schärfsten Position zurück: Er fährt zuerst um den <b>Überfahrweg</b> darüber
  hinaus und kommt in derselben Richtung wie der Durchlauf an, damit das Spiel der Mechanik den Fokus nicht verschiebt.
  Dann macht er eine <b>Kontrollaufnahme</b>, die grüne Raute im Diagramm. In der Zeile darunter trägt <span class="ui">Fokus verwenden als</span>
  <span class="ui">Stapelanfang</span> oder <span class="ui">Stapelende</span> die Position im Hauptfenster in die Sequenz ein.</li>
</ol>
{fig("visualizzatore-autofocus", [
    "<b>⌖ Autofokus</b> (<kbd>A</kbd>): öffnet das Feld; ein Klick ins Bild wählt den Bereich. <kbd>Esc</kbd> schließt es. Das Feld lässt sich an der Titelleiste verschieben; Doppelklick auf die Leiste: zurück in die Ecke.",
    "<b>Gemessener Bereich</b>: gestrichelt, solange der Autofokus läuft. Er bleibt an derselben Stelle, wenn man die Aufnahme wechselt oder zum Live-View geht. Mit <i>Folgt dem Motiv</i> wandert er während der Messung mit dem Motiv.",
    "<b>Modus</b>: <i>Schnell</i>, <i>Präzise</i> (Standard) oder <i>Echte Aufnahmen</i>; darunter, was er tun wird. <b>Weite Suche</b> schaltet sie ein, wenn das ganze Bild unscharf ist. <b>Bereich</b>: Seitenlänge des Quadrats in Sensorpixeln. Der <b>Wegbalken</b> reicht von − bis + zum maximalen Verfahrweg um den Start: hell der geplante Weg, dunkler der schon zurückgelegte, der Strich ist die aktuelle Position. Daneben zwei Symbole: <b>Fester Bereich</b> misst immer dieselbe Stelle des Bildes, <b>Folgt dem Motiv</b> verschiebt den Bereich mit dem Motiv, wenn das Bild beim Fokussieren wandert (siehe unten).",
    "<b>Schärfekurve</b>: ein Punkt pro Messung, waagerecht die Position des Fokussierers; darunter die Schrittweite. Frühere Durchläufe bleiben blasser unter dem laufenden, und das Diagramm zoomt auf den Bereich des feinen Durchlaufs. Die orangen Quadrate sind die echten Bestätigungsaufnahmen, die grüne Linie die gewählte Position, die grüne Raute die Kontrollaufnahme. Mit dem Mauszeiger auf einem Punkt liest man Position und Schärfe (in % des Maximums).",
    "<b>Status</b>: Durchlauf, laufende Aufnahme und Position, dann das Ergebnis mit Kontrolle und Spitzenbreite oder der Grund, warum kein Fokus gefunden wurde.",
    "<b>Wiederholen</b> und darunter <b>Fokus verwenden als Stapelanfang / Stapelende</b>, solange der Fokussierer auf der gefundenen Position bleibt. <b>Wiederholen</b> startet den Autofokus erneut; ein Klick auf einen anderen Punkt verschiebt den Bereich, ohne das Feld zu schließen. Während der Messung gibt es <b>Stopp</b>.",
], layout="full", anchors={6: "r"})}
<p>Bei jeder Aufnahme misst die App, wie scharf die Kanten im Bereich sind (der Helligkeitsgradient, geteilt durch die
mittlere Helligkeit, damit die Belichtung keine Rolle spielt). Weit vom Fokus ist die Kurve flach, in seiner Nähe steigt
sie zu einer schmalen Spitze an. Die App legt eine Kurve durch die Punkte um das Maximum, die gefundene Position kann
also auch zwischen zwei Aufnahmen liegen. Der Durchlauf endet von selbst, sobald die Spitze überschritten ist; liegt die
Spitze hinter der letzten Aufnahme, läuft er weiter, liegt sie vor der ersten, beginnt er weiter hinten neu. Bei RAW
misst sie die JPEG-Vorschau in der Datei: In Tests mit echten Stapeln ergibt sie denselben Fokus wie das entwickelte
RAW.</p>
<div class="box tip"><span class="t">Den Bereich wählen</span>Ein kontrastreiches Detail, alles in derselben Tiefe.
Liegen im Bereich zwei Dinge in unterschiedlicher Schärfeebene (Bein und Körper eines Insekts), hat die Kurve zwei
Spitzen und die App meldet es in Orange: den Bereich auf das gewünschte Detail verkleinern. Auf einem gleichmäßigen
Hintergrund gibt es nichts zu messen, und der Autofokus endet mit einer Meldung.</div>
<h3>Die Modi</h3>
<p><b>Live-View</b> ist schneller, aber sein Bild ist klein und komprimiert und bei wenig Licht verrauscht; <b>echte
Aufnahmen</b> messen das Foto so, wie es im Stapel sein wird, brauchen aber jeweils einige Sekunden. Die Modi
kombinieren beides:</p>
<ul>
<li><b>Schnell</b>: nur Live-View, ein Durchlauf. Um den Fokus zu suchen und für Versuche.</li>
<li><b>Präzise</b> (Standard): zwei Durchläufe mit Live-View, dann <b>3 echte Bestätigungsaufnahmen</b> um den gefundenen
  Fokus. Der Fokus wird aus diesen Aufnahmen neu berechnet (liegt die schärfste am Rand, kommen ein oder zwei dazu), und
  auch die Kontrollaufnahme ist eine echte Aufnahme. Das ist der Modus, um Anfang oder Ende eines Stapels festzulegen.</li>
<li><b>Echte Aufnahmen</b>: der ganze Durchlauf mit echten Aufnahmen. Am sichersten und am langsamsten.</li>
</ul>
<p>Jeder Modus merkt sich seine Einstellungen (Schrittweite, Aufnahmen pro Durchlauf, Durchläufe, Bilder,
Bestätigungsaufnahmen), die unter <span class="ui">Konfiguration › Autofokus</span> geändert werden.</p>
<p>Mit echten Aufnahmen (<i>Präzise</i> und <i>Echte Aufnahmen</i>) schaltet sich der Live-View vor der ersten
Aufnahme aus, wie bei einer Testaufnahme, und bleibt bis zum Ende des Autofokus aus: Die Kamera wechselt nicht ständig
zwischen Live-View und Aufnahme. Er startet von selbst wieder, wenn du den Fokussierer bewegst. Trennt sich die Kamera
während einer Aufnahme, versucht es die App erneut und verbindet sie wieder; wiederholen sich die Trennungen, prüfe die
Stromversorgung: Ein Akku-Dummy (<i>dummy battery</i>), der die Lastspitze der Aufnahme nicht verkraftet, trennt die
Kamera vom USB.</p>
<div class="box warn"><span class="t">Maximaler Verfahrweg: er schützt das Objekt</span>Der Autofokus entfernt sich nie
weiter von der Startposition als der <b>maximale Verfahrweg</b> (± Schritte, im Wegbalken). Müsste sich der Durchlauf
darüber hinaus verlängern, weil der Fokus weiter weg liegt als erwartet, hält er an und meldet es, statt weiter auf das
Objekt zuzufahren. Der berechnete Wert deckt den geplanten Weg mit einer Reserve ab; verringern Sie ihn, wenn das
Objekt nahe am Objektiv ist.</div>
<div class="box warn"><span class="t">Niedrige Kontrolle: Spiel</span>Ist die Kontrollaufnahme deutlich weniger scharf
als das Maximum der Kurve (unter 80 %), meldet die App es in Orange: Meist ist das Spiel der Mechanik größer als der
Überfahrweg. Erhöhen Sie ihn unter <span class="ui">Konfiguration › Autofokus</span>; anfangs gilt der Spielausgleich
der Sequenz, mindestens aber eine Spitzenbreite.</div>
<p>Alle Werte stehen unter <span class="ui">Konfiguration › Autofokus</span>, Kapitel 12.</p>
<h2>Inspektor</h2>
<p>Das Feld <span class="ui">Inspektor</span> (Taste <kbd>I</kbd>) bündelt Hilfen für Schärfe und Belichtung, wie bei Videomonitoren. Es ist schreibgeschützt: Es verändert die Fotos nicht. Es funktioniert auch mit dem Live-View: Mit scharfen Bereichen, Zebra oder Wellenform aktualisiert es sich fünfmal pro Sekunde.</p>
{fig("ispettore", [
    "<b>Blöcke</b> (Schaltfläche oben rechts): welche Blöcke in welcher Reihenfolge erscheinen (Kästchen und Pfeile ↑ ↓; <span class='ui'>Wiederherstellen</span> stellt den Anfangszustand her). Ein ausgeblendeter Block verändert das Bild nicht.",
    "<b>Ansicht</b>: horizontal oder vertikal spiegeln (mit beiden ist das Bild um 180° gedreht), etwa um es wie im Okular zu sehen; nur ein Kanal R, G oder B, in Grau. Nur die Ansicht ändert sich: die Dateien bleiben unverändert.",
    "<b>Fokus</b>: <span class='ui'>Scharfe Bereiche hervorheben</span> färbt scharfe Kanten ein (Focus Peaking), mit Empfindlichkeit von 1 bis 15, fünf Farben und dem Bild darunter farbig, grau, dunkel oder schwarz. <span class='ui'>Nur im Autofokus-Bereich</span> beschränkt alles auf das mit der Taste <kbd>A</kbd> gewählte Feld.",
    "<b>Schärfe</b>: dasselbe Maß wie beim Autofokus, mit einem Balken gegenüber dem höchsten gesehenen Wert und <span class='ui'>Zurücksetzen</span>.",
], layout="full")}
<p>Im Live-View den Fokus drehen, bis der Balken 100 % erreicht: Das ist der schärfste Punkt für diesen Bildausschnitt. Das Maximum beginnt von selbst neu, wenn Bereich, Auflösung oder Kanal wechseln oder zwischen Live-View und Aufnahmen gewechselt wird, weil diese Werte nicht vergleichbar sind. Mit dem Bild <span class="ui">Dunkel</span> sieht man während der Sequenz das scharfe Band von Aufnahme zu Aufnahme wandern: Springt es zwischen zwei Aufnahmen, ist der Schritt zu groß.</p>
<div class="box tip"><span class="t">Ein Kanal und chromatische Aberration</span>Mit nur einem Kanal nutzen auch scharfe Bereiche und Schärfe diesen Kanal. Auf R scharfstellen, dann auf B: Der Positionsunterschied ist die axiale chromatische Aberration des Objektivs. Ist die Ansicht gespiegelt oder auf einen Kanal beschränkt, zeigt ein Etikett oben rechts im Bild das an, auch bei geschlossenem Inspektor; ein Klick darauf bringt das normale Bild zurück.</div>
{fig("ispettore-esposizione", [
    "<b>Im Bild markieren</b>, auf drei Arten: <i>Markierungen</i> (Ausgebranntes rot, Schwarzes blau, in voller Auflösung), <i>Zebra</i> und <i>Falschfarben</i>. Die Tabelle darunter gibt den Anteil ausgebrannter und schwarzer Pixel für jede Regel an.",
    "<b>Zebra</b>: weiße und schwarze Streifen, wo der höchste Kanal die Schwelle erreicht (<span class='ui'>Lichter ab</span>); auf Wunsch hellblaue Streifen auf den <span class='ui'>Mitteltönen</span>, Wert ± Toleranz. <span class='ui'>= Median</span> zentriert sie auf den Median des Bildes: Bei einem Flat sind die Bereiche ohne Streifen die ungleichmäßig beleuchteten.",
    "<b>Histogramme</b> von Rot, Grün, Blau und Luminanz. Mit dem Zeiger über einer Stufe liest man, wie viele Pixel sie hat.",
    "<b>Wellenform</b>: waagerecht die Position im Bild, wie angezeigt; senkrecht der Pegel von 0 bis 100 %. Helligkeit, RGB überlagert oder nebeneinander. Ungleichmäßiges Licht ergibt einen schrägen oder gebogenen Kamm.",
    "<b>Unter dem Zeiger</b>: die Werte R, G, B und die Luminanz des Pixels unter der Maus.",
], layout="full")}
<p><i>Falschfarben</i> geben jedem Helligkeitsbereich eine Farbe (Legende im Feld): Violett für Schwarz, Blau für tiefe Schatten, Grün für Mitteltöne, Gelb für Lichter, Orange für fast ausgebrannt, Rot für ausgebrannt; der Rest bleibt grau. Zebra, Falschfarben und Wellenform nutzen das angezeigte 8-Bit-Bild nach der Tonkurve der Kamera: Bei RAW-Fotos ist das die umgewandelte Vorschau. Für den genauen Sensorpegel <span class="ui">Belichtung der Lights</span> (7.6) verwenden, die die echten RAW-Dateien misst.</p>
""")

# 9
add(f"""
<h1><span class="n">9</span>Sicherheitsgrenzen</h1>
<p class="lead">Die Grenzen verhindern, dass das Objektiv den Objektträger berührt oder die Mechanik auf Anschlag
fährt. Richten Sie sie als Erstes ein, in aller Ruhe.</p>
<p>Der Bereich <b>{ui('Configurazione')}</b> ist eine einzige Seite, gegliedert in die Gruppen {ui('Focheggiatore')},
{ui('App')} und {ui('Sistema')}. Die Bereiche {ui('Ottica')} und {ui('Calibrazione')} sind genauso aufgebaut.</p>
{fig("configurazione", [
    f"<b>{ui('Cerca')}</b>: Geben Sie einen Teil eines Namens ein (zum Beispiel „Spiel“), dann bleiben nur die Zeilen, die ihn enthalten.",
    "<b>Inhaltsverzeichnis</b>: Ein Klick springt zum Bereich; der hervorgehobene Eintrag folgt dem Scrollen. Ein Punkt zeigt ungespeicherte Änderungen oder ein verfügbares Update.",
    "<b>Titel des Bereichs</b>; das <b>?</b> öffnet die Anleitung an dieser Stelle.",
    f"<b>{ui('Dettagli')}</b>: die längeren Erklärungen, anfangs geschlossen.",
    f"<b>{ui('Riepilogo')}</b>, immer sichtbar: Auflösung, nutzbarer Weg, Firmware, App-Version und Fortschritt auf dem Smartphone.",
], layout="full")}
<p>Fast alles wird gespeichert, sobald Sie einen Wert ändern: Die Motoreinstellungen gehen sofort an die Firmware,
Mechanik und die anderen Optionen in die Einstellungen der App. Die Ausnahme sind die Grenzen, unten.</p>
{fig("fine-corsa", [
    f"<b>{ui('Fine corsa inferiore')}</b> in Schritten; <span class='ui'>⌖ {ui('Usa posizione attuale')}</span> übernimmt sie aus der Position des Fokussierers.",
    f"<b>{ui('Fine corsa superiore')}</b>. Leer = das Firmware-Maximum.",
    f"<b>{ui('Verso il campione (si avvicina) con')}</b>: ob die Schrittzahl bei Annäherung an das Präparat sinkt oder steigt. Damit werden {ui('Avvicina')}/{ui('Allontana')} richtig beschriftet.",
    f"<b>{ui('Salva fine corsa')}</b>, in der Leiste <i>{ui('Modifiche non salvate')}</i>, die erscheint, wenn Sie einen Wert ändern; <b>{ui('Annulla')}</b> kehrt zu den gespeicherten Werten zurück. Das ist der einzige Teil der Einstellungen, der nicht von selbst gespeichert wird.",
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
  <span class="ui">⌖ {ui('Usa posizione attuale')}</span>, dann auf <span class="ui">{ui('Salva fine corsa')}</span> und
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
    "<b>Ergebnis</b>: µm pro Schritt, Schritte pro µm, µm pro 1.000 Schritte. Änderungen werden automatisch gespeichert.",
])}
<h2>10.1 Der Antriebsstrang</h2>
<p>Vom Motor bis zum Objekttisch durchläuft die Bewegung mehrere Stufen, und jede multipliziert oder teilt:</p>
<p><b>Fester Bereich oder Motiv folgen.</b> Ist der Schlitten im Makrobereich nicht genau auf die Objektivachse ausgerichtet, wandert das Bild bei jedem Schritt ein wenig: mit festem Bereich kann das gewählte Detail das Feld verlassen und die Messung landet auf dem Hintergrund, mit einer Kurve ohne Spitze oder mit der falschen. Mit <i>Folgt dem Motiv</i> wird jedes Bild mit dem der nächsten bereits gemessenen Position verglichen, wo der Fokus fast gleich ist, und der Bereich geht dorthin, wo das Detail hingewandert ist; am Ende bleibt er dort. Ist das Detail nicht mehr auffindbar, hält der Autofokus mit „Motiv verloren“ an. Am Mikroskop oder bei gleichförmigen Strukturen (feine Linien, Raster) ist der feste Bereich besser.</p>
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
<p>Der Rechner befindet sich unten im Bereich <b>{ui('Ottica')}</b>, in der Gruppe <b>{ui('Strumenti')}</b> (das Ergebnis erscheint auch in der Übersicht rechts), und verwendet die numerische Apertur, die
Vergrößerung auf dem Sensor (Objektiv × Zwischenvergrößerung × Adapter) und die Pixelgröße des Sensors aus dem geöffneten Profil (Kapitel 7.2).</p>
{fig("profondita", [
    f"<b>{ui('Sovrapposizione (%)')}</b> zwischen einer scharfen Schicht und der nächsten; 20–30 % ist ein guter Wert.",
    "<b>Ergebnis</b>: Schärfentiefe, empfohlene Schrittweite in µm und in Motorschritten.",
    f"<b>{ui('Usa come passo della sequenza')}</b>: übernimmt den Wert in Schritten in das Feld Schrittweite der Serie.",
    "<b>Stapelschritt</b> im Profil, in Motorschritten: <span class='ui'>Empfohlen</span> trägt den oben berechneten Schritt ein, <span class='ui'>Aus Sitzung</span> den der Sequenz. Er wird mit dem Profil gespeichert; leer = das Profil ändert den Schritt nicht.",
], layout="full", anchors={4: "b"})}
<p>Der richtige Schritt hängt von Blende und Abbildungsmaßstab ab, also vom Profil: Im Profil gespeichert, setzt die Wahl des Profils in der Sitzung Blende und Schritt zusammen. Ein Preset der Sequenz behält dagegen seinen eigenen Schritt.</p>
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
<div class="box tip"><span class="t">Optovar, Adapter und Projektionsokulare</span>Geben Sie im Optikprofil (Kapitel 7.2)
den Faktor des Zwischenvergrößerungswechslers und den des Adapters oder Projektionsokulars an: Die App multipliziert sie
mit der Objektivvergrößerung. Zum Beispiel 10× mit Optovar 1,6× und Adapter 0,63× = 10 × 1,6 × 0,63 ≈ 10,1× auf dem
Sensor. Nur der zweite Term der Formel ändert sich, und der fällt bei schwachen Objektiven am stärksten ins Gewicht. Für
einen exakten Maßstab in µm messen Sie die µm pro Pixel mit einem Objektmikrometer: Die auf dem Zubehör angegebenen
Faktoren sind Nennwerte.</div>

<h2>11.2 Anfang, Ende und Anzahl der Aufnahmen</h2>
<ol class="steps">
<li>Schalten Sie das Live-View ein (am besten im Betrachter, vergrößert) und stellen Sie den Fokus <b>knapp über</b> den
  höchsten Teil des Objekts, der scharf werden soll: Klicken Sie neben <b>{ui('Inizio')}</b> auf <span class="ui">⌖ {ui('qui')}</span>.</li>
<li>Fahren Sie bis <b>knapp unter</b> den tiefsten Teil und klicken Sie neben <b>{ui('Fine')}</b> auf <span class="ui">⌖ {ui('qui')}</span>.</li>
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
<h1><span class="n">12</span>Motor, manuelle Steuerung, Autofokus, Updates, Temperatur</h1>
<h2>{ui('Motore (firmware)')}</h2>
{fig("motore", [
    f"<b>{ui('Microstep')}</b>: {ui('Passo intero')}, 1/2 … 1/32 (siehe 10.2). Eine Änderung ändert den Maßstab der Positionen: Prüfen Sie danach die Grenzen erneut.",
    f"<b>{ui('Velocità')}</b> der Firmware: {ui('Lenta')}, {ui('Media')}, {ui('Veloce')}. Mit dem myFocuserPro2 und der Firmware-Build 7 beträgt die Höchstgeschwindigkeit der Bewegungen 80, 200 und 400 Schritte pro Sekunde; jede Bewegung beginnt mit 40 Schritten pro Sekunde und beschleunigt.",
    f"<b>{ui('Alimentazione bobine motore')}</b>: Mit <b>{ui('Sempre quando connesso')}</b> hält der Motor im Stillstand seine Position, wird aber warm. <b>{ui(COIL_HOLD)}</b> (anfangs aus; nur wenn die erste Option an ist): Bleibt sie aus, werden die Spulen beim Trennen des Fokussierers oder beim Beenden der App abgeschaltet, damit der Motor nicht stundenlang warm bleibt; die erste Bewegung schaltet sie wieder ein. Schalten Sie sie ein, wenn das Gewicht einen senkrechten Schlitten absinken lassen kann. Erfordert Firmware-Build 8.",
    f"<b>{ui('Alimentale comunque durante la sequenza')}</b> (erscheint bei ausgeschalteten Spulen; standardmäßig aktiv): Die Spulen werden beim Start des Stapels eingeschaltet und nach der Rückkehr zum Anfang wieder ausgeschaltet.",
    f"<b>{ui('Inverti verso di rotazione')}</b>.",
    f"<b>{ui('Compensa il gioco IN')} / OUT</b>: Bei jeder Umkehr zu niedrigeren (IN) oder höheren (OUT) Positionen fährt die Firmware zusätzliche Schritte, ohne sie zu zählen, auch bei den Hardwaretasten.",
    "<b>Spiel IN / OUT</b> in Schritten, 0 bis 255 (siehe 10.5).",
    f"<b>{ui('Rileggi')}</b>: liest die Werte aus der Firmware.",
])}
<div class="box warn"><span class="t">Spulen aus: Der Schlitten rückt womöglich nicht vor</span>Ohne Strom im Stillstand
kann die Last den Schlitten bei jedem Halt zurückschieben, und beim Mikroschritt springt der Motor außerdem auf den
nächsten Vollschritt zurück: Der Zähler läuft weiter, der Schlitten aber nicht. Deshalb schaltet die App die Spulen bei
ausgeschalteten Spulen während der Serie ein (Nummer 4), und ein orangefarbener Hinweis erinnert daran, wenn Sie die
Option abwählen. Wird der Motor zu heiß, senken Sie lieber den Strom am Treiber, statt die Spulen auszuschalten.</div>
<h2>{ui('Comandi manuali')}</h2>
{fig("comandi-manuali", [
    f"<b>Schrittgrößen</b> der Tasten {ui('Allontana')}/{ui('Avvicina')}: in Zehnerpotenzen bis 1.000, 10.000 oder 100.000 Schritte. Ein Getriebe braucht große Schrittgrößen.",
    f"<b>{ui('Tieni premuto per muovere senza fermarti')}</b>: Beim Loslassen bremst der Motor ab und hält an; er hält in jedem Fall an der Grenze an und, falls die Seite nicht mehr reagiert, nach etwa einer Sekunde.",
    f"<b>{ui('Tratto massimo per comando (passi)')}</b>: Bei gedrückter Taste fährt der Motor nie mehr als einen Abschnitt (standardmäßig 500 Schritte) über die letzte Bestätigung der Seite hinaus, dass die Taste noch gedrückt ist.",
], layout="side")}
<p>Die Dauerbewegung funktioniert aus Sicherheitsgründen so: Bricht die Kommunikation ab (Netzwerk, hängende App, Kabel),
fährt der Motor höchstens einen Abschnitt. Mit <b>Firmware-Build 5</b> verschiebt jede Bestätigung das Ziel um einen
Abschnitt weiter, und der Motor hält nie an; mit älterer Firmware fährt er Abschnitt für Abschnitt, mit einer kurzen Pause
zwischen den Abschnitten (kurze Abschnitte sind sicherer, aber ruckartiger). Ab <b>Build 4</b> gibt es einen zusätzlichen
Schutz: Während der Dauerbewegung hält der Fokussierer selbstständig an, wenn er 1,5 s lang keine Befehle mehr vom Mac
erhält. <span class="ui">{ui('Vai')}</span>, die
Tasten mit einem einzelnen Klick und die Serie fahren dagegen immer bis zum Ziel, auch wenn die Bewegung viele Sekunden
dauert.</p>
<h2>Autofokus</h2>
<p>Die Einstellungen des Autofokus auf einen Punkt (Kapitel 8): zuerst der Modus und seine Einstellungen, dann die für
alle Modi gemeinsamen. Leere Felder verwenden den Standardwert, der grau im Feld steht; Schrittweiten und Aufnahmen
werden aus der <b>Spitzenbreite</b> berechnet, also dem Schrittbereich, in dem die Schärfe über der Hälfte des Maximums
bleibt.</p>
{fig("autofocus-config", [
    "<b>Modus</b>, den der Betrachter verwendet, mit einer Zusammenfassung, was er tut. Lässt sich auch im Feld wählen.",
    "<b>Einstellungen des Modus</b>: Bilder (Live-View oder echte Aufnahmen), Schrittweite und Aufnahmen des feinen Durchlaufs, Durchläufe. Leer = Standardwert des Modus oder aus der Spitzenbreite berechnet. <b>Modus zurücksetzen</b> stellt die Anfangswerte wieder her.",
    "<b>Bestätigung mit echten Aufnahmen</b> (nur mit Live-View): wie viele echte Aufnahmen um den gefundenen Fokus; 0 = keine Bestätigung.",
    "<b>Weite Suche</b>, wenn das ganze Bild unscharf ist, mit Umfang (± Schritte) und Schrittweite, eine Spitzenbreite: einige weit auseinanderliegende Aufnahmen.",
    "<b>Maximaler Verfahrweg ±</b> ab der Startposition: darüber hinaus hält der Autofokus an. Darunter Wartezeit nach Bewegung und <b>Überfahrweg gegen Spiel</b>.",
    "<b>Spitzenbreite</b>, die für die Berechnungen verwendet wird, und ihre Herkunft. <b>Messung vergessen</b> kehrt zur Schätzung zurück.",
], layout="side", anchors={2: "r", 4: "r"})}
<p>Beim ersten Mal wird die Spitzenbreite aus der Schärfentiefe des in der Sequenz gewählten Optikprofils und aus der
Mechanik (µm pro Schritt) geschätzt, ohne Profil aus dem Verfahrweg zwischen den Grenzen. Nach jedem erfolgreichen
Autofokus speichert die App die gemessene Breite für dieses Profil und verwendet sie danach. Die erste Schätzung ist grob:
Ist die Spitze breiter als erwartet, verlängert sich der Durchlauf von selbst; ist sie schmaler, wiederholt er die
Messung mit feinerer Schrittweite. Der <b>Überfahrweg gegen Spiel</b> ist die Strecke, um die der Fokussierer über eine
Position hinausfährt, bevor er zu ihr zurückkehrt: Er muss größer als das Spiel der Mechanik sein.
<span class="ui">Berechnete Werte wiederherstellen</span> leert die von Hand eingetragenen gemeinsamen Felder. Ist die
weite Suche aus und der Fokus weit weg, endet der Autofokus und schlägt vor, sie einzuschalten.</p>
<h2>{ui('Aggiornamenti')}</h2>
{fig("aggiornamenti", [
    "Version der <b>App</b> und Ergebnis der letzten Prüfung.",
    "Version der <b>Firmware</b> auf dem Fokussierer.",
    f"<b>{ui('Aggiorna firmware')}</b>: etwa 20 Sekunden; die Einstellungen des Fokussierers bleiben erhalten. Ziehen Sie das Kabel nicht ab; falls etwas schiefgeht, wiederholen Sie den Vorgang einfach. Build 5 macht die Bewegung bei gedrückter Taste durchgehend; ab Build 4 gibt es das automatische Anhalten, wenn der Mac nicht mehr kommuniziert. Build 7 lässt die Bewegungen sanfter anlaufen (40 Schritte pro Sekunde) und halbiert die langsame Geschwindigkeit des myFocuserPro2.",
    f"<b>{ui('Controlla ora')}</b>: sucht nach Updates der App.",
], layout="side")}
<p>Die App wählt selbst die passende Firmware für die Platine (myFocuserPro2 oder Ardufocus). Der <b>Ardufocus</b> startet
über das USB-Kabel nicht neu: Während der Aktualisierung fordert die App Sie auf, die <b>Reset-Taste</b> der Platine zu
drücken.</p>
<p>Die Platine speichert Position und Einstellungen erst etwa zehn Sekunden nach der letzten Bewegung in ihrem
dauerhaften Speicher. Damit die Position nicht verloren geht, lässt die App sie jedes Mal sofort speichern, wenn sie die
Verbindung schließt ({ui('Disconnetti')}, Beenden der App, Aktualisierung).</p>
<h2>{ui('Temperatura')}</h2>
<p>Die aktuelle Temperatur des Fühlers steht in der oberen Leiste. Die Kurve der letzten 60 Minuten befindet sich in der
Übersicht des Bereichs <b>{ui('Calibrazione')}</b> (Kapitel 7.6), neben den Darks. Die Temperatur jeder Aufnahme wird in
<code>sequence.json</code> gespeichert und in <code>sequence.txt</code> zusammengefasst: nützlich, weil sich der Fokus
durch Wärmeausdehnung verschiebt.</p>
""")

# 13
add(f"""
<h1><span class="n">13</span>Eine typische Sitzung, Schritt für Schritt</h1>
<h2>Einmalig (oder wenn sich die Mechanik ändert)</h2>
<ol class="steps">
<li><b>Mechanik</b>: Geben Sie die Daten ein und prüfen Sie die Auflösung mit einer Messung (Kapitel 10).</li>
<li><b>Richtung des Präparats</b> und <b>Grenzen</b>, mit den in die Firmware geschriebenen Grenzen (Kapitel 9).</li>
<li><b>Spiel</b>: Messen Sie es mit dem Live-View und entscheiden Sie, wo es ausgeglichen wird (Serie oder Firmware).</li>
<li><b>Motor</b>: Prüfen Sie die Spulen (Kapitel 12) und aktualisieren Sie die Firmware, wenn die App es anbietet.</li>
<li><b>Optikprofile</b>: Speichern Sie im Bereich {ui('Ottica')} ein Profil für jede Kombination aus Objektiv, Filter und
  Beleuchtung, am Mikroskop oder in der Makrofotografie (Kapitel 7.2 und 7.3).</li>
<li><b>Presets</b>: Berechnen Sie für jedes Objektiv die Schrittweite aus der Schärfentiefe und speichern Sie ein Preset;
  das Preset merkt sich auch das Optikprofil.</li>
</ol>
<h2>Bei jeder Sitzung</h2>
<ol class="steps">
<li>Schalten Sie Fokussierer und Kamera ein (Modus M), schließen Sie die Kabel an und öffnen Sie Focus Stack.</li>
<li>Fokussierer und Kamera verbinden sich von selbst; falls nicht, drücken Sie <b>{ui('Connetti')}</b> im Bereich {ui('Sessione')}.</li>
<li>Stellen Sie Belichtungszeit, ISO und Format ein; machen Sie eine <b>Testaufnahme</b> und prüfen Sie sie im Betrachter bei 100 %.</li>
<li>Wählen Sie das <b>Preset</b> des Objektivs (oder die Schrittweite) und prüfen Sie das <b>Optikprofil</b> in der Serie.</li>
<li>Suchen Sie mit dem <b>Live-View</b> und der Tastatur <b>Ende</b> und <b>Anfang</b> der Serie und klicken Sie jeweils auf ⌖ {ui('qui')}.</li>
<li>Falls nötig, bereiten Sie die <b>Darks</b> und <b>Flats</b> vor und berechnen Sie die Belichtung der Lights (Kapitel 7.6).</li>
<li>Prüfen Sie die Übersicht: Anzahl der Aufnahmen, Bereich, Dauer, kein roter Hinweis.</li>
<li><b>{ui('▶ Avvia sequenza')}</b>. Berühren Sie das Mikroskop nicht: Vibrationen verderben die Aufnahmen. Um die Serie
  aus der Ferne zu verfolgen, verwenden Sie den Fortschritt auf dem Smartphone (Kapitel 7.7).</li>
<li>Klicken Sie nach Ende der Serie auf <b>{ui('Apri nel Finder')}</b> und öffnen Sie den Ordner in der Fusionssoftware.</li>
</ol>
""")

# 14
add(f"""<h1><span class="n">14</span>Wenn etwas nicht funktioniert</h1>
<p>Das <b>{ui('Registro')}</b> (der letzte Bereich) listet jede Verbindung, Bewegung, Aufnahme und jeden Fehler mit Uhrzeit
auf: Wenn etwas nicht funktioniert, lesen Sie es zuerst. Oben können Sie nach Wörtern suchen und nur Warnungen (⚠)
und Fehler (✖) anzeigen. Wenn Sie ein Problem melden, drücken Sie <b>{ui('Esporta')}</b>: Das Protokoll wird als
Textdatei im Ordner „Downloads“ gespeichert, mit den Versionen von App und Firmware und den Daten von Fokussierer und
Kamera, ohne den Schlüssel des Smartphone-Links und ohne Ihren Benutzernamen. Hängen Sie diese Datei an die Meldung an.</p>
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
    ["Der ganze Stapel liegt in derselben Ebene: Der Schlitten rückt nicht vor", f"Die Spulen des Motors sind ausgeschaltet, und die Last schiebt den Schlitten bei jedem Halt zurück (Kapitel 12): Lassen Sie <i>{ui('Alimentale comunque durante la sequenza')}</i> aktiviert. Probieren Sie eine kleine Bewegung und beobachten Sie dabei das Live-View."],
    ["Die Serie hat von selbst pausiert", f"Die Aufnahme ist auch nach dem Neuverbinden der Kamera nicht gelungen. Lesen Sie die Meldung, prüfen Sie Akku, Kabel und Karte und klicken Sie dann auf <i>{ui('Riprendi')}</i>: Die Aufnahme wird an derselben Position wiederholt."],
    ["Die Kamera verschwindet mitten im Stapel", "Meist ist der Mac in den Ruhezustand gegangen und hat USB angehalten. Während der Serie verhindert die App das, aber nicht, wenn Sie den Deckel eines Notebooks ohne externen Monitor schließen. Prüfen Sie auch den Akku der Kamera."],
    ["Das Smartphone öffnet die Fortschrittsseite nicht", f"Das Telefon muss im selben WLAN wie der Mac sein; beim ersten Start fragt macOS, ob eingehende Verbindungen erlaubt werden sollen (antworten Sie Erlauben). Nach <i>{ui('Nuovo link')}</i> gilt der alte Code nicht mehr."],
]))

# 15
add(f"""<h1><span class="n">15</span>Tastaturkurzbefehle</h1>
<div class="two">
<div class="keep"><h2 style="margin-top:0">Bereich {ui('Sessione')}</h2>
<table><tbody>
<tr><td><kbd>↑</kbd></td><td>Objektiv vom Präparat wegfahren</td></tr>
<tr><td><kbd>↓</kbd></td><td>Objektiv näher an das Präparat fahren</td></tr>
<tr><td><kbd>↑</kbd>/<kbd>↓</kbd> gedrückt gehalten</td><td>durchgehende Bewegung bis zum Loslassen</td></tr>
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
<tr><td><kbd>I</kbd></td><td>{ui('Ispettore')}</td></tr>
<tr><td><kbd>G</kbd></td><td>Kompositionshilfen</td></tr>
<tr><td><kbd>A</kbd></td><td>Autofokus: öffnet das Feld, dann auf das Detail klicken</td></tr>
<tr><td><kbd>[</kbd> <kbd>]</kbd></td><td>Autofokus-Bereich kleiner / größer</td></tr>
<tr><td><kbd>Esc</kbd></td><td>schließt den Autofokus</td></tr>
<tr><td><kbd>F</kbd></td><td>Vollbild</td></tr>
</tbody></table></div>
</div>
<p style="margin-top:8mm;color:#5a6b80;font-size:9pt">Focus Stack ist freie Software (MIT-Lizenz) ·
github.com/teoteo/focus-stack · Die Firmware basiert auf myFocuserPro2 von Robert Brown (MIT-Lizenz).</p>
""")
