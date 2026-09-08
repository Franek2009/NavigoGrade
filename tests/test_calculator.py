import unittest

from navigator_grade.calculator import (
    CompetencyRecord,
    acquisition_percentage,
    analyze_grade,
    average_competency_level,
    grade_requirements_met,
    highest_grade_met,
    future_outlook,
)


class CompetencyRecordTests(unittest.TestCase):
    def test_evaluated_includes_all_levels_but_acquired_excludes_level_zero(self) -> None:
        record = CompetencyRecord(12, 2, 1, 3, 4)
        self.assertEqual(record.evaluated, 10)
        self.assertEqual(record.acquired, 8)
        self.assertEqual(record.remaining_future, 2)

    def test_rejects_evaluated_above_total_overall(self) -> None:
        with self.assertRaises(ValueError):
            CompetencyRecord(3, 1, 1, 1, 1)

    def test_rejects_negative_and_non_integer_counts(self) -> None:
        for field in range(5):
            values = [5, 0, 0, 0, 0]
            values[field] = -1
            with self.subTest(field=field):
                with self.assertRaises(ValueError):
                    CompetencyRecord(*values)
        with self.assertRaises(TypeError):
            CompetencyRecord(5, 0, 0, 0, 1.5)  # type: ignore[arg-type]


class CurrentCalculationTests(unittest.TestCase):
    def test_percentage_uses_evaluated_not_total_overall(self) -> None:
        record = CompetencyRecord(20, 2, 2, 3, 3)
        self.assertEqual(acquisition_percentage(record), 80.0)

    def test_average_uses_all_evaluated_competencies(self) -> None:
        record = CompetencyRecord(20, 2, 2, 3, 3)
        self.assertEqual(average_competency_level(record), 1.7)

    def test_empty_evaluated_state_has_no_percentage_average_or_grade(self) -> None:
        record = CompetencyRecord(10, 0, 0, 0, 0)
        self.assertIsNone(acquisition_percentage(record))
        self.assertIsNone(average_competency_level(record))
        self.assertIsNone(highest_grade_met(record))
        self.assertFalse(grade_requirements_met(2, record))

    def test_exact_percentage_boundaries_are_inclusive(self) -> None:
        acquired_at_boundary = {2: 11, 3: 12, 4: 15, 5: 16, 6: 18}
        for grade, acquired in acquired_at_boundary.items():
            record = CompetencyRecord(20, 20 - acquired, 0, 0, acquired)
            with self.subTest(grade=grade):
                self.assertTrue(grade_requirements_met(grade, record))

    def test_just_below_percentage_boundaries_is_rejected(self) -> None:
        acquired_at_boundary = {2: 11, 3: 12, 4: 15, 5: 16, 6: 18}
        for grade, boundary in acquired_at_boundary.items():
            acquired = boundary - 1
            record = CompetencyRecord(20, 20 - acquired, 0, 0, acquired)
            with self.subTest(grade=grade):
                self.assertFalse(grade_requirements_met(grade, record))

    def test_exact_average_boundaries_are_inclusive(self) -> None:
        records = {
            3: CompetencyRecord(20, 0, 7, 13, 0),
            4: CompetencyRecord(20, 0, 1, 19, 0),
            5: CompetencyRecord(20, 0, 0, 15, 5),
            6: CompetencyRecord(10, 0, 0, 3, 7),
        }
        for grade, record in records.items():
            with self.subTest(grade=grade):
                self.assertTrue(grade_requirements_met(grade, record))

    def test_just_below_average_boundaries_is_rejected(self) -> None:
        records = {
            3: CompetencyRecord(20, 0, 8, 12, 0),
            4: CompetencyRecord(20, 0, 2, 18, 0),
            5: CompetencyRecord(20, 0, 0, 16, 4),
            6: CompetencyRecord(10, 0, 0, 4, 6),
        }
        for grade, record in records.items():
            with self.subTest(grade=grade):
                self.assertFalse(grade_requirements_met(grade, record))

    def test_grade_two_ignores_average(self) -> None:
        record = CompetencyRecord(20, 9, 11, 0, 0)
        self.assertTrue(grade_requirements_met(2, record))

    def test_rejects_invalid_target_grades(self) -> None:
        record = CompetencyRecord(1, 0, 0, 0, 1)
        for grade in (1, 7, 2.0, "2", True):
            with self.subTest(grade=grade):
                with self.assertRaises(ValueError):
                    grade_requirements_met(grade, record)  # type: ignore[arg-type]


