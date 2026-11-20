import AppKit
import UserNotifications
import WebKit

/// Messaggi dalla pagina (web/native.js → window.webkit.messageHandlers.focusstack).
final class Bridge: NSObject, WKScriptMessageHandlerWithReply, UNUserNotificationCenterDelegate {
    var onTheme: (() -> Void)?
    private let dock = DockProgress()
    private var askedNotifications = false

    func userContentController(_ ucc: WKUserContentController, didReceive message: WKScriptMessage,
                               replyHandler: @escaping (Any?, String?) -> Void) {
        guard let body = message.body as? [String: Any], let cmd = body["cmd"] as? String else {
            replyHandler(nil, "messaggio non valido")
            return
        }
        switch cmd {
        case "chooseFolder":
            chooseFolder(start: body["start"] as? String, prompt: body["prompt"] as? String,
                         window: message.webView?.window) { replyHandler($0 ?? NSNull(), nil) }
        case "getPref":
            replyHandler(Prefs.value(body["key"] as? String ?? ""), nil)
        case "setPref":
            Prefs.set(body["key"] as? String ?? "", body["value"])
            replyHandler(nil, nil)
        case "theme":
            if let t = body["theme"] as? String, t != Theme.current || NSApp.appearance == nil {
                Theme.current = t
                onTheme?()
            }
            replyHandler(nil, nil)
        default:
            replyHandler(nil, "comando sconosciuto: \(cmd)")
        }
    }

    // MARK: cartella

    private func chooseFolder(start: String?, prompt: String?, window: NSWindow?, done: @escaping (String?) -> Void) {
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.canCreateDirectories = true
        panel.allowsMultipleSelection = false
        panel.prompt = Texts.choose
        if let prompt { panel.message = prompt }
        if let start, !start.isEmpty {
            let url = URL(fileURLWithPath: (start as NSString).expandingTildeInPath)
            if FileManager.default.fileExists(atPath: url.path) { panel.directoryURL = url }
        }
        let finish: (NSApplication.ModalResponse) -> Void = { resp in
            done(resp == .OK ? panel.url?.path : nil)
        }
        if let window, window.isVisible { panel.beginSheetModal(for: window, completionHandler: finish) }
        else { finish(panel.runModal()) }
    }

    // MARK: pila e calibrazione

    private var seqRunning = false
    private var calRunning = false
    private var activity: NSObjectProtocol?

    /// Chiamata ogni 3 s con lo stato del server. Dock, etichetta e notifiche le gestisce l'app e non la pagina:
    /// in una pila di ore, con la finestra nascosta o lo schermo spento, macOS rallenta o sospende la pagina e la
    /// fine della pila andava persa.
    func track(_ state: [String: Any]) {
        let q = state["sequence"] as? [String: Any] ?? [:]
        let k = state["calibration"] as? [String: Any] ?? [:]
        let num = { (d: [String: Any], key: String) in (d[key] as? NSNumber)?.doubleValue ?? 0 }
        let seqState = q["state"] as? String ?? ""
        let seq = ["running", "paused", "stopping"].contains(seqState)
        // senza kind è l'esposizione automatica: niente barra
        let cal = (k["busy"] as? Bool ?? false) && (k["kind"] as? String) != nil
        if seq { dock.update(active: true, done: num(q, "index"), total: num(q, "total")) }
        else if cal { dock.update(active: true, done: num(k, "index"), total: num(k, "total")) }
        else { dock.update(active: false, done: 0, total: 0) }

        if seqRunning && !seq {
            if seqState == "done" { notify(title: Texts.stackDone, body: Texts.shots(Int(num(q, "index"))), ok: true) }
            else if seqState == "error" { notify(title: Texts.stackError, body: q["message"] as? String ?? "", ok: false) }
        }
        if calRunning && !cal {
            let calState = k["state"] as? String ?? ""
            if calState == "done" { notify(title: Texts.calibrationDone, body: Texts.shots(Int(num(k, "index"))), ok: true) }
            else if calState == "error" { notify(title: Texts.calibrationError, body: k["message"] as? String ?? "", ok: false) }
        }
        seqRunning = seq
        calRunning = cal

        // durante il lavoro macOS non deve rallentare l'app (App Nap): i controlli ogni 3 s restano puntuali
        if (seq || cal) && activity == nil {
            activity = ProcessInfo.processInfo.beginActivity(options: .userInitiated, reason: "Focus Stack: pila o calibrazione in corso")
        } else if !(seq || cal), let a = activity {
            ProcessInfo.processInfo.endActivity(a)
            activity = nil
        }
    }

    // MARK: notifiche

