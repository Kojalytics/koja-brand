#!/usr/bin/env bash
# Forks one Craft app (github.com/storytold/<id>) to github.com/Kojalytics and rebrands it as a
# Koja app, the way WordKoja, GridKoja and DeckKoja were done:
#
#   brand/rebrand.sh pdfcraft PdfKoja
#   KOJALYTICS_DISCORD=https://discord.gg/<invite> brand/rebrand.sh pdfcraft PdfKoja
#                         (points ArtCraft's Discord links at Kojalytics' own server)
#
# - checks the code license (MIT or Apache-2.0 only) before touching anything
# - removes the ArtCraft marks (docs/brand) and renames ArtCraft → Kojalytics, <X>Craft → <X>Koja,
#   storytold → Kojalytics, getartcraft.com → kojalytics.com, ai.storyteller.* → com.kojalytics.*
# - keeps what the license requires: ArtCraft copyright lines, and NOTICE names the original
# - adds the Kojalytics license check (brand/koja_license.rs) and gates the app window with it
# - new DMG background with the Koja name, Keychain-profile notarization in package.sh
#
# It does not commit. It ends with a report of what still needs a human look (Discord/social links,
# authorship sentences, test fixtures) and the commands to build and test.
set -euo pipefail

ID="${1:?usage: rebrand.sh <app-id, e.g. pdfcraft> <KojaName, e.g. PdfKoja>}"
NEW="${2:?usage: rebrand.sh <app-id> <KojaName>}"
OLD="${NEW%Koja}Craft"
BRAND="$(cd "$(dirname "$0")" && pwd)"
APPS="$(dirname "$BRAND")"
REPO="$APPS/$ID"
step() { printf '\n==> %s\n' "$*"; }

step "license of storytold/$ID"
LICENSE="$(gh api "repos/storytold/$ID" --jq '.license.spdx_id // "NONE"')"
case "$LICENSE" in
  Apache-2.0 | MIT) echo "$LICENSE: may be modified and sold with attribution" ;;
  *) echo "error: storytold/$ID is licensed '$LICENSE', not MIT/Apache-2.0. Stop: check it by hand." >&2; exit 1 ;;
esac

step "fork and clone"
gh repo view "Kojalytics/$ID" >/dev/null 2>&1 || gh repo fork "storytold/$ID" --clone=false
if [ ! -d "$REPO/.git" ]; then
  git clone -q --depth 50 "https://github.com/Kojalytics/$ID.git" "$REPO"
  git -C "$REPO" remote add upstream "https://github.com/storytold/$ID.git"
fi
cd "$REPO"
[ -f "apps/$ID/src/main.rs" ] || { echo "error: apps/$ID/src/main.rs not found; this app is laid out differently" >&2; exit 1; }

step "remove the ArtCraft marks"
if git ls-files docs/brand | grep -q .; then git rm -q -r docs/brand && echo "docs/brand removed"; fi
# Code that embeds the marks (include_bytes!/include_image! of docs/brand/artcraft-*.svg) gets
# Kojalytics' own logo files instead.
if grep -rqI -e "docs/brand/artcraft-" -e "bytes://artcraft-" crates apps 2>/dev/null; then
  mkdir -p docs/brand
  cp "$BRAND/svg/"kojalytics-*.svg docs/brand/
  # PNG copies too, for apps that embed PNGs instead of SVGs.
  for s in docs/brand/kojalytics-logo docs/brand/kojalytics-logo-white; do resvg -h 216 "$s.svg" "$s.png"; done
  for s in docs/brand/kojalytics-mark docs/brand/kojalytics-mark-black; do resvg -w 256 -h 256 "$s.svg" "$s.png"; done
  grep -rlI -e "docs/brand/artcraft-" -e "bytes://artcraft-" crates apps | tr '\n' '\0' | xargs -0 perl -pi -e 's{artcraft-(logo-white|logo|mark-black|mark)\.(svg|png)}{kojalytics-$1.$2}g'
  echo "embedded logos now point at docs/brand/kojalytics-*.svg/.png"
fi

