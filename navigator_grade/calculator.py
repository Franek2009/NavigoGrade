from collections import Counter, defaultdict
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING

from .rules import GRADE_REQUIREMENTS, GradeRequirement


@dataclass(frozen=True)
class CompetencyRecord:
    """Overall course size and the competencies evaluated so far."""

    total_overall: int
    level_0: int
    level_1: int
    level_2: int
    level_3: int

    def __post_init__(self) -> None:
        values = (self.total_overall, *self.level_counts)
        if any(not isinstance(value, int) or isinstance(value, bool) for value in values):
            raise TypeError("competency counts must be integers")
        if self.total_overall < 0:
            raise ValueError("total_overall cannot be negative")
        if any(value < 0 for value in self.level_counts):
            raise ValueError("level counts cannot be negative")
        if self.evaluated > self.total_overall:
            raise ValueError("evaluated cannot exceed total_overall")

    @property
    def level_counts(self) -> tuple[int, int, int, int]:
        return self.level_0, self.level_1, self.level_2, self.level_3

    @property
    def evaluated(self) -> int:
        return sum(self.level_counts)

    @property
    def acquired(self) -> int:
        return self.level_1 + self.level_2 + self.level_3

    @property
    def remaining_future(self) -> int:
        return self.total_overall - self.evaluated

    @property
    def level_sum(self) -> int:
        return sum(level * count for level, count in enumerate(self.level_counts))


@dataclass(frozen=True)
class UpgradeOption:
    """A minimum-action plan using existing and/or future competencies."""

    upgrades: tuple[tuple[int, int, int], ...]
    future_acquisitions: tuple[tuple[int, int], ...]
    points_gained: int

    @property
    def competencies_changed(self) -> int:
        return sum(count for _, _, count in self.upgrades)

    @property
    def total_actions(self) -> int:
        return self.competencies_changed + sum(
            count for _, count in self.future_acquisitions
        )


@dataclass(frozen=True)
class GradeAnalysis:
    target_grade: int
    acquisition_requirement_met: bool | None
    average_requirement_met: bool | None
    additional_acquired_needed: int | None
    required_level_sum: int | None
    missing_level_points: int | None
    upgrade_options: tuple[UpgradeOption, ...]


def acquisition_percentage(record: CompetencyRecord) -> float | None:
    if record.evaluated == 0:
        return None
    return record.acquired / record.evaluated * 100


def average_competency_level(record: CompetencyRecord) -> float | None:
    if record.evaluated == 0:
        return None
    return record.level_sum / record.evaluated


def _requirement_for(target_grade: int) -> GradeRequirement:
    if type(target_grade) is not int or target_grade not in GRADE_REQUIREMENTS:
        raise ValueError("target_grade must be an integer from 2 to 6")
    return GRADE_REQUIREMENTS[target_grade]


def _ceiling_product(value: float, count: int, divisor: int = 1) -> int:
    result = Decimal(str(value)) * count / divisor
    return int(result.to_integral_value(rounding=ROUND_CEILING))


def _state_meets(state: tuple[int, int, int, int], requirement: GradeRequirement) -> bool:
    evaluated = sum(state)
    if evaluated == 0:
        return False
    acquired = state[1] + state[2] + state[3]
    if acquired < _ceiling_product(
        requirement.minimum_acquisition_percentage, evaluated, 100
    ):
        return False
    if requirement.minimum_average_level is None:
        return True
    level_sum = sum(level * count for level, count in enumerate(state))
    return level_sum >= _ceiling_product(requirement.minimum_average_level, evaluated)


def grade_requirements_met(target_grade: int, record: CompetencyRecord) -> bool:
    requirement = _requirement_for(target_grade)
    return _state_meets(record.level_counts, requirement)


Action = tuple[str, int, int]
ActionPlan = tuple[tuple[str, int, int, int], ...]


def _add_action(plan: ActionPlan, action: Action) -> ActionPlan:
    counts = Counter({item[:3]: item[3] for item in plan})
    counts[action] += 1
    return tuple((*key, count) for key, count in sorted(counts.items()))


