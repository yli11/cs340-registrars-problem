#! /usr/bin/env python3

import timeit
from random import randrange
from main import *


def check_one_schedule(partial_name):
    all_students = read_prefs(partial_name + "_studentprefs.txt")
    ntimes, all_rooms, all_classes, all_teachers = read_constraints(partial_name + "_constraints.txt")
    count_prefs(all_classes, all_students)
    schedule = make_schedule(all_students, all_classes, all_rooms, ntimes, all_teachers)
    choose_student(schedule)
    print_schedule(schedule, partial_name + "_schedule.txt")
    subprocess.call(["perl", "is_valid.pl", partial_name + "_constraints.txt", partial_name + "_studentprefs.txt", partial_name + "_schedule.txt"])


"""
make_random_input.pl
Usage:
make_random_input.pl: <number of rooms> <number of classes> <number of class times> <number of students> <contraint file> <student prefs file>
Note: inputs are <number of rooms> <number of classes> <number of class times> <number of students>, the other two arguments are output file names
"""
num_tests = 2 #change this number to however many experiments you want to run

for i in range(1, num_tests+1):
    # randomely choose an integer within a reasonable(?) range for each value
    nr = randrange(5, 200)
    nc = randrange(4, 500, 2)
    nt = randrange(20, 100)
    ns = randrange(50, 5000)
    print("Beginning experiment", i)
    print("The sizes are: nr, nc, nt, ns=", nr, nc, nt, ns)

    # make random input
    subprocess.call(["perl", "make_random_input.pl", str(nr), str(nc), str(nt), str(ns), "../test_data/"+str(i)+"_constraints.txt", "../test_data/"+str(i)+"_studentprefs.txt"])

    # make schedule and time the process
    start_time = timeit.default_timer()
    check_one_schedule("../test_data/"+str(i))
    elapsed = timeit.default_timer() - start_time
    print("\nTime taken:", elapsed)