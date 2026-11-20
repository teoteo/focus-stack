import AppKit
import WebKit

final class AppDelegate: NSObject, NSApplicationDelegate {
    private let server = Server()
    private let bridge = Bridge()
    private lazy var windows = WebWindows(server: server, bridge: bridge)
    private var monitor: Timer?
    private var debug: Debug?
    private var missed = 0
    /// Il server si è spento da solo (pulsante ⏻, aggiornamento): si esce senza chiedere nulla.
    private var serverGone = false
    private var quitting = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        AppLog.write("avvio \(Bundle.main.infoDictionary?["CFBundleShortVersionString"] ?? "?") (\(Bundle.main.bundleIdentifier ?? "senza bundle id"))")
        NSApp.appearance = Theme.appearance
        NSApp.mainMenu = buildMenu()
        bridge.onTheme = { [weak self] in self?.windows.applyTheme() }
        windows.createMainWindow()
        debug = Debug(windows: windows)
        NSApp.activate(ignoringOtherApps: true)
        Task { @MainActor in await self.startServer() }
    }

    @MainActor
    private func startServer() async {
        if await server.alive() {
            // già acceso (per esempio la versione di sviluppo): ci si collega soltanto
            ready()
            return
        }
        guard let layout = server.layout() else {
            fail(Texts.serverFailed + "Contents/Resources/app")
            return
        }
        do {
            try server.start(layout) { [weak self] _ in self?.serverExited() }
        } catch {
            fail(Texts.serverFailed + Paths.log.path + "\n\n" + error.localizedDescription)
            return
        }
        if await server.waitUntilAlive(seconds: 20) {
            ready()
        } else {
            fail(Texts.serverFailed + Paths.log.path + "\n\n" + server.logTail())
        }
    }

    private func ready() {
        windows.loadInterface()
        bridge.askNotificationPermission()
        // se il server si spegne (es. durante un aggiornamento) l'app si chiude da sola
        monitor = Timer.scheduledTimer(withTimeInterval: 3, repeats: true) { [weak self] _ in
            guard let self else { return }
            Task { @MainActor in
                if let state = await self.server.state(timeout: 1.5) {
                    self.missed = 0
                    self.bridge.track(state)
                    return
                }
                self.missed += 1
                if self.missed >= 2 { self.serverExited() }
            }
        }
    }

    private func serverExited() {
        guard !quitting else { return }
        serverGone = true
        NSApp.terminate(nil)
    }

    private func fail(_ message: String) {
        let a = NSAlert()
        a.alertStyle = .critical
        a.messageText = "Focus Stack"
        a.informativeText = message
        a.runModal()
        serverGone = true
        NSApp.terminate(nil)
    }

    // MARK: uscita

    func applicationShouldTerminate(_ sender: NSApplication) -> NSApplication.TerminateReply {
        if serverGone || quitting { return .terminateNow }
        Task { @MainActor in
            if let state = await server.sequenceState(), ["running", "paused", "stopping"].contains(state) {
                let a = NSAlert()
                a.alertStyle = .warning
                a.messageText = "Focus Stack"
                a.informativeText = Texts.busyQuit
                a.addButton(withTitle: Texts.cancel)
                a.addButton(withTitle: Texts.quitButton)
                if a.runModal() != .alertSecondButtonReturn {
                    NSApp.reply(toApplicationShouldTerminate: false)   // l'app resta aperta
                    return
                }
            }
            quitting = true
            monitor?.invalidate()
            // spegne il server e aspetta che chiuda le connessioni con l'hardware
            await server.shutdown()
            NSApp.reply(toApplicationShouldTerminate: true)
        }
        return .terminateLater
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { false }

    /// clic sull'icona nel Dock: riporta la finestra
    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        if !windows.mainWindow.isVisible { windows.showMain() }
        return true
    }

    func applicationDidBecomeActive(_ notification: Notification) {
        bridge.clearBadge()
    }

    // MARK: menu

    @objc private func showSettings() { windows.runScript("switchTab('config')") }
    @objc private func showGuide() { windows.runScript("window.open(guideUrl(), 'fs-guide')") }
    @objc private func showLog() { NSWorkspace.shared.open(Paths.log) }
    @objc private func showMainWindow() { windows.showMain() }
    @objc private func reloadPage() { windows.mainWebView?.reload() }
    @objc private func zoomActual() { windows.mainWebView?.pageZoom = 1 }
    @objc private func zoomIn() { if let wv = windows.mainWebView { wv.pageZoom = min(2, wv.pageZoom + 0.1) } }
    @objc private func zoomOut() { if let wv = windows.mainWebView { wv.pageZoom = max(0.5, wv.pageZoom - 0.1) } }

    private func buildMenu() -> NSMenu {
        let main = NSMenu()

        let app = submenu(main, "Focus Stack")
        app.addItem(withTitle: Texts.about, action: #selector(NSApplication.orderFrontStandardAboutPanel(_:)), keyEquivalent: "")
        app.addItem(.separator())
        item(app, Texts.settings, #selector(showSettings), ",")
        app.addItem(.separator())
        let services = NSMenu()
        app.addItem(withTitle: Texts.services, action: nil, keyEquivalent: "").submenu = services
        NSApp.servicesMenu = services
        app.addItem(.separator())
        app.addItem(withTitle: Texts.hide, action: #selector(NSApplication.hide(_:)), keyEquivalent: "h")
        app.addItem(withTitle: Texts.hideOthers, action: #selector(NSApplication.hideOtherApplications(_:)), keyEquivalent: "h")
            .keyEquivalentModifierMask = [.command, .option]
        app.addItem(withTitle: Texts.showAll, action: #selector(NSApplication.unhideAllApplications(_:)), keyEquivalent: "")
        app.addItem(.separator())
        app.addItem(withTitle: Texts.quit, action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")

        // senza il menu Modifica ⌘C, ⌘V, ⌘X e ⌘A non funzionano nei campi della pagina
        let edit = submenu(main, Texts.edit)
        edit.addItem(withTitle: Texts.undo, action: Selector(("undo:")), keyEquivalent: "z")
        edit.addItem(withTitle: Texts.redo, action: Selector(("redo:")), keyEquivalent: "Z")
        edit.addItem(.separator())
        edit.addItem(withTitle: Texts.cut, action: #selector(NSText.cut(_:)), keyEquivalent: "x")
        edit.addItem(withTitle: Texts.copy, action: #selector(NSText.copy(_:)), keyEquivalent: "c")
        edit.addItem(withTitle: Texts.paste, action: #selector(NSText.paste(_:)), keyEquivalent: "v")
        edit.addItem(withTitle: Texts.selectAll, action: #selector(NSText.selectAll(_:)), keyEquivalent: "a")

        let view = submenu(main, Texts.view)
        view.addItem(withTitle: Texts.back, action: #selector(WKWebView.goBack(_:)), keyEquivalent: "[")
        view.addItem(withTitle: Texts.forward, action: #selector(WKWebView.goForward(_:)), keyEquivalent: "]")
        view.addItem(.separator())
        item(view, Texts.reload, #selector(reloadPage), "r")
        view.addItem(.separator())
        item(view, Texts.actualSize, #selector(zoomActual), "0")
        item(view, Texts.zoomIn, #selector(zoomIn), "+")
        item(view, Texts.zoomOut, #selector(zoomOut), "-")
        view.addItem(.separator())
        view.addItem(withTitle: Texts.fullScreen, action: #selector(NSWindow.toggleFullScreen(_:)), keyEquivalent: "f")
            .keyEquivalentModifierMask = [.command, .control]

        let window = submenu(main, Texts.window)
        window.addItem(withTitle: Texts.minimize, action: #selector(NSWindow.performMiniaturize(_:)), keyEquivalent: "m")
        window.addItem(withTitle: Texts.zoom, action: #selector(NSWindow.performZoom(_:)), keyEquivalent: "")
        window.addItem(withTitle: Texts.close, action: #selector(NSWindow.performClose(_:)), keyEquivalent: "w")
        window.addItem(.separator())
        item(window, Texts.mainWindow, #selector(showMainWindow), "1")
        window.addItem(.separator())
        window.addItem(withTitle: Texts.bringAll, action: #selector(NSApplication.arrangeInFront(_:)), keyEquivalent: "")
        NSApp.windowsMenu = window

        let help = submenu(main, Texts.help)
        item(help, Texts.guide, #selector(showGuide), "?")
        item(help, Texts.showLog, #selector(showLog), "")
        NSApp.helpMenu = help
        return main
    }

    private func submenu(_ main: NSMenu, _ title: String) -> NSMenu {
        let m = NSMenu(title: title)
        main.addItem(withTitle: title, action: nil, keyEquivalent: "").submenu = m
        return m
    }

    @discardableResult
    private func item(_ menu: NSMenu, _ title: String, _ action: Selector, _ key: String) -> NSMenuItem {
        let i = menu.addItem(withTitle: title, action: action, keyEquivalent: key)
        i.target = self
        return i
    }
}
