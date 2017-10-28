#! /usr/bin/env python3

import argparse
import pandas as pd
import subprocess
import functools
from multiprocessing import Queue
from collections import defaultdict, OrderedDict
from random import shuffle
from components import ClassRoom, Student, Course

# set max column width so that the list of enrolled students will not be cut off
pd.set_option('max_colwidth', 100000000000)


def read_prefs(filename):
    """ Parse preference lists input
        Args:
            filename (string): name of the input preferece lists
        Returns:
            all_students (list): a list of Student objects with arrtibute `idx` (int) and `classes` (a list of int)
    """
    # read input file
    df_raw = pd.read_csv(filename, skiprows=1, delim_whitespace=True,
                         names=['Student', 'Class1', 'Class2', 'Class3', 'Class4'])

    # put each student's class choices into a list
    classes = defaultdict(list)
    for i in df_raw['Student']:
        classes[i].append(int(df_raw.loc[df_raw['Student'] == i, 'Class1']))
        classes[i].append(int(df_raw.loc[df_raw['Student'] == i, 'Class2']))
        classes[i].append(int(df_raw.loc[df_raw['Student'] == i, 'Class3']))
        classes[i].append(int(df_raw.loc[df_raw['Student'] == i, 'Class4']))

    # construct a new DataFrame and return a list
    df_students = pd.DataFrame(list(classes.items()), columns=['Student', 'Classes'])
    all_students = [Student(i, df_students.loc[i - 1, 'Classes']) for i in df_students['Student']]

    return all_students


def read_constraints(filename):
    """ Parse constraints info
        Args:
            filename (string): name of the input file
        Returns:
            all_rooms (list): a list of Classroom objects, with attributes `idx` (str) and `capacity` (int)
            all_classes (list): a list of Course objects, with attributes `name` (str), `teacher` (int), and `spec`s (empty list)
            ntimes (int): the number of non-overlapping time slots
    """
    # read file
    df_raw = pd.read_csv(filename, delim_whitespace=True, header=None)

    # record the number of time slots
    ntimes = int(df_raw.loc[0, 2])

    # parse remaining info into two parts, one about rooms, the other about teachers
    r_start = df_raw[df_raw[0] == "Rooms"].index[0]
    t_start = df_raw[df_raw[0] == "Teachers"].index[0]
    df_rooms = df_raw.loc[r_start:t_start - 2]
    new_header = df_rooms.iloc[0]
    nrooms = new_header[1]
    df_rooms = df_rooms[1:]
    df_rooms.columns = new_header
    df_teachers = df_raw.loc[t_start:]
    new_header = df_teachers.iloc[0]
    nteachers = new_header[1]
    df_teachers = df_teachers[1:]
    df_teachers.columns = new_header

    # construct ClassRoom and Course objects
    all_rooms = [ClassRoom(r, int(df_rooms.loc[df_rooms['Rooms'] == r, nrooms])) for r in df_rooms['Rooms']]
    all_classes = [Course(int(c), int(df_teachers.loc[df_teachers['Teachers'] == c, nteachers])) for c in
                   df_teachers['Teachers']]
    all_teachers = {}

    for t in range(1, int(nteachers) + 1):
        all_teachers[t] = list(map(int, df_teachers.loc[df_teachers[nteachers] == str(t), 'Teachers'].tolist()))

    return ntimes, all_rooms, all_classes, all_teachers


def count_prefs(C, S):
    """ Initialize the pool of prospective students for all classes
        Args:
            C (list): a list of Course objects - `specs` field will contain Student objects after executing this function
            S (list): a list of Student objects
    """
    for s in S:
        for c_id in s.classes:
            a_class = find_class(C, c_id)
            a_class.specs.append(s)
            # print('Adding student ' + str(s.idx) + ' to class ' + str(a_class.name))


def find_class(C, c_id):
    """ find the class object by its id
        Args:
            C (list): a list of Course objects
        Returns:
            this_class (Course object)
            False if no matching class found
    """
    for this_class in C:
        if this_class.name == c_id:
            return this_class
    return False


def print_schedule(schedule, fname):
    """ Output schedule using pandas
        Args:
            schedule (dict): {Course: (ClassRoom, time, [Students])}
    """
    # create a dictionary for pandas to print
    schedule = OrderedDict(sorted(schedule.items(), key=lambda t: t[0].name))
    dict_schedule = OrderedDict()
    keys = ["Course", "Room", "Teacher", "Time", "Students"]
    for i in keys:
        dict_schedule.setdefault(i, [])

    for course in schedule:
        dict_schedule["Course"].append(str(course.name))
        dict_schedule["Room"].append(schedule[course][0].idx)
        dict_schedule["Teacher"].append(str(course.teacher))
        dict_schedule["Time"].append(str(schedule[course][1]))
        dict_schedule["Students"].append(' '.join([str(s.idx) for s in sorted(schedule[course][2], key=lambda t: t.idx)]))

    # construct a DataFrame from dictionary and print schedule
    df_schedule = pd.DataFrame(dict_schedule)
    df_schedule.to_csv(fname, index=False, sep="\t")


def choose_student(schedule):
    """
    Choose student from specs to into the student list of corresponding class in dictionary
    """
    for a_class in schedule:
        student_list = a_class.specs
        shuffle(student_list)
        time = schedule[a_class][1]
        count = 0
        for student in student_list:
            if count >= schedule[a_class][0].capacity:
                break
            elif any(otherclass in schedule and schedule[otherclass][1] == time for otherclass in student.classes):
                continue
            else:
                schedule.get(a_class)[2].append(student)
                count = count + 1
                student.classes.append(a_class)


