"""Testo italiano della guida. Non è un modulo da importare: genera_guida.py lo esegue con exec()
in uno spazio di nomi che contiene già gli helper e i numeri comuni (fig, frac, table, num, diagram,
VERSION, ICON, IMG, UA, UB, GEAR17, um_step, dof, OBJ). Il testo riempie la lista H con le sezioni HTML.
"""
# ruff: noqa: F821  (i nomi arrivano da genera_guida.py)

META = {
    "lang": "it",
    "title": "Focus Stack — Guida all'uso",
    "footer": "Guida all'uso",
    "pdf": "Guida Focus Stack.pdf",
}


def ui(s):
    """Nome di un comando dell'app (in italiano coincide con la chiave)."""
    return s


DIAGRAM_LABELS = {
    "motor": "Motore", "gearbox": "Riduttore", "pulleys": "Pulegge / ingranaggi", "knob": "Micrometrica", "stage": "Tavolino",
    "motor1": "passi per giro", "motor2": "× microstep",
    "gearbox1": "(se presente)", "gearbox2": "es. 26,85 : 1",
    "pulleys1": "denti condotta", "pulleys2": "÷ denti motrice",
    "knob1": "µm per giro", "knob2": "della manopola",
    "stage1": "si sposta", "stage2": "in µm",
    "ratio": "rapporto di riduzione totale = riduttore × pulegge",
    "steps": "passi del motore per un giro della manopola = passi/giro × microstep × rapporto",
}

# tabella della profondità di campo (nomi degli obiettivi nella lingua della guida)
OBJ_NAMES = ["4× / 0,10", "10× / 0,25", "20× / 0,40", "40× / 0,65", "60× / 0,85", "100× / 1,25 olio"]
dof_rows = []
for name, (mag, na) in zip(OBJ_NAMES, OBJ):
    d = dof(na, mag, 3.9)
    s = d * 0.7
    dof_rows.append([name, num(d), num(s), str(max(1, round(s / UA))), str(max(1, round(s / UB)))])
dof_note = "per obiettivi a immersione in olio la formula dell'app (indice n = 1, aria) sottostima la profondità di campo: il passo calcolato è prudente."

H = []
add = H.append

add(f"""
<section class="cover">
  <div class="icon">{ICON}</div>
  <h1 class="title">Focus Stack</h1>
  <div class="sub">Guida all'uso<br>focheggiatore motorizzato e fotocamera per il focus stacking al microscopio</div>
  <div class="shot-c"><img src="{IMG}/sessione.png" alt=""></div>
  <div class="meta"><span>Versione dell'app {VERSION}</span><span>Ottobre 2026</span></div>
</section>
""")

add("""
<h1 style="break-before:auto">Indice</h1>
<div class="toc"><ol>
<li><span>1</span>Che cos'è Focus Stack<em>come funziona, che cosa serve</em></li>
<li><span>2</span>Installazione, avvio e aggiornamenti</li>
<li><span>3</span>L'interfaccia in breve<em>le tre schede e la barra superiore</em></li>
<li><span>4</span>Collegare il focheggiatore e la fotocamera<em>impostazioni della Nikon D5600 e delle altre fotocamere</em></li>
<li><span>5</span>Il focheggiatore: posizione, movimenti, STOP</li>
<li><span>6</span>Fotocamera, scatto di prova e live view</li>
<li><span>7</span>La sequenza di stacking</li>
<li><span>8</span>Il visualizzatore</li>
<li><span>9</span>Fine corsa di sicurezza</li>
<li><span>10</span>Configurazione meccanica: i calcoli<em>risoluzione in µm per passo, misura di verifica, corsa, velocità, gioco</em></li>
<li><span>11</span>Scegliere il passo della sequenza<em>profondità di campo, numero di scatti, durata</em></li>
<li><span>12</span>Motore, comandi manuali, aggiornamenti, temperatura</li>
<li><span>13</span>Una sessione tipo, passo per passo</li>
<li><span>14</span>Se qualcosa non va</li>
<li><span>15</span>Scorciatoie da tastiera</li>
</ol></div>
""")

# 1
add("""
<h1><span class="n">1</span>Che cos'è Focus Stack</h1>
<p class="lead">Focus Stack comanda dal Mac un focheggiatore motorizzato montato sulla vite micrometrica del
microscopio e una fotocamera collegata via USB. Esegue in automatico sequenze <b>sposta → attendi →
scatta</b>: decine di foto a fuochi diversi, pronte da fondere in un'unica immagine tutta a fuoco con
<b>Helicon Focus</b> (o un programma simile).</p>
<h2>Come funziona</h2>
<p>L'app Focus Stack avvia sul Mac un piccolo programma (il <i>server</i>) che parla con il focheggiatore
(una scheda Arduino con il firmware myFocuserPro2) e con la fotocamera. L'interfaccia si apre in
<b>Safari</b>, all'indirizzo <code>http://localhost:8765</code>, ed è raggiungibile solo da questo Mac.</p>
<ul>
<li>Il <b>focheggiatore</b> fa girare la manopola della messa a fuoco con un motore passo-passo. Ogni
  <i>passo</i> del motore sposta il tavolino (o l'obiettivo) di una frazione di micrometro: quanta, lo
  calcola la <b>configurazione meccanica</b> (capitolo 10).</li>
<li>La <b>fotocamera</b> viene comandata con lo stesso protocollo che usano i programmi dei produttori:
  tempo di posa, ISO, formato, scatto, scaricamento delle foto e live view.</li>
<li>I <b>pulsanti fisici</b> del focheggiatore continuano a funzionare anche con l'app aperta.</li>
</ul>
<h2>Che cosa serve</h2>
<ul>
<li>Un Mac con macOS 13 o successivo (Intel) oppure macOS 14 o successivo (Apple Silicon), con Safari.</li>
<li>Un focheggiatore <b>myFocuserPro2</b> (versione con driver DRV8825) oppure <b>Ardufocus</b> (circuito rev1 con
  DRV8825), collegato con il suo cavo USB e alimentato (12 V).</li>
<li>Una fotocamera Nikon, Canon o Sony con il cavo USB. In questa guida l'esempio è una <b>Nikon D5600</b>.</li>
<li>Un adattatore che proietti l'immagine del microscopio sul sensore (fototubo, raccordo T2 o simile).</li>
</ul>
<div class="box warn"><span class="t">Focheggiatori supportati</span>Focus Stack funziona con le schede
<b>myFocuserPro2</b> e <b>Ardufocus</b>, con il firmware incluso nell'app. Un myFocuserPro2 con il firmware originale si
collega subito e l'app propone di aggiornarlo con un clic. Un Ardufocus con il firmware originale (protocollo Moonlite)
invece non viene riconosciuto: la prima volta il firmware di Focus Stack va caricato a mano (istruzioni nel README su
github.com/teoteo/focus-stack); dopo, anche l'Ardufocus si aggiorna dall'app.</div>
<div class="box tip"><span class="t">Senza hardware</span>Nelle schede Focheggiatore e Fotocamera c'è la casella
<span class="ui">Simulatore</span>: permette di provare tutta l'app senza collegare niente. Le schermate di questa
guida sono state fatte così.</div>
""")

