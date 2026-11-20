import Foundation

/// Il server Python di Focus Stack: lo avvia (o si collega a uno già acceso), ne controlla lo stato e lo spegne.
/// Fa quello che faceva l'applet AppleScript fino alla 1.1 (packaging/launcher.applescript).
final class Server {
    let port: Int
    let base: URL
    private(set) var process: Process?
    private let session: URLSession

    /// Python e codice da usare: quelli dentro l'app, oppure (per lo sviluppo) quelli di FOCUSSTACK_SOURCE.
    struct Layout {
        let python: URL
        let appDir: URL
        let bundle: URL?        // FOCUSSTACK_APP: solo l'app installata si aggiorna da sola
    }

    init() {
        let env = ProcessInfo.processInfo.environment
        port = Int(env["FOCUSSTACK_PORT"] ?? "") ?? 8765
        base = URL(string: "http://127.0.0.1:\(port)/")!
        let cfg = URLSessionConfiguration.ephemeral
        cfg.timeoutIntervalForRequest = 2
        cfg.connectionProxyDictionary = [:]          // localhost: mai attraverso un proxy
        session = URLSession(configuration: cfg)
    }

    func layout() -> Layout? {
        // stesso percorso, senza collegamenti simbolici, per l'app, Python e FOCUSSTACK_APP: lo script di
        // aggiornamento riconosce i processi del pacchetto dal percorso del comando
        let bundle = Bundle.main.bundleURL.resolvingSymlinksInPath()
        let res = bundle.appendingPathComponent("Contents/Resources")
        let appDir = res.appendingPathComponent("app")
        if FileManager.default.fileExists(atPath: appDir.appendingPathComponent("run.py").path) {
            #if arch(arm64)
            let python = res.appendingPathComponent("python-arm64/bin/python3")
            #else
            let python = res.appendingPathComponent("python-x86_64/bin/python3")
            #endif
            return Layout(python: python, appDir: appDir, bundle: bundle)
        }
        if let src = ProcessInfo.processInfo.environment["FOCUSSTACK_SOURCE"] {
            let dir = URL(fileURLWithPath: src)
            return Layout(python: dir.appendingPathComponent(".venv/bin/python"), appDir: dir, bundle: nil)
        }
        return nil
    }

    // MARK: richieste

    private func request(_ path: String, method: String = "GET", timeout: TimeInterval = 2) async -> Data? {
        var req = URLRequest(url: base.appendingPathComponent(path), timeoutInterval: timeout)
        req.httpMethod = method
        if method == "POST" {
            // il server accetta i POST solo con questa intestazione (un sito esterno non può aggiungerla)
            req.setValue("1", forHTTPHeaderField: "X-FocusStack")
            req.setValue("application/json", forHTTPHeaderField: "Content-Type")
            req.httpBody = Data("{}".utf8)
        }
        guard let (data, resp) = try? await session.data(for: req),
              let http = resp as? HTTPURLResponse, http.statusCode < 500 else { return nil }
        return data
    }

    func alive(timeout: TimeInterval = 1) async -> Bool {
        await request("api/state", timeout: timeout) != nil
    }

    /// Stato completo del server (/api/state); nil se non risponde.
    func state(timeout: TimeInterval = 2) async -> [String: Any]? {
        guard let data = await request("api/state", timeout: timeout) else { return nil }
        return (try? JSONSerialization.jsonObject(with: data)) as? [String: Any]
    }

    /// Stato della sequenza: running, paused, stopping… nil se il server non risponde.
    func sequenceState() async -> String? {
        guard let data = await request("api/state"),
              let obj = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
              let seq = obj["sequence"] as? [String: Any] else { return nil }
        return seq["state"] as? String
    }

    /// Spegne il server e aspetta che abbia chiuso focheggiatore e fotocamera (al massimo 10 s).
    func shutdown() async {
        _ = await request("api/shutdown", method: "POST", timeout: 5)
        for _ in 0..<40 {
            if !(await alive(timeout: 0.5)) { break }
            try? await Task.sleep(nanoseconds: 250_000_000)
        }
        if let p = process, p.isRunning {
            for _ in 0..<20 where p.isRunning { try? await Task.sleep(nanoseconds: 250_000_000) }
        }
    }

    // MARK: avvio

    func start(_ layout: Layout, onExit: @escaping (Int32) -> Void) throws {
        if let bundle = layout.bundle { removeQuarantine(bundle) }
        try? FileManager.default.createDirectory(at: Paths.log.deletingLastPathComponent(), withIntermediateDirectories: true)
        FileManager.default.createFile(atPath: Paths.log.path, contents: nil)
        let log = try FileHandle(forWritingTo: Paths.log)
        let p = Process()
        p.executableURL = layout.python
        p.arguments = ["run.py", "--no-browser", "--port", String(port)]
        p.currentDirectoryURL = layout.appDir
        var env = ProcessInfo.processInfo.environment
        if let bundle = layout.bundle { env["FOCUSSTACK_APP"] = bundle.path }
        if let h = Paths.overrideHome { env["HOME"] = h }      // prove: impostazioni, registro e cache finti
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        env["PYTHONNOUSERSITE"] = "1"
        p.environment = env
        p.standardInput = FileHandle.nullDevice
        p.standardOutput = log
        p.standardError = log
        p.terminationHandler = { proc in
            DispatchQueue.main.async { onExit(proc.terminationStatus) }
        }
        try p.run()
        process = p
    }

    /// Aspetta che il server risponda (al massimo `seconds`). False se non parte o se il processo esce prima.
    func waitUntilAlive(seconds: Double) async -> Bool {
        let deadline = Date().addingTimeInterval(seconds)
        while Date() < deadline {
            if await alive(timeout: 0.5) { return true }
            if let p = process, !p.isRunning { return false }
            try? await Task.sleep(nanoseconds: 250_000_000)
        }
        return false
    }

    /// Ultime righe del registro, per l'avviso quando il server non parte.
    func logTail(lines: Int = 5) -> String {
        guard let text = try? String(contentsOf: Paths.log, encoding: .utf8) else { return "" }
        return text.split(separator: "\n", omittingEmptySubsequences: false).suffix(lines + 1)
            .joined(separator: "\n").trimmingCharacters(in: .whitespacesAndNewlines)
    }

    /// L'app è stata approvata all'apertura: si toglie la "quarantena" di macOS dai file interni, altrimenti
    /// il Python incluso verrebbe bloccato come programma non verificato. Solo la prima volta: dopo, il
    /// pacchetto non ha più l'attributo.
    private func removeQuarantine(_ bundle: URL) {
        let attr = "com.apple.quarantine"
        guard getxattr(bundle.path, attr, nil, 0, 0, XATTR_NOFOLLOW) >= 0 else { return }
        if let items = FileManager.default.enumerator(atPath: bundle.path) {
            for case let rel as String in items {
                removexattr(bundle.appendingPathComponent(rel).path, attr, XATTR_NOFOLLOW)
            }
        }
        removexattr(bundle.path, attr, XATTR_NOFOLLOW)
    }
}
