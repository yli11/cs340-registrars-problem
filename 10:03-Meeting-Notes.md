CS340 Project
# Procedure
* Given: teachers `|T| = m` , students `|S|=n` preference lists , a list of `2m` classes,   `x` possible time slots, and `y` rooms
* Without assumption of `x*y >= 2m`
* Create a variable `skippedSlot` - marking the previously skipped slot for the current (largest) classroom. If not `None`, put the next class here. Initialize to `null/None`.
1. For each class, calculate the # of students who wish to take that class
2. Sort by popularity, the first `x` popular classes must fit into different time slots (all go into the largest classroom)
3. Start w/ the largest classroom, fit in the first `x` popular classes into time slots 1 to x.
4. Look at the next `x` classes and pair them w/ the next largest classroom, checking conflict w/ teachers.
5. If `skippedSlot is not None`, put the next class in `skippedSlot` and set it to `None`.
6. Repeat until either all time slots at all classrooms are filled or all classes have been scheduled

# Discussion
## Rationale for Choosing the Algorithm
* For each class, we try to fit in as many students (who sign up for that class) as possible.
* Maximal utilization of classroom capacity

## Alternative Approaches

## Complications
* What if the # of students hoping to take most popular class exceeds the capacity of the largest classroom
* What if teacher conflicts


# Questions
* Currently N/A.

# Future Tasks
1. Apply code to basic data
2. Haverford Extension
3. Five further constraints
	1. subjects overlap (e.g. cs & math)
	2. students might have stronger preference for one class than another
#links for overleaf(our paper)
https://www.overleaf.com/11426327xrbzdmhwpvgf
feel free to edit it.
