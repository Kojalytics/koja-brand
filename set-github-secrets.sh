#!/usr/bin/env bash
# Stores the macOS signing and notarization secrets in all Kojalytics GitHub repos, for the
# "Kojalytics release (macOS)" workflow. Run it yourself in the terminal: it asks for the passwords
# without showing them, and passes every value to `gh secret set` on stdin (never on the command line).
#
#   bash brand/set-github-secrets.sh [path/to/certificate.p12]
set -euo pipefail

P12="${1:-$HOME/Desktop/kojalytics-developer-id.p12}"
REPOS=(craft-launcher wordcraft gridcraft deckcraft pdfcraft photocraft vectorcraft filmcraft lightcraft effectcraft designcraft cadcraft soundcraft figcraft)
TEAM_ID="SF4KRG2343"

[ -f "$P12" ] || { echo "Zertifikatsdatei nicht gefunden: $P12" >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "Bitte zuerst bei GitHub anmelden: gh auth login" >&2; exit 1; }

read -r -p "Apple-ID deines Developer-Kontos [farzad.khojazada@icloud.com]: " APPLE_ID
APPLE_ID="${APPLE_ID:-farzad.khojazada@icloud.com}"
read -r -s -p "Passwort der .p12-Datei (beim Export vergeben): " P12_PASSWORD; echo
read -r -s -p "App-spezifisches Passwort (abcd-efgh-ijkl-mnop): " APP_PASSWORD; echo

# Check the .p12 password before sending anything.
if ! openssl pkcs12 -in "$P12" -passin "pass:$P12_PASSWORD" -nokeys -legacy >/dev/null 2>&1 \
  && ! openssl pkcs12 -in "$P12" -passin "pass:$P12_PASSWORD" -nokeys >/dev/null 2>&1; then
  echo "Das .p12-Passwort passt nicht zur Datei. Nichts wurde gespeichert." >&2
  exit 1
fi
CERT_B64="$(base64 -i "$P12" | tr -d '\n')"

for repo in "${REPOS[@]}"; do
  printf '%s' "$CERT_B64"      | gh secret set APPLE_CERTIFICATE          -R "Kojalytics/$repo"
  printf '%s' "$P12_PASSWORD"  | gh secret set APPLE_CERTIFICATE_PASSWORD -R "Kojalytics/$repo"
  printf '%s' "$APPLE_ID"      | gh secret set APPLE_ID                   -R "Kojalytics/$repo"
  printf '%s' "$APP_PASSWORD"  | gh secret set APPLE_PASSWORD             -R "Kojalytics/$repo"
  printf '%s' "$TEAM_ID"       | gh secret set APPLE_TEAM_ID              -R "Kojalytics/$repo"
  echo "✓ $repo"
done
unset CERT_B64 P12_PASSWORD APP_PASSWORD
echo
echo "Fertig: Secrets in ${#REPOS[@]} Repos gespeichert."
echo "Lösche jetzt die Datei $P12 (oder bewahre sie sicher auf) — sie enthält deinen privaten Signaturschlüssel."
