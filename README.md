# Focus Stack — focheggiatore myFocuserPro2 + fotocamera per microscopia

Controlla da Safari (macOS) un focheggiatore DIY **myFocuserPro2** montato sul microscopio
e una fotocamera **Sony / Nikon / Canon** via USB, eseguendo sequenze automatiche
*muovi → attendi → scatta* pronte da elaborare in **Helicon Focus**.

## Perché un server locale + PWA (e non una PWA pura)

Safari non supporta né Web Serial né WebUSB, quindi una pagina web non può parlare
direttamente con l'Arduino o con la fotocamera. L'app è quindi divisa in due parti:

```
Safari (PWA, interfaccia)  ⇄  http://localhost:8765  ⇄  server Python
                                                        ├─ pyserial  → myFocuserPro2 (USB seriale)
                                                        └─ libgphoto2 → fotocamera (USB PTP)
```

Il server ascolta solo su `127.0.0.1`, quindi non è raggiungibile da altri computer.

## Installazione

1. Scarica `FocusStack-<versione>.zip` dall'[ultima release](https://github.com/teoteo/focus-stack/releases/latest)
   e aprilo: compare **Focus Stack**.
2. Trascina *Focus Stack* nella cartella **Applicazioni** (prima di aprirla).
3. Aprila. macOS avvisa che non può verificare lo sviluppatore (l'app non è firmata da Apple):
   apri **Impostazioni di Sistema › Privacy e sicurezza**, scorri in basso e premi **Apri comunque**.
   Serve solo la prima volta.

L'app contiene già tutto (Python, librerie, firmware): non serve installare altro. Funziona sui Mac
Apple Silicon (macOS 14 o successivo) e Intel (macOS 13 o successivo).

**Aggiornamenti:** all'avvio, e poi ogni 6 ore, l'app controlla le release su GitHub. Se c'è una
versione nuova compare una barra in alto con **Aggiorna e riavvia**: l'app scarica la nuova versione,
si chiude e si riapre da sola. Lo stesso controllo si fa a mano da *Configurazione › Aggiornamenti*.

**Firmware del focheggiatore:** l'app contiene anche il firmware. Quando il focheggiatore collegato ha
un firmware più vecchio (o quello originale myFocuserPro2), la barra in alto lo segnala e in
*Configurazione › Aggiornamenti* si aggiorna con un clic (circa 20 secondi, le impostazioni del
focheggiatore restano). Il caricamento usa il bootloader dell'Arduino, senza avrdude né Arduino IDE.

## Avvio

1. Fai doppio clic su **`Avvia Focus Stack.command`**. La prima volta crea l'ambiente
   Python e installa le dipendenze; poi apre Safari su `http://localhost:8765`.
2. Per provare senza hardware, spunta **Simulatore** nei pannelli Focheggiatore e Fotocamera.

**Come app per Mac:** Focus Stack.app avvia il server senza finestra del Terminale, apre Safari e
resta nel Dock finché il server è acceso; un clic sull'icona nel Dock riporta in primo piano la
pagina. Se il server non parte mostra un avviso; il registro è in `~/Library/Logs/FocusStack.log`.
Il punto 1 qui sopra (`Avvia Focus Stack.command`) serve solo per lo sviluppo, con il codice di
questa cartella.

Da Terminale: `.venv/bin/python run.py [--port 8765] [--no-browser]`

**Spegnimento:** chiudi l'app Focus Stack (⌘Q, oppure Esci dal menu dell'icona nel Dock). Il
server prima interrompe un'eventuale sequenza (l'app chiede conferma) e ferma il motore, poi si
spegne; la pagina in Safari mostra “Focus Stack è chiuso” e si ricarica da sola quando riapri l'app.
Se il server è stato avviato con “Avvia Focus Stack.command”, si spegne con `Ctrl+C` nella finestra
del Terminale (o chiudendola).
Chiudere Safari *non* spegne il server.
Se apri l'app mentre il server è già acceso, mostra solo la pagina; per ricaricare il codice dopo
un aggiornamento chiudi l'app e riaprila. “Avvia Focus Stack.command” invece chiude un server già
acceso e lo sostituisce con la versione aggiornata.

Requisiti: macOS con Python 3.10 o successivo (`brew install python`). La libreria libgphoto2
è già inclusa nel pacchetto `gphoto2` di pip, quindi Homebrew non serve per la fotocamera.

## Interfaccia

Il tema scuro è quello predefinito; il pulsante ◐ in alto a destra passa al tema chiaro.
L'app è divisa in tre schede:

- **Sessione**: posizione, barra dei fine corsa, movimento manuale, sequenza, fotocamera e ultimo scatto.
- **Configurazione**: fine corsa, meccanica, motore (firmware), temperatura e calcolo della profondità di campo.
- **Registro**: tutti gli eventi della sessione.

Nella barra sotto la posizione:

