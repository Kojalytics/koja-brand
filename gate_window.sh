#!/usr/bin/env bash
# Puts the Kojalytics license lock screen in front of a Koja app's window: the first lines of the
# `fn ui` of its outermost `impl eframe::App` return early (showing the lock screen) until a license
# is activated. Run after brand/rebrand.sh, which adds apps/<id>/src/license.rs.
#
#   brand/gate_window.sh photocraft
set -euo pipefail
ID="${1:?usage: gate_window.sh <app-id>}"
BRAND="$(cd "$(dirname "$0")" && pwd)"
cd "$(dirname "$BRAND")/$ID"
APP_MAIN="apps/$ID/src/main.rs"
APP_TOML="apps/$ID/Cargo.toml"

if grep -q "impl eframe::App for" "$APP_MAIN"; then
  TARGET="$APP_MAIN"
  GATE="crate::license::gate"
else
  # The window lives in the UI library (shared with the web build): move the module there.
  TARGET="crates/ui-egui/src/lib.rs"
  GATE="crate::license::gate"
  cp "$BRAND/koja_license.rs" crates/ui-egui/src/license.rs
  git rm -q --cached "apps/$ID/src/license.rs" 2>/dev/null || true
  rm -f "apps/$ID/src/license.rs"
  perl -0pi -e 's/^mod license;\n\n//m' "$APP_MAIN"
  perl -0pi -e 's/^base64 = "0\.22"\ned25519-dalek = \{ version = "2", default-features = false, features = \["std"\] \}\nsha2 = "0\.11"\n//m' "$APP_TOML"
  UI_TOML=crates/ui-egui/Cargo.toml
  grep -q '^ed25519-dalek' "$UI_TOML" || perl -0pi -e 's{^\[dependencies\]\n}{[dependencies]\ned25519-dalek = { version = "2", default-features = false, features = ["std"] }\n}m' "$UI_TOML"
  grep -qE '^sha2 ?=' "$UI_TOML" || perl -0pi -e 's{^\[dependencies\]\n}{[dependencies]\nsha2 = "0.11"\n}m' "$UI_TOML"
  grep -qE '^base64 ?=' "$UI_TOML" || perl -0pi -e 's{^\[dependencies\]\n}{[dependencies]\nbase64 = "0.22"\n}m' "$UI_TOML"
  # First top-level `mod`/`pub mod` line that has no attribute right above it.
  grep -q 'mod license;' "$TARGET" || perl -0pi -e 's/(\n\n)((?:pub )?mod [a-z_]+;\n)/$1#[cfg(not(target_arch = "wasm32"))]\nmod license;\n$2/' "$TARGET"
fi
[ "$TARGET" = "crates/ui-egui/src/lib.rs" ] && grep -q 'mod license;' "$TARGET" || [ "$TARGET" = "$APP_MAIN" ] || { echo "error: could not add mod license to $TARGET" >&2; exit 1; }

if grep -q 'license::gate(' "$TARGET"; then
  echo "$ID: already gated in $TARGET"
else
  GATE="$GATE" perl -0pi -e '
    my $g = $ENV{GATE};
    s{(impl eframe::App for [^\{]+\{.*?fn ui\(&mut self, (\w+): &mut egui::Ui, [^)]*\) \{\n)}{$1        // Without an activated Kojalytics license the window shows the lock screen instead.\n        #[cfg(not(target_arch = "wasm32"))]\n        if !$g($2) {\n            return;\n        }\n}s;
  ' "$TARGET"
  grep -q 'license::gate(' "$TARGET" && echo "$ID: gated in $TARGET" || { echo "error: $ID: no fn ui found in the eframe::App impl of $TARGET" >&2; exit 1; }
fi
