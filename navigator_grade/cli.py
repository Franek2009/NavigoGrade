from .calculator import (
    CompetencyRecord,
    acquisition_percentage,
    average_competency_level,
    grade_requirements_met,
)
from .rules import GRADE_REQUIREMENTS


def _read_non_negative_integer(prompt: str) -> int:
    while True:
        try:
            value = int(input(prompt))
            if value < 0:
                raise ValueError
            return value
        except ValueError:
            print("Enter a non-negative whole number.")


def _read_target_grade() -> int:
    while True:
        try:
            grade = int(input("Target final grade (2-6): "))
            if grade not in GRADE_REQUIREMENTS:
                raise ValueError
            return grade
        except ValueError:
            print("Enter a grade from 2 to 6.")


def run() -> None:
    print("NavigoGrade")
    total_realized = _read_non_negative_integer(
        "Competencies realized in the course/year: "
    )
    while total_realized == 0:
        print("The number realized must be greater than zero.")
        total_realized = _read_non_negative_integer(
            "Competencies realized in the course/year: "
        )
    attempted = _read_non_negative_integer("Competencies attempted by the student: ")
    level_counts = {
        level: _read_non_negative_integer(
            f"Acquired competencies at level {level}: "
        )
        for level in range(4)
    }
    target_grade = _read_target_grade()
    requirement = GRADE_REQUIREMENTS[target_grade]

    try:
        record = CompetencyRecord(
            total_realized=total_realized,
            attempted=attempted,
            level_0=level_counts[0],
            level_1=level_counts[1],
            level_2=level_counts[2],
            level_3=level_counts[3],
        )
        percentage = acquisition_percentage(record)
        average = (
            average_competency_level(record)
            if requirement.minimum_average_level is not None
            else None
        )
        meets_requirements = grade_requirements_met(target_grade, record)
    except ValueError as error:
        print(f"\nCannot calculate result: {error}.")
        return

    print(f"\nAcquired competencies: {record.acquired}")
    print(f"Acquisition percentage: {percentage:.2f}%")
    print(
        f"Grade {target_grade} requires at least "
        f"{requirement.minimum_acquisition_percentage:g}% acquired."
    )
    if average is not None:
        print(f"Average competency level: {average:.2f}")
        print(
            "It also requires an average competency level of at least "
            f"{requirement.minimum_average_level:.2f}."
        )
    result = "meets" if meets_requirements else "does not meet"
    print(f"Result: the student {result} the requirements for grade {target_grade}.")