# 2
add("""
<h1><span class="n">2</span>Installazione, avvio e aggiornamenti</h1>
<h2>Prima installazione</h2>
<ol class="steps">
<li>Scarica <code>FocusStack-&lt;versione&gt;.zip</code> dalla pagina
  <b>github.com/teoteo/focus-stack/releases</b> e aprilo: compare l'app <b>Focus Stack</b>.</li>
<li>Trascina Focus Stack nella cartella <b>Applicazioni</b>, prima di aprirla.</li>
<li>Aprila. macOS avvisa che non può verificare lo sviluppatore, perché l'app non è firmata da Apple.
  Apri <b>Impostazioni di Sistema › Privacy e sicurezza</b>, scorri in basso e premi <b>Apri comunque</b>.
  Serve solo la prima volta.</li>
</ol>
<p>L'app contiene già tutto quello che le serve: non bisogna installare altro.</p>
<h2>Avvio e chiusura</h2>
<ul>
<li>All'avvio Focus Stack apre Safari sulla sua pagina e resta nel Dock. Un clic sull'icona nel Dock
  riporta in primo piano la pagina.</li>
<li>Per chiudere: <kbd>⌘Q</kbd> sull'app, oppure <span class="ui">Esci</span> dal menu dell'icona nel Dock.
  Se c'è una sequenza in corso l'app chiede conferma, la interrompe e ferma il motore.</li>
<li>Chiudere Safari <b>non</b> chiude l'app. La pagina, se resta aperta, mostra “Focus Stack è chiuso” e
  si ricarica da sola quando riapri l'app.</li>
</ul>
<h2>Aggiornamenti</h2>
<p>All'avvio, e poi ogni 6 ore, l'app controlla se c'è una versione nuova. Se c'è, in alto compare una
barra con <span class="ui">Aggiorna e riavvia</span>: l'app scarica la nuova versione, si chiude e si riapre da
sola. Lo stesso controllo si fa a mano in <span class="ui">Configurazione › Aggiornamenti › Controlla ora</span>.</p>
<p>Anche il <b>firmware del focheggiatore</b> si aggiorna dall'app (capitolo 12): quando quello sulla
scheda è più vecchio di quello incluso nell'app, la stessa barra lo segnala.</p>
<h2>Lingua</h2>
<p>L'app parla italiano, inglese, francese, tedesco e spagnolo. Con <span class="ui">Automatica (lingua del sistema)</span> segue la lingua di macOS,
e per le altre lingue usa l'inglese; in <span class="ui">Configurazione › Lingua</span> si può scegliere una lingua
fissa. La scelta vale per l'interfaccia, i messaggi e il registro, e questa guida esiste nelle stesse lingue.</p>
""")

# 3
add(f"""
<h1><span class="n">3</span>L'interfaccia in breve</h1>
<p>La pagina ha tre schede, che si scelgono in alto:</p>
<ul>
<li><b>Sessione</b>: il lavoro al microscopio. Focheggiatore, sequenza, fotocamera e ultimo scatto.</li>
<li><b>Configurazione</b>: fine corsa, meccanica, comandi manuali, motore, aggiornamenti, temperatura e
  calcolo della profondità di campo. Si regola una volta e poi si tocca di rado.</li>
<li><b>Registro</b>: l'elenco di tutto quello che è successo nella sessione, con l'ora. È il primo posto
  dove guardare se qualcosa non va.</li>
</ul>
{fig("sessione", layout="full", caption="La scheda Sessione: a sinistra il focheggiatore, al centro la sequenza, a destra fotocamera e ultimo scatto.")}
<h2>Barra superiore</h2>
{fig("barra-superiore", [
    "<b>Schede</b> Sessione, Configurazione e Registro.",
    "<b>Stato dei collegamenti</b>: Server, Focheggiatore e Fotocamera. Verde = collegato, grigio = scollegato, rosso = errore.",
    "<b>Temperatura</b> letta dalla sonda del focheggiatore.",
    "<b>Tema</b> scuro o chiaro. Il tema scuro stanca meno durante le sessioni lunghe al microscopio.",
], layout="full below-marks", anchors={1: "b", 2: "b", 3: "b", 4: "b"})}
<p>Sotto la barra possono comparire due fasce: quella blu degli <b>aggiornamenti</b> e quella rossa di
<b>allarme</b>, per esempio quando i pulsanti fisici portano il focheggiatore oltre un fine corsa.</p>
""")

# 4
add(f"""
<h1><span class="n">4</span>Collegare il focheggiatore e la fotocamera</h1>
<h2>Focheggiatore</h2>
{fig("connessione-focheggiatore", [
    "<b>Porta seriale</b> del focheggiatore. Di solito si chiama <code>/dev/cu.usbserial-…</code> oppure <code>/dev/cu.wchusbserial…</code>; il nome cambia se usi un'altra presa USB del Mac.",
    "<b>Aggiorna l'elenco</b> delle porte, dopo aver collegato il cavo.",
    "<b>Simulatore</b>: un focheggiatore finto, per provare l'app.",
    "<b>Connetti</b>. All'apertura della porta l'Arduino si riavvia: il collegamento richiede 2–3 secondi.",
], layout="side narrow")}
<h2>Fotocamera</h2>
{fig("connessione-fotocamera", [
    "<b>Fotocamera</b>: lascia <i>Rilevamento automatico</i> oppure scegli il modello trovato.",
    "<b>Rileva</b> le fotocamere collegate.",
    "<b>Simulatore</b>: una fotocamera finta che genera immagini di prova.",
    "<b>Connetti</b>. Prima di collegarsi l'app chiude i servizi di macOS che si appropriano della fotocamera.",
], layout="side narrow")}
<h3>Impostazioni sulla fotocamera</h3>
{table(["Fotocamera", "Cosa impostare"], [
    ["<b>Nikon D5600</b> e altre Nikon", "Ghiera dei modi su <b>M</b> (manuale). Nel menu di riproduzione disattiva la <b>revisione immagine</b>. Spegni SnapBridge/Wi-Fi e Bluetooth, che possono occupare il collegamento. Tieni una scheda di memoria inserita e la batteria carica (o l'alimentatore EH-5/EP-5A)."],
    ["Canon", "Modo <b>M</b>. Lo scatto va nella memoria della fotocamera o sulla scheda secondo <i>Destinazione</i>. Per il ritardo dello specchio attiva il <b>blocco dello specchio</b> nel menu."],
    ["Sony", "Menu USB › <b>PC Remote</b>; modo <b>M</b>. Per il live view la fotocamera deve permetterlo in PC Remote."],
])}
<div class="box warn"><span class="t">Se la fotocamera non si collega</span>macOS prova a impossessarsi della
fotocamera appena la colleghi. L'app chiude quel servizio da sola; se non basta, chiudi <b>Foto</b>,
<b>Anteprima</b>, <b>Acquisizione Immagine</b>, NX Studio, EOS Utility e riprova. Scollegare e ricollegare il
cavo con la fotocamera accesa aiuta spesso.</div>
""")