- le **zone tratteggiate rosse** sono quelle vietate;
- la **fascia blu** è l'intervallo della sequenza, con una tacca per ogni scatto;
- la **linea bianca** è la posizione attuale.

Tastiera nella scheda Sessione:

| Tasto | Azione |
|---|---|
| ↑ | allontana l'obiettivo |
| ↓ | avvicina l'obiettivo |
| ⇧ con ↑ o ↓ | passo ×10 |
| 1, 2, 3, 4 | ampiezza del passo: 1, 10, 100, 1000 passi |
| Esc | STOP |

## Fine corsa (sicurezza del microscopio)

In **Configurazione › Fine corsa di sicurezza** imposti il fine corsa inferiore e quello superiore,
anche con *⌖ Usa posizione attuale*, e indichi in quale verso l'obiettivo si avvicina al campione.

- **Movimenti comandati dall'app**: il server controlla vai-a, jog, sequenza e compensazione del gioco
  *prima* di muovere il motore. Il jog si ferma al fine corsa; una sequenza che uscirebbe dai limiti non parte.
- **Pulsanti fisici del focheggiatore**: muovono il motore senza passare dall'app.
  - Il server legge la posizione ogni 0,2–0,5 s. Se esce dai limiti invia STOP e mostra un allarme rosso,
    ma tra una lettura e l'altra il motore può superare il limite di qualche decina di passi.
  - Protezione consigliata, applicata dal firmware stesso anche ai pulsanti:
    1. porta l'obiettivo al punto più basso sicuro e premi **Imposta qui lo zero**
       (fine corsa e sequenza vengono traslati di conseguenza);
    2. porta l'obiettivo al punto più alto sicuro, usalo come fine corsa superiore e premi
       **Scrivi il massimo nel firmware**.
  - Verifica una volta, a mano e lentamente, che il tuo firmware blocchi davvero i pulsanti a 0 e al massimo.
- **Pulsanti premuti durante una sequenza**: la sequenza va in pausa e, alla ripresa, ripete lo scatto
  dalla posizione corretta.

## Meccanica e motore

- **µm per passo**: si calcolano da passi motore per giro × microstep (letto dal firmware) × rapporto
  di riduzione e dalla corsa della micrometrica per giro. In alternativa si inseriscono a mano.
- **Motore**: microstep, velocità, bobine alimentate a motore fermo (tengono la posizione), inversione
  del verso, gioco del firmware. Il gioco lo compensa già l'app nella sequenza: lascia spento quello
  del firmware.
- **Temperatura**: grafico dell'ultima ora. Il valore di ogni scatto viene salvato in `sequence.json`.

## Focheggiatore: connessione

- Collega l'Arduino e scegli la porta `/dev/cu.usbserial-…`, `/dev/cu.wchusbserial…` o
  `/dev/cu.usbmodem…`. La velocità è 9600 baud.
- All'apertura della porta l'Arduino si resetta: la connessione richiede circa 2–3 s.
- Protocollo: driver INDI `myfocuserpro2` (`:00#` posizione, `:05xxxx#` vai a, `:27#` stop, …),
  implementato in `backend/focuser.py`.

## Visualizzatore scatti

Clic sull'ultimo scatto o su **Apri visualizzatore ↗**: si apre in una finestra separata, che puoi
spostare su un secondo monitor.

| Comando | Tasto | Effetto |
|---|---|---|
| **−** / **+** | − / + | zoom |
| **Adatta** / **Reset** | 0 o R | immagine intera nella finestra |
| **100%** | 1 | un pixel del sensore = un pixel dello schermo. Oltre il 150% i pixel restano netti, senza sfocatura di interpolazione |
| Trascina con il mouse | — | sposta l'immagine |
| Rotella (o pinch sul trackpad) | — | zoom centrato sul cursore |
| Doppio clic | — | alterna adatta ↔ 100% |
| ◀ ▶ e miniature in basso | ← → | scatto precedente o successivo |
| **Segui ultimo** | L | mostra automaticamente ogni nuovo scatto |
| **Blocca vista** | K | mantiene zoom e posizione cambiando scatto, utile per confrontare la messa a fuoco nello stesso punto |
| Schermo intero | F | — |

Gli scatti RAW vengono convertiti in JPEG con `sips` di macOS, prima un'anteprima e poi la piena risoluzione.
La conversione è in cache in `~/Library/Caches/MyFocuserStack`.

## Fotocamera

| Marca | Impostazioni sulla fotocamera |
|---|---|
| Sony | Menu USB → **PC Remote**; modo **M** |
| Nikon | modo **M**; disattiva la revisione immagine |
| Canon | modo **M**; lo scatto va in RAM, oppure sulla scheda se *Destinazione = card* |

- **Rileva** (⟳) e poi **Connetti**. Da qui si impostano tempo di posa, ISO, diaframma,
  formato e destinazione; dopo ogni modifica l'app rilegge il valore che la fotocamera ha
  effettivamente accettato.
