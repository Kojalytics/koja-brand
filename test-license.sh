#!/usr/bin/env bash
# Runs the tests in koja_license.rs on their own, without building an app: a throwaway crate with
# the dependencies rebrand.sh gives the apps (and their egui).
#
#   bash test-license.sh
set -euo pipefail
BRAND="$(cd "$(dirname "$0")" && pwd)"
DIR="${TMPDIR:-/tmp}/koja-license-test"
mkdir -p "$DIR/src"
cat >"$DIR/Cargo.toml" <<'EOF'
[package]
name = "koja-license-test"
version = "0.0.0"
edition = "2024"
publish = false

[lib]
path = "src/lib.rs"

[dependencies]
base64 = "0.22"
ed25519-dalek = { version = "2", default-features = false, features = ["std"] }
sha2 = "0.11"
serde_json = "1"
egui = "0.36"
EOF
printf '#[path = "%s/koja_license.rs"]\npub mod license;\n' "$BRAND" >"$DIR/src/lib.rs"
cargo test --manifest-path "$DIR/Cargo.toml" "$@"