step "rename what customers see"
# Only customer-visible text changes: whole installer files and translation catalogs, and the string
# literals in the Rust code (window titles, labels, About text, links). Identifiers, comments and
# tests stay as they are, so nothing internal breaks.
TEXT_DIRS=(crates apps packaging)
MATCH=(-e ArtCraft -e Craft -e storytold -e getartcraft -e ai.storyteller)
# Installer files and translation catalogs: everything in them is shown to the customer.
VISIBLE=$( { grep -rlI "${MATCH[@]}" packaging 2>/dev/null || true; grep -rlI "${MATCH[@]}" crates apps --include='*.tsv' --include='*.ftl' --include='*.po' --include='*.json' --include='*.toml' --include='*.yaml' --include='*.yml' 2>/dev/null | grep -iE 'i18n|/locales?/|/translations?/|/lang/' || true; } | sort -u)
[ -n "$VISIBLE" ] && printf '%s\n' "$VISIBLE" | tr '\n' '\0' | xargs -0 perl -pi "$BRAND/visible_rename.pl"
# Rust code: only inside "…" string literals, and not in tests.
CODE=$(grep -rlI "${MATCH[@]}" crates apps --include='*.rs' 2>/dev/null | grep -v -e '/tests/' -e 'tests\.rs$' -e '_tests\.rs$' || true)
[ -n "$CODE" ] && printf '%s\n' "$CODE" | tr '\n' '\0' | KOJA_CODE=1 xargs -0 perl -pi "$BRAND/visible_rename.pl"
echo "$(printf '%s\n' "$VISIBLE" | grep -c .) installer/translation files, $(printf '%s\n' "$CODE" | grep -c .) code files (string literals only)"
# The attribution the license requires names the original, in every language: undo the rename there.
git ls-files crates apps | grep -E '/i18n/|/locales?/|\.rs$' | tr '\n' '\0' | xargs -0 perl -pi -e 's/Based on (\w+)Koja by the Kojalytics team/Based on $1Craft by the ArtCraft team/g; s/Basiert auf (\w+)Koja vom Kojalytics-Team/Basiert auf $1Craft vom ArtCraft-Team/g'
# Shared libraries stay on ArtCraft's repos (MIT/Apache, fetched as dependencies).
find . -name Cargo.toml -not -path "./target/*" -print0 | xargs -0 perl -pi -e 's{git = "https://github\.com/Kojalytics/}{git = "https://github.com/storytold/}g'
find . -path ./target -prune -o -path ./.git -prune -o -name '*ai.storyteller.*' -print | while read -r f; do
  git mv "$f" "${f/ai.storyteller./com.kojalytics.}"
done

step "license check"
MAIN="apps/$ID/src/main.rs"
cp "$BRAND/koja_license.rs" "apps/$ID/src/license.rs"
grep -q '^mod license;' "$MAIN" || perl -0pi -e 's/^use /mod license;\n\nuse /m' "$MAIN"
grep -q 'license::gate(ui)' "$MAIN" || perl -0pi -e 's#(fn ui\(&mut self, ui: &mut egui::Ui, _?frame: &mut eframe::Frame\) \{\n)(\s*)self\.0\.ui\(ui\);#$1$2// Without an activated Kojalytics license the window shows the lock screen instead.\n$2if license::gate(ui) {\n$2    self.0.ui(ui);\n$2}#' "$MAIN"
GATED=$(grep -c 'license::gate(ui)' "$MAIN" || true)
TOML="apps/$ID/Cargo.toml"
grep -q '^ed25519-dalek' "$TOML" || perl -0pi -e 's{^\[dependencies\]\n}{[dependencies]\nbase64 = "0.22"\ned25519-dalek = { version = "2", default-features = false, features = ["std"] }\nsha2 = "0.11"\n}m' "$TOML"
echo "license.rs added, window gated: $GATED"

