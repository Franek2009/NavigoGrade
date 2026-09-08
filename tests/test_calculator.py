import unittest

from navigator_grade.calculator import (
    CompetencyRecord,
    acquisition_percentage,
    average_competency_level,
    grade_requirements_met,
)
from navigator_grade.rules import GRADE_REQUIREMENTS, GradeRequirement


class GradeRequirementTests(unittest.TestCase):
    def test_grade_requirements_match_school_thresholds(self) -> None:
        expected = {
            2: GradeRequirement(2, 55.0, None),
            3: GradeRequirement(3, 60.0, 1.65),
            4: GradeRequirement(4, 75.0, 1.95),
            5: GradeRequirement(5, 80.0, 2.25),
            6: GradeRequirement(6, 90.0, 2.70),
        }
        self.assertEqual(GRADE_REQUIREMENTS, expected)


class CompetencyRecordTests(unittest.TestCase):
    def test_acquired_is_sum_of_all_levels_including_level_zero(self) -> None:
        record = CompetencyRecord(10, 8, 2, 1, 2, 1)
        self.assertEqual(record.acquired, 6)

    def test_rejects_non_positive_total_realized(self) -> None:
        for total_realized in (0, -1):
            with self.subTest(total_realized=total_realized):
                with self.assertRaises(ValueError):
                    CompetencyRecord(total_realized, 0, 0, 0, 0, 0)

    def test_rejects_negative_attempted(self) -> None:
        with self.assertRaises(ValueError):
            CompetencyRecord(3, -1, 0, 0, 0, 0)

    def test_rejects_negative_level_count(self) -> None:
        for level_index in range(4):
            levels = [0, 0, 0, 0]
            levels[level_index] = -1
            with self.subTest(level=level_index):
                with self.assertRaises(ValueError):
                    CompetencyRecord(3, 0, *levels)

    def test_rejects_non_integer_counts_including_booleans(self) -> None:
        invalid_values = (1.5, "1", True)
        for invalid_value in invalid_values:
            values = [5, 4, 1, 1, 1, 1]
            for field_index in range(len(values)):
                invalid_record = values.copy()
                invalid_record[field_index] = invalid_value
                with self.subTest(value=invalid_value, field=field_index):
                    with self.assertRaises(TypeError):
                        CompetencyRecord(*invalid_record)

    def test_rejects_more_acquired_than_attempted(self) -> None:
        with self.assertRaises(ValueError):
            CompetencyRecord(5, 3, 1, 1, 1, 1)

    def test_rejects_more_attempted_than_realized(self) -> None:
        with self.assertRaises(ValueError):
            CompetencyRecord(3, 4, 1, 1, 1, 1)

    def test_does_not_assume_attempted_equals_acquired(self) -> None:
        record = CompetencyRecord(10, 8, 1, 1, 1, 1)
        self.assertEqual(record.attempted, 8)
        self.assertEqual(record.acquired, 4)


class CalculationTests(unittest.TestCase):
    def test_acquisition_percentage_includes_level_zero(self) -> None:
        record = CompetencyRecord(10, 8, 2, 1, 2, 1)
        self.assertEqual(acquisition_percentage(record), 60.0)

    def test_average_uses_attempted_not_acquired_as_denominator(self) -> None:
        record = CompetencyRecord(10, 8, 2, 1, 2, 1)
        self.assertEqual(average_competency_level(record), 1.0)

    def test_zero_attempts_returns_no_average(self) -> None:
        record = CompetencyRecord(5, 0, 0, 0, 0, 0)
        self.assertIsNone(average_competency_level(record))

    def test_grade_two_uses_acquisition_percentage_only(self) -> None:
        record = CompetencyRecord(20, 11, 11, 0, 0, 0)
        self.assertTrue(grade_requirements_met(2, record))

    def test_exact_percentage_boundaries_are_inclusive(self) -> None:
        acquired_at_boundary = {2: 11, 3: 12, 4: 15, 5: 16, 6: 18}
        for grade, acquired in acquired_at_boundary.items():
            record = CompetencyRecord(20, acquired, 0, 0, 0, acquired)
            with self.subTest(grade=grade):
                self.assertTrue(grade_requirements_met(grade, record))

    def test_just_below_each_percentage_boundary_is_rejected(self) -> None:
        acquired_at_boundary = {2: 11, 3: 12, 4: 15, 5: 16, 6: 18}
        for grade, boundary in acquired_at_boundary.items():
            acquired = boundary - 1
            record = CompetencyRecord(20, acquired, 0, 0, 0, acquired)
            with self.subTest(grade=grade):
                self.assertFalse(grade_requirements_met(grade, record))

    def test_exact_average_boundaries_are_inclusive(self) -> None:
        records = {
            3: CompetencyRecord(20, 20, 0, 7, 13, 0),   # 33 / 20 = 1.65
            4: CompetencyRecord(20, 20, 0, 1, 19, 0),   # 39 / 20 = 1.95
            5: CompetencyRecord(20, 20, 0, 0, 15, 5),   # 45 / 20 = 2.25
            6: CompetencyRecord(10, 10, 0, 0, 3, 7),    # 27 / 10 = 2.70
        }
        for grade, record in records.items():
            with self.subTest(grade=grade):
                self.assertTrue(grade_requirements_met(grade, record))

    def test_just_below_each_average_boundary_is_rejected(self) -> None:
        records = {
            3: CompetencyRecord(20, 20, 0, 8, 12, 0),   # 32 / 20 = 1.60
            4: CompetencyRecord(20, 20, 0, 2, 18, 0),   # 38 / 20 = 1.90
            5: CompetencyRecord(20, 20, 0, 0, 16, 4),   # 44 / 20 = 2.20
            6: CompetencyRecord(10, 10, 0, 0, 4, 6),    # 26 / 10 = 2.60
        }
        for grade, record in records.items():
            with self.subTest(grade=grade):
                self.assertFalse(grade_requirements_met(grade, record))

    def test_zero_attempts_cannot_meet_grade_requiring_average(self) -> None:
        record = CompetencyRecord(5, 0, 0, 0, 0, 0)
        self.assertFalse(grade_requirements_met(3, record))

    def test_both_requirements_must_be_met_for_higher_grade(self) -> None:
        meets = CompetencyRecord(10, 10, 0, 0, 1, 8)
        low_average = CompetencyRecord(10, 10, 8, 0, 0, 0)
        self.assertTrue(grade_requirements_met(5, meets))
        self.assertFalse(grade_requirements_met(5, low_average))

    def test_rejects_target_grades_outside_two_to_six(self) -> None:
        record = CompetencyRecord(1, 1, 0, 0, 0, 1)
        for grade in (1, 7):
            with self.subTest(grade=grade):
                with self.assertRaises(ValueError):
                    grade_requirements_met(grade, record)

    def test_rejects_non_integer_target_grade(self) -> None:
        record = CompetencyRecord(1, 1, 0, 0, 0, 1)
        for grade in (2.0, "2", True):
            with self.subTest(grade=grade):
                with self.assertRaises(ValueError):
                    grade_requirements_met(grade, record)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
