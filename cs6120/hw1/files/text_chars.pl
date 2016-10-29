#!/usr/bin/perl

$/ = '';

while (<>) {
    next if /^\s*$/;
    chomp;

    $_ = lc $_;
    s/\s+/\#/g;
    s/[^a-z\# ]//g;

    my $out = join(" ", split(//, $_));
    $out =~ s/\#/<space>/g;
    print $out, "\n";
}
