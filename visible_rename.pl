# Rebrands customer-visible text from ArtCraft's Craft apps to Kojalytics' Koja apps.
#   perl -pi visible_rename.pl FILES        whole lines (installer files, translation catalogs)
#   KOJA_CODE=1 perl -pi visible_rename.pl  only inside "…" string literals (Rust code)
# The original copyright lines stay as the license requires.
use strict;
use warnings;

sub rb {
    my $s = shift;
    $s =~ s/ai\.storyteller\./com.kojalytics./g;
    $s =~ s/\bai\.storyteller\b/com.kojalytics/g;
    $s =~ s/getartcraft\.com/kojalytics.com/g;
    $s =~ s{https://discord\.gg/artcraft}{$ENV{KOJALYTICS_DISCORD}}g if $ENV{KOJALYTICS_DISCORD};
    $s =~ s/storytold(?!\/craft-fonts)/Kojalytics/g;   # craft-fonts stays ArtCraft's (open fonts, build input)
    # "the ArtCraft team" is the attribution the license requires: it keeps its name.
    $s =~ s/ArtCraft(?! [Tt]eam)/Kojalytics/g;
    $s =~ s/Craft App Suite/Koja App Suite/g;
    $s =~ s/\b(Photo|Vector|Film|Light|Pdf|Effect|Design|Word|Deck|Grid|CAD|Sound|Fig)Craft(?=\b|[a-zäöüõ])/$1Koja/g;
    # The license requires naming the original: "Based on WordCraft by the ArtCraft team".
    $s =~ s/Based on (\w+)Koja by the (?:Kojalytics|ArtCraft) team/Based on $1Craft by the ArtCraft team/g;
    return $s;
}

if ($ENV{KOJA_CODE}) {
    s/("(?:[^"\\]|\\.)*")/rb($1)/ge;
} else {
    $_ = rb($_);
}
if (/Copyright|©/ && /Kojalytics Team/) {
    s/Kojalytics Team/ArtCraft Team/g;
    s/\b(\w+)Koja contributors/$1Craft contributors/g;
}