step "NOTICE"
if head -1 NOTICE | grep -q "^$OLD\$"; then
  NEWAPP="$NEW" OLDAPP="$OLD" perl -0pi -e '
    my ($n, $o) = ($ENV{NEWAPP}, $ENV{OLDAPP});
    s{\A\Q$o\E\n(Copyright \(c\) 2026 ArtCraft Team and the \Q$o\E contributors\.)\n}{$n\nCopyright (c) 2026 Kojalytics (modifications).\nBased on $o by the ArtCraft team:\n$1\n};
    s{The ArtCraft name, wordmark and logos in docs/brand/ are trademarks of the ArtCraft Team\. They are\nnot open source and are not covered by the license above; their terms are in\ndocs/brand/LICENSE-brand\.txt\.\n}{Changes by Kojalytics: renamed the app to $n, removed the ArtCraft name and marks,\npointed links and updates at github.com/Kojalytics and kojalytics.com, and added the Kojalytics\nlicense check. Kojalytics is not affiliated with, sponsored or endorsed by the ArtCraft Team.\nThe Kojalytics name and logo are trademarks of Kojalytics and are not covered by the license above.\n};
  ' NOTICE
  head -4 NOTICE
else
  echo "NOTICE starts differently: edit it by hand (keep the ArtCraft copyright, add Kojalytics' changes)"
fi

step "DMG background and notarization"
DMG=packaging/macos/dmg
if [ -d "$DMG" ]; then
  ICON="assets/app-icon/$ID-1024.png"
  ICON_ARGS=("$NEW")
  [ -f "$ICON" ] && ICON_ARGS+=("$ICON")
  python3 "$BRAND/build_dmg_background.py" "$BRAND/fonts/Inter-Variable.ttf" "$DMG/background.svg" "${ICON_ARGS[@]}"
  [ -f "$DMG/generate.py" ] && python3 "$DMG/generate.py" >/dev/null && echo "background.tiff and layout regenerated"
