import unittest

from navigator_grade.calculator import CompetencyRecord
from navigator_grade.gui import format_results, parse_gui_input


class GuiInputParsingTests(unittest.TestCase):
    def test_all_empty_level_fields_become_zero(self) -> None:
        record, grade = parse_gui_input("10", ("", "", "", ""), "4")
        self.assertEqual(record.level_counts, (0, 0, 0, 0))
        self.assertEqual(grade, 4)

    def test_some_empty_level_fields_become_zero(self) -> None:
        record, grade = parse_gui_input("12", ("", "2", "", "5"), "6")
        self.assertEqual(record.level_counts, (0, 2, 0, 5))
        self.assertEqual(grade, 6)

    def test_non_numeric_non_empty_level_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            parse_gui_input("10", ("", "abc", "2", "3"), "5")

    def test_total_and_target_remain_required(self) -> None:
        with self.assertRaises(ValueError):
            parse_gui_input("", ("", "", "", ""), "5")
        with self.assertRaises(ValueError):
            parse_gui_input("10", ("", "", "", ""), "")


class GuiResultFormattingTests(unittest.TestCase):
    def test_shows_success_for_met_target(self) -> None:
        result = format_results(CompetencyRecord(10, 0, 0, 0, 10), 6)
        self.assertIn("Ocena obecna: 6", result)
        self.assertIn("Zdobyte kompetencje: 10/10", result)
        self.assertIn("Procent zdobytych: 100.00%", result)
        self.assertIn("Spełniasz wymagania na ocenę 6.", result)

    def test_empty_state_shows_unavailable_current_values(self) -> None:
        result = format_results(CompetencyRecord(10, 0, 0, 0, 0), 4)
        self.assertIn("Procent zdobytych: brak danych", result)
        self.assertIn("Średnia poziomu: brak", result)

    def test_recommendations_come_from_corrected_planner(self) -> None:
        result = format_results(CompetencyRecord(10, 2, 1, 3, 2), 5)
        self.assertIn("Co trzeba poprawić", result)
        self.assertIn("Najprościej", result)

    def test_shows_maintenance_and_next_grade_motivation(self) -> None:
        result = format_results(CompetencyRecord(14, 0, 0, 0, 8), 5)
        self.assertIn("Aby utrzymać 5:", result)
        self.assertIn("Do oceny 6 brakuje:", result)
        self.assertIn("obecnie spełniasz wymagania; plan końcowy", result)


if __name__ == "__main__":
    unittest.main()
