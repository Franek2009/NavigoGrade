from .calculator import (
    CompetencyRecord,
    FutureOutlook,
    FuturePlan,
    UpgradeOption,
    acquisition_percentage,
    analyze_grade,
    average_competency_level,
    highest_grade_met,
    future_outlook,
)
from .rules import GRADE_REQUIREMENTS


def parse_compact_input(text: str) -> tuple[CompetencyRecord, int]:
    """Parse the six-value compact CLI format."""
    try:
        values = [int(value) for value in text.replace("|", " ").split()]
    except ValueError as error:
        raise ValueError("Wszystkie wartości muszą być liczbami całkowitymi.") from error

    if len(values) != 6:
        raise ValueError("Podaj dokładnie 6 liczb.")
    total_overall, level_0, level_1, level_2, level_3, target_grade = values

    if target_grade not in GRADE_REQUIREMENTS:
        raise ValueError("Ocena docelowa musi mieścić się w zakresie 2-6.")

    try:
        record = CompetencyRecord(
            total_overall, level_0, level_1, level_2, level_3
        )
    except (TypeError, ValueError) as error:
        raise ValueError(str(error)) from error
    return record, target_grade


def _read_positive_integer(prompt: str) -> int:
    while True:
        try:
            value = int(input(prompt))
            if value <= 0:
                raise ValueError
            return value
        except ValueError:
            print("Wpisz dodatnią liczbę całkowitą.")


def _read_bounded_integer(prompt: str, minimum: int, maximum: int) -> int:
    while True:
        try:
            value = int(input(prompt))
            if not minimum <= value <= maximum:
                raise ValueError
            return value
        except ValueError:
            print(f"Wpisz liczbę całkowitą od {minimum} do {maximum}.")


def _read_levels(total_overall: int) -> tuple[int, int, int, int]:
    while True:
        try:
            values = tuple(int(value) for value in input("Poziomy 0 1 2 3: ").split())
            if len(values) != 4 or any(value < 0 for value in values):
                raise ValueError
            if sum(values) > total_overall:
                print("Liczba ocenionych kompetencji nie może przekraczać wszystkich.")
                continue
            return values  # type: ignore[return-value]
        except ValueError:
            print("Wpisz cztery nieujemne liczby całkowite oddzielone spacjami.")


def _format_upgrade(option: UpgradeOption) -> str:
    parts = []
    for level, count in option.future_acquisitions:
        noun = _polish_plural(
            count,
            "przyszłą kompetencję",
            "przyszłe kompetencje",
            "przyszłych kompetencji",
        )
        parts.append(f"zdobądź {count} {noun} na poziomie co najmniej {level}")
    for source, target, count in option.upgrades:
        if source == 0:
            noun = _polish_plural(
                count, "kompetencję", "kompetencje", "kompetencji"
            )
            parts.append(
                f"zdobądź {count} {noun} z poziomu 0 na poziomie co najmniej {target}"
            )
        else:
            noun = _polish_plural(count, "kompetencję", "kompetencje", "kompetencji")
            parts.append(f"popraw {count} {noun}: {source} → {target}")
    separator = "\n→ " if len(parts) > 1 else ""
    return separator.join(parts)


def _polish_plural(count: int, singular: str, few: str, many: str) -> str:
    if count == 1:
        return singular
    if count % 100 not in (12, 13, 14) and count % 10 in (2, 3, 4):
        return few
    return many


def _format_future_actions(plan: FuturePlan) -> list[str]:
    lines = []
    for level, count in enumerate(plan.future_levels):
        if count:
            lines.append(f"→ {count} × przyszła kompetencja na poziomie {level}")
    if plan.upgrades:
        option = UpgradeOption(plan.upgrades, (), 0)
        lines.extend(f"→ {part}" for part in _format_upgrade(option).split("\n→ "))
    return lines


