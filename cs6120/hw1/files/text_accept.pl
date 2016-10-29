#!/usr/bin/perl

my $s = 0;

while (<>) {
    next if /^\s*$/;
    $_ = lc $_;
    s/\s+/ /g;
    s/[^a-z ]//g;

    foreach my $c ( split // ) {
	$c = '<space>' if $c eq ' ';
	print join("\t", $s++, $s, $c), "\n";
    }
}

print $s, "\n";

