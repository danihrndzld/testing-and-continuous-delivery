#!/usr/bin/env bash
# Renderiza un reporte HTML a PDF con Chrome headless (sin LaTeX).
# Uso: html_a_pdf.sh reporte.html [salida.pdf]
set -euo pipefail

in="${1:?uso: html_a_pdf.sh reporte.html [salida.pdf]}"
[ -f "$in" ] || { echo "no existe: $in" >&2; exit 1; }
out="${2:-${in%.html}.pdf}"

chrome="${CHROME:-}"
if [ -z "$chrome" ]; then
  for c in \
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
    "/Applications/Chromium.app/Contents/MacOS/Chromium" \
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge" \
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" \
    google-chrome google-chrome-stable chromium chromium-browser microsoft-edge brave-browser; do
    if [ -x "$c" ] || command -v "$c" >/dev/null 2>&1; then chrome="$c"; break; fi
  done
fi
[ -n "$chrome" ] || { echo "No encontré Chrome/Chromium/Edge/Brave. Instala uno o exporta CHROME=/ruta/al/binario." >&2; exit 1; }

uri="$(python3 -c 'import pathlib,sys;print(pathlib.Path(sys.argv[1]).resolve().as_uri())' "$in")"
rm -f "$out"
"$chrome" --headless=new --disable-gpu --no-pdf-header-footer \
  --generate-pdf-document-outline --print-to-pdf="$out" "$uri" 2>/dev/null || true

[ -s "$out" ] || { echo "Chrome no generó $out" >&2; exit 1; }
echo "$out"
