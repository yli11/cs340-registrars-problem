# Basic Version

## Generat Input

```$ perl make_random_input.pl <#rooms> <#classes> <#times> <#students> <../test_data/xx_constraints.txt> <../test_data/xx_studentprefs.txt>```

## Make Schedule (for a single set of input)

```$ python3 main.py <../test_data/xx_constraints.txt> <../test_data/xx_studentprefs.txt> -o <our_scheulde.txt>  ```

*Args*

- 1 -  input filename: student preferences
- 2 - input filename: constraints
- 3 - after `-o` : output filename

*Note* : The script automatically calls `is_valid.pl` and check validity of schedule

# Haverford Extension

## Generate Input

### Data from Haverford

*Note* : don't need to do this if you download the files in `../test_data/` directory

```$ python get_haverford_info.py haverfordEnrollmentDataS14.csv ../test_data/haverfordStudentPrefs.txt ../test_data/haverfordConstraints_1.txt ../test_data/haverfordConstraints_2.txt```

*Args*

* 1 -  input filename: the enrollment data csv file
* 2 - output filename: enrollment
* 3 - output filename: time slots and room capacities
* 4 - output filename: classes, teachers, department, and level

### Student Preferences 

Mark pls fill in this part

## Make Schedule (for a single set of input)

```$ python3 main.py ../test_data/haverfordStudentPrefs.txt ../test_data/haverfordConstraints_1.txt ../test_data/haverfordConstraints_2.txt --extension -o ../test_data/extension_schedule.txt```

*Args*

- 1 -  input filename: enrollment/expected class size
- 2 - input filename: time slots and room capacities
- 3 - input filename: classes, teachers, department, and level
- after `-o` : output schedule name

*Note* : the main function probably doesn't work at this point, so it's not called by the script. Only input is available. Can utilize the `—test` option to print parsed input
