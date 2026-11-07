#!/usr/bin/env bash
# WordKoja: mount the finished DMG for its signature check under the temp dir, not under the repo
# (macOS refuses mount points on external drives that ignore ownership, e.g. the build drive).
set -euo pipefail
perl -pi -e 's{local dmg="\$1" mount="\$WORK/dmg-check" copy="\$WORK/dmg-check-copy" rc=0}{local dmg="\$1" mount copy rc=0\n  # On the internal disk: macOS refuses mount points on external drives without ownership.\n  mount="\$(mktemp -d)/dmg-check"; copy="\$(mktemp -d)/dmg-check-copy"}' packaging/macos/package.sh