# 5
add(f"""
<h1><span class="n">5</span>Il focheggiatore: posizione, movimenti, STOP</h1>
{fig("focheggiatore", [
    "<b>Stato</b>: Fermo, In movimento, Disconnesso.",
    "<b>Collegamento</b>: porta, versione del firmware e massimo del firmware (la posizione più alta ammessa). <span class='ui'>Disconnetti</span> libera la porta.",
    "<b>Posizione</b> in passi del motore e, sotto, in millimetri o micrometri (se la meccanica è configurata).",
    "<b>Fine corsa</b> impostati e distanza che resta, verso il campione, prima del fine corsa.",
    "<b>Barra della corsa</b>: vedi la figura qui sotto.",
    "<b>Ampiezza del passo</b> dei pulsanti Allontana/Avvicina: 1, 10, 100… passi. Le ampiezze disponibili si scelgono in Configurazione › Comandi manuali.",
    "Lo stesso spostamento <b>in micrometri</b>.",
    "<b>Allontana / Avvicina</b>: un clic sposta dell'ampiezza scelta. Tenendo premuto il motore si muove senza fermarsi e rallenta fino a fermarsi al rilascio.",
    "<b>Vai alla posizione</b>: scrivi un numero di passi e premi Vai.",
    "<b>STOP</b>: ferma subito il motore e l'eventuale sequenza. Da tastiera: <kbd>Esc</kbd>.",
])}
<h2>La barra della corsa</h2>
{fig("binario", [
    "<b>Zone tratteggiate rosse</b>: fuori dai fine corsa, vietate.",
    "<b>Fascia blu</b>: l'intervallo della sequenza, con una tacca per ogni scatto.",
    "<b>Linea bianca</b>: la posizione attuale.",
], layout="side narrow")}
<p>Sotto la barra: il fine corsa inferiore, la freccia che indica <b>da che parte sta il campione</b> e il
fine corsa superiore. “Avvicina” muove sempre verso il campione, qualunque sia il verso dei numeri: lo
si imposta in Configurazione › Fine corsa (capitolo 9).</p>
<div class="box tip"><span class="t">Tastiera</span><kbd>↑</kbd> allontana, <kbd>↓</kbd> avvicina,
<kbd>⇧</kbd> insieme alla freccia moltiplica il passo per 10, i tasti numerici <kbd>1</kbd> <kbd>2</kbd>
<kbd>3</kbd>… scelgono l'ampiezza, <kbd>Esc</kbd> è lo STOP. Funzionano nella scheda Sessione anche
mentre guardi il live view.</div>
<div class="box warn"><span class="t">Pulsanti fisici</span>I pulsanti sul focheggiatore muovono il motore senza
passare dall'app. L'app li sorveglia e, se la posizione esce dai fine corsa, invia STOP e mostra un
allarme; per una protezione completa leggi il capitolo 9. Se li premi durante una sequenza, la sequenza va
in pausa.</div>
""")

# 6
add(f"""
<h1><span class="n">6</span>Fotocamera, scatto di prova e live view</h1>
{fig("fotocamera", [
    "<b>Stato</b>: Pronta, Scatto…, Disconnessa.",
    "<b>Modello</b> collegato e <span class='ui'>Disconnetti</span>.",
    "<b>Tempo di posa</b> e <b>ISO</b>.",
    "<b>Diaframma</b> e <b>Formato</b> (RAW, JPEG…). Al microscopio, senza obiettivo sulla fotocamera, il diaframma di solito non c'è.",
    "<b>Destinazione</b>: memoria della fotocamera o scheda.",
    "<b>Posa B</b> in secondi: 0 usa il tempo di posa; un valore maggiore di 0 fa una posa B comandata dal Mac, per tempi oltre i 30 s.",
    "<b>Ritardo specchio</b> (reflex), da 0,5 a 2,5 s: attesa fra il sollevamento dello specchio e lo scatto, per far smorzare le vibrazioni. Sulla Nikon D5600 l'app usa il <i>ritardo di esposizione</i> della fotocamera.",
    "<b>Rileggi</b> le impostazioni dalla fotocamera. Dopo ogni modifica l'app rilegge il valore che la fotocamera ha accettato davvero.",
    "<b>Scatto di prova</b>: una foto alla posizione attuale, che compare in Ultimo scatto e nel visualizzatore.",
])}
<h2>Ultimo scatto e live view</h2>
<div class="two">
{fig("ultimo-scatto", [
    "<b>● Live</b>: mostra l'immagine dal vivo della fotocamera.",
    "<b>Apri visualizzatore</b> in una finestra separata (capitolo 8).",
    "<b>Ultimo scatto</b>: un clic lo apre nel visualizzatore.",
    "Nome del file, posizione e temperatura al momento dello scatto.",
], layout="stack")}
{fig("live", [
    "<b>■ Ferma live</b> spegne il live view.",
    "Stato: <b>LIVE</b>, <b>SCATTO…</b> durante uno scatto di prova, <b>IN PAUSA</b> durante la sequenza.",
    "Modello della fotocamera. Doppio clic sull'immagine: schermo intero.",
], layout="stack")}
</div>
<p>Il live view arriva fino a 15 immagini al secondo ed è il modo più comodo per trovare il punto di
partenza e di arrivo della sequenza mentre muovi il focheggiatore con la tastiera. Durante la sequenza
viene spento (lo specchio deve scendere e la fotocamera deve scattare come al solito) e riparte da solo
alla fine. Sulle reflex lo specchio resta sollevato finché il live è acceso.</p>
<div class="box tip"><span class="t">Per mettere a fuoco con precisione</span>Apri il live nel
<b>visualizzatore</b>: puoi ingrandire al 100% e oltre e spostarti sul dettaglio che ti interessa
(capitolo 8).</div>
""")

