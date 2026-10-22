#!/usr/bin/env bash
# Builds, signs and notarizes the four Kojalytics DMGs (universal). Log: brand/dmg-build.log
set -uo pipefail
export PATH="$HOME/.cargo/bin:$PATH"
export MACOS_SIGN_IDENTITY="Developer ID Application: Farzad Khojazada (SF4KRG2343)"
export NOTARY_PROFILE=kojalytics-notary
B="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$B/brand/dmg-build.log"
: >"$LOG"
REPOS=("$@")
[ ${#REPOS[@]} -eq 0 ] && REPOS=(craft-launcher wordcraft gridcraft deckcraft)
for r in "${REPOS[@]}"; do
  echo "########## $r start $(date +%H:%M)" | tee -a "$LOG"
  (cd "$B/$r" && bash packaging/macos/package.sh --arch universal) >>"$LOG" 2>&1
  echo "########## $r exit=$? $(date +%H:%M)" | tee -a "$LOG"
  (cd "$B/$r" && cargo clean) >>"$LOG" 2>&1
done
echo "Fertig. DMGs:"
ls -la "$B"/*/dist/release/*.dmg 2>/dev/null
