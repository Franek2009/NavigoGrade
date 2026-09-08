import unittest

from navigator_grade.calculator import (
    CompetencyRecord,
    acquisition_percentage,
    analyze_grade,
    average_competency_level,
    grade_requirements_met,
    highest_grade_met,
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


class RecommendationTests(unittest.TestCase):
    def test_example_reports_two_missing_points_and_minimal_options(self) -> None:
        record = CompetencyRecord(12, 12, 0, 1, 3, 8)

        analysis = analyze_grade(6, record)

        self.assertTrue(analysis.acquisition_requirement_met)
        self.assertFalse(analysis.average_requirement_met)
        self.assertEqual(analysis.additional_acquired_needed, 0)
        self.assertEqual(analysis.required_level_sum, 33)
        self.assertEqual(analysis.missing_level_points, 2)
        self.assertEqual(analysis.upgrade_options[0].upgrades, ((1, 1),))
        self.assertEqual(analysis.upgrade_options[1].upgrades, ((2, 2),))

    def test_percentage_deficit_uses_ceiling(self) -> None:
        record = CompetencyRecord(12, 10, 0, 0, 0, 10)

        analysis = analyze_grade(6, record)

        self.assertFalse(analysis.acquisition_requirement_met)
        self.assertEqual(analysis.additional_acquired_needed, 1)

    def test_no_upgrade_ever_uses_level_three_as_a_source(self) -> None:
        record = CompetencyRecord(5, 5, 0, 1, 1, 3)

        analysis = analyze_grade(6, record)

        for option in analysis.upgrade_options:
            self.assertTrue(all(level < 3 for level, _ in option.upgrades))

    def test_options_prefer_fewer_changed_competencies(self) -> None:
        record = CompetencyRecord(12, 12, 1, 1, 3, 7)

        analysis = analyze_grade(6, record)

        changed_counts = [
            option.competencies_changed for option in analysis.upgrade_options
        ]
        self.assertEqual(changed_counts, sorted(changed_counts))

    def test_dominated_same_path_option_is_removed(self) -> None:
        record = CompetencyRecord(10, 10, 0, 4, 0, 6)

        analysis = analyze_grade(6, record)

        self.assertEqual(analysis.missing_level_points, 5)
        self.assertEqual(
            [option.upgrades for option in analysis.upgrade_options],
            [((1, 3),)],
        )

    def test_distinct_pure_and_mixed_upgrade_paths_are_preserved(self) -> None:
        record = CompetencyRecord(10, 10, 0, 3, 2, 5)

        analysis = analyze_grade(6, record)

        self.assertEqual(analysis.missing_level_points, 5)
        options = [option.upgrades for option in analysis.upgrade_options]
        self.assertIn(((1, 3),), options)
        self.assertIn(((1, 2), (2, 1)), options)

    def test_grade_two_analysis_has_no_average_deficit(self) -> None:
        record = CompetencyRecord(20, 11, 11, 0, 0, 0)

        analysis = analyze_grade(2, record)

        self.assertTrue(analysis.acquisition_requirement_met)
        self.assertIsNone(analysis.average_requirement_met)
        self.assertIsNone(analysis.required_level_sum)
        self.assertIsNone(analysis.missing_level_points)
        self.assertEqual(analysis.upgrade_options, ())

    def test_zero_attempts_projects_required_acquisitions_before_average(self) -> None:
        record = CompetencyRecord(5, 0, 0, 0, 0, 0)

        analysis = analyze_grade(3, record)

        self.assertFalse(analysis.average_requirement_met)
        self.assertEqual(analysis.additional_acquired_needed, 3)
        self.assertEqual(analysis.required_level_sum, 5)
        self.assertEqual(analysis.missing_level_points, 5)
        self.assertTrue(analysis.upgrade_options)

    def test_new_acquisition_increases_average_denominator_when_needed(self) -> None:
        record = CompetencyRecord(10, 7, 0, 0, 7, 0)

        analysis = analyze_grade(5, record)

        self.assertFalse(analysis.acquisition_requirement_met)
        self.assertFalse(analysis.average_requirement_met)
        self.assertEqual(analysis.additional_acquired_needed, 1)
        self.assertEqual(analysis.required_level_sum, 18)  # ceil(2.25 * 8)
        self.assertEqual(analysis.missing_level_points, 4)

    def test_existing_unacquired_attempt_does_not_increase_denominator(self) -> None:
        record = CompetencyRecord(10, 8, 0, 0, 7, 0)

        analysis = analyze_grade(5, record)

        self.assertEqual(analysis.additional_acquired_needed, 1)
        self.assertEqual(analysis.required_level_sum, 18)  # still 8 attempted
        self.assertEqual(analysis.missing_level_points, 4)

    def test_new_competency_levels_are_optimized_with_existing_upgrades(self) -> None:
        record = CompetencyRecord(10, 7, 0, 0, 0, 7)

        analysis = analyze_grade(6, record)

        self.assertEqual(analysis.additional_acquired_needed, 2)
        self.assertEqual(analysis.required_level_sum, 25)  # ceil(2.70 * 9)
        self.assertEqual(analysis.missing_level_points, 4)
        self.assertEqual(analysis.upgrade_options[0].acquisitions, ((2, 2),))
        self.assertEqual(analysis.upgrade_options[0].upgrades, ())
        self.assertEqual(analysis.upgrade_options[0].total_actions, 2)

    def test_combined_plan_optimizes_acquisition_level_and_existing_upgrades(self) -> None:
        record = CompetencyRecord(14, 12, 0, 4, 0, 8)

        analysis = analyze_grade(6, record)

        self.assertEqual(analysis.additional_acquired_needed, 1)
        self.assertEqual(analysis.required_level_sum, 36)  # ceil(2.70 * 13)
        best = analysis.upgrade_options[0]
        self.assertEqual(best.acquisitions, ((2, 1),))
        self.assertEqual(best.upgrades, ((1, 3),))
        self.assertEqual(best.total_actions, 4)
        self.assertEqual(record.level_sum + best.points_gained, 36)

    def test_conservative_level_zero_plan_is_removed_when_more_costly(self) -> None:
        record = CompetencyRecord(14, 12, 0, 4, 0, 8)

        options = analyze_grade(6, record).upgrade_options

        self.assertNotIn(
            (((0, 1),), ((1, 4),)),
            [(option.acquisitions, option.upgrades) for option in options],
        )

    def test_highest_grade_met_matches_example(self) -> None:
        record = CompetencyRecord(12, 12, 0, 1, 3, 8)
        self.assertEqual(highest_grade_met(record), 5)


if __name__ == "__main__":
    unittest.main()