# 7
add(f"""
<h1><span class="n">7</span>La sequenza di stacking</h1>
{fig("sequenza", [
    "<b>Stato</b>: Pronta, In corso, In pausa, Completata, Errore.",
    "<b>Inizio</b> e <b>Fine</b> in passi. <span class='ui'>⌖ qui</span> copia la posizione attuale.",
    "<b>Passo</b> fra uno scatto e il successivo, in passi del motore (capitolo 11).",
    "<b>Numero di scatti</b>. È collegato al passo: se cambi uno dei due, l'altro si ricalcola.",
    "<b>Riepilogo</b>: scatti, escursione in passi e in µm, passo in µm, durata stimata. Se la sequenza esce dai fine corsa compare un avviso rosso e la sequenza non parte.",
    "<b>Salva in</b>: la cartella delle foto. <span class='ui'>Scegli…</span> apre il pannello del Finder, <span class='ui'>Apri</span> la mostra nel Finder.",
    "<b>Attesa dopo il movimento</b>: tempo per far smorzare le vibrazioni prima dello scatto (1–3 s al microscopio). <b>Pausa dopo lo scatto</b>: tempo per scrivere sulla scheda e ricaricare il flash.",
    "<b>Compensazione gioco</b>: prima del primo scatto il motore arretra di questi passi e poi avanza, così ogni scatto viene raggiunto dalla stessa direzione.",
    "<b>Modalità di scatto</b>: <i>Scarica sul Mac</i> (consigliata), <i>Solo sulla scheda</i>, <i>Solo trigger</i> (più veloce: imposta la destinazione su scheda).",
    "<b>Nome della sessione</b>: le foto vanno in una sottocartella <code>nome_data-ora</code>, con nomi <code>nome_0001</code>, <code>nome_0002</code>…",
    "<b>Torna all'inizio</b> a fine sequenza.",
    "<b>Preset</b>: salva e richiama le impostazioni della sequenza, per esempio uno per obiettivo.",
    "<b>Avanzamento</b>: scatti fatti, tempo che resta, posizione.",
    "<b>Avvia</b>, <b>Pausa</b>/<b>Riprendi</b> e <b>Interrompi</b>.",
    "<b>Apri in Helicon Focus</b>: a fine sequenza carica tutte le foto in Helicon Focus.",
])}
<p>Le impostazioni dei tempi e del gioco sono nel riquadro richiudibile <span class="ui">Tempi, gioco e nome
della sessione</span>. Nella stessa cartella delle foto l'app salva <code>sequence.json</code>, con i parametri
usati e la posizione e la temperatura di ogni scatto.</p>
<h2>Durante la sequenza</h2>
{fig("sequenza-in-corso", [
    "Lo stato diventa <b>In corso</b> (ambra).",
    "Scatti fatti sul totale, tempo stimato che resta e posizione attuale. Sulla barra della corsa le tacche degli scatti fatti cambiano colore.",
    "<b>Pausa</b> sospende dopo lo scatto in corso; <b>Interrompi</b> termina la sequenza. Lo <b>STOP</b> del focheggiatore ferma subito anche il motore.",
], layout="side narrow")}
<ul>
<li>Se premi i <b>pulsanti fisici</b> del focheggiatore, la sequenza va in pausa; alla ripresa torna alla
  posizione giusta e ripete lo scatto.</li>
<li>I campi della sequenza sono bloccati finché la sequenza è in corso.</li>
<li>Ogni nuova foto arriva in Ultimo scatto e nel visualizzatore.</li>
</ul>
""")

# 8
add(f"""
<h1><span class="n">8</span>Il visualizzatore</h1>
<p>Si apre con <span class="ui">Apri visualizzatore ↗</span> o con un clic sull'ultimo scatto, in una finestra
separata che puoi spostare su un secondo monitor. Mostra le foto a piena risoluzione (anche i RAW, convertiti
al volo) con zoom e spostamento, e il live view della fotocamera.</p>
{fig("visualizzatore", [
    "<b>◀ ▶</b> scatto precedente e successivo (frecce <kbd>←</kbd> <kbd>→</kbd>).",
    "Nome del file; numero dello scatto, tipo, posizione, temperatura e ora.",
    "<b>● Live</b> (<kbd>L</kbd>): il live view nella stessa finestra, con zoom e spostamento.",
    "<b>Zoom</b> − e + (<kbd>−</kbd> <kbd>+</kbd>) e livello di ingrandimento.",
    "<b>Adatta</b> (<kbd>0</kbd>), <b>100%</b> (<kbd>1</kbd>: un pixel del sensore = un pixel dello schermo), <b>Reset</b> (<kbd>R</kbd>).",
    "<b>Segui ultimo</b> (<kbd>U</kbd>): mostra da solo ogni nuovo scatto.",
    "<b>Blocca vista</b> (<kbd>K</kbd>): cambiando scatto mantiene zoom e posizione, per confrontare la messa a fuoco nello stesso punto.",
    "<b>Finder</b>: mostra il file nel Finder.",
    "<b>Schermo intero</b> (<kbd>F</kbd>).",
    "<b>Miniature</b>: un clic apre lo scatto. <i>P</i> = scatto di prova, i numeri sono gli scatti della sequenza.",
], layout="full", anchors={n: "b" for n in range(1, 10)})}
<p>Con il mouse: trascina per spostare l'immagine, rotella (o pizzico sul trackpad) per lo zoom centrato
sul cursore, doppio clic per passare da “adatta” al 100% e viceversa. Oltre il 150% i pixel restano netti,
senza sfocatura.</p>
{fig("visualizzatore-live", [
    "<b>■ Ferma live</b> torna alle foto; anche ◀ ▶ o un clic su una miniatura escono dal live.",
    "Stato del live: LIVE, SCATTO…, IN PAUSA durante la sequenza.",
], layout="full", anchors={1: "b"}, caption="Il live view nel visualizzatore, qui con il simulatore a fuoco (la scacchiera è nitida). Al 100% il live view ha la risoluzione dell'anteprima della fotocamera, più bassa di quella delle foto.")}
""")

# 9
add(f"""
<h1><span class="n">9</span>Fine corsa di sicurezza</h1>
<p class="lead">I fine corsa impediscono che l'obiettivo tocchi il vetrino o che la meccanica arrivi a
battuta. Vanno impostati prima di tutto, con calma.</p>
{fig("fine-corsa", [
    "<b>Fine corsa inferiore</b> in passi; <span class='ui'>⌖ Usa posizione attuale</span> lo prende dalla posizione del focheggiatore.",
    "<b>Fine corsa superiore</b>. Vuoto = il massimo del firmware.",
    "<b>Verso il campione</b>: se avvicinandosi al campione i passi diminuiscono o aumentano. Serve a etichettare giusti Avvicina/Allontana.",
    "<b>Salva fine corsa</b>.",
    "<b>Imposta qui lo zero</b>: la posizione attuale diventa 0; fine corsa e sequenza vengono traslati di conseguenza.",
    "<b>Scrivi il massimo nel firmware</b>: il fine corsa superiore diventa il limite del firmware.",
], layout="full")}
<h2>Che cosa protegge che cosa</h2>
<ul>
<li><b>Movimenti comandati dall'app</b> (vai a, Allontana/Avvicina, sequenza, compensazione del gioco):
  l'app li controlla <i>prima</i> di muovere il motore. Il movimento continuo si ferma al fine corsa; una
  sequenza che uscirebbe dai limiti non parte.</li>
<li><b>Pulsanti fisici</b>: l'app legge la posizione ogni 0,2–0,5 s; se esce dai limiti invia STOP e mostra
  l'allarme. Fra una lettura e l'altra il motore può però superare il limite di qualche decina di passi.</li>
</ul>
<h2>Protezione consigliata: limiti nel firmware</h2>
<p>Il firmware applica i suoi limiti anche ai pulsanti fisici: non scende mai sotto 0 e non sale mai oltre
il suo massimo.</p>
<ol class="steps">
<li>Con un obiettivo a secco e senza vetrino, oppure con grande prudenza, porta il tavolino alla posizione
  <b>più vicina al campione che sia ancora sicura</b> e premi <span class="ui">Imposta qui lo zero</span>.</li>
<li>Porta il tavolino alla posizione più lontana utile, premi <span class="ui">⌖ Usa posizione attuale</span>
  sul fine corsa superiore, poi <span class="ui">Salva fine corsa</span> e <span class="ui">Scrivi il massimo nel firmware</span>.</li>
<li>Verifica una volta, a mano e lentamente con i pulsanti fisici, che il focheggiatore si fermi davvero a 0
  e al massimo.</li>
</ol>
<div class="box danger"><span class="t">Attenzione</span>Il fine corsa “verso il campione” dipende dall'obiettivo e dallo
spessore del vetrino: con un obiettivo a corta distanza di lavoro (40×, 100×) il margine è di pochi decimi di
millimetro. Ricontrolla i fine corsa quando cambi obiettivo, e dopo aver cambiato il <b>microstep</b>, che
cambia la scala delle posizioni.</div>
""")

