import Foundation

/// Testi dell'app nativa (menu e dialoghi), nella lingua scelta in Configurazione.
/// Stessa regola del server: settings.json "language", altrimenti la prima lingua di macOS se è una delle
/// cinque, se no l'inglese. I testi dell'interfaccia web li traduce il server.
enum Texts {
    static let languages = ["it", "en", "fr", "de", "es"]

    static let code: String = {
        if let lang = settingsLanguage(), languages.contains(lang) { return lang }
        let system = String((Locale.preferredLanguages.first ?? "en").prefix(2))
        return languages.contains(system) ? system : "en"
    }()

    private static func settingsLanguage() -> String? {
        let url = Paths.home.appendingPathComponent("Library/Application Support/MyFocuserStack/settings.json")
        guard let data = try? Data(contentsOf: url),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any] else { return nil }
        return obj["language"] as? String
    }

    /// testi = [italiano, inglese, francese, tedesco, spagnolo]
    private static func tx(_ texts: [String]) -> String {
        texts[languages.firstIndex(of: code) ?? 1]
    }

    static var about: String { tx(["Informazioni su Focus Stack", "About Focus Stack", "À propos de Focus Stack", "Über Focus Stack", "Acerca de Focus Stack"]) }
    static var settings: String { tx(["Impostazioni…", "Settings…", "Réglages…", "Einstellungen …", "Ajustes…"]) }
    static var services: String { tx(["Servizi", "Services", "Services", "Dienste", "Servicios"]) }
    static var hide: String { tx(["Nascondi Focus Stack", "Hide Focus Stack", "Masquer Focus Stack", "Focus Stack ausblenden", "Ocultar Focus Stack"]) }
    static var hideOthers: String { tx(["Nascondi altre", "Hide Others", "Masquer les autres", "Andere ausblenden", "Ocultar otros"]) }
    static var showAll: String { tx(["Mostra tutte", "Show All", "Tout afficher", "Alle einblenden", "Mostrar todo"]) }
    static var quit: String { tx(["Esci da Focus Stack", "Quit Focus Stack", "Quitter Focus Stack", "Focus Stack beenden", "Salir de Focus Stack"]) }

    static var edit: String { tx(["Modifica", "Edit", "Édition", "Bearbeiten", "Edición"]) }
    static var undo: String { tx(["Annulla", "Undo", "Annuler", "Widerrufen", "Deshacer"]) }
    static var redo: String { tx(["Ripeti", "Redo", "Rétablir", "Wiederholen", "Rehacer"]) }
    static var cut: String { tx(["Taglia", "Cut", "Couper", "Ausschneiden", "Cortar"]) }
    static var copy: String { tx(["Copia", "Copy", "Copier", "Kopieren", "Copiar"]) }
    static var paste: String { tx(["Incolla", "Paste", "Coller", "Einsetzen", "Pegar"]) }
    static var selectAll: String { tx(["Seleziona tutto", "Select All", "Tout sélectionner", "Alles auswählen", "Seleccionar todo"]) }

    static var view: String { tx(["Vista", "View", "Présentation", "Darstellung", "Visualización"]) }
    static var back: String { tx(["Indietro", "Back", "Précédent", "Zurück", "Atrás"]) }
    static var forward: String { tx(["Avanti", "Forward", "Suivant", "Vorwärts", "Adelante"]) }
    static var reload: String { tx(["Ricarica la pagina", "Reload Page", "Recharger la page", "Seite neu laden", "Volver a cargar la página"]) }
    static var actualSize: String { tx(["Dimensioni reali", "Actual Size", "Taille réelle", "Originalgröße", "Tamaño real"]) }
    static var zoomIn: String { tx(["Ingrandisci", "Zoom In", "Agrandir", "Vergrößern", "Ampliar"]) }
    static var zoomOut: String { tx(["Riduci", "Zoom Out", "Réduire", "Verkleinern", "Reducir"]) }
    static var fullScreen: String { tx(["Schermo intero", "Enter Full Screen", "Plein écran", "Vollbild", "Pantalla completa"]) }

    static var window: String { tx(["Finestra", "Window", "Fenêtre", "Fenster", "Ventana"]) }
    static var minimize: String { tx(["Contrai", "Minimize", "Placer dans le Dock", "Im Dock ablegen", "Minimizar"]) }
    static var zoom: String { tx(["Ridimensiona", "Zoom", "Réduire/agrandir", "Zoomen", "Zoom"]) }
    static var close: String { tx(["Chiudi finestra", "Close Window", "Fermer la fenêtre", "Fenster schließen", "Cerrar ventana"]) }
    static var mainWindow: String { "Focus Stack" }
    static var bringAll: String { tx(["Porta tutto in primo piano", "Bring All to Front", "Tout ramener au premier plan", "Alle nach vorne bringen", "Traer todo al frente"]) }

    static var help: String { tx(["Aiuto", "Help", "Aide", "Hilfe", "Ayuda"]) }
    static var guide: String { tx(["Guida di Focus Stack", "Focus Stack Guide", "Guide de Focus Stack", "Focus Stack-Anleitung", "Guía de Focus Stack"]) }
    static var showLog: String { tx(["Mostra il registro", "Show Log", "Afficher le journal", "Protokoll anzeigen", "Mostrar el registro"]) }

    static var stackDone: String { tx(["Pila completata", "Stack complete", "Pile terminée", "Stapel abgeschlossen", "Pila completada"]) }
    static var stackError: String { tx(["Pila fermata da un errore", "Stack stopped by an error", "Pile arrêtée par une erreur", "Stapel durch einen Fehler angehalten", "Pila detenida por un error"]) }
    static var calibrationDone: String { tx(["Calibrazione completata", "Calibration complete", "Calibration terminée", "Kalibrierung abgeschlossen", "Calibración completada"]) }
    static var calibrationError: String { tx(["Calibrazione fermata da un errore", "Calibration stopped by an error", "Calibration arrêtée par une erreur", "Kalibrierung durch einen Fehler angehalten", "Calibración detenida por un error"]) }
    static func shots(_ n: Int) -> String {
        tx(["\(n) scatti", "\(n) shots", "\(n) photos", "\(n) Aufnahmen", "\(n) fotos"])
    }

    static var starting: String { tx(["Avvio di Focus Stack…", "Starting Focus Stack…", "Démarrage de Focus Stack…", "Focus Stack wird gestartet …", "Iniciando Focus Stack…"]) }
    static var serverFailed: String { tx(["Il server non è partito. Dettagli nel registro: ", "The server did not start. Details in the log: ", "Le serveur n'a pas démarré. Détails dans le journal : ", "Der Server ist nicht gestartet. Details im Protokoll: ", "El servidor no se ha iniciado. Detalles en el registro: "]) }
    static var busyQuit: String { tx(["È in corso una sequenza di scatti. Chiudendo Focus Stack la sequenza viene interrotta e il motore fermato.", "A shooting sequence is running. Quitting Focus Stack stops the sequence and the motor.", "Une séquence de prises de vue est en cours. Quitter Focus Stack arrête la séquence et le moteur.", "Eine Aufnahmeserie läuft. Wenn Sie Focus Stack beenden, werden die Serie und der Motor gestoppt.", "Hay una secuencia de disparos en curso. Al salir de Focus Stack se detienen la secuencia y el motor."]) }
    static var cancel: String { tx(["Annulla", "Cancel", "Annuler", "Abbrechen", "Cancelar"]) }
    static var quitButton: String { tx(["Chiudi", "Quit", "Quitter", "Beenden", "Salir"]) }
    static var ok: String { "OK" }
    static var choose: String { tx(["Scegli", "Choose", "Choisir", "Auswählen", "Elegir"]) }
}

