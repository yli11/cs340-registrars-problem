class Student(object):
    """A student is a class containing unique identity and a list of preference classes"""
    def __init__(self,id, classes):
        self.id = id
        self.classes = classes

class ClassRoom(object):
    def __init__(self,size):
        self.capacity = size


class Course(object):
    def __init__(self,name,teacher):
        self.name = name
        self.teacher = teacher
        self.students = []