# 10 — meccanica
add(f"""
<h1><span class="n">10</span>Configurazione meccanica: i calcoli</h1>
<p class="lead">L'app ragiona in <b>passi del motore</b>. Per mostrarti spostamenti, escursioni e passi della
sequenza in <b>micrometri</b>, e per calcolare il passo giusto dalla profondità di campo, deve sapere quanti
micrometri vale un passo. Questo numero si chiama <b>risoluzione</b> (µm/passo) e dipende da come il motore
è collegato alla micrometrica.</p>
{fig("meccanica", [
    "<b>Modalità</b>: <i>Calcola dalla meccanica</i> (dai dati qui sotto) oppure <i>Inserisci µm/passo</i> (un valore misurato).",
    "<b>Passi motore per giro</b>: 200 per un motore da 1,8°, 400 per uno da 0,9°.",
    "<b>Microstep</b>: letto dal firmware, non si modifica qui (vedi Motore).",
    "<b>Rapporto di riduzione</b>: quanti giri fa il motore per un giro della manopola.",
    "<b>Corsa per giro manopola</b>: di quanti µm si sposta il tavolino a ogni giro della manopola micrometrica.",
    "<b>Risultato</b>: µm per passo, passi per µm, µm ogni 1000 passi.",
    "<b>Salva meccanica</b>.",
])}
<h2>10.1 La catena della trasmissione</h2>
<p>Dal motore al tavolino il movimento passa per alcuni stadi, e ognuno moltiplica o divide:</p>
{diagram(DIAGRAM_LABELS)}
<div class="formula">
  risoluzione (µm/passo) = {frac("corsa per giro della manopola (µm)", "passi per giro × microstep × rapporto di riduzione")}
  <span class="lbl">È esattamente il calcolo che fa l'app in “Calcola dalla meccanica”.</span>
</div>
<h2>10.2 I quattro numeri, uno per uno</h2>
<h3>Passi motore per giro</h3>
<p>Si ricava dall'angolo di passo scritto sull'etichetta o sulla scheda tecnica del motore:</p>
<div class="formula">passi per giro = {frac("360°", "angolo di passo")}
<span class="lbl">1,8° → 200 passi · 0,9° → 400 passi · 7,5° → 48 passi</span></div>
<p>Il NEMA 14 OMC 14HM11-0404S del focheggiatore myFocuserPro2 è da 0,9°: <b>400</b>. Il NEMA 17
17HS13-0404S-PG27 con riduttore è da 1,8°: <b>200</b>, e il riduttore va nel rapporto (sotto), non qui.</p>
<h3>Microstep</h3>
<p>Il driver può dividere ogni passo in 2, 4, 8, 16 o 32 micro-passi. Con il microstep 1/8 un giro del
motore richiede 8 volte più passi e la risoluzione diventa 8 volte più fine (ma la coppia per micro-passo
cala e la velocità massima in µm/s si riduce di 8 volte).</p>
<ul>
<li><b>myFocuserPro2</b>: il microstep lo imposta il firmware e si cambia in Configurazione › Motore. L'app lo
  legge e lo usa da sola nel calcolo.</li>
<li><b>Ardufocus</b>: il microstep è fissato sulla scheda (ponticelli o collegamenti del driver) e il firmware
  non lo comanda. Imposta in Configurazione › Motore <b>lo stesso valore della scheda</b>, altrimenti il calcolo
  è sbagliato dello stesso fattore. Se non sai qual è, misuralo (10.4).</li>
</ul>
<h3>Rapporto di riduzione</h3>
<p>È il numero di giri del motore per <b>un</b> giro della manopola. Si moltiplicano fra loro tutti gli stadi:</p>
<div class="formula">rapporto = riduttore × {frac("denti della puleggia sulla manopola", "denti della puleggia sul motore")}
<span class="lbl">con ruote a frizione o O-ring: al posto dei denti, i diametri</span></div>
<ul>
<li><b>Accoppiamento diretto</b> (motore sull'asse della manopola, senza riduttore): rapporto 1.</li>
<li><b>Cinghia dentata</b> da una puleggia GT2 da 20 denti sul motore a una da 60 sulla manopola: 60 ÷ 20 = <b>3</b>.</li>
<li><b>Riduttore epicicloidale</b>: il rapporto scritto sul motore. Il PG27 del 17HS13 è 26 103/121 = 26 + 103 ÷ 121
  = <b>26,851</b> (non esattamente 27: usa il valore preciso). Con accoppiamento diretto il rapporto è 26,851; con
  una cinghia 20 → 40 denti diventa 26,851 × 2 = 53,70.</li>
</ul>
<h3>Corsa per giro della manopola</h3>
<p>Di quanto si sposta il tavolino (o il tubo, sui microscopi che muovono l'obiettivo) a ogni giro della
manopola che il motore fa girare, di solito la <b>micrometrica</b>. Molti microscopi hanno 100 µm per giro,
alcuni 200 µm o valori diversi. Il modo più sicuro per saperlo è contare le tacche della manopola:</p>
<div class="formula">corsa per giro = numero di tacche sulla manopola × µm per tacca
<span class="lbl">esempio: 100 tacche da 1 µm = 100 µm per giro · 50 tacche da 2 µm = 100 µm per giro</span></div>
<p>Il valore per tacca è spesso inciso sulla manopola o sul corpo del microscopio (“1 µm”, “2 µm”) o scritto
nel manuale. Se il motore muove la <b>macrometrica</b> invece della micrometrica, la corsa per giro è di
alcuni millimetri: la risoluzione è molto più grossolana e va verificata con cura.</p>

<h2>10.3 Esempi svolti</h2>
<h3>Esempio A: myFocuserPro2 con NEMA 14 e cinghia</h3>
<div class="calc">motore 0,9°            → passi per giro = 360 ÷ 0,9 = 400
microstep              → 1 (passo intero)
pulegge 20 → 60 denti  → rapporto = 60 ÷ 20 = 3
micrometrica           → 100 µm per giro

passi per giro della manopola = 400 × 1 × 3 = 1200
risoluzione = 100 ÷ 1200 = <b>{num(UA, 4)} µm/passo</b>   (12 passi = 1 µm; 1000 passi = {num(UA * 1000, 1)} µm)</div>
<p>È la configurazione delle schermate di questa guida. Con il microstep 1/8 lo stesso focheggiatore darebbe
100 ÷ (400 × 8 × 3) = <b>{num(um_step(100, 400, 8, 3), 4)} µm/passo</b>.</p>
<h3>Esempio B: Ardufocus con NEMA 17 e riduttore PG27</h3>
<div class="calc">motore 1,8°              → passi per giro = 200
microstep (sulla scheda) → 1
riduttore 26 103/121     → 26,851, accoppiamento diretto alla manopola
micrometrica             → 100 µm per giro

passi per giro della manopola = 200 × 1 × 26,851 = {num(200 * GEAR17, 0)}
risoluzione = 100 ÷ {num(200 * GEAR17, 0)} = <b>{num(UB, 4)} µm/passo</b>   (1 µm = {num(1 / UB, 1)} passi)</div>
<p>Il riduttore rende la risoluzione circa 4,5 volte più fine dell'esempio A e dà molta più coppia, ma servono
molti più passi per lo stesso spostamento: per questo l'app permette ampiezze fino a 100 000 passi
(capitolo 12).</p>

<h2>10.4 Verificare con una misura</h2>
<p>Il calcolo vale se tutti i dati sono giusti e se nulla slitta (cinghia lenta, puleggia che gira
sull'asse). Conviene sempre una verifica, ed è indispensabile se non conosci uno dei numeri.</p>
<h3>Con le tacche della micrometrica</h3>
<ol class="steps">
<li>Avvicina sempre dalla stessa direzione (per escludere il gioco): fai qualche centinaio di passi in un
  verso, poi annota la tacca della manopola allineata al riferimento.</li>
<li>Con <span class="ui">Vai alla posizione</span> sposta di un numero di passi <b>N</b> grande, nello stesso verso,
  in modo che la manopola faccia almeno mezzo giro (esempio A: N = 1000; esempio B: N = 5000).</li>
<li>Conta le tacche percorse <b>T</b> e moltiplica per i µm per tacca.</li>
</ol>
<div class="formula">risoluzione misurata = {frac("T × µm per tacca", "N")}</div>
<div class="calc">Esempio A: N = 1000 passi, la manopola avanza di 83 tacche da 1 µm
risoluzione = 83 × 1 ÷ 1000 = <b>0,083 µm/passo</b>   (il calcolo dava {num(UA, 4)}: torna)</div>
<h3>Con un comparatore</h3>
<p>Un comparatore centesimale o millesimale appoggiato al tavolino misura direttamente lo spostamento. Muovi di
N passi (sempre dalla stessa direzione) e dividi lo spostamento in µm per N. Più grande è N, più precisa la misura.</p>
<h3>Se la misura non torna</h3>
<ul>
<li>Differenza di un fattore 2, 4, 8, 16: il <b>microstep</b> non è quello che pensi (tipico dell'Ardufocus).</li>
<li>Differenza di un fattore 2 esatto: motore da 0,9° scambiato per 1,8° o viceversa.</li>
<li>Differenza irregolare, che cambia da una misura all'altra: qualcosa <b>slitta</b> (cinghia, grano della
  puleggia) o il motore <b>perde passi</b> (velocità troppo alta, corrente troppo bassa).</li>
<li>Se i dati della meccanica sono incerti ma la misura è ripetibile, scegli <span class="ui">Inserisci µm/passo</span>
  e scrivi il valore misurato.</li>
</ul>
{fig("meccanica-manuale", [
    "<b>Inserisci µm/passo</b>: per usare un valore misurato.",
    "<b>µm per passo</b> misurati.",
    "Il risultato si aggiorna mentre scrivi.",
], layout="side narrow")}

<h2>10.5 Altri conti utili</h2>
<h3>Corsa utile in millimetri</h3>
<div class="calc">corsa (µm) = (fine corsa superiore − fine corsa inferiore) × risoluzione
esempio A: (45 000 − 2 000) × {num(UA, 4)} = <b>{num(43000 * UA, 0)} µm ≈ {num(43000 * UA / 1000, 2)} mm</b></div>
<h3>Velocità in µm al secondo</h3>
<div class="calc">velocità (µm/s) = passi al secondo × risoluzione
esempio A, firmware a 400 passi/s:   400 × {num(UA, 4)} ≈ <b>{num(400 * UA, 0)} µm/s</b>
esempio B, firmware a 2000 passi/s: 2000 × {num(UB, 4)} ≈ <b>{num(2000 * UB, 0)} µm/s</b></div>
<p>Serve a capire quanto tempo richiede uno spostamento lungo: 1 mm nell'esempio A richiede circa
{num(1000 / (400 * UA), 0)} secondi.</p>
<h3>Il gioco (backlash) in passi</h3>
<p>Quando il motore inverte il verso, per qualche passo la manopola non si muove: è il <b>gioco</b> della
trasmissione (cinghia, denti, riduttore, filettatura della micrometrica). Si compensa in passi, quindi
conviene misurarlo in passi:</p>
<ol class="steps">
<li>Apri il live nel visualizzatore al 100% o più, su un dettaglio piccolo e ben contrastato.</li>
<li>Muovi di qualche centinaio di passi in un verso, poi inverti con l'ampiezza 1 o 10.</li>
<li>Conta i passi dopo l'inversione prima che l'immagine cominci a muoversi: quello è il gioco. Ripeti
  qualche volta e prendi il valore più alto, con un piccolo margine.</li>
</ol>
<p>Dal gioco angolare dichiarato si può stimare l'ordine di grandezza. Il riduttore PG27 dichiara al massimo
1° di gioco all'uscita, cioè 1/360 di giro della manopola:</p>
<div class="calc">gioco in passi = (1° ÷ 360°) × passi per giro della manopola = {num(200 * GEAR17, 0)} ÷ 360 ≈ <b>{num(200 * GEAR17 / 360, 0)} passi</b>
gioco in µm    = (1° ÷ 360°) × 100 µm ≈ <b>{num(100 / 360, 2)} µm</b></div>
<p>Il gioco della cinghia e della micrometrica si aggiunge a questo: la misura col live view resta il dato buono.
Il valore va poi in <b>uno solo</b> dei due posti: la <b>compensazione della sequenza</b> (capitolo 7) oppure il
<b>gioco IN/OUT del firmware</b> (capitolo 12, al massimo 255 passi), non in entrambi.</p>
<h3>Quanto deve essere fine la risoluzione</h3>
<p>Il passo della sequenza (capitolo 11) dovrebbe valere almeno una decina di passi del motore, così gli
arrotondamenti al passo intero contano poco. Con l'esempio A e un obiettivo 60× il passo consigliato è di
circa 7 passi: si può fare, ma per gli obiettivi molto forti conviene una risoluzione più fine (microstep o
riduzione maggiore).</p>
""")

