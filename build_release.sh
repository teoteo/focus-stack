#!/bin/zsh
# Costruisce "Focus Stack.app" autonoma e universale (Apple Silicon + Intel) e, con --publish,
# la pubblica come release su GitHub. L'app installata controlla le release e si aggiorna da sola.
#
#   ./build_release.sh            build in build/dist/
#   ./build_release.sh --publish  build + release GitHub v<VERSION> (richiede `gh auth login`)
#
# Firma: senza SIGN_ID è ad hoc (nessun account Apple; alla prima apertura serve «Apri comunque»).
# Con SIGN_ID="Developer ID Application: Nome (TEAMID)" firma con il runtime rafforzato e notarizza;
# le credenziali si salvano una volta nel portachiavi con
#   xcrun notarytool store-credentials focusstack-notary --apple-id … --team-id …
# (NOTARY_PROFILE per usare un altro nome).
#
# Prima di pubblicare: aumentare VERSION; se è cambiato il firmware aumentare anche FSBUILD in
# firmware/myFP2F_DRV8825_330/fsbuild.h. Requisiti sul Mac di chi pubblica: arduino-cli con il
# core arduino:avr e le librerie di myFocuserPro2 in ~/Documents/Arduino/libraries.
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"
VERSION="$(tr -d '[:space:]' < VERSION)"
PUBLISH=0
[[ "${1:-}" == "--publish" ]] && PUBLISH=1

# Python autonomo (python-build-standalone) e librerie per ciascuna architettura.
PY_VERSION=3.12.15
PBS_TAG=20261003
typeset -A PBS_ARCH=(arm64 aarch64 x86_64 x86_64)
# gphoto2 per Intel: la 2.6.4 richiede macOS 15, la 2.6.3 funziona da macOS 13
typeset -A GPHOTO=(arm64 2.6.4 x86_64 2.6.3)
typeset -A PLATFORM=(arm64 macosx_14_0_arm64 x86_64 macosx_13_0_x86_64)
PACKAGES=(fastapi uvicorn websockets pyserial)

CACHE="$ROOT/build/cache"
STAGE="$ROOT/build/stage"
DIST="$ROOT/build/dist"
APP="$STAGE/Focus Stack.app"
mkdir -p "$CACHE" "$DIST"
rm -rf "$STAGE"; mkdir -p "$STAGE"

echo "== Focus Stack $VERSION"

# ---------- firmware ----------
SKETCH="$ROOT/firmware/myFP2F_DRV8825_330"
FSBUILD="$(sed -nE 's/^#define FSBUILD ([0-9]+).*/\1/p' "$SKETCH/fsbuild.h")"
echo "== Firmware build $FSBUILD"
arduino-cli compile -b arduino:avr:nano:cpu=atmega328old --build-path "$ROOT/build/firmware" "$SKETCH" | tail -2
FWOUT="$ROOT/firmware/build"
rm -rf "$FWOUT"; mkdir -p "$FWOUT"
cp "$ROOT/build/firmware/myFP2F_DRV8825_330.ino.hex" "$FWOUT/firmware.hex"
# stessa build per la scheda Ardufocus (opzione ARDUFOCUSPCB in focuserconfig.h)
arduino-cli compile -b arduino:avr:nano:cpu=atmega328old --build-property "compiler.cpp.extra_flags=-DARDUFOCUSPCB" \
  --build-path "$ROOT/build/firmware-ardufocus" "$SKETCH" | tail -2
cp "$ROOT/build/firmware-ardufocus/myFP2F_DRV8825_330.ino.hex" "$FWOUT/firmware-ardufocus.hex"
printf '{"build": %s, "hex": "firmware.hex", "boards": {"ardufocus": "firmware-ardufocus.hex"}}\n' "$FSBUILD" > "$FWOUT/manifest.json"

