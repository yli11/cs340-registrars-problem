#!/usr/bin/perl -w
use strict;
use POSIX;

my $maxroomcapacity = 100;
my $minroomcapacity = 10;
#we only leave the part generate students
if (!$ARGV[0] || !$ARGV[1]) {

	print "$0 takes schedule bounds and randomly creates two files for input to a schedule maker.\n";
	print "The first contains all the class-specific constrains, and the second the student class preferences.\n";
	print "Usage:\n";
	print "$0: <number of students> <student prefs file>\n";
	exit 1;
}


#my $numrooms = $ARGV[0];
my $numclasses = 365;
#my $numslots = $ARGV[2];


my $numstudents = $ARGV[0];
#my $numteachers = $numclasses / 2;
#my $constraintfile = $ARGV[4];
my $prefsfile = $ARGV[1];


#for naming the preference value list file
if ($prefsfile) {
	$prefsfile =~ /^(.+)$/;
	$prefsfile = $1;
}

my $classesperstudentmax = 6;
my $classesperstudentmin = 2;


open (PREFS, ">> $prefsfile") || die "Can't open file: $prefsfile\n";

print PREFS "Students\t$numstudents\n";
foreach my $student ((1..$numstudents)) {
    my @chosenclasses = ();
    my $newval =  rand();  # gives a random value between 0 and 1
    my $realclassnumber =  floor($newval * ($classesperstudentmax - $classesperstudentmin) + $classesperstudentmin);
	for my $i ((1..$realclassnumber)) {
		my $wantclass = ceil(rand() * $numclasses);
		while (inarray($wantclass, \@chosenclasses)) {
			$wantclass = ceil(rand() * $numclasses);
		}
		push @chosenclasses, $wantclass;
	}
	print PREFS "$student\t@chosenclasses\n";
}


sub inarray {
	my $val = $_[0];
	my $arr = $_[1];
	foreach my $i ((0..$#{$arr})) {
		if ($arr->[$i] == $val) {
			return 1;
		}
	}
	return 0;
}

exit 0;
