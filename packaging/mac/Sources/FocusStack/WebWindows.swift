import AppKit
import WebKit

/// Colori di sfondo della pagina (web/style.css), per non mostrare un lampo bianco durante il caricamento.
enum Theme {
    static var current: String {
        get { UserDefaults.standard.string(forKey: "Theme") ?? "dark" }
        set { UserDefaults.standard.set(newValue, forKey: "Theme") }
    }
    static var background: NSColor {
        current == "light" ? NSColor(srgbRed: 0xee / 255, green: 0xf1 / 255, blue: 0xf5 / 255, alpha: 1)
                           : NSColor(srgbRed: 0x0d / 255, green: 0x11 / 255, blue: 0x17 / 255, alpha: 1)
    }
    static var appearance: NSAppearance? { NSAppearance(named: current == "light" ? .aqua : .darkAqua) }
}

/// Finestre con l'interfaccia web: la principale e quelle aperte dalla pagina (visualizzatore, guida).
final class WebWindows: NSObject, WKUIDelegate, WKNavigationDelegate, NSWindowDelegate {
    let server: Server
    let bridge: Bridge
    private(set) var mainWindow: NSWindow!
    private(set) var mainWebView: WKWebView?
    private var placeholder: NSView?
    private var popups: [NSWindow: NSKeyValueObservation] = [:]
    private let navigation = NavigationToolbar()

    init(server: Server, bridge: Bridge) {
        self.server = server
        self.bridge = bridge
        super.init()
    }

    // MARK: finestra principale

