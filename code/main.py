#! /usr/bin/env python3

import argparse
import pandas as pd
import subprocess
import functools
import numpy as np
from multiprocessing import Queue
from collections import defaultdict, OrderedDict
from random import shuffle, randrange
from copy import deepcopy
from components import ClassRoom, Student, Course

# set max column width so that the list of enrolled students will not be cut off
pd.set_option('max_colwidth', 100000000000)


major_count = {"ANTH": 23, "ASTR": 7, "PHYS": 39, "BIOL": 70, "CHEM": 57, "ARCH": 6, "CMSC": 45, "COML": 9, "EAST": 9, "ECON": 91, "ENGL": 59, "ARTS": 11, "FREN": 14, "GERM": 7, "HIST": 21, "LING": 15, "MATH": 45, "MUSC": 12, "PHIL": 24, "POLS": 54, "PSYC": 54, "RELG": 9, "SOCL": 7, "SPAN": 36, "EDUC": 18, "ENVS": 19}


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
    try:
        for i in df_raw['Student']:
            classes[int(i)].append(
                int(df_raw.loc[df_raw['Student'] == i, 'Class1']))
            classes[int(i)].append(
                int(df_raw.loc[df_raw['Student'] == i, 'Class2']))
            classes[int(i)].append(
                int(df_raw.loc[df_raw['Student'] == i, 'Class3']))
            classes[int(i)].append(
                int(df_raw.loc[df_raw['Student'] == i, 'Class4']))
    except:
        print("Something's wrong while reading student preferences. Please check input format.")
        print("The student", i, 'went wrong.')
        print("His/hers prefereces are", df_raw.loc[i - 1])
        print("Here's what we've got when tring to get Class 1:")
        print(df_raw.loc[df_raw['Student'] == i, 'Class1'])
        exit(-1)

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
            all_classes (list): a list of Course objects, with attributes `name` (str), `teacher` (int), and `spec`s
            (empty list)
            ntimes (int): the number of non-overlapping time slots
            all_teachers (dict): {teacher_id (int): class_name (int)}
    """
    # read file
    df_raw = pd.read_csv(filename, sep='\t', header=None)

    # record the number of time slots
    ntimes = int(df_raw.loc[0, 2])

    # parse remaining info into two parts, one about rooms, the other about
    # teachers
    r_start = df_raw[df_raw[0] == "Rooms"].index[0]
    t_start = df_raw[df_raw[0] == "Teachers"].index[0]
    df_rooms = df_raw[r_start:t_start - 2]
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
    all_rooms = [ClassRoom(r, int(
        df_rooms.loc[df_rooms['Rooms'] == r, nrooms])) for r in df_rooms['Rooms']]
    all_classes = [Course(int(c), int(df_teachers.loc[df_teachers['Teachers'] == c, nteachers])) for c in
                   df_teachers['Teachers']]
    all_teachers = {}

    # construct teacher list
    for t in range(1, int(nteachers) + 1):
        all_teachers[t] = list(map(int, df_teachers.loc[df_teachers[
                               nteachers] == str(t), 'Teachers'].tolist()))

    return ntimes, all_rooms, all_classes, all_teachers


def read_extension_prefs(filename):
    """ Parse preference lists input
        Args:
            filename (string): name of the input preferece lists
        Returns:
            all_students (list): a list of Student objects with arrtibute `idx` (int) and `classes` (a list of int)
    """
    # read input file
    df = pd.read_csv(filename, skiprows=1, sep="\t", names=['Student', 'Classes'])

    try:
        # put each student's class choices into a list
        student_classes = {}
        for index, row in df.iterrows():
            student_classes[int(row['Student'])] = list(map(int, row['Classes'].split()))
    except:
        print("Index, row went wrong:", index, row)

    # construct a list of Student objects
    all_students = [Student(i, student_classes[i]) for i in student_classes]

    return all_students


def read_extension_constraints(filename_rt, filename_c):
    """ Parse constraints info
        Args:
            filename (string): name of the input file
        Returns:
            all_rooms (list): a list of Classroom objects, with attributes `idx` (str) and `capacity` (int)
            all_classes (list): a list of Course objects, with attributes `name` (str), `teacher` (int), and 
            `specs` (empty list), `dept` (string), `level` (int), core=False
            all_times (dict): {index_time: [start(string), end(string), day(string)]}
            all_teachers (dict): {teacher_id (int): [class_name (int), personal_conflicts (list of ints)]}
    """

    # read file
    df_raw = pd.read_csv(filename_rt, sep='\t', header=None)

    # process last two lines of constraint file 1
    num_classes = int(df_raw[df_raw[0] == "Classes"].iloc[:, 1])
    num_profs = int(df_raw[df_raw[0] == "Teachers"].iloc[:, 1])

    # TODO: Process time
    r_start = df_raw[df_raw[0] == "Rooms"].index[0]
    ntimes = int(df_raw.loc[0, 1])
    df_times = df_raw[1:r_start]
    all_times = {}
    for index, times in df_times.iterrows():
        row = times.to_string(header=False, index=False)
        row = row[row.find("\n"):].strip()
        split_1 = row.find("M") + 1
        start = row[:split_1]
        row = row[split_1 + 1:].strip()
        split_2 = row.find("M")
        end = row[:split_2 + 1]
        days = row[split_2 + 2:]
        all_times[index] = [start, end, days]

    # process room info
    df_rooms = df_raw[r_start + 1:]
    all_rooms = [ClassRoom(row[0], int(row[1]))
                 for index, row in df_rooms.iterrows()]

    # process class info from second file
    df_class_info = pd.read_csv(filename_c, sep='\t', header=None)
    df_class_info.columns = ['Class', 'Teacher', 'Subject', 'Level']
    all_classes = []
    classes_with_labs = []
    all_teachers = defaultdict(list)

    # construct Course objects for lectures
    # record which teacher teach which classes
    # All labs don't have instructor ID, find them and put into a separate list
    try:
        for index, row in df_class_info.iterrows():
            # check for NaN, should be false if teacher is NaN
            if "L" in row['Class']:
                if row['Teacher'] != row['Teacher']:
                    classes_with_labs.append([int(row['Class'][:-1]), 0])
                else:
                    classes_with_labs.append([int(row['Class'][:-1]), int(row['Teacher'])])
            else:
                all_classes.append(Course(int(row['Class']), int(
                    row['Teacher']), None, row['Subject'], int(row['Level'])))
                all_teachers[int(row['Teacher'])].append(int(row['Class']))

    except:
        print("When trying to process the following class, something went wrong:")
        print(row, index)
        exit(-1)

    # add has_lab attribute and append Course ID to lab instructor's class list
    try:
        for i in classes_with_labs:
            c = find_class(all_classes, i[0])
            c.has_lab = [c.teacher if i[1]==0 else i[1]]
            if i[1]!=0:
                all_teachers[i[1]].append(i[0])
    except:
        print("Possibly can't find the lecture section of this lab")
        print(i)

    # add prof personal conflict info
    for t in all_teachers:
        n_unavailable_t = randrange(0, 2)
        all_teachers[t] = [all_teachers[t], [randrange(1, len(all_times)+1) for n in range(n_unavailable_t)]]

    return all_times, all_rooms, all_classes, all_teachers



def count_prefs(C, S):
    """ Initialize the pool of prospective students for all classes
        Args:
            C (list): a list of Course objects - `specs` field will contain Student objects after executing this function
            S (list): a list of Student objects
    """
    for s in S:
        for c_id in s.classes:
            a_class = find_class(C, c_id)
            if a_class and s not in a_class.specs:
                a_class.specs.append(s)
            # print('Adding student ' + str(s.idx) + ' to class ' + str(a_class.name))


def find_class(C, c_id):
    """ find the class object by its id
        Args:
            C (iterable): a list of Course objects or a dictionary with Course objects as keys
            c_id (int): index of the class
        Returns:
            this_class (Course object)
            False if no matching class found
    """
    for this_class in C:
        if this_class.name == c_id:
            return this_class
    return False


def build_time_table(time_list):
    """ Convert format from string to 24h clock in order to detect time conlifcts """

    for time in time_list:
        # parse start time
        split_point_s = time_list[time][0].find(":")
        start_h = int(time_list[time][0][:split_point_s])
        start_min = int(time_list[time][0][split_point_s + 1:split_point_s + 3])
        if time_list[time][0][-2] == "P":
            if start_h != 12:
                start_h += 12
        time_list[time][0] = start_h * 100 + start_min
        # parse end time
        split_point_e = time_list[time][1].find(":")
        end_h = int(time_list[time][1][:split_point_e])
        end_min = int(time_list[time][1][split_point_e + 1:split_point_e + 3])
        if time_list[time][1][-2] == "P":
            if end_h != 12:
                end_h += 12
        time_list[time][1] = end_h * 100 + end_min
        # parse day
        """
        day_list = []
        for char in time_list[time][2] :
            if char != " ":
                day_list.append(char)
        time_list[time][2] = day_list
        """
        time_list[time][2] = time_list[time][2].split()


def time_conflict(t1, t2, time_list):
    """ Return true if two time slots t1 and t2 overlaps, false otherwise """
    # test whether days are the same
    if any(day in time_list[t1][2] for day in time_list[t2][2]):
        # if t1.start >= t2.end, t2.start >= t1.end it must be overlapped
        if (time_list[t1][0] >= time_list[t2][1]) or (time_list[t1][0] >= time_list[t2][1]):
            return False
        elif (time_list[t1][0] < time_list[t2][0] and time_list[t1][1] <= time_list[t2][0]) or \
                (time_list[t2][0] < time_list[t1][0] and time_list[t2][1] <= time_list[t1][0]):
            return False
        else:
            return True
    # if no shared day, must not have time conflict.
    else:
        return False


def seperate_time_table(time_list):
    """ Separate lab times and lecture times """

    temp = deepcopy(time_list)
    lab_time = {}
    class_time = {}
    for time_slot in time_list:
        # if time slot is more than two and half hours, we consider it as a lab session
        if time_list[time_slot][1] - time_list[time_slot][0] > 270:
            lab_time[time_slot] = time_list[time_slot]
        else:
            class_time[time_slot] = time_list[time_slot]
    return lab_time, class_time


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
        dict_schedule["Students"].append(' '.join(
            [str(s.idx) for s in sorted(schedule[course][2], key=lambda t: t.idx)]))

    # construct a DataFrame from dictionary and print schedule
    df_schedule = pd.DataFrame(dict_schedule)
    df_schedule.to_csv(fname, index=False, sep="\t")


def choose_student(schedule):
    """ Choose student from specs to into the student list of corresponding class in dictionary
        Args:
            schedule (dict): {Course: (ClassRoom, time, [Students])}
    """
    for a_class in schedule:
        student_list = a_class.specs
        shuffle(student_list)
        time = schedule[a_class][1]
        count = 0
        for student in student_list:
            if count >= schedule[a_class][0].capacity:
                break
            elif schedule[a_class][1] in student.taken:
                continue
            else:
                schedule.get(a_class)[2].append(student)
                count = count + 1
                student.taken.append(schedule[a_class][1])


def assign_core(class_list):
    core_count = {}
    class_list.sort(key=lambda x: len(x.specs), reverse=True)
    # initialize the core_count dictionary
    for subject in major_count:
        core_count[subject] = [2, 2, 2]
    for course in class_list:
        if course.dept == "WRPR":
            course.is_core = True
        elif course.dept in core_count and course.level > 0 and course.level < 4:
            if core_count[course.dept][course.level - 1] != 0:
                course.is_core = True
                core_count[course.dept][course.level -1] = core_count[course.dept][course.level - 1] - 1


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
    classes = teacherList[teacher]
    already_scheduled = [find_class(result, c) for c in classes if find_class(result, c)]
    return (not any(result[c][1] == timeToSchedule for c in already_scheduled))


def sort_class(course):
    weight = 0
    if course.dept in major_count:
        weight += major_count[course.dept] * 0.5
    weight += 3 * (5 - course.level)
    if course.is_core:
        weight = weight * 2
    return weight

def make_schedule_basic(all_students, all_classes, all_rooms, ntimes, teacherList):
    # sort classes by popularity, sort classrooms by size
    all_classes.sort(key=lambda x: len(x.specs), reverse=True)
    all_rooms.sort(key=lambda x: x.capacity, reverse=True)

    skipped_slots = Queue()
    nrooms = len(all_rooms)
    max_num_classes = min(len(all_classes), len(all_rooms) * ntimes)
    index_class = 0
    index_slot = 0
    result = {}

    # index_slot represents the current slot in the while_loop
    # index_room = index_slot//ntimes
    # index_time = index_slot % ntimes+1
    while index_class < max_num_classes:
        if skipped_slots.empty():
            while not TeacherIsValid(teacherList, result, all_classes[index_class], index_slot % ntimes + 1):
                # class name : location, time, students
                skipped_slots.put(index_slot)
                index_slot = index_slot + 1
            result[all_classes[index_class]] = (all_rooms[index_slot // ntimes], index_slot % ntimes + 1, [])
            index_slot = index_slot + 1
        else:
            copy_skipped_slots = Queue()
            assigned = False  # mark whether current class has been assigned
            while not skipped_slots.empty():
                possible_time = skipped_slots.get_nowait()
                if TeacherIsValid(teacherList, result, all_classes[index_class], possible_time % ntimes + 1):
                    # class name : location, time, Students
                    result[all_classes[index_class]] = (all_rooms[possible_time // ntimes], possible_time % ntimes + 1, [])
                    assigned = True
                    break
                else:
                    copy_skipped_slots.put(possible_time)
            if skipped_slots.empty():
                skipped_slots = copy_skipped_slots
                if not assigned:
                    while not TeacherIsValid(teacherList, result, all_classes[index_class], index_slot % ntimes + 1):
                        # class name : location, time, students
                        skipped_slots.put(index_slot)
                        index_slot = index_slot + 1
                    result[all_classes[index_class]] = (all_rooms[index_slot // ntimes], index_slot % ntimes + 1, [])
                    index_slot = index_slot + 1
            else:                               # recover skipped_slots
                while not copy_skipped_slots.empty():
                    skipped_slots.put(copy_skipped_slots.get())
        index_class = index_class + 1

    return result


# check for room-time conflicts and teacher-time conflicts
def check_time_conflict(t1, timetable, timelist, all_rooms, index):
    for t2 in timetable:
        if time_conflict(t1, t2, timelist):
            return False
    for t3 in  all_rooms[index].taken:
        if time_conflict(t1,t3,timelist):
            return False
    return True


# TODO: don't have all_labs???
def make_lab(lab, timelist, lec_time, lec_queue, lab_queue, teacherList, all_classes, all_rooms, result, index_slots,
             ntimes, all_labs):
    if lab_queue.emtpy():
        while not check_time_conflict(index_slots % ntimes+1, teacherList[all_labs[lab]],
                        timelist, all_rooms, index_slots//ntimes) or index_slots % ntimes+1 in lec_time.keys():
            if index_slots % ntimes+1 in lec_time.keys():
                lec_queue.put(index_slots)
            else:
                lab_queue.put(index_slots)
            index_slots = index_slots + 1
        result[all_classes[lab]+" (lab)"] = (all_rooms[index_slots // ntimes], index_slots % ntimes + 1, [])
        # assign time to room
        all_rooms[index_slots // ntimes].taken.put(index_slots % ntimes + 1)
        index_slots = index_slots + 1
    else:
        copy_lab = Queue()
        assigned = False
        while not lab_queue.empty():
            possible_time = lab_queue.get_nowait()
            if check_time_conflict(possible_time % ntimes+1, teacherList[all_labs[lab]], timelist,
                                   all_rooms, possible_time//ntimes):
                # class name : location, time, Students
                result[all_classes[lab]+" (lab)"] = (all_rooms[possible_time // ntimes], possible_time % ntimes + 1, [])
                all_rooms[possible_time // ntimes].taken.put(possible_time % ntimes + 1)
                assigned = True
                break
            else:
                copy_lab.put(possible_time)
        if lab_queue.emtpy():
            lab_queue = copy_lab
            if not assigned:
                while not check_time_conflict(index_slots % ntimes+1, teacherList[all_labs[lab]],
                                              timelist, all_rooms, index_slots // ntimes) or index_slots % ntimes+1 \
                                              in lec_time.keys():
                    if index_slots % ntimes + 1 in lec_time.keys():
                        lec_queue.put(index_slots)
                    else:
                        lab_queue.put(index_slots)
                    index_slots = index_slots + 1
                result[all_labs[lab]+" (lab)"] = (all_rooms[index_slots // ntimes], index_slots % ntimes + 1, [])
                all_rooms[index_slots // ntimes].taken.put(index_slots % ntimes + 1)
                index_slots = index_slots + 1
            else:                               # recover skipped_slots
                while not copy_lab.empty():
                    lab_queue.put(copy_lab.get())
        return result, index_slots, lec_queue, lab_queue


# TODO: 1. don't have all_labs, course.has_lab = [190] or [] (i.e. classes w/ no labs has an empty list
#           otherwise, it's an instructor ID)
# TODO: 2. Fine arts classes also need to be scheduled during lab time (i.e. if course.dept = "ARTS")

# room now has a tuple to store all taken time,cwhich will help us check room-time comflict
def make_schedule_extension(all_classes, all_rooms, teacherList, time_list, all_labs):
    all_classes.sort(key=lambda x: sort_class(x), reverse=True)
    all_rooms.sort(key=lambda x: x.capacity, reverse=True)
    lec_time, lab_time = seperate_time_table(time_list)
    skipped_slots_lec = Queue()
    skipped_slots_lab = Queue()
    ntimes = len(lec_time)
    max_num_classes = min(len(all_classes), len(all_rooms) * ntimes)
    index_class = 0
    index_slots = 0
    result = {}
    while index_class < max_num_classes:
        if skipped_slots_lec.empty():
            # teacherList[all_classes[index_class].teacher][1] are time that have already been taken
            while not check_time_conflict(index_slots % ntimes + 1, teacherList[all_classes[index_class].teacher][1],
                                          time_list, all_rooms, index_slots // ntimes) or index_slots % ntimes+1\
                                        in lab_time.keys():
                # class name : location, time, students
                if index_slots % ntimes + 1 in lab_time.keys():
                    skipped_slots_lab.put(index_slots)
                else:
                    skipped_slots_lec.put(index_slots)
            result[all_classes[index_class]] = (all_rooms[index_slots // ntimes], index_slots % ntimes + 1, [])
            all_rooms[index_slots // ntimes].taken.put(index_slots % ntimes + 1)
            index_slots = index_slots + 1
            if all_classes[index_class].has_lab:
                result, index_slots, skipped_slots_lec, skipped_slots_lab = \
                    make_lab(index_class, time_list, lec_time, skipped_slots_lec, skipped_slots_lab, teacherList,
                             all_classes, all_rooms, result, index_slots, ntimes, all_labs)
        else:
            copy_skipped_slots = Queue()
            assigned = False  # mark whether current class has been assigned
            while not skipped_slots_lec.empty():
                possible_time = skipped_slots_lec.get_nowait()
                if check_time_conflict(possible_time % ntimes+1, teacherList[all_classes[index_class].teacher][1],
                                       time_list, all_rooms, possible_time//ntimes):
                    # class name : location, time, Students
                    result[all_classes[index_class]] = (all_rooms[possible_time // ntimes], possible_time % ntimes + 1,
                                                        [])
                    all_rooms[possible_time // ntimes].taken.put(possible_time % ntimes + 1)
                    assigned = True
                    if all_classes[index_class].has_lab:
                        result, index_slots, skipped_slots_lec, skipped_slots_lab = \
                        make_lab(index_class, time_list, lec_time, skipped_slots_lec, skipped_slots_lab, teacherList,
                                 all_classes, all_rooms, result, index_slots, ntimes)
                    break
                else:
                    copy_skipped_slots.put(possible_time)
            if skipped_slots_lec.empty():
                skipped_slots_lec = copy_skipped_slots
                if not assigned:
                    while not check_time_conflict(index_slots % ntimes + 1,
                                                  teacherList[all_classes[index_class].teacher][1], time_list,
                                                  all_rooms, index_slots // ntimes) or index_slots % ntimes+1 in \
                                                  lab_time.keys():
                        # class name : location, time, students
                        skipped_slots_lec.put(index_slot)
                        index_slot = index_slot + 1
                    result[all_classes[index_class]] = (all_rooms[index_slot // ntimes], index_slot % ntimes + 1, [])
                    all_rooms[index_slot // ntimes].taken.put(index_slot % ntimes + 1)
                    index_slot = index_slot + 1
                    if all_classes[index_class].has_lab:
                        result, index_slots, skipped_slots_lec, skipped_slots_lab = \
                        make_lab(index_class, time_list, lec_time, skipped_slots_lec, skipped_slots_lab, teacherList,
                                 all_classes, all_rooms, result, index_slots, ntimes)
            else:  # recover skipped_slots
                while not copy_skipped_slots.empty():
                    skipped_slots_lec.put(copy_skipped_slots.get())
        index_class = index_class + 1
    return result




if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Usage: python3 main.py <studentprefs.txt> <basic_constraints.txt> '
                    '(<extension_constriants.txt>) (--extension)')
    parser.add_argument('infiles', type=str, nargs='+',
                        help='Name of input file(s). Assuming the first file contains preference lists, '
                             'the second file contains basic constraints, the third one contains constraints for '
                             'Haverford extension.')
    parser.add_argument('--outfile', '-o', type=str,
                        help='Name of output schedule')
    parser.add_argument('--extension', action='store_true',
                        help="whether allowing haverford extension, by default, run the basic version")
    parser.add_argument('--test', action='store_true',
                        help="print intermediate outputs")
    args = parser.parse_args()

    if not args.extension:
        # read input
        all_students = read_prefs(args.infiles[0])
        ntimes, all_rooms, all_classes, all_teachers = read_constraints(args.infiles[1])
        count_prefs(all_classes, all_students)

        # make schedule for basic version
        schedule = make_schedule_basic(all_students, all_classes, all_rooms, ntimes, all_teachers)
        choose_student(schedule)
        print_schedule(schedule, args.outfile)
        subprocess.call(["perl", "is_valid.pl", args.infiles[1], args.infiles[0], args.outfile])

    else:
        # read input
        all_students = read_extension_prefs(args.infiles[0])
        all_times, all_rooms, all_classes, all_teachers = read_extension_constraints(args.infiles[1], args.infiles[2])
        build_time_table(all_times)
        lab_time, class_time = seperate_time_table(all_times)
        count_prefs(all_classes, all_students)
        assign_core(all_classes)

    if args.test:
        print("\nLab Times:")
        for t in lab_time:
            print(t, lab_time[t])

        print("\nLecture Times:")
        for t in class_time:
            print(t, class_time[t])

        print("\nInput - Room information:")
        for r in all_rooms:
            print("Room location:", r.idx, "Size:", r.capacity)

        print("\nInput - Teacher information:")
        count = 0
        for t in all_teachers:
            print("ID:", t, "Classes:", all_teachers[t][0], "Personal Conflicts:", all_teachers[t][1])
            count += len(all_teachers[t][0])
        print('\n', count, "classes have instructors.")

        print("\nInput - Class information:")
        for c in all_classes:
            print("Class name:", c.name, "Teacher:", c.teacher, "Dept:", c.dept,
                  "Level", c.level, "Is Core?", c.is_core, "Has_Lab?", c.has_lab)
            print("specs:", [s.idx for s in c.specs])

"""
        print("\nOutput - Class schedule with students")
        total_enrollment = 0
        for course in schedule:
            print("Class name:", course.name, "Teacher:", course.teacher, "Time:", schedule[course][1])
            print("Location:", schedule[course][0].idx, "Classroom size:", schedule[course][0].capacity, "Enrollment:",
                  len(schedule[course][2]))
            total_enrollment += len(schedule[course][2])
            print("Students:", [s.idx for s in schedule[course][2]], "\n")

        print("Total Enrollment:", total_enrollment)
"""
