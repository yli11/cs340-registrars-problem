# CS340: Registrar's Problem 

Generate a valid class schedule given a set of classes, teachers, time slots, room capacities, and student preferences. The Haverford extension uses actual Haverford enrollment data from Spring 2014 and schedules classes without student preferences. Student preferences are processed after course schedule is finalized.

## Requirements

Python 3.4+, pandas >= 0.19.2

## Generating Schedules (Integrated)

Run multiple experiments with a set of specified input sizes. Need the `.txt` constraint files in this directory.

This will probably generate plenty of intermediate output files in the same directory, preceded by the index of the experiment.

Before calling the script a second time, remove previously generated data (since `make_random_input.pl` doesn't overwrite the content of an existing file when writing to the same file name).

For basic version, do:

```$ python3 run_experiments.py <#rooms> <#classes> <#times> <#students> -n <#experiments>```

For Haverford extension, do:

```$ python3 run_experiments.py <#students> -n <#experiments> -e```

_Note_: the output file `i_extension_schedule.txt` is the actual schedule. `i_extension_schedule_test.txt` replaces all rooms and times with their indices in order to pass `is_valid.pl`. Also, labs are removed from the schedule to be tested by `is_valid`.

## Basic Version

### Generat Input

```$ perl make_random_input.pl <#rooms> <#classes> <#times> <#students> <constraints.txt> <studentprefs.txt>```

###  Make Schedule (for a single set of input)

```$ python3 main.py <studentprefs.txt> <constraints.txt> -o <scheulde.txt>  ```

*Args*

- 1 -  input filename: student preferences
- 2 - input filename: constraints
- 3 - after `-o` : output filename

The script automatically times the process and calls `is_valid.pl` to check schedule validity

## Haverford Extension

### Generate Input

#### Data from Haverford

*Note* : don't need to run this if using the input files provided

```$ python get_haverford_info.py <haverfordEnrollmentDataS14.csv> <S14Enrollment.txt> <haverfordConstraints_1.txt> <haverfordConstraints_2.txt>```

*Args*

* 1 -  input filename: the enrollment data csv file
* 2 - output filename: past enrollment data
* 3 - output filename: file containing time slots and room capacities
* 4 - output filename: file containing class info, teachers, department, and level

#### Student Preferences

```$ perl make_random_input_e_student.pl <#students>  <studentprefs.txt>```

### Make Schedule (for a single set of input)

```$ python3 main.py <S14Enrollment.txt> <haverfordConstraints_1.txt> <haverfordConstraints_2.txt> <studentprefs.txt> --extension -o <extension_schedule.txt>```

*Args*

- 1 -  input filename: enrollment/expected class size
- 2 - input filename: time slots and room capacities
- 3 - input filename: classes, teachers, department, and level
- after `-o` : output schedule name

The script automatically times the process and calls `is_valid.pl` to check schedule validity

## Authors

Yutong Li, Jiaping Wang, Tianming Xu

## Acknowledgements

We thank Professor Dianna Xu for her guidance and advice regarding this project.