enum Paths {
    /// Cartella Inizio. FOCUSSTACK_HOME serve alle prove (cartella finta, passata anche al server): si può mettere
    /// in LSEnvironment dell'Info.plist, dove invece macOS ignora HOME. Altrimenti HOME, come il server.
    static let overrideHome: String? = {
        let h = ProcessInfo.processInfo.environment["FOCUSSTACK_HOME"] ?? ""
        return h.isEmpty ? nil : h
    }()
    static let home: URL = {
        if let h = overrideHome { return URL(fileURLWithPath: h) }
        if let h = ProcessInfo.processInfo.environment["HOME"], !h.isEmpty { return URL(fileURLWithPath: h) }
        return URL(fileURLWithPath: NSHomeDirectory())
    }()
    static let log = home.appendingPathComponent("Library/Logs/FocusStack.log")
}

/// Registro dell'app nativa (~/Library/Logs/FocusStack-app.log): avvio, notifiche, errori che la pagina non vede.
/// Il registro del server resta FocusStack.log.
enum AppLog {
    static let url = Paths.home.appendingPathComponent("Library/Logs/FocusStack-app.log")
    private static let queue = DispatchQueue(label: "AppLog")

    static func write(_ text: String) {
        let line = "\(ISO8601DateFormatter().string(from: Date())) \(text)\n"
        queue.async {
            if let h = try? FileHandle(forWritingTo: url) {
                h.seekToEndOfFile()
                h.write(Data(line.utf8))
                try? h.close()
            } else {
                try? FileManager.default.createDirectory(at: url.deletingLastPathComponent(), withIntermediateDirectories: true)
                try? Data(line.utf8).write(to: url)
            }
        }
    }
}

/// Preferenze dell'app per Mac, scelte in Configurazione (web/native.js getPref/setPref) e tenute in UserDefaults.
enum Prefs {
    /// Con due schermi il visualizzatore si apre sull'altro, a tutto schermo (attivo se non è mai stato cambiato).
    static var viewerOtherScreen: Bool {
        UserDefaults.standard.object(forKey: "ViewerOtherScreen") as? Bool ?? true
    }

    static func value(_ key: String) -> Any? {
        switch key {
        case "viewerOtherScreen": return viewerOtherScreen
        default: return nil
        }
    }

    static func set(_ key: String, _ value: Any?) {
        switch key {
        case "viewerOtherScreen": UserDefaults.standard.set(value as? Bool ?? true, forKey: "ViewerOtherScreen")
        default: break
        }
    }
}
