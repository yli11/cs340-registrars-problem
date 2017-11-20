#! /usr/bin/env python3

import argparse
import pandas as pd
import subprocess
import functools
import timeit
import traceback
#from multiprocessing import Queue
from collections import defaultdict, OrderedDict
from random import shuffle, randrange
from copy import deepcopy
from components import ClassRoom, Student, Course
from call_is_valid import *

# set max column width so that the list of enrolled students will not be cut off
pd.set_option('max_colwidth', 1000000000000000)


major_count = {"ANTH": 23, "ASTR": 7, "PHYS": 39, "BIOL": 70, "CHEM": 57, "ARCH": 6, "CMSC": 45, "COML": 9, "EAST": 9, "ECON": 91, "ENGL": 59, "ARTS": 11, "FREN": 14, "GERM": 7, "HIST": 21, "LING": 15, "MATH": 45, "MUSC": 12, "PHIL": 24, "POLS": 54, "PSYC": 54, "RELG": 9, "SOCL": 7, "SPAN": 36, "EDUC": 18, "ENVS": 19}

""" Input/Output Processing """

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
        traceback.print_exc()
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
    ntimes = int(df_raw.loc[0, 1])

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
        all_teachers[t] = list(map(int, df_teachers.loc[df_teachers[nteachers] == t, 'Teachers'].tolist()))

    return ntimes, all_rooms, all_classes, all_teachers


def read_enrollment(filename):
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
        traceback.print_exc()
        print("Index, row went wrong:", index, row)
        exit(-1)

    # construct a list of Student objects
    all_students = [Student(i, student_classes[i]) for i in student_classes]

    return all_students

def map_prefs(i, all_classes):
    """ Used for map, need all_classes to be global"""
    return all_classes[int(i)-1].name


def read_extension_prefs(filename, all_classes):
    """ Parse preference lists input
        Args:
            filename (string): name of the input preferece lists
        Returns:
            all_students (list): a list of Student objects with arrtibute `idx` (int) and `classes` (a list of int)
    """
    # read input file
    df = pd.read_csv(filename, sep="\t", names=['Student', 'Classes'])[1:]

    try:
        # put each student's class choices into a list
        student_classes = {}
        for index, row in df.iterrows():
            student_classes[int(row['Student'])] = [map_prefs(i, all_classes) for i in row['Classes'].split()]
    except:
        print("When reading extension prefs, something went wrong:")
        traceback.print_exc()
        print("The student's row:", index, row)
        exit(1)

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
    teacher_line =  df_raw[df_raw[0] == "Teachers"].index[0]
    num_classes = int(df_raw[df_raw[0] == "Classes"].iloc[:, 1])
    num_profs = int(df_raw[df_raw[0] == "Teachers"].iloc[:, 1])

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
    df_rooms = df_raw[r_start + 1:teacher_line]
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
        traceback.print_exc()
        print(row, index)
        exit(-1)

    # add has_lab attribute and append Course ID to lab instructor's class list
    try:
        for i in classes_with_labs:
            c = find_class(all_classes, i[0])
            c.has_lab = c.teacher if i[1]==0 else i[1]
            if i[1]!=0:
                all_teachers[i[1]].append(i[0])
    except:
        traceback.print_exc()
        print("Possibly can't find the lecture section of this lab")
        print(i)
        exit(-1)

    # add prof personal conflict info
    for t in all_teachers:
        n_unavailable_t = randrange(0, 5)
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


def print_schedule(schedule, fname):
    """ Output schedule using pandas
        Args:
            schedule (dict): {Course: (ClassRoom, time, [Students])}
    """
    # create a dictionary for pandas to print
    schedule = OrderedDict(sorted(schedule.items(), key=lambda t:t[0].name))
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


def print_schedule_extension(schedule, fname, all_times):
    """ Output schedule using pandas
        Args:
            schedule (dict): {Course: (ClassRoom, time, [Students])}
    """
    # create a dictionary for pandas to print
    schedule = OrderedDict(sorted(schedule.items(), key=lambda t:t[0].name))

    f = open(fname, 'w')
    f.write("Course\tRoom\tTeacher\tTime\tStudents\n")
    for course in schedule:
        f.write(str(course.name))
        f.write("\t")
        f.write(schedule[course][0].idx)
        f.write("\t")
        f.write(str(course.teacher))
        f.write("\t")
        f.write(repr_time(all_times[schedule[course][1]]))
        f.write("\t")
        f.write(' '.join([str(s.idx) for s in sorted(schedule[course][2], key=lambda t: t.idx)]))
        f.write("\n")
    f.close()