# 11 — passo della sequenza
add(f"""
<h1><span class="n">11</span>Scegliere il passo della sequenza</h1>
<p class="lead">Ogni foto è nitida solo in uno strato sottile del campione, la <b>profondità di campo</b>. Per
avere tutto a fuoco dopo lo stacking, fra uno scatto e il successivo il fuoco non deve spostarsi più di
quello strato, con un po' di sovrapposizione.</p>
{fig("profondita", [
    "<b>Apertura numerica (NA)</b>: il secondo numero inciso sull'obiettivo (10×/<b>0,25</b>).",
    "<b>Ingrandimento sul sensore</b>: ingrandimento dell'obiettivo × fattore dell'adattatore della fotocamera.",
    "<b>Pixel del sensore</b> in µm. Nikon D5600: <b>3,9 µm</b> (23,5 mm ÷ 6000 pixel).",
    "<b>Sovrapposizione</b> fra uno strato nitido e il successivo; il 20–30% è un buon valore.",
    "<b>Risultato</b>: profondità di campo, passo consigliato in µm e in passi del motore.",
    "<b>Usa come passo della sequenza</b>: copia il valore in passi nel campo Passo della sequenza.",
])}
<h2>11.1 La formula</h2>
<p>L'app usa la formula di Berek, la più usata in microscopia:</p>
<div class="formula">profondità di campo (µm) = {frac("λ · n", "NA²")} + {frac("n · e", "M · NA")}
<span class="lbl">λ = lunghezza d'onda = 0,55 µm (luce verde) · n = indice del mezzo fra obiettivo e vetrino = 1 (aria) ·
e = dimensione del pixel del sensore (µm) · M = ingrandimento sul sensore</span></div>
<p>Il primo termine è il limite dell'ottica (diffrazione), il secondo quello del sensore. Poi:</p>
<div class="formula">passo (µm) = profondità di campo × (1 − sovrapposizione) &nbsp;&nbsp;&nbsp; passo (passi motore) = {frac("passo (µm)", "risoluzione (µm/passo)")}</div>
<h3>Esempio svolto: obiettivo 10×/0,25, Nikon D5600, adattatore 1×</h3>
<div class="calc">primo termine    = 0,55 × 1 ÷ 0,25²       = 0,55 ÷ 0,0625 = 8,80 µm
secondo termine  = 1 × 3,9 ÷ (10 × 0,25)  = 3,9 ÷ 2,5     = 1,56 µm
profondità di campo = 8,80 + 1,56 = <b>10,36 µm</b>
passo con il 30% di sovrapposizione = 10,36 × 0,70 = <b>7,25 µm</b>
in passi, esempio A: 7,25 ÷ {num(UA, 4)} = 87,0 → <b>87 passi</b>   esempio B: 7,25 ÷ {num(UB, 4)} → <b>{max(1, round(dof(.25, 10, 3.9) * .7 / UB))} passi</b></div>
<h3>Valori tipici (D5600, adattatore 1×, sovrapposizione 30%)</h3>
{table(["Obiettivo", "Profondità di campo (µm)", "Passo (µm)", "Passi, esempio A", "Passi, esempio B"], dof_rows, right=(1, 2, 3, 4))}
<p style="font-size:9pt;color:#5a6b80">Esempio A = {num(UA, 4)} µm/passo; esempio B = {num(UB, 4)} µm/passo (capitolo 10.3). Nota: {dof_note}</p>
<div class="box tip"><span class="t">L'adattatore della fotocamera</span>Se il raccordo ha un fattore diverso da 1
(per esempio 0,5× o 2,5×), moltiplica l'ingrandimento dell'obiettivo per quel fattore: 10× con adattatore 0,5×
= 5 sul sensore. Cambia solo il secondo termine della formula, che con gli obiettivi deboli conta di più.</div>

<h2>11.2 Inizio, fine e numero di scatti</h2>
<ol class="steps">
<li>Accendi il live (meglio nel visualizzatore, ingrandito) e porta il fuoco <b>appena sopra</b> la parte più
  alta del soggetto che vuoi nitida: premi <span class="ui">⌖ qui</span> accanto a <b>Inizio</b>.</li>
<li>Scendi fino <b>appena sotto</b> la parte più bassa e premi <span class="ui">⌖ qui</span> accanto a <b>Fine</b>.</li>
<li>Scrivi il passo (o usa <span class="ui">Usa come passo della sequenza</span>): l'app calcola il numero di scatti.</li>
</ol>
<div class="formula">numero di scatti = {frac("|fine − inizio|", "passo")} + 1
<span class="lbl">arrotondato per difetto, più uno scatto finale esatto sulla fine se la divisione non è intera</span></div>
<div class="calc">esempio: inizio 24 000, fine 26 000, passo 87
2000 ÷ 87 = 22,99 → 22 + 1 = 23, più lo scatto finale su 26 000 = <b>24 scatti</b>
escursione = 2000 × {num(UA, 4)} = <b>{num(2000 * UA, 1)} µm</b></div>
<p>Al contrario, se scrivi il <b>numero di scatti</b>, l'app ricalcola il passo: passo = escursione ÷ (scatti − 1),
arrotondato al passo intero.</p>
<h2>11.3 Durata stimata</h2>
<p>Per ogni scatto l'app somma:</p>
<div class="formula">attesa dopo il movimento + pausa dopo lo scatto + ritardo specchio + tempo di posa + 1,5 s + {frac("passo", "400")} s</div>
<p>dove 1,5 s è una stima del tempo di scatto e trasferimento e passo ÷ 400 il tempo di spostamento. Con
l'esempio (1,5 s + 0,5 s + 0 + 1/60 s + 1,5 s + 0,22 s ≈ 3,7 s per scatto × 24 scatti) la durata è di circa
<b>1 minuto e mezzo</b>, come nella schermata del capitolo 7. Durante la sequenza la stima viene aggiornata con i
tempi reali.</p>
<div class="box warn"><span class="t">L'attesa dopo il movimento conta</span>Un microscopio vibra per un
po' dopo ogni spostamento. Se le foto risultano mosse o “doppie”, aumenta l'attesa (2–3 s) e, sulle reflex,
il ritardo dello specchio, prima di cercare altre cause.</div>
""")

