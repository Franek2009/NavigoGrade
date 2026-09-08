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

Enter the total, four level counts on one line, and a target grade from 2 through
6. When all realized competencies are acquired, `attempted` is inferred safely
and the normal workflow takes three input lines. If fewer competencies are
acquired than realized, the CLI asks for `attempted` separately.

### Example

```text
$ python main.py
NavigoGrade

Liczba kompetencji: 12
Poziomy [0 1 2 3]: 0 1 3 8
Cel: 6

Obecnie: 5
Zdobyte: 12/12 (100%)
Średnia: 2.58

Do oceny 6:
✓ wymagane 90% kompetencji
✗ wymagana średnia 2.70

Brakuje: 2 punktów poziomu.

Najprościej:
→ 1 kompetencję z poziomu 1 na 3

Alternatywnie:
→ 2 kompetencje z poziomu 2 na 3
```

## Run the tests

The test suite uses Python's standard library and requires no additional
dependencies:

```bash
python -m unittest discover -s tests
```