# ---------- app per Mac (Swift, packaging/mac) e icona ----------
# Una finestra nativa sull'interfaccia web: avvia il server Python incluso e lo spegne quando si esce.
echo "== App Swift (Apple Silicon + Intel)"
SWIFT_DIR="$ROOT/packaging/mac"
SWIFT_ARGS=(--package-path "$SWIFT_DIR" -c release --arch arm64 --arch x86_64)
swift build "${SWIFT_ARGS[@]}" 2>&1 | grep -v "x86_64 architecture is deprecated" | tail -1
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$(swift build "${SWIFT_ARGS[@]}" --show-bin-path)/FocusStack" "$APP/Contents/MacOS/Focus Stack"
sed "s/__VERSION__/$VERSION/g" "$SWIFT_DIR/Info.plist" > "$APP/Contents/Info.plist"
plutil -lint -s "$APP/Contents/Info.plist"
printf 'APPL????' > "$APP/Contents/PkgInfo"
# testi di Info.plist nelle 5 lingue (e lingue dichiarate: i menu di sistema seguono la lingua di macOS)
cp -R "$SWIFT_DIR/lproj/"*.lproj "$APP/Contents/Resources/"
# icona: packaging/icon (rigenerare con packaging/icon/make-icons.sh). Assets.car = icona a livelli Liquid
# Glass (macOS 26+, CFBundleIconName); AppIcon.icns = la stessa appiattita per macOS 13-25 (CFBundleIconFile)
ICON_DIR="$ROOT/packaging/icon"
mkdir -p "$STAGE/icon"
xcrun actool "$ICON_DIR/AppIcon.icon" --compile "$STAGE/icon" --platform macosx --minimum-deployment-target 13.0 \
  --app-icon AppIcon --output-partial-info-plist "$STAGE/icon/partial.plist" --output-format human-readable-text >/dev/null
cp "$STAGE/icon/Assets.car" "$APP/Contents/Resources/"
ICONSET="$STAGE/AppIcon.iconset"; mkdir -p "$ICONSET"
ICON_SRC="$ICON_DIR/AppIcon-1024.png"
for s in 16 32 128 256 512; do
  sips -z $s $s "$ICON_SRC" --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
  d=$((s * 2)); sips -z $d $d "$ICON_SRC" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/AppIcon.icns"
rm -rf "$ICONSET" "$STAGE/icon"

# ---------- guida HTML (web/guide/, aperta dai «?» dell'app) ----------
python3 "$ROOT/docs/guida/genera_guida_web.py" | tail -1

# ---------- codice ----------
RES="$APP/Contents/Resources"
mkdir -p "$RES/app/firmware"
cp -R "$ROOT/backend" "$ROOT/web" "$ROOT/run.py" "$ROOT/VERSION" "$RES/app/"
cp -R "$FWOUT" "$RES/app/firmware/build"
# misura dei RAW per calibrazione ed esposizione automatica: LibRaw 0.22.3 (sottomodulo third_party/LibRaw)
[ -f "$ROOT/third_party/LibRaw/Makefile.dist" ] || git -C "$ROOT" submodule update --init third_party/LibRaw
echo "== fs-rawstat (LibRaw)"
python3 "$ROOT/tools/rawstat/build.py" --out "$RES/app/bin" | tail -1
find "$RES/app" -name __pycache__ -type d -prune -exec rm -rf {} +

# ---------- Python per Apple Silicon e Intel ----------
for arch in arm64 x86_64; do
  tarball="cpython-$PY_VERSION+$PBS_TAG-${PBS_ARCH[$arch]}-apple-darwin-install_only_stripped.tar.gz"
  if [ ! -f "$CACHE/$tarball" ]; then
    echo "== Scarico Python $PY_VERSION ($arch)"
    curl -fL --retry 3 -o "$CACHE/$tarball.part" \
      "https://github.com/astral-sh/python-build-standalone/releases/download/$PBS_TAG/$tarball"
    mv "$CACHE/$tarball.part" "$CACHE/$tarball"
  fi
  dest="$RES/python-$arch"
  mkdir -p "$dest"
  tar -xzf "$CACHE/$tarball" -C "$dest" --strip-components 1
  # parti di Python che l'app non usa
  rm -rf "$dest"/lib/python3.12/{test,idlelib,tkinter,turtledemo,ensurepip} "$dest"/lib/{tcl,tk,itcl,thread}* \
         "$dest"/lib/python3.12/site-packages/pip* "$dest"/include "$dest"/share
  echo "== Librerie per $arch (gphoto2 ${GPHOTO[$arch]})"
  # pip gira con il Python di questo Mac, scaricando le wheel della piattaforma di destinazione
  "$ROOT/.venv/bin/python" -m pip install --quiet --disable-pip-version-check \
    --target "$dest/lib/python3.12/site-packages" \
    --platform "${PLATFORM[$arch]}" --python-version 3.12 --implementation cp --only-binary=:all: \
    "${PACKAGES[@]}" "gphoto2==${GPHOTO[$arch]}"