    func createMainWindow() {
        let w = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1400, height: 900),
                         styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        w.title = "Focus Stack"
        w.minSize = NSSize(width: 760, height: 560)
        w.tabbingMode = .disallowed
        w.isReleasedWhenClosed = false
        w.collectionBehavior.insert(.fullScreenPrimary)
        w.backgroundColor = Theme.background
        w.delegate = self
        w.center()
        w.setFrameAutosaveName("FocusStackMain")
        mainWindow = w
        showPlaceholder()
        w.makeKeyAndOrderFront(nil)
    }

    /// «Avvio di Focus Stack…» mentre il server parte.
    private func showPlaceholder() {
        let box = NSView()
        box.wantsLayer = true
        box.layer?.backgroundColor = Theme.background.cgColor
        let spinner = NSProgressIndicator()
        spinner.style = .spinning
        spinner.controlSize = .regular
        spinner.startAnimation(nil)
        let label = NSTextField(labelWithString: Texts.starting)
        label.textColor = .secondaryLabelColor
        label.font = .systemFont(ofSize: 14)
        let stack = NSStackView(views: [spinner, label])
        stack.orientation = .vertical
        stack.spacing = 12
        stack.translatesAutoresizingMaskIntoConstraints = false
        box.addSubview(stack)
        NSLayoutConstraint.activate([stack.centerXAnchor.constraint(equalTo: box.centerXAnchor),
                                     stack.centerYAnchor.constraint(equalTo: box.centerYAnchor)])
        mainWindow.contentView = box
        placeholder = box
    }

    func loadInterface() {
        let wv = makeWebView(configuration: makeConfiguration())
        mainWindow.contentView = wv
        placeholder = nil
        mainWebView = wv
        wv.load(URLRequest(url: server.base))
    }

    func showMain() {
        mainWindow.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    /// Esegue una funzione dell'interfaccia (es. "switchTab('config')"); niente se la pagina non è pronta.
    func runScript(_ js: String) {
        showMain()
        mainWebView?.evaluateJavaScript(js, completionHandler: nil)
    }

    // MARK: WebKit

    private func makeConfiguration() -> WKWebViewConfiguration {
        let cfg = WKWebViewConfiguration()
        cfg.websiteDataStore = .default()        // localStorage persistente: tema, scheda, guide…
        cfg.preferences.isElementFullscreenEnabled = true
        cfg.mediaTypesRequiringUserActionForPlayback = []
        cfg.userContentController.addScriptMessageHandler(bridge, contentWorld: .page, name: "focusstack")
        return cfg
    }

    private func makeWebView(configuration: WKWebViewConfiguration) -> WKWebView {
        let wv = WKWebView(frame: .zero, configuration: configuration)
        wv.uiDelegate = self
        wv.navigationDelegate = self
        wv.allowsBackForwardNavigationGestures = false
        wv.allowsMagnification = false           // pinch e zoom li gestisce la pagina (visualizzatore)
        wv.setValue(false, forKey: "drawsBackground")
        wv.underPageBackgroundColor = Theme.background
        if #available(macOS 13.3, *) {
            // Web Inspector: defaults write local.focusstack.app WebInspector -bool yes
            wv.isInspectable = UserDefaults.standard.bool(forKey: "WebInspector")
        }
        return wv
    }

    /// Pagine di Focus Stack (stesso server): restano nell'app. Tutto il resto va nel browser predefinito.
    private func isOwn(_ url: URL?) -> Bool {
        guard let url else { return false }
        if url.scheme == "about" || url.scheme == "blob" || url.scheme == "data" { return true }
        return ["127.0.0.1", "localhost"].contains(url.host ?? "") && (url.port ?? 80) == server.port
    }

    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        if let url = action.request.url, action.targetFrame?.isMainFrame != false, !isOwn(url) {
            NSWorkspace.shared.open(url)
            decisionHandler(.cancel)
            return
        }
        decisionHandler(.allow)
    }

    /// window.open e i link con target (visualizzatore "focusstack-viewer", guida "fs-guide"): una finestra
    /// nativa con la configurazione ricevuta, così la pagina che l'ha aperta può ancora usarla (focus, hash).
    func webView(_ webView: WKWebView, createWebViewWith configuration: WKWebViewConfiguration,
                 for action: WKNavigationAction, windowFeatures: WKWindowFeatures) -> WKWebView? {
        if let url = action.request.url, !isOwn(url) {
            NSWorkspace.shared.open(url)
            return nil
        }
        let wv = makeWebView(configuration: configuration)
        let width = CGFloat(windowFeatures.width?.doubleValue ?? 1280)
        let height = CGFloat(windowFeatures.height?.doubleValue ?? 900)
        let w = NSWindow(contentRect: NSRect(x: 0, y: 0, width: width, height: height),
                         styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        w.isReleasedWhenClosed = false
        w.tabbingMode = .disallowed
        w.collectionBehavior.insert(.fullScreenPrimary)
        w.backgroundColor = Theme.background
        w.contentView = wv
        w.delegate = self
        w.title = "Focus Stack"
        // posizione e dimensione ricordate per tipo di finestra (visualizzatore, guida)
        let kind = (action.request.url?.path ?? "").contains("/guide/") ? "Guide" : "Viewer"
        if kind == "Guide" {
            // la guida ha link interni (indice, rimandi fra capitoli): serve poter tornare indietro
            wv.allowsBackForwardNavigationGestures = true
            let bar = NSToolbar(identifier: "FocusStackGuide")
            bar.delegate = navigation
            bar.displayMode = .iconOnly
            w.toolbar = bar
            w.toolbarStyle = .unifiedCompact
        }
        if !w.setFrameUsingName("FocusStack\(kind)") { w.cascadeTopLeft(from: mainWindow.frame.origin) }
        w.setFrameAutosaveName("FocusStack\(kind)")
        popups[w] = wv.observe(\.title, options: [.new]) { [weak w] view, _ in
            if let t = view.title, !t.isEmpty { w?.title = t }
        }
        let other = kind == "Viewer" && Prefs.viewerOtherScreen ? otherScreen() : nil
        if let other {
            // sull'altro schermo, poi a tutto schermo: la finestra principale resta dov'è
            let area = other.visibleFrame
            let size = NSSize(width: min(w.frame.width, area.width * 0.9), height: min(w.frame.height, area.height * 0.9))
            w.setFrame(NSRect(x: area.midX - size.width / 2, y: area.midY - size.height / 2,
                              width: size.width, height: size.height), display: false)
        }
        w.makeKeyAndOrderFront(nil)
        if other != nil {
            DispatchQueue.main.async { if !w.styleMask.contains(.fullScreen) { w.toggleFullScreen(nil) } }
        }
        return wv
    }

    /// Lo schermo dove non c'è la finestra principale (il più grande, se sono più di uno); nil con uno schermo solo.
    private func otherScreen() -> NSScreen? {
        let main = mainWindow.screen ?? NSScreen.main
        return NSScreen.screens.filter { $0 != main }
            .max { $0.frame.width * $0.frame.height < $1.frame.width * $1.frame.height }
    }

    /// Il processo che disegna la pagina può chiudersi (memoria, pila di ore): senza questo la finestra resta vuota.
    func webViewWebContentProcessDidTerminate(_ webView: WKWebView) {
        AppLog.write("pagina ricaricata: il processo di WebKit si era chiuso (\(webView.url?.path ?? "-"))")
        webView.reload()
    }

    func webViewDidClose(_ webView: WKWebView) {
        webView.window?.close()
    }

    // alert, confirm e prompt della pagina: senza questi WebKit non mostra nulla (confirm darebbe sempre "no")
    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let a = NSAlert()
        a.messageText = message
        a.addButton(withTitle: Texts.ok)
        present(a, in: webView) { _ in completionHandler() }
    }

    func webView(_ webView: WKWebView, runJavaScriptConfirmPanelWithMessage message: String,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (Bool) -> Void) {
        let a = NSAlert()
        a.messageText = message
        a.addButton(withTitle: Texts.ok)
        a.addButton(withTitle: Texts.cancel)
        present(a, in: webView) { completionHandler($0 == .alertFirstButtonReturn) }
    }

    func webView(_ webView: WKWebView, runJavaScriptTextInputPanelWithPrompt prompt: String, defaultText: String?,
                 initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping (String?) -> Void) {
        let a = NSAlert()
        a.messageText = prompt
        let field = NSTextField(frame: NSRect(x: 0, y: 0, width: 300, height: 24))
        field.stringValue = defaultText ?? ""
        a.accessoryView = field
        a.addButton(withTitle: Texts.ok)
        a.addButton(withTitle: Texts.cancel)
        a.window.initialFirstResponder = field
        present(a, in: webView) { completionHandler($0 == .alertFirstButtonReturn ? field.stringValue : nil) }
    }

    private func present(_ alert: NSAlert, in webView: WKWebView, done: @escaping (NSApplication.ModalResponse) -> Void) {
        if let w = webView.window, w.isVisible {
            alert.beginSheetModal(for: w, completionHandler: done)
        } else {
            done(alert.runModal())
        }
    }

    // MARK: finestre

    /// Chiudere la finestra principale la nasconde soltanto: la pagina resta viva (avanzamento nel Dock,
    /// notifiche) e il clic sull'icona nel Dock la riporta. Per uscire: ⌘Q.
    func windowShouldClose(_ sender: NSWindow) -> Bool {
        if sender === mainWindow {
            if sender.styleMask.contains(.fullScreen) { sender.toggleFullScreen(nil) }
            sender.orderOut(nil)
            return false
        }
        return true
    }

    func windowWillClose(_ notification: Notification) {
        guard let w = notification.object as? NSWindow, w !== mainWindow else { return }
        popups[w]?.invalidate()
        popups[w] = nil
        if let wv = w.contentView as? WKWebView {
            wv.stopLoading()
            // chiude i flussi del live view: senza, la connessione resterebbe aperta col server
            wv.loadHTMLString("", baseURL: nil)
        }
    }

    func applyTheme() {
        NSApp.appearance = Theme.appearance
        for w in NSApp.windows where w.contentView is WKWebView || w === mainWindow {
            w.backgroundColor = Theme.background
            (w.contentView as? WKWebView)?.underPageBackgroundColor = Theme.background
        }
    }
}