    /// Il permesso si chiede all'avvio (la prima volta macOS mostra la richiesta): chiesto a metà pila, la
    /// risposta poteva arrivare troppo tardi e la notifica di fine pila andava persa.
    func askNotificationPermission() {
        guard !askedNotifications, notificationsAvailable else { return }
        askedNotifications = true
        let center = UNUserNotificationCenter.current()
        center.delegate = self
        // .badge: con il permesso alle notifiche, macOS mostra l'etichetta sull'icona del Dock (gli scatti che
        // mancano, «!» dopo un errore) solo se l'app l'ha chiesta
        center.requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
            AppLog.write("notifiche: permesso \(granted ? "concesso" : "negato")\(error.map { " (\($0.localizedDescription))" } ?? "")")
        }
    }

    private func notify(title: String, body: String, ok: Bool) {
        if !ok { dock.badge("!") }
        if !NSApp.isActive { NSApp.requestUserAttention(ok ? .informationalRequest : .criticalRequest) }
        guard notificationsAvailable else { return }
        askNotificationPermission()
        let content = UNMutableNotificationContent()
        content.title = title
        content.body = body
        content.sound = nil              // il suono di fine pila lo fa già il server
        let req = UNNotificationRequest(identifier: UUID().uuidString, content: content, trigger: nil)
        UNUserNotificationCenter.current().getNotificationSettings { settings in
            AppLog.write("notifica «\(title)»: autorizzazione \(settings.authorizationStatus.rawValue), avvisi \(settings.alertSetting.rawValue), badge \(settings.badgeSetting.rawValue)")
        }
        UNUserNotificationCenter.current().add(req) { error in
            if let error { AppLog.write("notifica non inviata: \(error.localizedDescription)") }
        }
    }

    /// Anche con Focus Stack in primo piano la notifica si mostra (macOS altrimenti la tiene solo nel Centro notifiche).
    func userNotificationCenter(_ center: UNUserNotificationCenter, willPresent notification: UNNotification,
                                withCompletionHandler done: @escaping (UNNotificationPresentationOptions) -> Void) {
        done([.banner, .list])
    }

    /// Le notifiche richiedono un'app vera (con Info.plist): con `swift run` non ci sono.
    private var notificationsAvailable: Bool { Bundle.main.bundleIdentifier != nil }

    func clearBadge() { dock.badge(nil) }

    // clic sulla notifica: riporta la finestra
    func userNotificationCenter(_ center: UNUserNotificationCenter, didReceive response: UNNotificationResponse,
                                withCompletionHandler done: @escaping () -> Void) {
        DispatchQueue.main.async { NSApp.activate(ignoringOtherApps: true) }
        done()
    }
}

/// Barra di avanzamento sull'icona del Dock durante una pila o una serie di calibrazione.
/// Sull'etichetta dell'icona, durante il lavoro, gli scatti che mancano; dopo un errore «!» finché non si torna all'app.
final class DockProgress {
    private let view = DockProgressView()
    private var error = false

    func update(active: Bool, done: Double, total: Double) {
        let tile = NSApp.dockTile
        if active, total > 0 {
            error = false
            view.fraction = max(0, min(1, done / total))
            view.frame = NSRect(origin: .zero, size: tile.size)
            if tile.contentView !== view { tile.contentView = view }
            let left = Int((total - done).rounded())
            tile.badgeLabel = left > 0 ? String(left) : nil
        } else {
            if tile.contentView != nil { tile.contentView = nil }
            if !error { tile.badgeLabel = nil }
        }
        tile.display()
    }

    func badge(_ text: String?) {
        error = text != nil
        NSApp.dockTile.badgeLabel = text
    }
}

private final class DockProgressView: NSView {
    var fraction: Double = 0
    /// L'icona piatta (AppIcon.icns): NSApp.applicationIconImage, per un'icona Liquid Glass, è una resa più chiara
    /// di quella che mostra il Dock, e l'icona cambierebbe colore mentre c'è la barra.
    private let icon: NSImage? = Bundle.main.url(forResource: "AppIcon", withExtension: "icns")
        .flatMap { NSImage(contentsOf: $0) } ?? NSApp.applicationIconImage

    override func draw(_ dirtyRect: NSRect) {
        icon?.draw(in: bounds)
        // barra alta e chiara: deve leggersi anche con l'icona piccola e sul Dock scuro
        let inset = bounds.width * 0.1
        let height = max(12, bounds.height * 0.17)
        let track = NSRect(x: inset, y: bounds.height * 0.08, width: bounds.width - 2 * inset, height: height)
        let radius = height / 2
        NSColor(white: 1, alpha: 0.92).setFill()
        NSBezierPath(roundedRect: track, xRadius: radius, yRadius: radius).fill()
        NSColor(white: 0, alpha: 0.35).setStroke()
        let outline = NSBezierPath(roundedRect: track.insetBy(dx: 0.5, dy: 0.5), xRadius: radius, yRadius: radius)
        outline.lineWidth = 1
        outline.stroke()
        let pad = max(2, height * 0.18)
        var fill = track.insetBy(dx: pad, dy: pad)
        fill.size.width = max(fill.height, fill.width * fraction)
        NSColor.controlAccentColor.setFill()
        NSBezierPath(roundedRect: fill, xRadius: fill.height / 2, yRadius: fill.height / 2).fill()
    }
}