done
find "$RES" -name __pycache__ -type d -prune -exec rm -rf {} +

# ---------- firma e zip ----------
SIGN_ID="${SIGN_ID:-}"
NOTARY_PROFILE="${NOTARY_PROFILE:-focusstack-notary}"
ZIP="$DIST/FocusStack-$VERSION.zip"
rm -f "$ZIP"
if [[ -z "$SIGN_ID" ]]; then
  echo "== Firma ad hoc"
  codesign --force --deep --sign - "$APP"
  ditto -c -k --keepParent "$APP" "$ZIP"
else
  echo "== Firma Developer ID: $SIGN_ID"
  SIGN=(codesign --force --timestamp --options runtime --sign "$SIGN_ID")
  # dall'interno verso l'esterno: librerie, poi programmi (Python, fs-rawstat), infine l'app
  find "$RES" -type f \( -name "*.so" -o -name "*.dylib" \) -print0 | xargs -0 "${SIGN[@]}"
  find "$RES" -type f -perm +111 ! -name "*.so" ! -name "*.dylib" -print0 |
    while IFS= read -r -d '' f; do
      if file -b "$f" | grep -q "Mach-O"; then
        "${SIGN[@]}" --entitlements "$ROOT/packaging/mac/python.entitlements" "$f"
      fi
    done
  "${SIGN[@]}" "$APP"
  codesign --verify --deep --strict "$APP"
  echo "== Notarizzazione (qualche minuto)"
  ditto -c -k --keepParent "$APP" "$ZIP"
  NOTARY_OUT="$(xcrun notarytool submit "$ZIP" --keychain-profile "$NOTARY_PROFILE" --wait 2>&1)" || true
  echo "$NOTARY_OUT" | tail -3
  if ! echo "$NOTARY_OUT" | grep -q "status: Accepted"; then
    echo "Notarizzazione non riuscita: dettagli con xcrun notarytool log <id> --keychain-profile $NOTARY_PROFILE" >&2
    exit 1
  fi
  xcrun stapler staple "$APP"
  rm -f "$ZIP"
  ditto -c -k --keepParent "$APP" "$ZIP"
  spctl -a -vv "$APP"
fi
echo "== Creato $ZIP ($(du -h "$ZIP" | cut -f1))"

if (( PUBLISH )); then
  NOTES="$ROOT/build/release-notes.md"
  {
    echo "Focus Stack $VERSION — firmware del focheggiatore build $FSBUILD."
    echo
    echo "**Prima installazione:** scarica lo zip, aprilo, trascina *Focus Stack* in Applicazioni e aprila."
    if [[ -z "$SIGN_ID" ]]; then
      echo "macOS dirà che non può verificare lo sviluppatore: apri Impostazioni di Sistema → Privacy e sicurezza,"
      echo "scorri in basso e premi **Apri comunque**. Serve solo la prima volta: poi l'app si aggiorna da sola."
    else
      echo "Poi l'app si aggiorna da sola."
    fi
  } > "$NOTES"
  gh release create "v$VERSION" "$ZIP" --title "Focus Stack $VERSION" --notes-file "$NOTES"
  echo "== Pubblicata la release v$VERSION"
fi
