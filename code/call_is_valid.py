import subprocess
from collections import OrderedDict
import pandas as pd

def map_prefs_for_perl(i, all_classes):
    """ Used for map, need all_classes to be global"""
    return str(all_classes[int(i)-1].name)

def print_prefs(nstudents, all_classes, studentprefs, original_prefs):
    df = pd.read_csv(original_prefs, skiprows=1, sep="\t", names=['Student', 'Classes'])
    f = open(studentprefs, 'w')
    f.write("Students\t"+str(nstudents))
    for index, row in df.iterrows():
        f.write("\n"+str(row['Student'])+'\t'+' '.join([map_prefs_for_perl(i, all_classes) for i in row['Classes'].split()]))
    f.close()


def print_constraints(all_rooms, all_classes, all_times, all_teachers,constraints):
    """
    all_rooms (list): a list of Classroom objects, with attributes `idx` (str) and `capacity` (int)
    all_classes (list): a list of Course objects, with attributes `name` (str), `teacher` (int), and 
    `specs` (empty list), `dept` (string), `level` (int), core=False
    all_times (dict): {index_time: [start(int), end(int), day(list of string)]}
    all_teachers (dict): {teacher_id (int): [class_name (int), personal_conflicts (list of ints)]}
    """
    nrooms = len(all_rooms)
    ntimes = len(all_times)
    nteachers = len(all_teachers)
    nclasses = len(all_classes)

    f = open(constraints, 'w')
    f.write("Class Times\t"+str(ntimes))
    f.write("\nRooms\t"+str(nrooms))
    for i in range(nrooms):
        f.write("\n"+str(i)+"\t"+str(all_rooms[i].capacity))
    f.write("\nClasses\t"+str(nclasses))
    f.write("\nTeachers\t"+str(nteachers))
    for c in all_classes:
        f.write("\n"+str(c.name)+"\t"+str(c.teacher))
    f.close()



def print_schedule_call_perl(schedule, fname, all_times, all_rooms, constraints, studentprefs):
    """ Output schedule using pandas
        Args:
            schedule (dict): {Course: (ClassRoom, time, [Students])}
    """
    # create a dictionary for pandas to print
    schedule = OrderedDict(sorted(schedule.items(), key=lambda t:t[0].name))

    f = open(fname, 'w')
    f.write("Course\tRoom\tTeacher\tTime\tStudents\n")
    for course in schedule:
        if course.has_lab > -1:
            f.write(str(course.name))
            f.write("\t")
            f.write(str(all_rooms.index(schedule[course][0])))
            f.write("\t")
            f.write(str(course.teacher))
            f.write("\t")
            f.write(str(schedule[course][1]))
            f.write("\t")
            f.write(' '.join([str(s.idx) for s in sorted(schedule[course][2], key=lambda t: t.idx)]))
            f.write("\n")
        #prev_course = course.name
    f.close()
    subprocess.call(["perl", "is_valid.pl", constraints, studentprefs, fname])
