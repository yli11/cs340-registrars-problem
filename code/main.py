import argparse
import pandas as pd
from multiprocessing import Queue
from collections import defaultdict
from components import ClassRoom, Student, Course


def read_prefs(filename):
    """ Parse preference lists input
         Args:
            filename (string): name of the input preferece lists
        Returns:
            all_students (list): a list of Student objects
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
            all_rooms (list): a list of Classroom objects
            all_classes (list): a list of Course objects
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

    """ dict versions for testing
    all_rooms = {int(r): int(df_rooms.loc[df_rooms['Rooms']==r, nrooms]) for r in df_rooms['Rooms']}
    all_classes = {int(c): int(df_teachers.loc[df_teachers['Teachers']==c, nteachers]) for c in df_teachers['Teachers']}
    """

    # construct ClassRoom and Course objects
    all_rooms = [ClassRoom(int(r), int(df_rooms.loc[df_rooms['Rooms'] == r, nrooms])) for r in df_rooms['Rooms']]
    all_classes = [Course(int(c), int(df_teachers.loc[df_teachers['Teachers'] == c, nteachers])) for c in
                   df_teachers['Teachers']]
    all_teachers = {}

    for t in range(1,int(nteachers)+1):
        all_teachers[t] = list(map(int, df_teachers.loc[df_teachers[nteachers] == str(t), 'Teachers'].tolist()))

    return ntimes, all_rooms, all_classes, all_teachers


def count_prefs(C, S):
    """ Initialize the pool of prospective students for all classes
         Args:
            C (list): a list of Course objects
            S (list): a list of Student objects
    """
    for s in S:
        for c_id in s.classes:
            a_class = find_class(C, c_id)
            a_class.specs.append(s)
            print('Adding student ' + str(s.idx) + ' to class ' + str(a_class.name))


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


def choose_student(course):
    """
    choose student from specs to into the student list of corresponding class in dictionary
    """
    if course:
        for a_class in course:
	    s = a_class.specs
	    time = course.get(a_class)[1]
            counter = 0
	    for student in s:
                if counter > course.get(a_class)[0].capacity:
                    break
                else:
		    flag = True
		    for c in student.classes:
		        if c == a_class:
		            continue
                        else:
                            if time == course.get(c)[1]:
                                flag = False
                                break
                            if flag == True:
                                course.get(a_class)[2].append(student)
                                counter += 1
                            else:
                                continue
            
                        

    return course


def TeacherIsValid(teacherList, result, classToSchedule, timeToSchedule):
    """
    Test whether the class we are scheduling has conflict respect to teachers (whether they're taught by the same teacher
    and both classes are at the same time slot)
    Args:
        teacherList: A dictionary where key is teacher value is a list of classes he or she is teaching
        result: The schedule we have so far. Key is class, value is a tuple -> (location, time, students)
        classToSchedule: The class we're currently scheduling.
        timeToSchedule: The time we're considering.
    """
    teacher = classToSchedule.teacher
    classes = teacherList.get(teacher)
    if not result.has_key(classes[0]) and not result.has_key(classes[1]):
        return True
    elif result.has_key(classes[0]):
        if result.get(classes[0])[1] == timeToSchedule:
            return False
        else:
            return True
    else:
        if result.get(classes[1])[1] == timeToSchedule:
            return False
        else:
            return True

def makeSchedule(all_students, all_classes, all_rooms, ntimes, teacherList):
    all_classes.sort(key=lambda x: len(x.specs), reverse=True)
    all_rooms.sort(reverse=True)
    skipped_slots = Queue.Queue()
    num_classes = len(all_classes)
    num_rooms = len(all_rooms)*ntimes   # This can avoid a while loop stated in line 9 from our pseudocode
    index_class = 0
    index_room = 0
    index_time = 0
    result = {}
    while index_class < num_classes:
        if index_room == num_rooms:
            index_room = 0
        if index_time == ntimes+1:
            index_time = 0
        if skipped_slots.empty():
            if TeacherIsValid(teacherList, result, all_classes[index_class], index_time):
                # class name : location, time, students
                result[all_classes[index_class]] = (all_rooms[index_room//ntimes], index_time, [])
                index_time = index_time + 1
                index_room = index_room + 1
            else:
                skipped_slots.put(index_time)
                index_time = index_time+1        # don't need to increment index_room here since no room is assigned

    #result is a dictionary without student list
    result = choose_student(result)
    return result















if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Schedule classes')
    parser.add_argument('infiles', type=str, nargs='+', help='Name of input file(s). Assuming the first file contains preference lists, the second file contains basic constraints, the third one contains constraints for Haverford extension.')
    parser.add_argument('--outfile', '-o', type=str, help='Name of output schedule')
    parser.add_argument('--extension', action='store_true',
                        help="whether allowing haverford extension, by default, run the basic version")
    args = parser.parse_args()

    # parse input
    all_students = read_prefs(args.infiles[0])
    ntimes, all_rooms, all_classes, all_teachers = read_constraints(args.infiles[1])
    count_prefs(all_classes, all_students)

    """
    for c in all_classes:
        print(c.name, "specs: ", [s.idx for s in c.specs])
    """
