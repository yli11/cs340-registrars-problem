# Checkpiont 2 

## Implementation

* Classes should be implemented in a separate file `data_structures.py` Need constructor and accessor, no mutator needed at this point.
* `class Student`
  * attribute: `prefs`
  * (poss. extension): ranking of preference for each class, `class_year`,`major`
* `class Classroom`
  * attribute: `capacity`
* `class Course`
  * attributes: `name` (int for basic version),`teacher`, `specs` - a list of prospective students, initialize to `[]`
  * possible extension: `department`, `is_core`
* functions`schedule_class`, `choose_student`, `print_output`

## Packages to use
* `import pandas as pd`
* `from queue import` whatever function/methods you need
* `from collections import defaultdict`

// Ignore this

Output format

* File 1:
  * Rows headers: Classrooms
  * Columns: time slots
* File 2:
  * Row headers: Classes

  ​

## Tasks:
* Yutong - parse input
* Mark - class implementation
* Jiaping - output schedule


*Deadline*: try to finish by _next Monday_ (including as much of the haverford extension as we can do)

## Extended Version: 

### Tentative Constraints

1. Must schedule core classes for each department -- randomly choose two core classes from each level from each department.(we need to parse department)
2. Assign popularity to time slots. Schedule popular class at more popular times. -- we sort time slots table based on the popularity of time slot, and we put the time slots with high priority before time slots with low priority.
3. class times overlap: all_times: an array, each time represented by a tuple (start, end, a-list-of-days).  we need a class times slot table.
5. Teachers have personal conflicts - an additioal time attribute in teacher class (using array), and modify teach is valid function in the main function based on that.
8. Lectures vs. Labs (1 class can have multiple lab sections, but lab runs only once a week) -- some classes will have labs,labs always take 3 hours, which means it will take two consecutive time slots. And we assume the student take that course must take lab.

2. Assign priority to students according to class year --randomly assign a priority number to student as a weight. So when choosing student, we just weigh student by their priority. --in doubt
6. Classes have prerequisites - these can be scheduled at the same time. --too hard


4. Can have multiple potential teachers for the same course
7. Quarter classes vs. semester classes

### Available Info

1. Enrollment data from the past
2. number of major & minor students
3. class level (higher level classes in smaller classrooms)
4. department info (allow conflicts across categories SO, HU, NS)
