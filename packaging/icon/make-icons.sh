#!/usr/bin/env bash
# Rigenera l'icona dell'app dai disegni SVG in src/ (macOS: Quick Look; Python con uv). Stesso metodo di
# Focus Fusion (packaging/icons/make-icons.sh), con cui l'icona è coordinata.
#
#   src/above.svg, src/focus.svg, src/below.svg   livelli dell'icona Liquid Glass (AppIcon.icon, formato Icon Composer)
#   src/flat.svg                                  la stessa icona appiattita, per .icns (macOS 13-25) e PNG
#
# Uscita: AppIcon.icon/ (si apre e si ritocca con Icon Composer) e AppIcon-1024.png.
# build_release.sh compila AppIcon.icon in Assets.car (actool) e AppIcon-1024.png in AppIcon.icns (iconutil).
set -euo pipefail
cd "$(dirname "$0")"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

# 1. SVG -> PNG con trasparenza vera. Quick Look disegna sempre su bianco: ogni disegno si rende su bianco e
#    su nero e l'alfa si ricava dalla differenza, a = 1 - (bianco - nero) / 255.
for f in above focus below flat; do
  cp "src/$f.svg" "$tmp/${f}_w.svg"
  awk '/^<svg/ && !done {print; print "<rect width=\"1024\" height=\"1024\" fill=\"#000000\"/>"; done=1; next}1' \
    "src/$f.svg" > "$tmp/${f}_b.svg"
done
(cd "$tmp" && qlmanage -t -s 1024 -o . ./*_w.svg ./*_b.svg >/dev/null 2>&1)
uv run -q --no-project --with pillow --with numpy python -I - "$tmp" <<'PY'
import sys
import numpy as np
from PIL import Image
t = sys.argv[1]
for f in ["above", "focus", "below", "flat"]:
    w = np.asarray(Image.open(f"{t}/{f}_w.svg.png").convert("RGB")).astype(np.float64)
    b = np.asarray(Image.open(f"{t}/{f}_b.svg.png").convert("RGB")).astype(np.float64)
    a = np.clip(1 - (w - b).mean(axis=2) / 255, 0, 1)
    c = np.where(a[..., None] > 1e-3, b / np.maximum(a[..., None], 1e-3), 0)
    Image.fromarray(np.dstack([np.clip(c, 0, 255), a * 255]).round().astype(np.uint8), "RGBA").save(f"{t}/{f}.png")
PY

# 2. icona Liquid Glass (documento di Icon Composer): sfondo ardesia #283241 (i colori dell'interfaccia)
#    + tre gruppi, dal più vicino a chi guarda.
#    Gli anelli sopra il piano a fuoco passano davanti: sono più vicini.
rm -rf AppIcon.icon
mkdir -p AppIcon.icon/Assets
cp "$tmp/above.png" "$tmp/focus.png" "$tmp/below.png" AppIcon.icon/Assets/
cat > AppIcon.icon/icon.json <<'JSON'
{
  "fill" : {
    "automatic-gradient" : "extended-srgb:0.15686,0.19608,0.25490,1.00000"
  },
  "groups" : [
    {
      "layers" : [
        { "image-name" : "above.png", "name" : "above", "position" : { "scale" : 1, "translation-in-points" : [ 0, 0 ] } }
      ],
      "name" : "out of focus, above",
      "shadow" : { "kind" : "neutral", "opacity" : 0.3 },
      "specular" : false,
      "translucency" : { "enabled" : true, "value" : 0.5 }
    },
    {
      "layers" : [
        { "image-name" : "focus.png", "name" : "ring in focus", "position" : { "scale" : 1, "translation-in-points" : [ 0, 0 ] } }
      ],
      "name" : "in focus",
      "shadow" : { "kind" : "neutral", "opacity" : 0.5 },
      "specular" : true,
      "translucency" : { "enabled" : false, "value" : 0.5 }
    },
    {
      "layers" : [
        { "image-name" : "below.png", "name" : "below", "position" : { "scale" : 1, "translation-in-points" : [ 0, 0 ] } }
      ],
      "name" : "out of focus, below",
      "shadow" : { "kind" : "neutral", "opacity" : 0.3 },
      "specular" : false,
      "translucency" : { "enabled" : true, "value" : 0.5 }
    }
  ],
  "supported-platforms" : {
    "squares" : "shared"
  }
}
JSON

# 3. icona piatta
cp "$tmp/flat.png" AppIcon-1024.png

# 4. icone della pagina web (logo, scheda del browser, telefono): la stessa icona senza il margine di macOS.
#    icon-512.png è a tutto quadrato: iPhone e iPad arrotondano gli angoli da soli.
WEB=../../web
sed -e 's|width="1024" height="1024" viewBox="0 0 1024 1024"|viewBox="100 100 824 824"|' \
    -e 's|<!-- icona piatta per .icns.*|<!-- Logo e icona della pagina: generato da packaging/icon/make-icons.sh (src/flat.svg senza il margine di macOS).|' \
    src/flat.svg > "$WEB/icon.svg"
sed -e 's|viewBox="100 100 824 824"|width="512" height="512" viewBox="100 100 824 824"|' -e 's| rx="228"| rx="0"|g' \
    -e 's|<rect x="5" y="5" width="1014" height="1014" rx="223"[^>]*/>||' "$WEB/icon.svg" > "$tmp/square.svg"
(cd "$tmp" && qlmanage -t -s 512 -o . ./square.svg >/dev/null 2>&1)
sips -s format png "$tmp/square.svg.png" --out "$WEB/icon-512.png" >/dev/null
echo "AppIcon.icon, AppIcon-1024.png, web/icon.svg e web/icon-512.png aggiornati"