def _next_states(
    state: tuple[int, int, int, int], total_overall: int
):
    for source in range(3):
        if state[source] == 0:
            continue
        for target in range(source + 1, 4):
            changed = list(state)
            changed[source] -= 1
            changed[target] += 1
            yield tuple(changed), ("existing", source, target)
    if sum(state) < total_overall:
        for target in range(1, 4):
            changed = list(state)
            changed[target] += 1
            yield tuple(changed), ("future", -1, target)


def _to_option(plan: ActionPlan) -> UpgradeOption:
    upgrades = tuple(
        (source, target, count)
        for kind, source, target, count in plan
        if kind == "existing"
    )
    future = tuple(
        (target, count)
        for kind, _, target, count in plan
        if kind == "future"
    )
    points = sum(
        (target - source if kind == "existing" else target) * count
        for kind, source, target, count in plan
    )
    return UpgradeOption(upgrades, future, points)


def _minimum_plans(
    record: CompetencyRecord, requirement: GradeRequirement, limit: int = 3
) -> tuple[UpgradeOption, ...]:
    start = record.level_counts
    if _state_meets(start, requirement):
        return ()

    layer: dict[tuple[int, int, int, int], set[ActionPlan]] = {start: {()}}
    seen_depth = {start: 0}
    depth = 0

    while layer:
        depth += 1
        next_layer: dict[tuple[int, int, int, int], set[ActionPlan]] = defaultdict(set)
        goals: list[tuple[tuple[int, int, int, int], ActionPlan]] = []
        for state, plans in layer.items():
            for next_state, action in _next_states(state, record.total_overall):
                previous_depth = seen_depth.get(next_state)
                if previous_depth is not None and previous_depth < depth:
                    continue
                seen_depth[next_state] = depth
                for plan in plans:
                    next_plan = _add_action(plan, action)
                    next_layer[next_state].add(next_plan)
                    if _state_meets(next_state, requirement):
                        goals.append((next_state, next_plan))
        if goals:
            unique_goals = {(state, plan) for state, plan in goals}
            def excess(item):
                state, plan = item
                evaluated = sum(state)
                level_sum = sum(level * count for level, count in enumerate(state))
                required_sum = (
                    _ceiling_product(requirement.minimum_average_level, evaluated)
                    if requirement.minimum_average_level is not None
                    else 0
                )
                return level_sum - required_sum

            minimum_excess = min(excess(item) for item in unique_goals)
            unique_goals = {
                item for item in unique_goals if excess(item) == minimum_excess
            }
            if any(
                not any(action[0] == "future" for action in plan)
                for _, plan in unique_goals
            ):
                unique_goals = {
                    (state, plan)
                    for state, plan in unique_goals
                    if not any(action[0] == "future" for action in plan)
                }

            ordered = sorted(unique_goals, key=lambda item: (len(item[1]), item[1]))
            return tuple(_to_option(plan) for _, plan in ordered[:limit])
        layer = next_layer
    return ()


def analyze_grade(target_grade: int, record: CompetencyRecord) -> GradeAnalysis:
    requirement = _requirement_for(target_grade)
    percentage = acquisition_percentage(record)
    average = average_competency_level(record)

    if record.evaluated == 0:
        acquisition_met = None
        average_met = None
        additional = None
        required_sum = None
        missing_points = None
    else:
        required_acquired = _ceiling_product(
            requirement.minimum_acquisition_percentage, record.evaluated, 100
        )
        acquisition_met = record.acquired >= required_acquired
        additional = max(0, required_acquired - record.acquired)
        if requirement.minimum_average_level is None:
            average_met = None
            required_sum = None
            missing_points = None
        else:
            required_sum = _ceiling_product(
                requirement.minimum_average_level, record.evaluated
            )
            average_met = average is not None and average >= requirement.minimum_average_level
            missing_points = max(0, required_sum - record.level_sum)

    return GradeAnalysis(
        target_grade,
        acquisition_met,
        average_met,
        additional,
        required_sum,
        missing_points,
        _minimum_plans(record, requirement),
    )


def highest_grade_met(record: CompetencyRecord) -> int | None:
    for grade in sorted(GRADE_REQUIREMENTS, reverse=True):
        if grade_requirements_met(grade, record):
            return grade
    return None
