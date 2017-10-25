class Student(object):
    """A student is a class containing unique identity and a list of preference classes"""
    def __init__(self,idx, classes=[]):
        self.idx = idx
        self.classes = classes

class ClassRoom(object):
    """A classroom is a room with specific size"""
    def __init__(self,idx,size=0):
        self.idx = idx
        self.capacity = size


class Course(object):
    """A course is an object with unique name, 
                                  unique teacher(for the basic version), and 
                                  students who wants to take it(will be determined by random choice for bacic version)
    """
    def __init__(self,name,teacher, specs=[]):
        self.name = name
        self.teacher = teacher
        self.specs = specs