- **Posa Bulb (s)** > 0 usa la posa B controllata dal computer, per tempi oltre i 30 s.
- **Se la connessione fallisce:** macOS (`ptpcamerad`) si appropria della fotocamera appena
  la colleghi. L'app termina quel processo prima di connettersi; se non basta, chiudi Foto,
  Anteprima, Acquisizione Immagine, EOS Utility e NX Studio, poi riprova.
- Lo **scatto di prova** finisce nella galleria e si apre nel visualizzatore come gli scatti della sequenza.

## Sequenza

| Campo | Significato |
|---|---|
| Inizio / Fine | posizioni in passi (⌖ copia la posizione attuale) |
| Passo / N. scatti | sono collegati: modificandone uno si ricalcola l'altro |
| Attesa dopo movimento | smorzamento delle vibrazioni prima dello scatto (1–3 s su un microscopio) |
| Pausa dopo scatto | tempo per scrivere sulla scheda e ricaricare il flash |
| Compensazione gioco | prima del primo scatto il motore arretra di N passi e poi avanza, così ogni scatto viene raggiunto dalla stessa direzione |
| Modalità | **Scarica sul Mac** (consigliata), **Solo scheda**, **Solo trigger** (più veloce; con questa imposta la destinazione su scheda) |

**Cartella di salvataggio:** nella scheda Sequenza, riga *Salva in*. **Scegli…** apre il pannello
"Scegli cartella" di macOS; **Apri** mostra la cartella nel Finder. Safari non può leggere percorsi
del disco, quindi il pannello lo apre il server. Se la cartella non esiste viene creata e, prima di
salvarla, l'app verifica di poterci scrivere.

Gli scatti vengono salvati nella cartella scelta (predefinita `~/Pictures/FocusStack`), in una
sottocartella `<nome>_<data-ora>/`, con nomi
`<nome>_0001.ARW`, `_0002…`. Nella stessa cartella c'è `sequence.json` con i parametri usati.
A fine sequenza **Apri in Helicon Focus** carica direttamente tutte le immagini.

Pausa, ripresa e interruzione sono sempre disponibili; **STOP** ferma subito anche il motore.
Le sequenze si possono salvare come **preset**, ad esempio uno per obiettivo.

## Pubblicare una nuova versione

Sul Mac di sviluppo servono `gh` autenticato (`gh auth login`), `arduino-cli` con il core
`arduino:avr` e le librerie di myFocuserPro2 in `~/Documents/Arduino/libraries`.

1. Aumenta il numero in `VERSION` (es. `1.0.0` → `1.0.1`).
2. Se hai modificato il firmware, aumenta anche `FSBUILD` in `firmware/myFP2F_DRV8825_330/fsbuild.h`:
   è il numero con cui l'app capisce che il focheggiatore va aggiornato.
3. Fai il commit e il push delle modifiche.
4. Esegui `./build_release.sh --publish`: compila il firmware, scarica Python per Apple Silicon e
   Intel, assembla l'app universale (~60 MB) e crea la release `v<VERSIONE>` su GitHub.
   Senza `--publish` crea solo `build/dist/FocusStack-<VERSIONE>.zip` per provarla.

Le app installate vedono la nuova release entro 6 ore (o subito con *Controlla ora*).

## Firmware

`firmware/myFP2F_DRV8825_330` è myFocuserPro2 330 di Robert Brown (licenza MIT, vedi le note di
copyright nei file) per scheda DRV8825, con: pulsanti, sonda di temperatura, display OLED a tre
righe (Position, Target, Temp) senza sfarfallio; pulsanti con movimento continuo a velocità
crescente (`PB_SPEED*` in `focuserconfig.h`); rampa di accelerazione e decelerazione per i movimenti
comandati (`MOVE_*`); comando `:97#` che restituisce il numero di build (`fsbuild.h`).

## Struttura

```
backend/focuser.py   driver seriale myFocuserPro2 + simulatore
backend/camera.py    controllo fotocamera (python-gphoto2, sessione persistente) + simulatore
backend/sequence.py  motore delle sequenze
backend/main.py      API REST + WebSocket di stato
backend/settings.py  impostazioni in ~/Library/Application Support/MyFocuserStack/
backend/updater.py   versione, aggiornamenti da GitHub, firmware incluso
backend/flasher.py   caricamento del firmware sull'Arduino (protocollo STK500 del bootloader)
packaging/           programma di avvio dell'app (AppleScript)
build_release.sh     costruzione e pubblicazione dell'app universale
firmware/            sorgente del firmware del focheggiatore
web/index.html …     interfaccia principale (PWA, nessuna dipendenza esterna)
web/viewer.*         visualizzatore con zoom e pan
```

## Licenza

MIT (vedi `LICENSE`). Il firmware in `firmware/` deriva da myFocuserPro2 di Robert Brown e
collaboratori, anch'esso con licenza MIT: le note di copyright originali sono nei file.
