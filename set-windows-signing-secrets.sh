#!/usr/bin/env bash
# Stores the SSL.com eSigner secrets for Windows code signing in all Kojalytics GitHub repos, for
# the "Kojalytics release (Windows)" workflow. Run it yourself in the terminal: it asks for the
# values without showing them and passes each to `gh secret set` on stdin (never on the command line).
#
#   bash brand/set-windows-signing-secrets.sh
set -euo pipefail

REPOS=(craft-launcher wordcraft gridcraft deckcraft pdfcraft photocraft vectorcraft filmcraft lightcraft effectcraft designcraft cadcraft soundcraft figcraft)

gh auth status >/dev/null 2>&1 || { echo "Bitte zuerst bei GitHub anmelden: gh auth login" >&2; exit 1; }

read -r -p "SSL.com-Benutzername: " ES_USERNAME
read -r -s -p "SSL.com-Passwort: " ES_PASSWORD; echo
read -r -p "eSigner Credential ID (aus der Bestellung): " CREDENTIAL_ID
read -r -s -p "eSigner secret code (TOTP-Secret, unter dem QR-Code): " ES_TOTP_SECRET; echo
for v in ES_USERNAME ES_PASSWORD CREDENTIAL_ID ES_TOTP_SECRET; do
  [ -n "${!v}" ] || { echo "$v ist leer. Nichts wurde gespeichert." >&2; exit 1; }
done

for repo in "${REPOS[@]}"; do
  printf '%s' "$ES_USERNAME"    | gh secret set ES_USERNAME    -R "Kojalytics/$repo"
  printf '%s' "$ES_PASSWORD"    | gh secret set ES_PASSWORD    -R "Kojalytics/$repo"
  printf '%s' "$CREDENTIAL_ID"  | gh secret set CREDENTIAL_ID  -R "Kojalytics/$repo"
  printf '%s' "$ES_TOTP_SECRET" | gh secret set ES_TOTP_SECRET -R "Kojalytics/$repo"
  echo "✓ $repo"
done
unset ES_PASSWORD ES_TOTP_SECRET
echo
echo "Fertig: Windows-Signatur-Secrets in ${#REPOS[@]} Repos gespeichert."
