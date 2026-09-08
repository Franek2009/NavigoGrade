from dataclasses import dataclass


@dataclass(frozen=True)
class GradeRequirement:
    """Minimum requirements for a final grade."""

    grade: int
    minimum_acquisition_percentage: float
    minimum_average_level: float | None = None


GRADE_REQUIREMENTS: dict[int, GradeRequirement] = {
    2: GradeRequirement(2, 55.0),
    3: GradeRequirement(3, 60.0, 1.65),
    4: GradeRequirement(4, 75.0, 1.95),
    5: GradeRequirement(5, 80.0, 2.25),
    6: GradeRequirement(6, 90.0, 2.70),
}
