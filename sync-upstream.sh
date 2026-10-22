#!/usr/bin/env bash
# Brings one Koja app up to the newest ArtCraft release and rebrands it again:
#
#   brand/sync-upstream.sh wordcraft WordKoja          (in Kojalytics-Apps, or CI with BRAND/APPS set)
#
# 1. finds the newest release tag of storytold/<id>; stops (exit 0) when we already have it
# 2. merges it on branch koja-sync; where ArtCraft and Kojalytics changed the same lines, ArtCraft's
#    code wins (keeps the app correct) and the branding is applied again in step 3
# 3. brand/rebrand.sh, then brand/brand-guard.sh: nothing ArtCraft/Craft/Discord may be visible
# 4. tests; on success a commit "Update to <X>Craft <version>" on koja-sync (not pushed, not merged)
# Exit 0 = up to date or ready, 1 = blocked (guard, merge or tests): a person must look.
set -euo pipefail
ID="${1:?usage: sync-upstream.sh <app-id> <KojaName>}"
NEW="${2:?usage: sync-upstream.sh <app-id> <KojaName>}"
OLD="${NEW%Koja}Craft"
BRAND="${BRAND:-$(cd "$(dirname "$0")" && pwd)}"
APPS="${APPS:-$(dirname "$BRAND")}"
cd "$APPS/$ID"
export PATH="$HOME/.cargo/bin:$PATH"

git remote get-url upstream >/dev/null 2>&1 || git remote add upstream "https://github.com/storytold/$ID.git"
git fetch -q upstream --tags
LATEST=$(git ls-remote --tags --refs upstream 'v*' | sed 's|.*refs/tags/||' | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1)
OURS="v$(grep -m1 -E '^version = "' Cargo.toml | cut -d'"' -f2)"
if [ "$(printf '%s\n%s\n' "$OURS" "$LATEST" | sort -V | tail -1)" = "$OURS" ]; then
  echo "$NEW is up to date ($OURS, ArtCraft $LATEST)"; exit 0
fi
echo "==> $NEW $OURS → $OLD $LATEST"

[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "error: $ID has uncommitted changes" >&2; exit 1; }
git switch -q -C koja-sync
git merge -q --no-edit -X theirs "$LATEST" || { echo "BLOCKED: merge of $LATEST failed" >&2; git merge --abort; exit 1; }

bash "$BRAND/rebrand.sh" "$ID" "$NEW" >"$APPS/$ID-rebrand.log" 2>&1 || { echo "BLOCKED: rebrand.sh failed (see $ID-rebrand.log)" >&2; exit 1; }
bash "$BRAND/brand-guard.sh" . "$ID" || { echo "BLOCKED: branding guard failed: fix and run again" >&2; exit 1; }

# Tests: a failure blocks only when ArtCraft's own release passes that test (their bugs aren't ours).
failed() { grep -E '^[^ ]+ --- FAILED$' "$1" | sed 's/ --- FAILED$//' | sort -u; }
if ! cargo test --release --workspace --no-fail-fast -q >"$APPS/$ID-tests.log" 2>&1; then
  OURS_FAILED=$(failed "$APPS/$ID-tests.log")
  UP="$APPS/.$ID-upstream"
  git worktree add -q --detach "$UP" "$LATEST"
  for pkg in $(grep -oE 'to rerun pass `-p [^ ]+ [^`]*`' "$APPS/$ID-tests.log" | sed -E 's/.*`(.*)`/\1/' | tr ' ' '#' | sort -u); do
    (cd "$UP" && CARGO_TARGET_DIR="$APPS/$ID/target" cargo test --release -q ${pkg//#/ } --no-fail-fast) >>"$APPS/$ID-upstream-tests.log" 2>&1 || true
  done
  git worktree remove --force "$UP"
  NEW_FAILED=$(comm -23 <(printf '%s\n' "$OURS_FAILED") <(failed "$APPS/$ID-upstream-tests.log"))
  if [ -n "$NEW_FAILED" ]; then
    echo "BLOCKED: tests that pass in $OLD ${LATEST#v} fail in $NEW (see $ID-tests.log):" >&2
    printf '  %s\n' $NEW_FAILED >&2; exit 1
  fi
  echo "tests: only failures ArtCraft's release has too:"; printf '  %s\n' $OURS_FAILED
fi

git add -A
git commit -q -m "Update to $OLD ${LATEST#v} (rebranded as $NEW)"
echo "READY: $NEW ${LATEST#v} on branch koja-sync (brand guard and tests passed)"
