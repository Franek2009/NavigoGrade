import unittest

from navigator_grade.calculator import CompetencyRecord
from navigator_grade.gui import format_results


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


if __name__ == "__main__":
    unittest.main()
