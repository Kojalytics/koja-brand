#!/usr/bin/env bash
# VectorKoja: mount the finished DMG for its signature check under the temp dir, not under the repo
# (macOS refuses mount points on external drives that ignore ownership, e.g. the build drive).
set -euo pipefail
perl -pi -e 's{^MOUNT="\$WORK/dmg-check"$}{MOUNT="\$(mktemp -d)/dmg-check"   # internal disk: no mount points on external drives}' packaging/macos/package.sh