def _format_future_outlook(outlook: FutureOutlook, remaining_future: int) -> str:
    lines = []
    if outlook.target_currently_met:
        lines.append(f"Aby utrzymać {outlook.target_grade}:")
        if outlook.target_plan is None:
            lines.append("→ brak możliwego planu końcowego")
        elif remaining_future == 0:
            lines.append("→ nie pozostały żadne przyszłe kompetencje")
        else:
            lines.append(f"→ z pozostałych {remaining_future} kompetencji wystarczy:")
            for level, count in enumerate(outlook.target_plan.future_levels):
                if count:
                    lines.append(f"   {count} × poziom {level}")
    else:
        lines.append(f"Aby zdobyć {outlook.target_grade}:")
        if outlook.target_plan is None:
            lines.append("→ osiągnięcie tej oceny nie jest możliwe")
        else:
            lines.extend(_format_future_actions(outlook.target_plan))

    if outlook.next_grade is not None:
        lines.extend(["", f"Do oceny {outlook.next_grade} brakuje:"])
        next_analysis = outlook.next_grade_analysis
        if next_analysis.acquisition_requirement_met is None:
            lines.append("— brak ocenionych kompetencji do bieżącego porównania")
        else:
            if next_analysis.additional_acquired_needed:
                lines.append(
                    f"— {next_analysis.additional_acquired_needed} "
                    "zdobytych kompetencji w bieżącym stanie"
                )
            if next_analysis.missing_level_points:
                lines.append(
                    f"— {next_analysis.missing_level_points} punktów poziomu "
                    "w bieżącym stanie"
                )
            if (
                next_analysis.acquisition_requirement_met
                and next_analysis.average_requirement_met is not False
            ):
                lines.append("— obecnie spełniasz wymagania; plan końcowy:")
        if outlook.next_grade_plan is None:
            lines.append("→ osiągnięcie tej oceny nie jest możliwe")
        else:
            lines.extend(_format_future_actions(outlook.next_grade_plan))
    return "\n".join(lines)


def _read_interactively() -> tuple[CompetencyRecord, int]:
    total_overall = _read_positive_integer("Wszystkich kompetencji: ")
    levels = _read_levels(total_overall)
    target_grade = _read_bounded_integer("Cel: ", 2, 6)
    return CompetencyRecord(total_overall, *levels), target_grade


def run() -> None:
    print("NavigoGrade\n")
    print("Format:")
    print("wszystkie | poziom 0 | poziom 1 | poziom 2 | poziom 3 | cel")
    print("\nPrzykład:")
    print("12 | 0 | 1 | 3 | 8 | 6")
    print()

    while True:
        compact_input = input("> ").strip()
        if not compact_input:
            record, target_grade = _read_interactively()
            break
        try:
            record, target_grade = parse_compact_input(compact_input)
            break
        except ValueError as error:
            print(f"Błąd: {error}")

    analysis = analyze_grade(target_grade, record)
    outlook = future_outlook(target_grade, record)
    average = average_competency_level(record)
    current_grade = highest_grade_met(record)
    requirement = GRADE_REQUIREMENTS[target_grade]

    current_grade_text = str(current_grade) if current_grade is not None else "poniżej 2"
    average_text = f"{average:.2f}" if average is not None else "brak danych"
    print(f"\nOcena obecna: {current_grade_text}")
    print(f"Cel: {target_grade}")

    acquisition_mark = (
        "✓" if analysis.acquisition_requirement_met else "✗"
        if analysis.acquisition_requirement_met is not None else "—"
    )
    percentage = acquisition_percentage(record)
    percentage_text = f"{percentage:.0f}%" if percentage is not None else "brak danych"
    print(
        f"Zdobyte kompetencje: {record.acquired}/{record.evaluated} "
        f"({percentage_text}) {acquisition_mark}"
    )
    if analysis.average_requirement_met is not None:
        average_mark = "✓" if analysis.average_requirement_met else "✗"
        print(
            f"Średnia poziomu: {average_text} / "
            f"{requirement.minimum_average_level:.2f} {average_mark}"
        )
    else:
        print(f"Średnia poziomu: {average_text} (brak wymogu dla oceny 2)")

    if analysis.additional_acquired_needed:
        competency_word = _polish_plural(
            analysis.additional_acquired_needed,
            "kompetencja",
            "kompetencje",
            "kompetencji",
        )
        print(
            f"\nDo zdobycia: {analysis.additional_acquired_needed} "
            f"{competency_word}."
        )

    if analysis.missing_level_points:
        # "Brakuje" takes the genitive: punktu / punktów.
        genitive_word = "punktu" if analysis.missing_level_points == 1 else "punktów"
        print(
            f"\nBrakuje {analysis.missing_level_points} "
            f"{genitive_word} poziomu."
        )
        if analysis.upgrade_options:
            print("\nNajprościej:")
            print(f"→ {_format_upgrade(analysis.upgrade_options[0])}")
            if len(analysis.upgrade_options) > 1:
                print("\nAlternatywnie:")
                for option in analysis.upgrade_options[1:]:
                    print(f"→ {_format_upgrade(option)}")
        else:
            print("Nie można uzyskać tych punktów przez podniesienie istniejących poziomów.")
    elif analysis.average_requirement_met is False and average is None:
        print("\nNie można obliczyć średniej bez podjętych kompetencji.")

    if (
        analysis.acquisition_requirement_met
        and analysis.average_requirement_met is not False
    ):
        print(f"\nSpełniasz wymagania na ocenę {target_grade}.")

    print(f"\n{_format_future_outlook(outlook, record.remaining_future)}")
