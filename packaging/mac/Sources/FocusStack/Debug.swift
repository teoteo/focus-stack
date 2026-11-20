import AppKit
import WebKit

/// Aiuto per le prove automatiche, attivo solo se l'app parte con FOCUSSTACK_DEBUG_DIR=<cartella>.
/// Ogni secondo cerca <cartella>/cmd.js: lo esegue nella finestra web in primo piano (o nella principale),
/// scrive il risultato in result.txt e salva un'immagine di ogni finestra web in win-<n>.png.
/// Un file cmd.txt con «menu:<titolo>» preme la voce di menu con quel titolo.
final class Debug {
    private let dir: URL
    private weak var windows: WebWindows?
    private var timer: Timer?

    init?(windows: WebWindows) {
        guard let path = ProcessInfo.processInfo.environment["FOCUSSTACK_DEBUG_DIR"], !path.isEmpty else { return nil }
        dir = URL(fileURLWithPath: path)
        self.windows = windows
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        timer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in self?.poll() }
    }

    private func poll() {
        let js = dir.appendingPathComponent("cmd.js")
        let txt = dir.appendingPathComponent("cmd.txt")
        if let code = try? String(contentsOf: js, encoding: .utf8) {
            try? FileManager.default.removeItem(at: js)
            let target = (NSApp.keyWindow?.contentView as? WKWebView) ?? windows?.mainWebView
            target?.evaluateJavaScript(code) { [weak self] result, error in
                self?.write("\(error.map { "ERRORE: \($0)" } ?? String(describing: result ?? "nil"))")
                DispatchQueue.main.asyncAfter(deadline: .now() + 1) { self?.snapshots() }
            }
        } else if let cmd = try? String(contentsOf: txt, encoding: .utf8) {
            try? FileManager.default.removeItem(at: txt)
            let c = cmd.trimmingCharacters(in: .whitespacesAndNewlines)
            if c.hasPrefix("menu:") { press(String(c.dropFirst(5)), in: NSApp.mainMenu) }
            if c == "snap" { snapshots() }
            if c == "windows" {
                write(NSApp.windows.filter(\.isVisible).map { "\($0.title) \(Int($0.frame.width))x\(Int($0.frame.height)) key=\($0.isKeyWindow) schermo=\($0.screen?.localizedName ?? "-") tuttoschermo=\($0.styleMask.contains(.fullScreen))" }
                    .joined(separator: "\n") + "\nactive=\(NSApp.isActive) appearance=\(NSApp.appearance?.name.rawValue ?? "-") dock=\(NSApp.dockTile.contentView != nil) badge=\(NSApp.dockTile.badgeLabel ?? "-")")
            }
        }
    }

    @discardableResult
    private func press(_ title: String, in menu: NSMenu?) -> Bool {
        for item in menu?.items ?? [] {
            if item.title == title, let action = item.action {
                NSApp.sendAction(action, to: item.target, from: item)
                write("menu ok: \(title)")
                return true
            }
            if press(title, in: item.submenu) { return true }
        }
        return false
    }

    private func write(_ text: String) {
        try? text.write(to: dir.appendingPathComponent("result.txt"), atomically: true, encoding: .utf8)
    }

    private func snapshots() {
        var n = 0
        for w in NSApp.windows where w.isVisible {
            guard let wv = w.contentView as? WKWebView else { continue }
            n += 1
            let file = dir.appendingPathComponent("win-\(n).png")
            wv.takeSnapshot(with: nil) { image, _ in
                guard let image, let tiff = image.tiffRepresentation,
                      let png = NSBitmapImageRep(data: tiff)?.representation(using: .png, properties: [:]) else { return }
                try? png.write(to: file)
            }
        }
    }
}
