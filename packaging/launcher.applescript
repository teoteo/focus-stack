-- Focus Stack.app (applet "stay open" creato da build_release.sh).
-- Avvia il server Python incluso nell'app, resta nel Dock finché il server è acceso e,
-- quando si chiude l'app (⌘Q o Esci dal Dock), spegne il server.
-- Tutto è dentro il pacchetto: Contents/Resources/app (codice) e python-arm64 / python-x86_64.

-- Variabili globali e non "property": gli applet salvano le property dentro il pacchetto
-- alla chiusura, e questo modificherebbe l'app firmata.
global serverURL, started, pythonPath

on run
	set serverURL to "http://127.0.0.1:8765/"
	set started to false
	set res to (POSIX path of (path to me)) & "Contents/Resources/"
	if (do shell script "uname -m") is "arm64" then
		set pythonPath to res & "python-arm64/bin/python3"
	else
		set pythonPath to res & "python-x86_64/bin/python3"
	end if
	if serverAlive() then
		-- server già acceso: mostra solo l'interfaccia
		do shell script "open -a Safari " & quoted form of serverURL
	else
		startServer(res)
	end if
	set started to true
end run

-- clic sull'icona nel Dock: riporta in primo piano l'interfaccia
on reopen
	do shell script "open -a Safari " & quoted form of serverURL
end reopen

-- se il server si spegne (es. durante un aggiornamento) l'app si chiude da sola
on idle
	if started and not serverAlive() then
		set started to false
		tell me to quit
	end if
	return 3
end idle

on quit
	if serverAlive() then
		if sequenceBusy() then
			set cancelLabel to tx({"Annulla", "Cancel", "Annuler", "Abbrechen", "Cancelar"})
			try
				display dialog tx({"È in corso una sequenza di scatti. Chiudendo Focus Stack la sequenza viene interrotta e il motore fermato.", "A shooting sequence is running. Quitting Focus Stack stops the sequence and the motor.", "Une séquence de prises de vue est en cours. Quitter Focus Stack arrête la séquence et le moteur.", "Eine Aufnahmeserie läuft. Wenn Sie Focus Stack beenden, werden die Serie und der Motor gestoppt.", "Hay una secuencia de disparos en curso. Al salir de Focus Stack se detienen la secuencia y el motor."}) buttons {cancelLabel, tx({"Chiudi", "Quit", "Quitter", "Beenden", "Salir"})} default button cancelLabel cancel button cancelLabel with title "Focus Stack" with icon caution
			on error number -128
				return -- l'utente ha annullato: l'app resta aperta
			end try
		end if
		try
			do shell script "curl -s -m 5 -X POST -H 'X-FocusStack: 1' -H 'Content-Type: application/json' -d '{}' " & serverURL & "api/shutdown"
		end try
		-- attende che il server sia davvero spento (chiude le connessioni con l'hardware)
		repeat 40 times
			if not serverAlive() then exit repeat
			delay 0.25
		end repeat
	end if
	continue quit
end quit

on startServer(res)
	set bundlePath to text 1 thru -2 of (POSIX path of (path to me))
	set logFile to (POSIX path of (path to library folder from user domain)) & "Logs/FocusStack.log"
	-- l'app è già stata approvata all'apertura: si toglie la "quarantena" di macOS dai file
	-- interni, altrimenti Python incluso nell'app verrebbe bloccato come programma non verificato
	try
		do shell script "xattr -dr com.apple.quarantine " & quoted form of bundlePath
	end try
	-- "cd ...;" separato e tutti i canali rediretti: altrimenti do shell script resta in attesa
	-- finché il server è acceso e l'app non risponde più
	do shell script "cd " & quoted form of (res & "app") & "; FOCUSSTACK_APP=" & quoted form of bundlePath & " PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 nohup " & quoted form of pythonPath & " run.py > " & quoted form of logFile & " 2>&1 < /dev/null &"
	repeat 80 times
		if serverAlive() then return
		delay 0.25
	end repeat
	set tailLog to ""
	try
		set tailLog to do shell script "tail -5 " & quoted form of logFile
	end try
	display alert "Focus Stack" message tx({"Il server non è partito. Dettagli nel registro: ", "The server did not start. Details in the log: ", "Le serveur n'a pas démarré. Détails dans le journal : ", "Der Server ist nicht gestartet. Details im Protokoll: ", "El servidor no se ha iniciado. Detalles en el registro: "}) & logFile & return & return & tailLog as critical
	quit
end startServer

-- lingua dei dialoghi: quella scelta in Configurazione (settings.json: it, en, fr, de, es),
-- altrimenti la prima lingua di macOS se è una di queste, se no l'inglese
on appLanguage()
	try
		return do shell script "l=$(plutil -extract language raw -o - \"$HOME/Library/Application Support/MyFocuserStack/settings.json\" 2>/dev/null); case \"$l\" in it|en|fr|de|es) echo \"$l\";; *) s=$(defaults read -g AppleLanguages 2>/dev/null | sed -n 2p | tr -d ' \",' | cut -c1-2); case \"$s\" in it|en|fr|de|es) echo \"$s\";; *) echo en;; esac;; esac"
	on error
		return "en"
	end try
end appLanguage

-- testi = {italiano, inglese, francese, tedesco, spagnolo}
on tx(texts)
	set langs to {"it", "en", "fr", "de", "es"}
	set code to appLanguage()
	repeat with i from 1 to count of langs
		if item i of langs is code then return item i of texts
	end repeat
	return item 2 of texts
end tx

on serverAlive()
	try
		do shell script "curl -s -m 1 -o /dev/null " & serverURL & "api/state"
		return true
	on error
		return false
	end try
end serverAlive

on sequenceBusy()
	try
		set seqState to do shell script "curl -s -m 2 " & serverURL & "api/state | " & quoted form of pythonPath & " -c 'import json,sys; print(json.load(sys.stdin)[\"sequence\"][\"state\"])'"
		return seqState is in {"running", "paused", "stopping"}
	on error
		return false
	end try
end sequenceBusy
