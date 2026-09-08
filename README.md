# NavigoGrade

NavigoGrade is an unofficial terminal application that checks whether a student
meets the requirements for a selected final grade under Navigo's
competency-based grading rules. When requirements are missing, it calculates a
minimal practical plan for acquiring additional competencies and improving
existing competency levels.

> **Alpha warning:** `v0.3.0-alpha.1` is an early test release. Results should
> be checked against the current school statute before they are used for an
> important decision.

NavigoGrade is an independent, unofficial project. It is not affiliated with or
endorsed by the school.

## Requirements

- Python 3.10 or newer
- A terminal

The project uses only the Python standard library. There is currently no GUI.

## Install and run

Clone the repository, enter its directory, and run the application:

```bash
git clone <repository-url>
cd NavigoGrade
python main.py
```

Depending on your system, the Python command may be `python3` instead of
`python`.

## Input

The fastest input format contains the total number of realized competencies,
the acquired counts at levels 0 through 3, and the target grade:

```text
wszystkie | poziom 0 | poziom 1 | poziom 2 | poziom 3 | cel
```

Example:

```text
12 | 0 | 1 | 3 | 8 | 6
```

Spaces can be used instead of `|` separators. When not all competencies are
acquired, also provide the number attempted:

```text
wszystkie | przystąpiono | poziom 0 | poziom 1 | poziom 2 | poziom 3 | cel
20 | 16 | 0 | 1 | 5 | 10 | 4
```

Press Enter at the initial `>` prompt to use the guided input flow instead:

```text
Wszystkich kompetencji: 10
Poziomy 0 1 2 3: 0 4 2 2
Przystąpiono [10]:
Cel: 5
```

Pressing Enter at `Przystąpiono` accepts the displayed default.

## Grading rules

The student must meet every requirement listed for the selected grade:

| Target grade | Minimum acquisition percentage | Minimum average level |
|-------------:|-------------------------------:|----------------------:|
| 2 | 55% | None |
| 3 | 60% | 1.65 |
| 4 | 75% | 1.95 |
| 5 | 80% | 2.25 |
| 6 | 90% | 2.70 |

Grade 2 has no average-level requirement. An acquired competency may be at any
level from 0 through 3, so level 0 counts as acquired.

The calculations are:

- acquisition percentage = acquired / total realized × 100;
- average level = weighted sum of acquired competency levels / attempted.

The application keeps these counts distinct:

- `total_realized`: all competencies realized in the course or school year;
- `attempted`: competencies the student attempted;
- `acquired`: the sum of acquired competencies at levels 0, 1, 2, and 3.

Input must satisfy `acquired <= attempted <= total_realized`. This is a data
consistency rule inferred from the meanings of the terms, not a separate grading
threshold explicitly stated in the statute.

## Current limitations

- This is an early alpha and may still contain defects or incomplete wording.
- The application relies on aggregate counts entered manually by the user.
- Recommendations are mathematical plans based on the configured rules; they do
  not predict how or when a competency can be reassessed.
- The interface is terminal-based and currently written in Polish.
- There is no GUI.

## Run the tests

From the project directory:

```bash
python -m unittest discover -s tests
```

No additional test dependencies are required.

## License

NavigoGrade is available under the MIT License. See [LICENSE](LICENSE).
