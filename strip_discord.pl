# Removes ArtCraft's Discord buttons, menu entries and links from Rust code (Koja apps have no
# Discord). Whole-file mode:  perl -0777 -pi strip_discord.pl FILES
# It knows the shapes the Craft apps use; anything it misses, brand-guard.sh reports.
use strict;
use warnings;

my $B = qr/(\{(?:[^{}]++|(?-1))*\})/;   # a balanced { … } block

# `if … show_discord { … }`: the title-bar pill. Off by default too, in case a use survives.
s/\n[ \t]*if [^\n{]*show_discord\s*$B//g;
s/\bshow_discord: true\b/show_discord: false/g;
# A settings checkbox for the pill.
s/\n[^\n]*show_discord[^\n]*\);[ \t]*(?=\n)//g;
# `if id == "discord" { … } else { BODY }` → BODY
s/if\s+\w+\s*==\s*"discord"\s*$B\s*else\s*$B/my $b = $2; $b =~ s#\A\{\s*##; $b =~ s#\s*\}\z##; $b/ge;
# Menu entries as (label, id) pairs and keytips c("…", "ui.discord").
s/,\s*\("[^"]*[Dd]iscord[^"]*",\s*"[^"]*"\)//g;
s/\(\s*"[^"]*[Dd]iscord[^"]*",\s*"[^"]*"\),\s*//g;
s/\b[a-z]\("[^"]*",\s*"ui\.discord"\),\s*//g;
# The command itself: its match arm, `| "ui.discord"` alternatives, list entries.
s/\n[ \t]*"ui\.discord"\s*=>\s*$B,?//g;
s/\n[ \t]*\|\s*"ui\.discord"//g;
s/"ui\.discord",\s*//g;
s/,\s*"ui\.discord"//g;
# Remaining one-line statements that open Discord: a ribbon button, a hyperlink.
s/\n[^\n]*(?:"ui\.discord"|discord\.gg)[^\n]*;[ \t]*(?=\n)//g;