def TeacherIsValid(teacherList, result, classToSchedule, timeToSchedule):
    """
    Test whether the class we are scheduling has conflict respect to teachers (whether they're taught by the same teacher and both classes are at the same time slot)
    Args:
        teacherList: A dictionary where key is teacher value is a list of classes he or she is teaching
        result: The schedule we have so far. Key is class, value is a tuple -> (location, time, students)
        classToSchedule: The class we're currently scheduling.
        timeToSchedule: The time we're considering.
    """
    teacher = classToSchedule.teacher
    classes = teacherList.get(teacher)
    if (not classes[0] in result) and (not classes[1] in result):
        return True
    elif classes[0] in result:
        if result.get(classes[0])[1] == timeToSchedule:
            return False
        else:
            return True
    else:
        if result.get(classes[1])[1] == timeToSchedule:
            return False
        else:
            return True


def make_schedule(all_students, all_classes, all_rooms, ntimes, teacherList):
    # sort classes by popularity, sort classrooms by size
    all_classes.sort(key=lambda x: len(x.specs), reverse=True)
    all_rooms.sort(key=lambda x: x.capacity, reverse=True)

    skipped_slots = Queue()
    num_rooms = len(all_rooms) * ntimes
    max_num_classes = min(len(all_classes), num_rooms)
    index_class = 0
    index_room = 0
    index_time = 0
    result = {}
    while index_class < max_num_classes:
        if skipped_slots.empty():
            while not TeacherIsValid(teacherList, result, all_classes[index_class], index_time):
                # class name : location, time, students
                skipped_slots.put(index_time)
                index_time = (index_time + 1) % ntimes
            result[all_classes[index_class]] = (all_rooms[index_room//ntimes], index_time, [])
            index_time = (index_time + 1) % ntimes
            index_room = index_room + 1
            index_class = index_class + 1
        else:
            copy_skipped_slots = Queue()
            assigned = False  # mark whether current class has been assigned
            while not skipped_slots.empty():
                possible_time = skipped_slots.get_nowait()
                if TeacherIsValid(teacherList, result, all_classes[index_class], possible_time):
                        # class name : location, time, students
                    result[all_classes[index_class]] = (all_rooms[index_room//ntimes], possible_time, [])
                    index_room = index_room + 1
                    index_class = index_class + 1
                    assigned = True
                else:
                    copy_skipped_slots.put(possible_time)
            if skipped_slots.empty():
                skipped_slots = copy_skipped_slots
                if not assigned:
                    while not TeacherIsValid(teacherList, result, all_classes[index_class], index_time):
                        # class name : location, time, students
                        skipped_slots.put(index_time)
                        index_time = (index_time + 1) % ntimes
                    result[all_classes[index_class]] = (all_rooms[index_room//ntimes], index_time, [])
                    index_time = (index_time + 1) % ntimes
                    index_room = index_room + 1
                    index_class = index_class + 1
            else:                               # recover skipped_slots
                while not copy_skipped_slots.empty():
                    skipped_slots.put(copy_skipped_slots.get())
    return result



if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Usage: python3 main.py <studentprefs.txt> <basic_constraints.txt> '
                    '(<extension_constriants.txt>) (--extension)')
    parser.add_argument('infiles', type=str, nargs='+',
                        help='Name of input file(s). Assuming the first file contains preference lists, '
                             'the second file contains basic constraints, the third one contains constraints for '
                             'Haverford extension.')
    parser.add_argument('--outfile', '-o', type=str, help='Name of output schedule')
    parser.add_argument('--extension', action='store_true',
                        help="whether allowing haverford extension, by default, run the basic version")
    parser.add_argument('--test', action='store_true',
                        help="print intermediate outputs")
    args = parser.parse_args()

    # read input
    all_students = read_prefs(args.infiles[0])
    ntimes, all_rooms, all_classes, all_teachers = read_constraints(args.infiles[1])
    count_prefs(all_classes, all_students)

    if not args.extension:
        # make schedule for basic version
        schedule = make_schedule(all_students, all_classes, all_rooms, ntimes, all_teachers)
        choose_student(schedule)
        print_schedule(schedule, args.outfile)
        subprocess.call(["perl", "is_valid.pl", args.infiles[1], args.infiles[0], args.outfile])



    if args.test:
        print("\nInput - Time Information:")
        print("# of time slots:", ntimes)

        print("\nInput - Room information:")
        for r in all_rooms:
            print("Room location:", r.idx, "Size:", r.capacity)

        print("\nInput - Student Preferences")
        for s in all_students:
            print("ID:", s.idx, "Preferences:", [c for c in s.classes])

        print("\nInput - Class information:")
        for c in all_classes:
            print("Class name:", c.name, "Teacher:", c.teacher, "specs:", [s.idx for s in c.specs])

        print("\nOutput - Class schedule with students")
        total_enrollment = 0
        for course in schedule:
            print("Class name:", course.name, "Teacher:", course.teacher, "Time:", schedule[course][1])
            print("Location:", schedule[course][0].idx, "Classroom size:", schedule[course][0].capacity, "Enrollment:",
                  len(schedule[course][2]))
            total_enrollment += len(schedule[course][2])
            print("Students:", [s.idx for s in schedule[course][2]], "\n")

        print("Total Enrollment:", total_enrollment)
