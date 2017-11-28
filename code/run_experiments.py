#! /usr/bin/env python3

import argparse
import timeit
from main import *


def check_one_schedule(partial_name):
    subprocess.call(["python3", "main.py", partial_name + "_basic_studentprefs.txt", partial_name + "_basic_constraints.txt", '-o', partial_name + "_basic_schedule.txt"])

def check_one_schedule_extension(partial_name):
    subprocess.call(['python3', 'main.py', 'S14Enrollment.txt', 'haverfordConstraints_1.txt', 'haverfordConstraints_2.txt', partial_name+'_extension_studentprefs.txt', '--extension', '-o', partial_name+'_extension_schedule.txt'])


"""
make_random_input.pl
Usage:
make_random_input.pl: <number of rooms> <number of classes> <number of class times> <number of students> <contraint file> <student prefs file>
Note: inputs are <number of rooms> <number of classes> <number of class times> <number of students>, the other two arguments are output file names
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='For basic version, enter: <#rooms> <#classes> <#times> <#students> -n <#experiments>. For Haverford extension, enter ')
    parser.add_argument('insize', type=str, nargs='+',
                        help='input sizes. For basic version, enter <nr> <nc> <nt> <ns>. For extension, enter student number only.')
    parser.add_argument('--nexp', '-n', type=int,
                        help='The number of experiment you want to run. Will use the same input size and generate multiple sets of random iputs.')
    parser.add_argument('--extension','-e', action='store_true',
                        help="whether allowing haverford extension, by default, run the basic version")
    args = parser.parse_args()
    
    num_tests = args.nexp

    if not args.extension:
        if len(args.insize) != 4:
            print("Wrong input sizes. <nr> <nc> <nt> <ns>")
            exit(-1)

        nr = args.insize[0]
        nc = args.insize[1] 
        nt = args.insize[2]
        ns = args.insize[3]
        print("\nThe input sizes are: nr, nc, nt, ns=", nr, nc, nt, ns)

        for i in range(1, num_tests+1):
            print("Beginning experiment", i)
            # make random input
            subprocess.call(["perl", "make_random_input.pl", str(nr), str(nc), str(nt), str(ns), str(i)+"_basic_constraints.txt", str(i)+"_basic_studentprefs.txt"])

            # make schedule and time the process
            check_one_schedule(str(i))
    else:
        if len(args.insize) != 1:
            print("Wrong input sizes. Only <ns> is required.")
            exit(-1)

        ns = args.insize[0]
        print("\nStudent size is", ns)

        for i in range(1, num_tests+1):
            # randomely choose an integer within a reasonable(?) range for each value
            subprocess.call(["perl", "make_random_input_e_student.pl", str(ns), str(i)+"_extension_studentprefs.txt"])
            print("Beginning experiment", i)
            check_one_schedule_extension(str(i))