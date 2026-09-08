# NavigoGrade

NavigoGrade is an unofficial Python application that checks whether a student
meets the requirements for a selected final grade under Navigo's
competency-based grading rules. When requirements are missing, it calculates a
minimal practical plan for acquiring additional competencies and improving
existing competency levels. It includes both a terminal interface and a simple
Tkinter graphical interface.

> **Release candidate warning:** `v0.9.0-rc.1` is a pre-release version. Results
> should be checked against the current school statute before they are used for
> an important decision.

NavigoGrade is an independent, unofficial project. It is not affiliated with or
endorsed by the school.

## Requirements

- Python 3.10 or newer
- A terminal for the CLI
- Tkinter for the graphical interface

The project uses only the Python standard library.

## Quick Start

Clone the repository and enter its directory:

```bash
git clone <repository-url>
cd NavigoGrade
```

Depending on your system, the Python command may be `python3` instead of
`python`.

Install NavigoGrade locally:

```bash
python -m pip install .
```

### Terminal interface

```bash
navigograde
```

Enter the six values shown by the prompt, or press Enter to switch to guided
input.

### Graphical interface

Launch the Tkinter interface with:

```bash
navigograde-gui
```

You can also run directly from a source checkout with `python main.py` for the
CLI or `python -m navigator_grade.gui` for the GUI.

In the GUI, empty level fields are treated as zero. The total number of
competencies and the target grade are still required.

#### Installing Tkinter on Linux

Some Linux distributions package Tkinter separately from Python. Install the
package for your distribution, for example:

```bash
# Debian or Ubuntu
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

Package names can vary with the distribution or Python version. Verify the
installation with:

```bash
python -m tkinter
```

## Input

The fastest input format contains the expected total number of competencies,
the evaluated counts at levels 0 through 3, and the target grade:

```text
wszystkie | poziom 0 | poziom 1 | poziom 2 | poziom 3 | cel
```

Example:

```text
12 | 0 | 1 | 3 | 8 | 6
```

Spaces can be used instead of `|` separators.

Press Enter at the initial `>` prompt to use the guided input flow instead:

```text
Wszystkich kompetencji: 10
Poziomy 0 1 2 3: 0 4 2 2
Cel: 5
```

## Grading rules

The student must meet every requirement listed for the selected grade:

| Target grade | Minimum acquisition percentage | Minimum average level |
|-------------:|-------------------------------:|----------------------:|
| 2 | 55% | None |
| 3 | 60% | 1.65 |
| 4 | 75% | 1.95 |
| 5 | 80% | 2.25 |
| 6 | 90% | 2.70 |

Grade 2 has no average-level requirement. Level 0 means that a competency was
evaluated but not acquired. Levels 1, 2, and 3 are acquired competencies.

The calculations are:

- evaluated = level 0 + level 1 + level 2 + level 3;
- acquired = level 1 + level 2 + level 3;
- acquisition percentage = acquired / evaluated × 100;
- average level = weighted sum of all evaluated competency levels / evaluated.

The application keeps these counts distinct:

- `total_overall`: the expected total number of competencies for the whole
  course or school year;
- `evaluated`: competencies that have occurred so far, including level 0;
- `acquired`: evaluated competencies at levels 1, 2, and 3;
- `remaining_future`: competencies expected later in the course or school year.

Input must satisfy `evaluated <= total_overall`. Current grade calculations use
only evaluated competencies. The overall total is used by recommendation
planning to determine whether future competencies are available.

## Future planning

NavigoGrade simulates the final course/year state by assigning every remaining
future competency a level from 0 through 3. If the selected grade is not yet
met, it finds a minimum-action combination of future results and improvements to
existing competencies. If the grade is already met, it finds the weakest future
level distribution that still preserves it. The same outlook also reports the
current distance and a final-state plan for the next higher grade, when one
exists.

Future simulation does not change the current-grade calculation: current
percentage and average always use only competencies evaluated so far.

## Current limitations

- This is a release candidate and may still contain defects or incomplete
  wording.
- The application relies on aggregate counts entered manually by the user.
- Recommendations are mathematical plans based on the configured rules; they do
  not predict how or when a competency can be reassessed.
- The interfaces are currently written in Polish.
- The GUI is an intentionally simple presentation layer over the same
  calculator used by the terminal application.

## Development

Run the complete test suite from the project directory:

```bash
python -m unittest discover -s tests
```

No additional test dependencies are required.

## License

NavigoGrade is available under the MIT License. See [LICENSE](LICENSE).