# 12
add(f"""
<h1><span class="n">12</span>Motore, comandi manuali, aggiornamenti, temperatura</h1>
<h2>Motore (firmware)</h2>
{fig("motore", [
    "<b>Microstep</b>: passo intero, 1/2 … 1/32 (vedi 10.2). Cambiarlo cambia la scala delle posizioni: dopo, ricontrolla i fine corsa.",
    "<b>Velocità</b> del firmware: lenta, media, veloce.",
    "<b>Bobine alimentate a motore fermo</b>: il motore tiene la posizione, ma scalda.",
    "<b>Inverti verso di rotazione</b>.",
    "<b>Compensa il gioco IN / OUT</b>: a ogni inversione verso posizioni più basse (IN) o più alte (OUT) il firmware fa dei passi in più senza contarli, anche con i pulsanti fisici.",
    "<b>Gioco IN / OUT</b> in passi, da 0 a 255 (vedi 10.5).",
    "<b>Rileggi</b> i valori dal firmware.",
])}
<h2>Comandi manuali</h2>
{fig("comandi-manuali", [
    "<b>Ampiezze</b> dei pulsanti Allontana/Avvicina: per decine fino a 1000, 10 000 o 100 000 passi. Con un riduttore servono ampiezze grandi.",
    "<b>Tieni premuto per muovere senza fermarti</b>: al rilascio il motore rallenta e si ferma; si ferma comunque al fine corsa e, se la pagina smette di rispondere, dopo circa un secondo.",
], layout="side")}
<h2>Aggiornamenti</h2>
{fig("aggiornamenti", [
    "Versione dell'<b>app</b> e stato dell'ultimo controllo.",
    "Versione del <b>firmware</b> sul focheggiatore.",
    "<b>Aggiorna firmware</b>: circa 20 secondi, le impostazioni del focheggiatore restano. Non scollegare il cavo; se qualcosa va storto, basta ripetere.",
    "<b>Controlla ora</b> se ci sono aggiornamenti dell'app.",
], layout="side")}
<p>L'app sceglie da sola il firmware adatto alla scheda (myFocuserPro2 o Ardufocus). L'<b>Ardufocus</b> non si
riavvia dal cavo USB: durante l'aggiornamento l'app chiede di premere il <b>tasto reset</b> della scheda.</p>
<h2>Temperatura</h2>
{fig("temperatura", [
    "Temperatura attuale della sonda.",
    "Andamento degli ultimi 60 minuti. La temperatura di ogni scatto viene salvata in <code>sequence.json</code>: utile perché il fuoco si sposta con la dilatazione termica.",
], layout="side")}
""")