/// Pulsanti Indietro e Avanti nella barra della finestra della guida. Agiscono sulla finestra in primo piano
/// attraverso la catena dei responder (WKWebView.goBack/goForward), che li abilita solo quando si può.
final class NavigationToolbar: NSObject, NSToolbarDelegate {
    private static let back = NSToolbarItem.Identifier("back")
    private static let forward = NSToolbarItem.Identifier("forward")

    func toolbarDefaultItemIdentifiers(_ toolbar: NSToolbar) -> [NSToolbarItem.Identifier] { [Self.back, Self.forward] }
    func toolbarAllowedItemIdentifiers(_ toolbar: NSToolbar) -> [NSToolbarItem.Identifier] { [Self.back, Self.forward] }

    func toolbar(_ toolbar: NSToolbar, itemForItemIdentifier id: NSToolbarItem.Identifier,
                 willBeInsertedIntoToolbar flag: Bool) -> NSToolbarItem? {
        let isBack = id == Self.back
        let item = NSToolbarItem(itemIdentifier: id)
        item.label = isBack ? Texts.back : Texts.forward
        item.toolTip = item.label + (isBack ? " (⌘[)" : " (⌘])")
        item.image = NSImage(systemSymbolName: isBack ? "chevron.left" : "chevron.right", accessibilityDescription: item.label)
        item.action = isBack ? #selector(WKWebView.goBack(_:)) : #selector(WKWebView.goForward(_:))
        item.isNavigational = true
        item.isBordered = true
        return item
    }
}
