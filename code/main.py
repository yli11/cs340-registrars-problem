import argparse
import pandas as pd
from collections import defaultdict



""" Parse preference lists input

     Args:
        filename (string): name of the input preferece lists

    Returns:
        all_students (list): a list of Student objects
"""
def read_prefs(filename):
    # read input file
    df_raw = pd.read_csv(filename, skiprows=1, delim_whitespace=True, names=['Student','Class1','Class2','Class3','Class4'])
    
    # put each student's class choices into a list
    classes = defaultdict(list)
    for i in df_raw['Student']:
        classes[i].append(int(df_raw.loc[df_raw['Student']==i, 'Class1']))
        classes[i].append(int(df_raw.loc[df_raw['Student']==i, 'Class2']))
        classes[i].append(int(df_raw.loc[df_raw['Student']==i, 'Class3']))
        classes[i].append(int(df_raw.loc[df_raw['Student']==i, 'Class4']))

    # construct a new DataFrame and return
    all_students = pd.DataFrame(list(classes.items()),columns=['Student', 'Classes'])
    #all_students = [ Student(i, df_students.loc[i-1, 'Classes']) for i in df_students['Student'] ]

    return all_students


""" Parse constraints info

     Args:
        filename (string): name of the input file

    Returns:
        all_rooms (list): a list of Classroom objects
        all_classes (list): a list of Course objects
        ntimes (int): the number of non-overlapping time slots
"""
def read_constraints(filename):
    # read file
    df_raw = pd.read_csv(filename, delim_whitespace=True, header=None)

    # record the number of time slots
    ntimes = int(df_raw.loc[0,2])

    # parse remaining info into two parts, one about rooms, the other about teachers
    r_start = df_raw[df_raw[0] == "Rooms"].index[0]
    t_start = df_raw[df_raw[0] == "Teachers"].index[0]
    df_rooms = df_raw.loc[r_start:t_start-2]
    new_header = df_rooms.iloc[0]
    nrooms = new_header[1]
    df_rooms = df_rooms[1:]
    df_rooms.columns = new_header
    df_teachers = df_raw.loc[t_start:]
    new_header = df_teachers.iloc[0]
    nteachers = new_header[1]
    df_teachers = df_teachers[1:]
    df_teachers.columns = new_header


    # dict versions for testing
    all_rooms = {int(r): int(df_rooms.loc[df_rooms['Rooms']==r, nrooms]) for r in df_rooms['Rooms']}
    all_classes = {int(c): int(df_teachers.loc[df_teachers['Teachers']==c, nteachers]) for c in df_teachers['Teachers']}
    
    # construct Room and Course objects
    #all_rooms = [Classroom(int(r): int(df_rooms.loc[df_rooms['Rooms']==r, nrooms])) for r in df_rooms['Rooms']]
    #all_classes = [Course(int(c), int(df_teachers.loc[df_teachers['Teachers']==c, nteachers])) for c in df_teachers['Teachers']]

    return ntimes, all_rooms, all_classes


""" Construct the pool of prospective students for all classes

     Args:
        C (list): a list of Course objects
        S (list): a list of Student objects

    Returns:
        C (list): a list of Course objects whose `specs` field stores a list of students hoping to take this class
"""
def create_classes(C, S):

    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Schedule classes')
    parser.add_argument('infiles', type=str, nargs='+', help='Name of input file(s)')
    parser.add_argument('--outfile','-o', type=str, help='Name of output schedule')
    parser.add_argument('--extension', action='store_true', help="whether allowing haverford extension, by default, run the basic version") 
    args = parser.parse_args()


    # print results for testing
    all_students = read_prefs(args.infiles[0])
    ntimes, all_rooms, all_classes = read_constraints(args.infiles[1])
    print("Student preference lists:\n", all_students)
    print("# of time slots: " + str(ntimes))
    print("Classroom capacities: ", all_rooms)
    print("Classes teacher info: ", all_classes)

    