# 13
add("""
<h1><span class="n">13</span>Una sessione tipo, passo per passo</h1>
<h2>Una volta sola (o quando cambia la meccanica)</h2>
<ol class="steps">
<li><b>Meccanica</b>: inserisci i dati e controlla la risoluzione con una misura (capitolo 10).</li>
<li><b>Verso del campione</b> e <b>fine corsa</b>, con i limiti scritti nel firmware (capitolo 9).</li>
<li><b>Gioco</b>: misuralo col live view e scegli dove compensarlo (sequenza oppure firmware).</li>
<li><b>Preset</b>: per ogni obiettivo calcola il passo dalla profondità di campo e salva un preset.</li>
</ol>
<h2>A ogni sessione</h2>
<ol class="steps">
<li>Accendi il focheggiatore e la fotocamera (modo M), collega i cavi e apri Focus Stack.</li>
<li>Connetti il focheggiatore e la fotocamera dalla scheda Sessione.</li>
<li>Imposta tempo di posa, ISO e formato; fai uno <b>scatto di prova</b> e controllalo nel visualizzatore al 100%.</li>
<li>Scegli il <b>preset</b> dell'obiettivo (oppure il passo).</li>
<li>Con il <b>live</b> e la tastiera trova la <b>fine</b> e l'<b>inizio</b> della sequenza e premi ⌖ qui.</li>
<li>Controlla il riepilogo: numero di scatti, escursione, durata, nessun avviso rosso.</li>
<li><b>Avvia sequenza</b>. Non toccare il microscopio: le vibrazioni rovinano gli scatti.</li>
<li>A fine sequenza premi <b>Apri in Helicon Focus</b>.</li>
</ol>
""")

# 14
add(f"""<h1><span class="n">14</span>Se qualcosa non va</h1>
<p>Il <b>Registro</b> (terza scheda) elenca con l'ora ogni collegamento, movimento, scatto ed errore: quando
qualcosa non va, leggilo per primo.</p>
""")
add(table(["Problema", "Che cosa fare"], [
    ["La fotocamera non si collega", "Chiudi Foto, Anteprima, Acquisizione Immagine, NX Studio, EOS Utility; scollega e ricollega il cavo con la fotocamera accesa; controlla che sia in modo M e che Wi-Fi/SnapBridge siano spenti."],
    ["Il live view non parte (Nikon D5600)", "Ghiera su <b>M</b> (con le modalità scena il live da USB può essere bloccato), scheda inserita, batteria carica, revisione immagine spenta. Il messaggio esatto compare in basso e nel <b>Registro</b> (“Live view interrotto: …”): è la prima cosa da guardare. Controlla anche di avere l'ultima versione dell'app."],
    ["Il live è lento con due finestre aperte", "Aggiorna l'app: dalla versione 1.0.6 la finestra principale e il visualizzatore ricevono tutti i fotogrammi."],
    ["Il focheggiatore non compare fra le porte", "Premi ⟳ dopo aver collegato il cavo; prova un'altra presa USB o un altro cavo (alcuni cavi caricano soltanto)."],
    ["Il motore vibra ma non gira, o perde passi", "Velocità troppo alta per il carico o corrente del driver troppo bassa; controlla anche che la puleggia non slitti sull'asse."],
    ["Le distanze in µm non tornano", "Rifai la misura del capitolo 10.4; per l'Ardufocus controlla il microstep."],
    ["Allarme rosso “fuori dai fine corsa”", "Un pulsante fisico ha portato il focheggiatore oltre un limite. Riporta la posizione dentro i limiti con Allontana/Avvicina; per evitarlo scrivi i limiti nel firmware (capitolo 9)."],
    ["La sequenza non parte", "Leggi l'avviso rosso nel riepilogo: di solito la sequenza, con la compensazione del gioco, esce dai fine corsa."],
    ["Foto mosse o doppie", "Aumenta l'attesa dopo il movimento e il ritardo specchio; usa la posa B o lo scatto silenzioso se la fotocamera lo permette."],
    ["“Focus Stack è chiuso” nella pagina", "L'app è stata chiusa: riaprila e la pagina si ricarica da sola."],
]))

# 15
add("""<h1><span class="n">15</span>Scorciatoie da tastiera</h1>
<div class="two">
<div class="keep"><h2 style="margin-top:0">Scheda Sessione</h2>
<table><tbody>
<tr><td><kbd>↑</kbd></td><td>allontana l'obiettivo dal campione</td></tr>
<tr><td><kbd>↓</kbd></td><td>avvicina l'obiettivo al campione</td></tr>
<tr><td><kbd>⇧</kbd> + <kbd>↑</kbd>/<kbd>↓</kbd></td><td>passo × 10</td></tr>
<tr><td><kbd>1</kbd> <kbd>2</kbd> <kbd>3</kbd> …</td><td>ampiezza del passo: 1, 10, 100 …</td></tr>
<tr><td><kbd>Esc</kbd></td><td>STOP</td></tr>
</tbody></table></div>
<div class="keep"><h2 style="margin-top:0">Visualizzatore</h2>
<table><tbody>
<tr><td><kbd>←</kbd> <kbd>→</kbd></td><td>scatto precedente / successivo</td></tr>
<tr><td><kbd>L</kbd></td><td>live view acceso / spento</td></tr>
<tr><td><kbd>−</kbd> <kbd>+</kbd></td><td>zoom</td></tr>
<tr><td><kbd>0</kbd> o <kbd>R</kbd></td><td>adatta alla finestra</td></tr>
<tr><td><kbd>1</kbd></td><td>100%</td></tr>
<tr><td><kbd>U</kbd></td><td>segui ultimo</td></tr>
<tr><td><kbd>K</kbd></td><td>blocca vista</td></tr>
<tr><td><kbd>F</kbd></td><td>schermo intero</td></tr>
</tbody></table></div>
</div>
<p style="margin-top:8mm;color:#5a6b80;font-size:9pt">Focus Stack è software libero (licenza MIT) ·
github.com/teoteo/focus-stack · Il firmware deriva da myFocuserPro2 di Robert Brown (licenza MIT).</p>
""")
