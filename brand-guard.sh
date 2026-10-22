#!/usr/bin/env bash
# Branding guard: fails (exit 1) when anything a customer can see still shows ArtCraft, a Craft app
# name, Discord, ArtCraft's links or developer ID, or when the Kojalytics license check is missing.
# Run it in a repo before every release:  bash brand-guard.sh <repo-dir> <app-id>
# Allowed: the attribution the license requires (copyright lines, "Based on <X>Craft by the
# ArtCraft team"), crate/dependency names and tests.
set -uo pipefail
REPO="${1:?usage: brand-guard.sh <repo-dir> <app-id>}"
ID="${2:?usage: brand-guard.sh <repo-dir> <app-id>}"
cd "$REPO" || exit 2
FAIL=0
bad() { printf '  ✗ %s\n' "$*"; FAIL=1; }

# Visible text: string literals in Rust code (not tests), installer files, translation catalogs.
PATTERN='ArtCraft|getartcraft|storytold|ai\.storyteller|\b(Photo|Vector|Film|Light|Pdf|Effect|Design|Word|Deck|Grid|CAD|Sound|Fig)Craft\b|Craft App Suite|[Dd]iscord|DJ6XS33FX8'
ALLOW='Copyright|©|Based on|ArtCraft Team and|by the ArtCraft team|not affiliated with|git = "https://github.com/storytold'
RS=$(git ls-files 'crates/*.rs' 'apps/*.rs' | grep -vE '(^|/)tests?(/|\.rs$)|_tests?\.rs$|/tests_[a-z0-9_]+\.rs$|/benches/|/examples/|^crates/mcp/|-cli/|/i18n(\.rs|/)')
HITS=$(printf '%s\n' "$RS" | tr '\n' '\0' | P="$PATTERN" A="$ALLOW" xargs -0 perl -ne '
  next if /^\s*\/\//;                       # comments
  $in_test = 1 if /^\s*#\[cfg\(test\)\]/;   # test modules at the end of a file
  next if $in_test;
  while (/("(?:[^"\\]|\\.)*")/g) { my $s = $1; next if $s =~ /^.discord.$/; print "$ARGV:$.: $s\n" if $s =~ /$ENV{P}/ && $_ !~ /$ENV{A}/; }
} continue { if (eof) { close ARGV; $in_test = 0 }')
# Catalogs also hold unused entries (a removed Discord button's label), so only names and links count
# there; a label the code still uses shows up in the Rust check above.
NAMES='ArtCraft|getartcraft|storytold|ai\.storyteller|\b(Photo|Vector|Film|Light|Pdf|Effect|Design|Word|Deck|Grid|CAD|Sound|Fig)Craft\b|Craft App Suite'
OTHER=$(git ls-files packaging 'crates/*' 'apps/*' | grep -E '^packaging/macos/|/i18n/|/locales?/' \
  | grep -vE '\.(rs|png|tiff|icns|ico|ttf|otf|md)$|LICENSE|\.attribution$' \
  | tr '\n' '\0' | xargs -0 grep -nIE "$NAMES" 2>/dev/null | grep -vE "$ALLOW" | grep -vE '^[^:]+:[0-9]+:\s*(#|//)')
[ -z "$HITS$OTHER" ] || { bad "visible ArtCraft/Craft/Discord text:"; printf '%s\n' "$HITS" "$OTHER" | grep . | cut -c1-200 | head -40 | sed 's/^/      /'; }

# The attribution must name the original, not claim Kojalytics wrote it.
CLAIM=$( { printf '%s\n' "$RS" | tr '\n' '\0' | xargs -0 grep -nE 'Based on [A-Za-z]+Koja|by the Kojalytics [Tt]eam' 2>/dev/null
  git ls-files 'crates/*' 'apps/*' | grep -E '/i18n/|/locales?/' | tr '\n' '\0' | xargs -0 grep -nE 'Based on [A-Za-z]+Koja|Basiert auf [A-Za-z]+Koja' 2>/dev/null; } | grep -vE '^[^:]+:[0-9]+:\s*//')
[ -z "$CLAIM" ] || { bad "attribution rewritten (must say 'Based on <X>Craft by the ArtCraft team'):"; printf '%s\n' "$CLAIM" | cut -c1-200 | head -5 | sed 's/^/      /'; }

# GitHub buttons and source links in the UI.
GH=$(printf '%s\n' "$RS" | grep -vE '/i18n(\.rs|/)|^crates/mcp/' | tr '\n' '\0' | xargs -0 grep -nE 'help\.github|links::GITHUB|"Source code|Source on GitHub|GitHub repository|tl!\("GitHub"\)' 2>/dev/null | grep -vE '^[^:]+:[0-9]+:\s*//')
[ -z "$GH" ] || { bad "GitHub buttons/links in the UI:"; printf '%s\n' "$GH" | cut -c1-200 | head -10 | sed 's/^/      /'; }

# ArtCraft's logo files.
LOGOS=$(git ls-files | grep -iE '(^|/)artcraft-(logo|mark)[^/]*\.(svg|png)$')
[ -z "$LOGOS" ] || bad "ArtCraft logo files: $LOGOS"

# The Kojalytics license check (apps only, not the launcher).
if [ "$ID" != craft-launcher ]; then
  GATE=$(git grep -l 'license::gate(' -- "apps/$ID/src" 'crates/ui-egui/src' 2>/dev/null | head -1)
  [ -n "$GATE" ] || bad "license check (license::gate) missing in apps/$ID/src and crates/ui-egui/src"
  git grep -q 'kojalytics-device:' -- "apps/$ID/src" 'crates/ui-egui/src' 2>/dev/null || bad "Kojalytics license module missing"
else
  grep -q 'TEAM_ID: &str = "SF4KRG2343"' crates/native/src/install.rs || bad "launcher does not trust team SF4KRG2343"
fi

# Bundle id and the NOTICE attribution.
PLIST=$(git ls-files 'packaging/macos/*' | xargs grep -lE 'CFBundleIdentifier' 2>/dev/null | head -1)
[ -z "$PLIST" ] || ! grep -q 'ai\.storyteller' "$PLIST" || bad "bundle id still ai.storyteller in $PLIST"
grep -q 'Kojalytics' NOTICE 2>/dev/null || bad "NOTICE has no Kojalytics attribution"

if [ "$FAIL" = 0 ]; then echo "✓ brand guard: $ID is clean"; else echo "✗ brand guard: $ID FAILED"; fi
exit "$FAIL"
