#!/bin/zsh
# Costruisce "Focus Stack.app" autonoma e universale (Apple Silicon + Intel) e, con --publish,
# la pubblica come release su GitHub. L'app installata controlla le release e si aggiorna da sola.
#
#   ./build_release.sh            build in build/dist/
#   ./build_release.sh --publish  build + release GitHub v<VERSION> (richiede `gh auth login`)
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
printf '{"build": %s, "hex": "firmware.hex"}\n' "$FSBUILD" > "$FWOUT/manifest.json"

# ---------- applet (programma di avvio) e icona ----------
osacompile -s -o "$APP" "$ROOT/packaging/launcher.applescript"
ICONSET="$STAGE/AppIcon.iconset"; mkdir -p "$ICONSET"
for s in 16 32 128 256 512; do
  sips -z $s $s "$ROOT/web/icon-512.png" --out "$ICONSET/icon_${s}x${s}.png" >/dev/null
  d=$((s * 2)); [ $d -le 512 ] && sips -z $d $d "$ROOT/web/icon-512.png" --out "$ICONSET/icon_${s}x${s}@2x.png" >/dev/null
done
iconutil -c icns "$ICONSET" -o "$APP/Contents/Resources/applet.icns"
rm -rf "$ICONSET" "$APP/Contents/Resources/Assets.car"
PLIST="$APP/Contents/Info.plist"
/usr/libexec/PlistBuddy -c "Delete :CFBundleIconName" "$PLIST" 2>/dev/null || true
plutil -replace CFBundleIdentifier -string local.focusstack.app "$PLIST"
plutil -replace CFBundleName -string "Focus Stack" "$PLIST"
plutil -replace CFBundleShortVersionString -string "$VERSION" "$PLIST"
plutil -replace CFBundleVersion -string "$VERSION" "$PLIST"
plutil -replace LSMinimumSystemVersion -string "13.0" "$PLIST"

# ---------- codice ----------
RES="$APP/Contents/Resources"
mkdir -p "$RES/app/firmware"
cp -R "$ROOT/backend" "$ROOT/web" "$ROOT/run.py" "$ROOT/VERSION" "$RES/app/"
cp -R "$FWOUT" "$RES/app/firmware/build"
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

# ---------- firma ad hoc (non serve un account Apple) e zip ----------
codesign --force --deep --sign - "$APP"
ZIP="$DIST/FocusStack-$VERSION.zip"
rm -f "$ZIP"
ditto -c -k --keepParent "$APP" "$ZIP"
echo "== Creato $ZIP ($(du -h "$ZIP" | cut -f1))"

if (( PUBLISH )); then
  NOTES="$ROOT/build/release-notes.md"
  {
    echo "Focus Stack $VERSION — firmware del focheggiatore build $FSBUILD."
    echo
    echo "**Prima installazione:** scarica lo zip, aprilo, trascina *Focus Stack* in Applicazioni e aprila."
    echo "macOS dirà che non può verificare lo sviluppatore: apri Impostazioni di Sistema → Privacy e sicurezza,"
    echo "scorri in basso e premi **Apri comunque**. Serve solo la prima volta: poi l'app si aggiorna da sola."
  } > "$NOTES"
  gh release create "v$VERSION" "$ZIP" --title "Focus Stack $VERSION" --notes-file "$NOTES"
  echo "== Pubblicata la release v$VERSION"
fi
