class Student:
    """A student is a class containing unique identity and a list of preference classes
        
       Args:
            idx : A unique label of a student
            classes: classes this student wants to take
            taken: list of times this student is unavailable

    """
    def __init__(self,idx, classes=None):
        self.idx = idx
        if classes is None:
            self.classes = []
        else:
            self.classes = classes
        self.taken = []

class ClassRoom:
    """A classroom is a room with specific size
       Args:
            idx: A unique label of a room
            capacity: the size of thie room
            
    """
    def __init__(self,idx,size=0):
        self.idx = idx
        self.capacity = size


class Course:
    """A course is an object with unique name, 
                                  unique teacher(for the basic version), and 
                                  students who wants to take it(will be determined by random choice for bacic version)
                       
       Args:
            name : the unique name of a course
            teacher: The one who teaches this class
            specs: Students who will take this class, by defaul an empty list
            dept: four-letter string represeting department number
    """
    def __init__(self,name,teacher, specs=None, dept="", level=0):
        self.name = name
        self.teacher = teacher
        self.dept = dept
        self.level = level
        self.is_core = False
        self.has_lab = False
        if specs is None:
            self.specs = []
        else:
            self.specs = specs
