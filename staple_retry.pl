# Wraps `xcrun stapler staple|validate` in package.sh with retries: Apple's ticket service drops
# connections now and then (stapler Error 68), mostly right after notarization.
#   perl -0777 -pi staple_retry.pl packaging/macos/package.sh
use strict; use warnings;
unless (/koja_retry\(\)/) {
    s{\A((?:#![^\n]*\n)(?:#[^\n]*\n)*)}{$1\n# Retries a command (Apple's stapler drops connections now and then).\nkoja_retry() { local i; for i in 1 2 3 4 5 6; do "\$@" && return 0; echo "retry \$i/6: \$*" >&2; sleep \$((i * 20)); done; return 1; }\n};
}
s{^(\s*)(?:retry\s+)?xcrun stapler (staple|validate) }{$1koja_retry xcrun stapler $2 }mg;
