import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from navigator_grade.cli import _polish_plural, parse_compact_input, run


class CompactInputTests(unittest.TestCase):
    def test_six_values_infer_attempted_when_all_are_acquired(self) -> None:
        record, target_grade = parse_compact_input("12 0 1 3 8 6")

        self.assertEqual(record.total_realized, 12)
        self.assertEqual(record.attempted, 12)
        self.assertEqual(record.level_counts, (0, 1, 3, 8))
        self.assertEqual(target_grade, 6)

    def test_seven_values_use_explicit_attempted(self) -> None:
        record, target_grade = parse_compact_input("20 16 0 1 5 10 4")

        self.assertEqual(record.total_realized, 20)
        self.assertEqual(record.attempted, 16)
        self.assertEqual(record.level_counts, (0, 1, 5, 10))
        self.assertEqual(target_grade, 4)

    def test_accepts_pipe_separators(self) -> None:
        record, target_grade = parse_compact_input("12 | 0 | 1 | 3 | 8 | 6")

        self.assertEqual(record.level_counts, (0, 1, 3, 8))
        self.assertEqual(record.attempted, 12)
        self.assertEqual(target_grade, 6)

    def test_six_values_reject_ambiguous_attempted_count(self) -> None:
        with self.assertRaises(ValueError):
            parse_compact_input("20 0 1 5 10 4")

    def test_rejects_wrong_number_of_values(self) -> None:
        for text in ("", "12 0 1 3 8", "12 12 0 1 3 8 6 9"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_compact_input(text)

    def test_rejects_non_integer_values(self) -> None:
        with self.assertRaises(ValueError):
            parse_compact_input("12 0 1 two 8 6")

    def test_rejects_target_grade_outside_range(self) -> None:
        for grade in (1, 7):
            with self.subTest(grade=grade):
                with self.assertRaises(ValueError):
                    parse_compact_input(f"12 0 1 3 8 {grade}")

    def test_rejects_invalid_competency_relationships(self) -> None:
        invalid_inputs = (
            "20 15 0 1 5 10 4",  # acquired > attempted
            "20 21 0 1 5 10 4",  # attempted > total
            "20 16 0 -1 5 10 4",  # negative level count
            "0 0 0 0 0 2",  # total must be positive
        )
        for text in invalid_inputs:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_compact_input(text)


class CliOutputTests(unittest.TestCase):
    def test_polish_plural_forms(self) -> None:
        cases = {
            1: ("punkt", "kompetencja"),
            2: ("punkty", "kompetencje"),
            4: ("punkty", "kompetencje"),
            5: ("punktów", "kompetencji"),
            12: ("punktów", "kompetencji"),
            22: ("punkty", "kompetencje"),
        }
        for count, (point, competency) in cases.items():
            with self.subTest(count=count):
                self.assertEqual(
                    _polish_plural(count, "punkt", "punkty", "punktów"), point
                )
                self.assertEqual(
                    _polish_plural(
                        count, "kompetencja", "kompetencje", "kompetencji"
                    ),
                    competency,
                )

    def test_result_layout_and_singular_recommendations(self) -> None:
        output = StringIO()
        with patch("builtins.input", return_value="12 | 0 | 1 | 2 | 9 | 6"):
            with redirect_stdout(output):
                run()

        result = output.getvalue()
        self.assertIn("Ocena obecna: 5\nCel: 6", result)
        self.assertIn("Zdobyte kompetencje: 12/12 (100%) ✓", result)
        self.assertIn("Średnia poziomu: 2.67 / 2.70 ✗", result)
        self.assertIn("Brakuje 1 punktu poziomu.", result)
        self.assertIn("→ 1 kompetencja: 2 → 3", result)
        self.assertIn("→ 1 kompetencja: 1 → 3", result)

    def test_startup_explains_both_compact_formats(self) -> None:
        output = StringIO()
        with patch("builtins.input", return_value="12 0 1 2 9 6"):
            with redirect_stdout(output):
                run()

        result = output.getvalue()
        self.assertIn(
            "wszystkie | poziom 0 | poziom 1 | poziom 2 | poziom 3 | cel",
            result,
        )
        self.assertIn("12 | 0 | 1 | 3 | 8 | 6", result)
        self.assertIn(
            "wszystkie | przystąpiono | poziom 0 | poziom 1 | poziom 2 | "
            "poziom 3 | cel",
            result,
        )
        self.assertIn("20 | 16 | 0 | 1 | 5 | 10 | 4", result)

    def test_combined_plan_prints_each_action_on_separate_line(self) -> None:
        output = StringIO()
        with patch(
            "builtins.input", return_value="14 | 12 | 0 | 4 | 0 | 8 | 6"
        ):
            with redirect_stdout(output):
                run()

        result = output.getvalue()
        self.assertIn(
            "Najprościej:\n"
            "→ zdobądź 1 nową kompetencję na poziomie co najmniej 2\n"
            "→ popraw 3 kompetencje z poziomu 1 na 3",
            result,
        )
        self.assertNotIn("co najmniej 2 oraz 3 kompetencje", result)

    def test_guided_flow_uses_expected_prompts(self) -> None:
        answers = ["", "10", "0 4 2 2", "", "5"]
        with patch("builtins.input", side_effect=answers) as mocked_input:
            with redirect_stdout(StringIO()):
                run()

        prompts = [call.args[0] for call in mocked_input.call_args_list]
        self.assertEqual(
            prompts,
            [
                "> ",
                "Wszystkich kompetencji: ",
                "Poziomy 0 1 2 3: ",
                "Przystąpiono [10]: ",
                "Cel: ",
            ],
        )

    def test_invalid_attempted_reprompts_only_attempted(self) -> None:
        answers = ["", "10", "0 4 2 2", "7", "11", "9", "5"]
        output = StringIO()
        with patch("builtins.input", side_effect=answers) as mocked_input:
            with redirect_stdout(output):
                run()

        prompts = [call.args[0] for call in mocked_input.call_args_list]
        self.assertEqual(prompts.count("Wszystkich kompetencji: "), 1)
        self.assertEqual(prompts.count("Poziomy 0 1 2 3: "), 1)
        self.assertEqual(prompts.count("Przystąpiono [10]: "), 3)
        self.assertIn("nie może być mniejsza", output.getvalue())
        self.assertIn("nie może przekraczać", output.getvalue())

    def test_invalid_levels_reprompt_only_levels(self) -> None:
        answers = ["", "10", "0 4 2 2 1", "0 4 2 2", "", "5"]
        with patch("builtins.input", side_effect=answers) as mocked_input:
            with redirect_stdout(StringIO()):
                run()

        prompts = [call.args[0] for call in mocked_input.call_args_list]
        self.assertEqual(prompts.count("Wszystkich kompetencji: "), 1)
        self.assertEqual(prompts.count("Poziomy 0 1 2 3: "), 2)

if __name__ == "__main__":
    unittest.main()
