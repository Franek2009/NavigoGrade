from dataclasses import dataclass

from .rules import GRADE_REQUIREMENTS


@dataclass(frozen=True)
class CompetencyRecord:
    """Counts used by the statute's acquisition and average calculations."""

    total_realized: int
    attempted: int
    level_0: int
    level_1: int
    level_2: int
    level_3: int

    def __post_init__(self) -> None:
        values = (
            self.total_realized,
            self.attempted,
            self.level_0,
            self.level_1,
            self.level_2,
            self.level_3,
        )
        if any(not isinstance(value, int) or isinstance(value, bool) for value in values):
            raise TypeError("competency counts must be integers")
        if self.total_realized <= 0:
            raise ValueError("total_realized must be greater than zero")
        if self.attempted < 0:
            raise ValueError("attempted cannot be negative")
        if any(value < 0 for value in self.level_counts):
            raise ValueError("level counts cannot be negative")
        # These subset constraints follow from the ordinary meanings of
        # acquired, attempted, and realized. They are input-consistency
        # invariants, not separate grade requirements stated by the statute.
        if self.acquired > self.attempted:
            raise ValueError("acquired cannot exceed attempted")
        if self.attempted > self.total_realized:
            raise ValueError("attempted cannot exceed total_realized")

    @property
    def level_counts(self) -> tuple[int, int, int, int]:
        return self.level_0, self.level_1, self.level_2, self.level_3

    @property
    def acquired(self) -> int:
        return sum(self.level_counts)

    @property
    def level_sum(self) -> int:
        return sum(level * count for level, count in enumerate(self.level_counts))


def acquisition_percentage(record: CompetencyRecord) -> float:
    """Return acquired competencies as a percentage of those realized."""
    return record.acquired / record.total_realized * 100


def average_competency_level(record: CompetencyRecord) -> float | None:
    """Calculate the statutory average using attempted as the denominator."""
    if record.attempted == 0:
        return None
    return record.level_sum / record.attempted


def grade_requirements_met(target_grade: int, record: CompetencyRecord) -> bool:
    """Return whether the record meets every requirement for the target grade."""
    if type(target_grade) is not int or target_grade not in GRADE_REQUIREMENTS:
        raise ValueError("target_grade must be an integer from 2 to 6")
    requirement = GRADE_REQUIREMENTS[target_grade]

    if acquisition_percentage(record) < requirement.minimum_acquisition_percentage:
        return False
    if requirement.minimum_average_level is None:
        return True
    average = average_competency_level(record)
    return average is not None and average >= requirement.minimum_average_level
