// swift-tools-version:5.9
// App per Mac di Focus Stack: una finestra nativa (WKWebView) sull'interfaccia web del server Python incluso.
// build_release.sh la compila universale (arm64 + x86_64) e la mette in Contents/MacOS/Focus Stack.
//
//   swift build -c release --arch arm64 --arch x86_64
//
// Per provarla senza pacchetto: FOCUSSTACK_SOURCE=<cartella del progetto> FOCUSSTACK_PORT=8799 swift run
import PackageDescription

let package = Package(
    name: "FocusStack",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(name: "FocusStack", path: "Sources/FocusStack"),
    ]
)