def repr_time(t):
    """ convert time back to a printable form 
        Args:
            t (list): [start (int), end (int), days (list)] e.g.[1000, 1100, ['T', 'H']]
        Returns:
            str_t (string): "10:00 AM  11:00 AM TH"
    """
    str_t = ""
    for i in range(2):
        if t[i] >= 1200:
            if t[i] // 100 == 12:
                str_t += str(t[i] // 100)+ ":" + str(t[i] % 100).zfill(2) + " PM"
            else:
                str_t += str(t[i] // 100 - 12)+ ":" + str(t[i] % 100).zfill(2) + " PM"
        else:
            str_t += str(t[i] // 100)+ ":" + str(t[i] % 100).zfill(2) + " AM"
        str_t += " "
    str_t += "".join(t[2])
    return str_t


""" Helper Functions """

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


def seperate_time_table(time_list):
    """ Separate lab times and lecture times """
    lab_time = {}
    class_time = {}
    for time_slot in time_list:
        # if time slot is more than two and half hours, we consider it as a lab session
        if time_list[time_slot][1] - time_list[time_slot][0] > 270:
            lab_time[time_slot] = time_list[time_slot]
        else:
            class_time[time_slot] = time_list[time_slot]
    return lab_time, class_time


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
            elif time in student.taken:
                continue
            else:
                schedule.get(a_class)[2].append(student)
                count = count + 1
                student.taken.append(time)


def find_lab(schedule,course):
    """ find whether a course has a lab. If so return a tuple contains this class and lab, otherwise, return an
        empty tuple:
        Args:
             schedule (dict): {Course: (ClassRoom, time, [Students])}
             course: Course 
    """
    for lab in schedule:
        if lab.name == course.name and lab != course:
            return lab
                
def check_student_conflict(t1,student,time_list):
    """
       check whether a student has conflicted class in his schedule with input time
    """
    for t2 in student.taken:
        if time_conflict(t1,t2,time_list):
            return True
    return False
            
                
def choose_student_extension(schedule,time_list):
    """ Choose student from specs to into the student list of corresponding class in dictionary
        Args:
            schedule (dict): {Course: (ClassRoom, time, [Students])}
        If the course has a lab, lab will share the same name of that course and stored time in it.
    """
    for a_class in schedule:
        student_list = a_class.specs
        shuffle(student_list)
        time_class = schedule[a_class][1]
        count = 0
        #if a_class has lab, its has_lab attribute will be more than 0, and we will find lab
        if a_class.has_lab > 0 and find_lab(schedule,a_class):
            lab = find_lab(schedule,a_class)
            time_lab = schedule[lab][1]
            for student in student_list:
                 if count >= schedule[a_class][0].capacity:
                     break
                 elif check_student_conflict(time_class, student, time_list):
                     continue
                 elif check_student_conflict(time_lab, student, time_list):
                     continue
                 else:
                     schedule[a_class][2].append(student)
                     schedule[lab][2].append(student)
                     count = count + 1
                     student.taken.append(schedule[a_class][1])
                     student.taken.append(schedule[lab][1])
        elif a_class.has_lab == 0:
            for student in student_list:
                 if count >= schedule[a_class][0].capacity:
                     break
                 elif check_student_conflict(time_class, student, time_list):
                     continue
                 else:
                     schedule[a_class][2].append(student)
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
    weight = len(course.specs) 
    if course.dept in major_count:
        weight += major_count[course.dept] * 0.5
    weight += 5 * (5 - course.level)
    if course.is_core:
        weight += 50
    return weight


def time_conflict(t1, t2, time_list):
    """ Return true if two time slots t1 and t2 overlaps, false otherwise """
    # test whether days are the same
    if any(day in time_list[t1][2] for day in time_list[t2][2]):
        #if days overlap, sort by start time
        sorted_by_start = sorted([time_list[t1], time_list[t2]], key=lambda x: x[0])
        # if start time of the second is earlier than the end of the first one, there's overlap
        if sorted_by_start[1][0] <= sorted_by_start[0][1]:
            return True
    return False


def check_time_conflict(t1, teacher_unavailable, timelist, all_rooms, index_r):
    """ check for room-time conflicts and teacher-time conflicts """
    for t2 in teacher_unavailable:
        if time_conflict(t1, t2, timelist):
            return True
    for t3 in all_rooms[index_r].taken:
        if time_conflict(t1, t3, timelist):
            return True
    return False


""" Actual Scheduling Algorithm """    

def make_schedule_basic(all_students, all_classes, all_rooms, ntimes, teacherList):
    # sort classes by popularity, sort classrooms by size
    all_classes.sort(key=lambda x: len(x.specs), reverse=True)
    all_rooms.sort(key=lambda x: x.capacity, reverse=True)

    skipped_slots = []
    nslots = len(all_rooms) * ntimes
    index_class = 0
    index_slot = 0
    result = {}

    # index_slot represents the current slot in the while_loop
    # index_room = index_slot//ntimes
    # index_time = index_slot % ntimes+1
    while index_class < len(all_classes) and index_slot < nslots:
        if len(skipped_slots) == 0:
            while not TeacherIsValid(teacherList, result, all_classes[index_class], index_slot % ntimes + 1) and index_slot < nslots:
                # class name : location, time, students
                skipped_slots.append(index_slot)
                index_slot = index_slot + 1
            if index_slot < nslots: #else will actually break out of while loop
                result[all_classes[index_class]] = (all_rooms[index_slot // ntimes], index_slot % ntimes + 1, [])
                index_slot = index_slot + 1
        else:
            copy_skipped_slots = []
            assigned = False  # mark whether current class has been assigned
            while len(skipped_slots) > 0:
                possible_time = skipped_slots.pop(0)
                if TeacherIsValid(teacherList, result, all_classes[index_class], possible_time % ntimes + 1):
                    # class name : location, time, Students
                    result[all_classes[index_class]] = (all_rooms[possible_time // ntimes], possible_time % ntimes + 1, [])
                    assigned = True
                    break
                else:
                    copy_skipped_slots = [possible_time] + copy_skipped_slots                 
            if len(skipped_slots) == 0:
                if not assigned:
                    while not TeacherIsValid(teacherList, result, all_classes[index_class], index_slot % ntimes + 1) and index_slot < nslots:
                        # class name : location, time, students
                        skipped_slots.append(index_slot)                        
                        index_slot = index_slot + 1
                    if index_slot < nslots: #else will actually break out of while loop
                        result[all_classes[index_class]] = (all_rooms[index_slot // ntimes], index_slot % ntimes + 1, [])
                        index_slot += 1
            # recover skipped_slots
            skipped_slots += copy_skipped_slots

        index_class = index_class + 1

    # try to fully utilize skipped slots
    while index_class < len(all_classes):
        skipped_copy = []
        while len(skipped_slots) > 0:
            possible_time = skipped_slots.pop(0)
            if TeacherIsValid(teacherList, result, all_classes[index_class], possible_time % ntimes + 1):
                result[all_classes[index_class]] = (all_rooms[possible_time // ntimes], possible_time % ntimes + 1, [])
                break
            else:
                skipped_copy.append(possible_time)
        index_class += 1
        skipped_slots = skipped_copy

    return result


def make_lab(lab, timelist, lec_time, lec_queue, lab_queue, teacherList, all_classes, all_rooms, result, index_slot,
             ntimes, lab_prof):
    nslots = len(timelist) * len(all_rooms)
    if index_slot < nslots:
        if len(lab_queue) == 0:
            while index_slot < nslots and (index_slot % ntimes + 1 in lec_time.keys() or \
                    check_time_conflict(index_slot % ntimes + 1, teacherList[lab_prof][1],
                                            timelist, all_rooms, index_slot // ntimes)):
                if index_slot % ntimes + 1 in lec_time.keys():
                    lec_queue.append(index_slot)
                else:
                    lab_queue.append(index_slot)
                index_slot = index_slot + 1
            if index_slot < nslots:
                if all_classes[lab].dept == "ARTS":
                    result[all_classes[lab]] = (all_rooms[index_slot // ntimes], index_slot % ntimes + 1, [])
                else:
                    new_course = Course(all_classes[lab].name, lab_prof, all_classes[lab].specs,
                                        all_classes[lab].dept, all_classes[lab].level)
                    new_course.has_lab = -1
                    result[new_course] = (all_rooms[index_slot // ntimes], index_slot % ntimes + 1, [])
                # assign time to room
                all_rooms[index_slot // ntimes].taken.append(index_slot % ntimes + 1)
                print("before:", teacherList[lab_prof][1])
                teacherList[lab_prof][1].append(index_slot % ntimes + 1)
                print("after:", teacherList[lab_prof][1])
                index_slot = index_slot + 1

        else:
            copy_lab = []
            assigned = False
            while not len(lab_queue) == 0:
                possible_time = lab_queue.pop(0)

                # if no conflict, assign class
                if not check_time_conflict(possible_time % ntimes + 1, teacherList[lab_prof][1], timelist,
                                       all_rooms, possible_time // ntimes):
                    # class name : location, time, Students
                    if all_classes[lab].dept == "ARTS":
                        result[all_classes[lab]] = (all_rooms[possible_time // ntimes],
                                                    possible_time % ntimes + 1, [])
                    else:
                        new_course = Course(all_classes[lab].name, lab_prof, all_classes[lab].specs,
                                            all_classes[lab].dept, all_classes[lab].level)
                        new_course.has_lab = -1
                        result[new_course] = (all_rooms[possible_time // ntimes],
                                              possible_time % ntimes + 1, [])
                    all_rooms[possible_time // ntimes].taken.append(possible_time % ntimes + 1)
                    print("before:", teacherList[lab_prof][1])
                    teacherList[lab_prof][1].append(possible_time % ntimes + 1)
                    print("after:", teacherList[lab_prof][1])
                    assigned = True
                    break
                else:
                    copy_lab.append(possible_time)

            if len(lab_queue) == 0:
                if not assigned:
                    while index_slot < nslots and (check_time_conflict(index_slot % ntimes + 1, teacherList[lab_prof][1],
                                                  timelist, all_rooms, index_slot // ntimes) or index_slot % ntimes + 1 in lec_time.keys()):
                        if index_slot % ntimes + 1 in lec_time.keys():
                            lec_queue.append(index_slot)
                        else:
                            lab_queue.append(index_slot)
                        index_slot = index_slot + 1
                    if index_slot < nslots:
                        if all_classes[lab].dept == "ARTS":
                            result[all_classes[lab]] = (all_rooms[index_slot // ntimes],
                                                        index_slot % ntimes + 1, [])
                        else:
                            new_course = Course(all_classes[lab].name, lab_prof, all_classes[lab].specs,
                                                all_classes[lab].dept, all_classes[lab].level)
                            result[new_course] = (all_rooms[index_slot // ntimes],
                                                  index_slot % ntimes + 1, [])
                        all_rooms[index_slot // ntimes].taken.append(index_slot % ntimes + 1)
                        print("before:", teacherList[lab_prof][1])
                        teacherList[lab_prof][1].append(possible_time % ntimes + 1)
                        print("after:", teacherList[lab_prof][1])
                        index_slot = index_slot + 1
            # recover skipped_slots
            lab_queue += copy_lab

    return result, index_slot, lec_queue, lab_queue, teacherList


def make_schedule_extension(all_classes, all_rooms, teacherList, time_list):
    """
        Args:
            all_classes (list): list of Course objects w/ attr. name (int), teacher (int), dept (str),
                                level (int), specs (list of ints), is_core (bool), has_lab (int)
            all_rooms (list): list of ClassRoom obejcts, w/ attr. idx (str), capacity (int)
            teacherList (dict): {teacher_id (int): [class_name (int), personal_conflicts (list of ints)]}
            time_list (dict): {index_time: [start(int), end(int), day(list of strings)]}
        Returns:
            schedule (dict): {Course: (ClassRoom, time, [Students])}
    """

    all_classes.sort(key=lambda x: sort_class(x), reverse=True)
    all_rooms.sort(key=lambda x: x.capacity, reverse=True)
    lab_time, lec_time = seperate_time_table(time_list)
    skipped_slots_lec = []
    skipped_slots_lab = []
    ntimes = len(time_list)
    nslots = len(all_rooms) * ntimes
    index_class = 0
    index_slot = 0
    result = {}
    while index_class < len(all_classes) and index_slot < nslots:
        if all_classes[index_class].dept == "ARTS":
            result, index_slot, skipped_slots_lec, skipped_slots_lab, teacherList= \
                make_lab(index_class, time_list, lec_time, skipped_slots_lec,
                         skipped_slots_lab, teacherList, all_classes, all_rooms, result, index_slot,
                         ntimes, all_classes[index_class].teacher)
            teacherList[all_classes[index_class].teacher][1].append((index_slot-1) % ntimes + 1)
        else:
            if len(skipped_slots_lec) == 0:
                # teacherList[all_classes[index_class].teacher][1] are time that have already been taken
                while index_slot < nslots and (index_slot % ntimes + 1 in lab_time.keys() or check_time_conflict(
                    index_slot % ntimes + 1, teacherList[all_classes[index_class].teacher][1],
                    time_list, all_rooms, index_slot // ntimes)):
                    # class name : location, time, students
                    if index_slot % ntimes + 1 in lab_time.keys():
                        skipped_slots_lab.append(index_slot)
                    else:
                        skipped_slots_lec.append(index_slot)
                    index_slot = index_slot + 1

                if index_slot < nslots: #else will actually exit out of while loop
                    result[all_classes[index_class]] = (all_rooms[index_slot // ntimes], index_slot % ntimes + 1, [])
                    all_rooms[index_slot // ntimes].taken.append(index_slot % ntimes + 1)
                    teacherList[all_classes[index_class].teacher][1].append(index_slot % ntimes + 1)
                    index_slot += 1
                    
                    if all_classes[index_class].has_lab != 0 and index_slot < nslots:
                        # append the lecture's time to lab instructor's list of unavailable times so that lab
                        # doesn't conflict with lecture
                        # teacherList[all_classes[index_class].has_lab][1].append((index_slot-1) % ntimes + 1)
                        result, index_slot, skipped_slots_lec, skipped_slots_lab, teacherList = make_lab(
                            index_class, time_list, lec_time, skipped_slots_lec, skipped_slots_lab, 
                            teacherList, all_classes, all_rooms, result, index_slot, ntimes, 
                            all_classes[index_class].has_lab)
                        teacherList[all_classes[index_class].has_lab][1].append((index_slot-1) % ntimes + 1)

            else:
                copy_skipped_slots = []
                assigned = False  # mark whether current class has been assigned
                while len(skipped_slots_lec) > 0:
                    possible_time = skipped_slots_lec.pop(0)

                    # if no conflict, assign class
                    if not check_time_conflict(possible_time % ntimes + 1, teacherList[all_classes[index_class].teacher][1],
                                           time_list, all_rooms, possible_time // ntimes):
                        # class name : location, time, Students
                        result[all_classes[index_class]] = (
                            all_rooms[possible_time // ntimes], possible_time % ntimes + 1, [])
                        all_rooms[possible_time // ntimes].taken.append(possible_time % ntimes + 1)
                        teacherList[all_classes[index_class].teacher][1].append(possible_time % ntimes + 1)
                        assigned = True
                        if all_classes[index_class].has_lab > 0:
                            # append the lecture's time to lab instructor's list of unavailable times so that lab
                            # doesn't conflict with lecture
                            # teacherList[all_classes[index_class].has_lab][1].append(possible_time % ntimes + 1)
                            result, index_slot, skipped_slots_lec, skipped_slots_lab, teacherList = make_lab(
                                index_class, time_list, lec_time, skipped_slots_lec, skipped_slots_lab, 
                                teacherList, all_classes, all_rooms, result, index_slot, ntimes, 
                                all_classes[index_class].has_lab)
                            teacherList[all_classes[index_class].has_lab][1].append((index_slot-1) % ntimes + 1)
                        break
                    else:
                        copy_skipped_slots.append(possible_time)

                if len(skipped_slots_lec) == 0:
                    if not assigned:
                        while index_slot < nslots and (index_slot % ntimes + 1 in lab_time.keys() or check_time_conflict(
                            index_slot % ntimes + 1, teacherList[all_classes[index_class].teacher][1], time_list,
                            all_rooms, index_slot // ntimes)):
                            # class name : location, time, students
                            if index_slot % ntimes + 1 in lab_time.keys():
                                skipped_slots_lab.append(index_slot)

                            else:
                                skipped_slots_lec.append(index_slot)

                            index_slot = index_slot + 1

                        if index_slot < nslots: #else will actually exit out of while loop
                            result[all_classes[index_class]] = (all_rooms[index_slot // ntimes], index_slot % ntimes + 1, [])
                            all_rooms[index_slot // ntimes].taken.append(index_slot % ntimes + 1)
                            teacherList[all_classes[index_class].teacher][1].append(index_slot % ntimes + 1)
                            index_slot += 1
                            if all_classes[index_class].has_lab > 0:
                                result, index_slot, skipped_slots_lec, skipped_slots_lab, teacherList = make_lab(
                                        index_class, time_list, lec_time, skipped_slots_lec,
                                             skipped_slots_lab, teacherList, all_classes, all_rooms, result, index_slot,
                                             ntimes, all_classes[index_class].has_lab)
                            teacherList[all_classes[index_class].has_lab][1].append((index_slot-1) % ntimes)
                # recover skipped_slots
                skipped_slots_lec += copy_skipped_slots

        index_class = index_class + 1


    # try to schedule remaining classes with skipped slots
    while index_class < len(all_classes) and (skipped_slots_lec or skipped_slots_lab):
        if all_classes[index_class].dept == "ARTS" and skipped_slots_lab:
            skipped_copy = []
            while len(skipped_slots_lec):
                potential_time = skipped_slots_lab.pop(0)
                if not check_time_conflict(potential_time % ntimes + 1, teacherList[all_classes[index_class].teacher][1],
                                            time_list, all_rooms, potential_time // ntimes):
                    result[all_classes[index_class]] = (all_rooms[potential_time // ntimes], potential_time % ntimes + 1, [])
                    break
                else:
                    skipped_copy.append(potential_time)
            index_class += 1
            skipped_slots = skipped_copy
        elif skipped_slots_lec and all_classes[index_class].has_lab == 0:
            skipped_copy = []
            while len(skipped_slots_lec) > 0:
                potential_time = skipped_slots_lec.pop(0)
                if not check_time_conflict(potential_time % ntimes + 1, teacherList[all_classes[index_class].teacher][1],
                                        time_list, all_rooms, potential_time // ntimes):
                    result[all_classes[index_class]] = (all_rooms[potential_time // ntimes], potential_time % ntimes + 1, [])
                    break
                else:
                    skipped_copy.append(potential_time)
            index_class += 1
            skipped_slots_lec = skipped_copy
        else: # not scheduling classes with labs because it's too complicated... for now
            index_class += 1

    return result





if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Usage: python3 main.py <studentprefs/enrollment.txt> <basic_constraints.txt> '
                    '(<extension_constriants-2.txt> <random_prefs.txt>) (--extension)')
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
        start_time = timeit.default_timer()
        all_students = read_prefs(args.infiles[0])
        ntimes, all_rooms, all_classes, all_teachers = read_constraints(args.infiles[1])
        count_prefs(all_classes, all_students)
        # make schedule for basic version
        schedule = make_schedule_basic(all_students, all_classes, all_rooms, ntimes, all_teachers)
        choose_student(schedule)
        print_schedule(schedule, args.outfile)
        elapsed = timeit.default_timer() - start_time
        print("\nTime taken:", elapsed)
        subprocess.call(["perl", "is_valid.pl", args.infiles[1], args.infiles[0], args.outfile])

    else:
        # read enrollment data
        all_students = read_enrollment(args.infiles[0])
        all_times, all_rooms, all_classes, all_teachers = read_extension_constraints(args.infiles[1], args.infiles[2])
        build_time_table(all_times)
        count_prefs(all_classes, all_students)
        assign_core(all_classes)
        # make schedule
        start_time = timeit.default_timer()
        #try:
        schedule = make_schedule_extension(all_classes, all_rooms, all_teachers, all_times)
        #except IOError as e:
            #if e.errno == errno.EPIPE:
                #pass
        # remove previous enrolled student data
        for c in schedule:
            c.specs = []
        # read in preregistration data
        all_students = read_extension_prefs(args.infiles[3], all_classes)
        count_prefs(all_classes, all_students)
        choose_student_extension(schedule, all_times)
        elapsed = timeit.default_timer() - start_time
        print("\nTime taken:", elapsed)
        
        # for calling is_valid.pl
        # However, doesn't really work because labs share the same class name with lectures
        print_prefs(len(all_students), all_classes, args.infiles[3][:-4]+"_test.txt", args.infiles[3])
        print_constraints(all_rooms, all_classes, all_times, all_teachers, "../test_data/extension_constraints.txt")
        print_schedule_call_perl(schedule, args.outfile[:-4]+"_test.txt", all_times, all_rooms, "../test_data/extension_constraints.txt", args.infiles[3][:-4]+"_test.txt")
        
        print_schedule_extension(schedule, args.outfile, all_times)


        # for printing intermediate results
        lab_time, lec_time = seperate_time_table(all_times)



    if args.test:

        print("\nLab Times:")
        for t in lab_time:
            print(t, lab_time[t])

        print("\nLecture Times:")
        for t in lec_time:
            print(t, lec_time[t])

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

        print("\n ===============Schedule=============\n")
        for c in schedule:
            # schedule (dict): {Course: (ClassRoom, time_index, [Students])}
            print(c.name, "\t", c.teacher, "\t", schedule[c][0].idx, "\t", repr_time(all_times[schedule[c][1]]))
            print("Students:", ' '.join([str(s.idx) for s in schedule[c][2]]))

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