class PlannerTests(unittest.TestCase):
    def test_acquiring_level_zero_is_distinct_from_improving_acquired_level(self) -> None:
        record = CompetencyRecord(10, 2, 0, 0, 8)

        plan = analyze_grade(6, record).upgrade_options[0]

        self.assertIn((0, 3, 1), plan.upgrades)
        self.assertEqual(plan.future_acquisitions, ())

    def test_level_one_and_level_two_improvements_are_both_available(self) -> None:
        record = CompetencyRecord(12, 0, 1, 2, 9)

        plans = analyze_grade(6, record).upgrade_options

        paths = [plan.upgrades for plan in plans]
        self.assertIn(((1, 2, 1),), paths)
        self.assertIn(((2, 3, 1),), paths)
        self.assertTrue(all(plan.total_actions == 1 for plan in plans))

    def test_future_competencies_are_not_used_when_existing_route_is_as_short(self) -> None:
        record = CompetencyRecord(14, 1, 1, 2, 8)

        plans = analyze_grade(6, record).upgrade_options

        self.assertTrue(plans)
        self.assertTrue(all(not plan.future_acquisitions for plan in plans))

    def test_future_competency_is_used_when_nothing_has_been_evaluated(self) -> None:
        record = CompetencyRecord(10, 0, 0, 0, 0)

        plan = analyze_grade(6, record).upgrade_options[0]

        self.assertEqual(plan.future_acquisitions, ((3, 1),))
        self.assertEqual(plan.upgrades, ())

    def test_future_competency_is_unavailable_when_all_are_evaluated(self) -> None:
        record = CompetencyRecord(12, 0, 1, 3, 8)

        plans = analyze_grade(6, record).upgrade_options

        self.assertTrue(plans)
        self.assertTrue(all(not plan.future_acquisitions for plan in plans))

    def test_plans_are_ranked_by_minimum_action_count(self) -> None:
        record = CompetencyRecord(12, 0, 1, 3, 8)
        plans = analyze_grade(6, record).upgrade_options
        self.assertTrue(all(plan.total_actions == 1 for plan in plans))

    def test_equal_action_plans_prefer_smaller_excess_points(self) -> None:
        record = CompetencyRecord(12, 0, 1, 2, 9)

        plans = analyze_grade(6, record).upgrade_options

        self.assertTrue(all(plan.points_gained == 1 for plan in plans))
        self.assertNotIn(((1, 3, 1),), [plan.upgrades for plan in plans])

    def test_analysis_reports_current_deficits(self) -> None:
        record = CompetencyRecord(10, 2, 1, 3, 2)
        analysis = analyze_grade(5, record)
        self.assertFalse(analysis.acquisition_requirement_met)
        self.assertFalse(analysis.average_requirement_met)
        self.assertEqual(analysis.additional_acquired_needed, 1)
        self.assertGreater(analysis.missing_level_points, 0)


class FutureSimulationTests(unittest.TestCase):
    def test_not_yet_met_target_gets_feasible_final_plan(self) -> None:
        record = CompetencyRecord(10, 2, 1, 3, 2)

        outlook = future_outlook(5, record)

        self.assertFalse(outlook.target_currently_met)
        self.assertIsNotNone(outlook.target_plan)
        self.assertGreaterEqual(outlook.target_plan.final_acquisition_percentage, 80)
        self.assertGreaterEqual(outlook.target_plan.final_average_level, 2.25)

    def test_met_target_gets_weakest_maintenance_plan_without_upgrades(self) -> None:
        record = CompetencyRecord(14, 0, 0, 0, 8)

        outlook = future_outlook(5, record)

        self.assertTrue(outlook.target_currently_met)
        self.assertEqual(outlook.target_plan.future_levels, (0, 4, 2, 0))
        self.assertEqual(outlook.target_plan.upgrades, ())
        self.assertGreaterEqual(outlook.target_plan.final_average_level, 2.25)

    def test_next_grade_includes_distance_and_reach_plan(self) -> None:
        record = CompetencyRecord(10, 2, 1, 3, 2)

        outlook = future_outlook(5, record)

        self.assertEqual(outlook.next_grade, 6)
        self.assertIsNotNone(outlook.next_grade_analysis)
        self.assertIsNotNone(outlook.next_grade_plan)
        self.assertGreaterEqual(outlook.next_grade_plan.final_average_level, 2.70)

    def test_zero_remaining_future_uses_empty_distribution(self) -> None:
        record = CompetencyRecord(10, 0, 0, 0, 10)

        outlook = future_outlook(5, record)

        self.assertEqual(outlook.target_plan.future_levels, (0, 0, 0, 0))
        self.assertEqual(outlook.target_plan.action_count, 0)

    def test_target_is_impossible_when_final_total_is_zero(self) -> None:
        record = CompetencyRecord(0, 0, 0, 0, 0)

        outlook = future_outlook(2, record)

        self.assertFalse(outlook.target_currently_met)
        self.assertIsNone(outlook.target_plan)

    def test_exact_final_percentage_and_average_boundaries_are_accepted(self) -> None:
        record = CompetencyRecord(20, 8, 0, 3, 9)

        outlook = future_outlook(3, record)

        self.assertTrue(outlook.target_currently_met)
        self.assertEqual(outlook.target_plan.final_acquisition_percentage, 60.0)
        self.assertEqual(outlook.target_plan.final_average_level, 1.65)


if __name__ == "__main__":
    unittest.main()