fi
PKG=packaging/macos/package.sh
if [ -f "$PKG" ] && ! grep -q NOTARY_PROFILE "$PKG"; then
  perl -0pi -e '
    s{elif \[ -n "\$\{APPLE_ID:-\}" \] && \[ -n "\$\{APPLE_PASSWORD:-\}" \] && \[ -n "\$\{APPLE_TEAM_ID:-\}" \]; then\n  NOTARIZE=1}{elif [ -n "\${NOTARY_PROFILE:-}" ] || { [ -n "\${APPLE_ID:-}" ] && [ -n "\${APPLE_PASSWORD:-}" ] && [ -n "\${APPLE_TEAM_ID:-}" ]; }; then\n  NOTARIZE=1};
    s{(notarize\(\) \{\n  local file="\$1" out id status\n)}{$1  # NOTARY_PROFILE: a Keychain profile from `xcrun notarytool store-credentials` (no password in env).\n  local auth=(--apple-id "\${APPLE_ID:-}" --password "\${APPLE_PASSWORD:-}" --team-id "\${APPLE_TEAM_ID:-}")\n  [ -n "\${NOTARY_PROFILE:-}" ] && auth=(--keychain-profile "\$NOTARY_PROFILE")\n};
    s{  out="\$\(xcrun notarytool submit "\$file" --apple-id "\$APPLE_ID" --password "\$APPLE_PASSWORD" \\\n    --team-id "\$APPLE_TEAM_ID" --wait --timeout 1h --output-format json\)" \|\| true\n  echo "\$out"\n  id="\$\(printf \x27%s\x27 "\$out" \| plutil -extract id raw -o - - 2>/dev/null \|\| true\)"\n  status="\$\(printf \x27%s\x27 "\$out" \| plutil -extract status raw -o - - 2>/dev/null \|\| true\)"\n}{  out="\$(xcrun notarytool submit "\$file" "\${auth[@]}" --output-format json)" || true\n  echo "\$out"\n  id="\$(printf \x27%s\x27 "\$out" | plutil -extract id raw -o - - 2>/dev/null || true)"\n  status=""\n  # Apple can take long (a new account: an hour or more). A dropped connection only ends this\n  # wait, not the submission, so ask again.\n  for _ in 1 2 3 4 5 6; do\n    [ -n "\$id" ] || break\n    out="\$(xcrun notarytool wait "\$id" "\${auth[@]}" --timeout 1h --output-format json)" || true\n    echo "\$out"\n    status="\$(printf \x27%s\x27 "\$out" | plutil -extract status raw -o - - 2>/dev/null || true)"\n    case "\$status" in Accepted | Invalid | Rejected) break ;; esac\n    sleep 30\n  done\n};
    s{xcrun notarytool log "\$id" --apple-id "\$APPLE_ID" --password "\$APPLE_PASSWORD" --team-id "\$APPLE_TEAM_ID"}{xcrun notarytool log "\$id" "\${auth[@]}"};
  ' "$PKG"
  bash -n "$PKG" && echo "package.sh: notarization via NOTARY_PROFILE ($(grep -c 'notarytool wait' "$PKG") wait loop)"
fi

step "report: check these by hand"
echo "-- bundled assets whose license is not MIT/Apache/OFL/CC0/public domain (check before selling):"
for f in ATTRIBUTION.md NOTICE assets/*/LICENSE* assets/LICENSE*; do
  [ -f "$f" ] || continue
  grep -nIiE "license|licen[cs]e|CC[- ]BY|GPL|non-?commercial|all rights reserved|proprietary" "$f" 2>/dev/null \
    | grep -viE "MIT|Apache|OFL|Open Font|CC0|public domain|Unlicense|zlib|BSD" | sed "s|^|$f:|" | cut -c1-170 | head -15 || true
done
echo "-- leftovers (should be empty):"
grep -rnI -e ArtCraft -e getartcraft -e ai.storyteller -e "discord.gg/artcraft" "${TEXT_DIRS[@]}" 2>/dev/null | grep -v 'git = "https://github.com/storytold' | grep -v 'ArtCraft Team and the' | cut -c1-160 | head -20 || true
# Installers (Linux metainfo, Windows MSI, macOS credits) link ArtCraft's Discord as the help link.
grep -rlI "discord\.gg/artcraft" packaging 2>/dev/null | tr '\n' '\0' | xargs -0 perl -pi -e 's{https://discord\.gg/artcraft}{https://www.kojalytics.com/contact}g; s{discord\.gg/artcraft}{kojalytics.com/contact}g' 2>/dev/null || true
echo "-- Discord buttons, commands and social links: REMOVE them (Koja apps have no Discord):"
grep -rnIi -e discord -e "x.com/" -e instagram -e tiktok -e youtube.com "${TEXT_DIRS[@]}" --include='*.rs' --include='*.in' --include='*.wxs' --include='*.rtf' --include='*.desktop' 2>/dev/null | grep -v "/tests/" | cut -c1-160 | head -30 || true
echo "   (tests that look for a Discord button need the same change)"
echo "-- GitHub buttons and source links: REMOVE them (Koja apps link only to kojalytics.com):"
grep -rnI -e 'help\.github' -e 'links::GITHUB' -e 'on GitHub' -e 'Source code' -e 'Source on GitHub' -e 'GitHub repository' -e 'tl!("GitHub")' "${TEXT_DIRS[@]}" --include='*.rs' 2>/dev/null | grep -v "/tests/" | cut -c1-160 | head -20 || true
# kojalytics.com has no per-app pages: every app links to the Koja apps page.
grep -rlI "kojalytics\.com/apps/" "${TEXT_DIRS[@]}" 2>/dev/null | tr '\n' '\0' | xargs -0 perl -pi -e 's{https://kojalytics\.com/apps/[a-z]+}{https://www.kojalytics.com/koja-apps}g; s{(?<![/.\w])kojalytics\.com/apps/[a-z]+}{kojalytics.com/koja-apps}g' 2>/dev/null || true
echo "-- sentences that now claim Kojalytics wrote it (say 'Based on $OLD by the ArtCraft team' instead):"
grep -rnI -e "Kojalytics team" -e "Kojalytics-Team" -e "Part of Kojalytics" -e "from the Kojalytics" "${TEXT_DIRS[@]}" --include='*.rs' 2>/dev/null | cut -c1-160 | head -10 || true
[ "$GATED" = 1 ] || echo "!! the app window is NOT gated yet: add 'if license::gate(ui) { … }' to fn ui in $MAIN"
cat <<EOF

Next:
  cd "$REPO"
  cargo build --release && cargo test --release --workspace --no-fail-fast
  (test fixtures that embed the old name, e.g. fonts, may need their names back: see DeckKoja's)
  git add -A && git commit && git push
  then add "$ID" to LISTED in craft-launcher/crates/core/src/catalog.rs once its release is out.
EOF
