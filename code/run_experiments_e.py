#! /usr/bin/env python3

import timeit
from random import randrange
from main import *


def check_one_schedule(partial_name):
    all_students = read_enrollment("../test_data/haverfordStudentPrefs.txt")
    all_times, all_rooms, all_classes, all_teachers = read_extension_constraints("../test_data/haverfordConstraints_1.txt", "../test_data/haverfordConstraints_2.txt")
    build_time_table(all_times)
    count_prefs(all_classes, all_students)
    assign_core(all_classes)
    schedule = make_schedule_extension(all_classes, all_rooms, all_teachers, all_times)
    for c in schedule:
        c.specs = []
    # read in preregistration data
    all_students = read_extension_prefs(partial_name + "_studentprefs.txt")
    count_prefs(all_classes, all_students)
    choose_student_extension(schedule, all_times)
    count = 0
    for c in schedule:
        count += len(schedule[c][2])
    print("Total enrollment:", count)
    print_schedule_extension(schedule, partial_name + "_schedule.txt", all_times)
    #subprocess.call(["perl", "is_valid.pl", "../test_data/haverfordConstraints.txt", args.infiles[0], args.outfile])

        # for printing intermediate results
    lab_time, lec_time = seperate_time_table(all_times)



"""
make_random_input_e_student.pl
Usage:
make_random_input.pl: <number of rooms> <number of classes> <number of class times> <number of students> <contraint file> <student prefs file>
Note: inputs are <number of rooms> <number of classes> <number of class times> <number of students>, the other two arguments are output file names
"""
num_tests = 2 #change this number to however many experiments you want to run

for i in range(1, num_tests+1):
    # randomely choose an integer within a reasonable(?) range for each value
    ns = randrange(1000, 1200)
    print("Beginning experiment", i)
    print("The sizes are: ns=",  ns)

    # make random input
    subprocess.call(["perl", "make_random_input_e_student.pl", str(ns), "../test_data/"+str(i)+"_studentprefs.txt"])

    # make schedule and time the process
    start_time = timeit.default_timer()
    check_one_schedule("../test_data/"+str(i))
    elapsed = timeit.default_timer() - start_time
    print("\nTime taken:", elapsed)
