import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

from navigator_grade.calculator import UpgradeOption
from navigator_grade.cli import _format_upgrade, parse_compact_input, run


class CompactInputTests(unittest.TestCase):
    def test_parses_six_values_with_spaces_or_pipes(self) -> None:
        for text in ("12 0 1 3 8 6", "12 | 0 | 1 | 3 | 8 | 6"):
            with self.subTest(text=text):
                record, grade = parse_compact_input(text)
                self.assertEqual(record.total_overall, 12)
                self.assertEqual(record.level_counts, (0, 1, 3, 8))
                self.assertEqual(record.evaluated, 12)
                self.assertEqual(record.acquired, 12)
                self.assertEqual(grade, 6)

    def test_rejects_old_seven_value_format(self) -> None:
        with self.assertRaises(ValueError):
            parse_compact_input("20 16 0 1 5 10 4")

    def test_rejects_invalid_input(self) -> None:
        invalid = (
            "",
            "12 0 1 3 8",
            "12 0 1 two 8 6",
            "3 1 1 1 1 4",
            "12 0 1 3 8 7",
        )
        for text in invalid:
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_compact_input(text)


class CliTests(unittest.TestCase):
    def test_startup_advertises_only_the_six_value_format(self) -> None:
        output = StringIO()
        with patch("builtins.input", return_value="12 0 1 2 9 6"):
            with redirect_stdout(output):
                run()
        result = output.getvalue()
        self.assertIn(
            "wszystkie | poziom 0 | poziom 1 | poziom 2 | poziom 3 | cel",
            result,
        )
        self.assertNotIn("przystąpiono", result.lower())

    def test_empty_compact_input_uses_guided_flow_without_attempted(self) -> None:
        answers = ["", "10", "0 4 2 2", "5"]
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
                "Cel: ",
            ],
        )

    def test_formats_existing_level_zero_and_future_actions_distinctly(self) -> None:
        option = UpgradeOption(
            upgrades=((0, 2, 1), (1, 3, 2)),
            future_acquisitions=((3, 1),),
            points_gained=9,
        )
        result = _format_upgrade(option)
        self.assertIn("zdobądź 1 przyszłą kompetencję", result)
        self.assertIn("zdobądź 1 kompetencję z poziomu 0", result)
        self.assertIn("popraw 2 kompetencje: 1 → 3", result)


if __name__ == "__main__":
    unittest.main()
