from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING

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


@dataclass(frozen=True)
class UpgradeOption:
    """A way to gain level-points by moving acquired competencies to level 3."""

    upgrades: tuple[tuple[int, int], ...]
    points_gained: int

    @property
    def competencies_changed(self) -> int:
        return sum(count for _, count in self.upgrades)


@dataclass(frozen=True)
class GradeAnalysis:
    """Current results and independent deficits for one target grade."""

    target_grade: int
    acquisition_requirement_met: bool
    average_requirement_met: bool | None
    additional_acquired_needed: int
    required_level_sum: int | None
    missing_level_points: int | None
    upgrade_options: tuple[UpgradeOption, ...]


def acquisition_percentage(record: CompetencyRecord) -> float:
    """Return acquired competencies as a percentage of those realized."""
    return record.acquired / record.total_realized * 100


def average_competency_level(record: CompetencyRecord) -> float | None:
    """Calculate the statutory average using attempted as the denominator."""
    if record.attempted == 0:
        return None
    return record.level_sum / record.attempted


def _requirement_for(target_grade: int):
    if type(target_grade) is not int or target_grade not in GRADE_REQUIREMENTS:
        raise ValueError("target_grade must be an integer from 2 to 6")
    return GRADE_REQUIREMENTS[target_grade]


def grade_requirements_met(target_grade: int, record: CompetencyRecord) -> bool:
    """Return whether the record meets every requirement for the target grade."""
    requirement = _requirement_for(target_grade)

    if acquisition_percentage(record) < requirement.minimum_acquisition_percentage:
        return False
    if requirement.minimum_average_level is None:
        return True
    average = average_competency_level(record)
    return average is not None and average >= requirement.minimum_average_level


def _ceiling_product(value: float, count: int, divisor: int = 1) -> int:
    result = Decimal(str(value)) * count / divisor
    return int(result.to_integral_value(rounding=ROUND_CEILING))


def _upgrade_options(
    record: CompetencyRecord, missing_points: int, limit: int = 3
) -> tuple[UpgradeOption, ...]:
    if missing_points <= 0:
        return ()

    candidates: list[UpgradeOption] = []
    for from_level_0 in range(record.level_0 + 1):
        for from_level_1 in range(record.level_1 + 1):
            points_before_level_2 = 3 * from_level_0 + 2 * from_level_1
            still_missing = max(0, missing_points - points_before_level_2)
            from_level_2 = min(record.level_2, still_missing)
            points = points_before_level_2 + from_level_2
            if points < missing_points:
                continue
            upgrades = tuple(
                (level, count)
                for level, count in enumerate(
                    (from_level_0, from_level_1, from_level_2)
                )
                if count
            )
            candidates.append(UpgradeOption(upgrades, points))

    candidates.sort(
        key=lambda option: (
            option.competencies_changed,
            option.points_gained - missing_points,
            option.upgrades,
        )
    )
    return tuple(candidates[:limit])


def analyze_grade(target_grade: int, record: CompetencyRecord) -> GradeAnalysis:
    """Calculate requirement status, deficits, and practical level upgrades."""
    requirement = _requirement_for(target_grade)
    required_acquired = _ceiling_product(
        requirement.minimum_acquisition_percentage, record.total_realized, 100
    )
    additional_acquired = max(0, required_acquired - record.acquired)
    acquisition_met = additional_acquired == 0

    if requirement.minimum_average_level is None:
        return GradeAnalysis(
            target_grade,
            acquisition_met,
            None,
            additional_acquired,
            None,
            None,
            (),
        )

    average = average_competency_level(record)
    if average is None:
        return GradeAnalysis(
            target_grade,
            acquisition_met,
            False,
            additional_acquired,
            None,
            None,
            (),
        )

    required_level_sum = _ceiling_product(
        requirement.minimum_average_level, record.attempted
    )
    missing_points = max(0, required_level_sum - record.level_sum)
    return GradeAnalysis(
        target_grade,
        acquisition_met,
        missing_points == 0,
        additional_acquired,
        required_level_sum,
        missing_points,
        _upgrade_options(record, missing_points),
    )


def highest_grade_met(record: CompetencyRecord) -> int | None:
    """Return the highest configured grade met, or None when grade 2 is not met."""
    for grade in sorted(GRADE_REQUIREMENTS, reverse=True):
        if grade_requirements_met(grade, record):
            return grade
    return None
