# NavigoGrade

NavigoGrade is a small terminal application for checking competency-based final
grade requirements.

## Grading rules

The student must meet every requirement listed for the selected target grade:

| Target grade | Minimum acquisition percentage | Minimum average level |
|-------------:|-------------------------------:|----------------------:|
| 2 | 55% | None |
| 3 | 60% | 1.65 |
| 4 | 75% | 1.95 |
| 5 | 80% | 2.25 |
| 6 | 90% | 2.70 |

Grade 2 has no average-level requirement.

## Competency counts

The CLI keeps three concepts distinct:

- `total_realized`: all competencies realized in the course or school year;
- `attempted`: competencies the student attempted;
- `acquired`: competencies the student acquired, calculated as the sum of the
  counts at levels 0, 1, 2, and 3.

An acquired competency may be at any level from 0 through 3. Consequently, level
0 competencies count toward the number acquired and toward the acquisition
percentage.

The calculations follow the statute literally:

- acquisition percentage = acquired / total realized * 100;
- average level = weighted sum of acquired competency levels / attempted.

`attempted` is modeled separately from `acquired`. Input must satisfy:

```text
acquired <= attempted <= total_realized
```

This relationship is an input-consistency rule inferred from the meanings of the
terms. It is not an explicit grading threshold stated separately in the statute.
When `attempted` is zero, the average is absent (`None`) rather than assigned an
invented numeric value.

## Run the CLI

From the project directory, run:

```bash
python main.py
```

Enter the requested counts and a target grade from 2 through 6.

### Example

```text
$ python main.py
NavigoGrade
Competencies realized in the course/year: 20
Competencies attempted by the student: 16
Acquired competencies at level 0: 0
Acquired competencies at level 1: 1
Acquired competencies at level 2: 5
Acquired competencies at level 3: 10
Target final grade (2-6): 4

Acquired competencies: 16
Acquisition percentage: 80.00%
Grade 4 requires at least 75% acquired.
Average competency level: 2.56
It also requires an average competency level of at least 1.95.
Result: the student meets the requirements for grade 4.
```

## Run the tests

The test suite uses Python's standard library and requires no additional
dependencies:

```bash
python -m unittest discover -s tests
```
