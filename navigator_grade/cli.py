from .calculator import (
    CompetencyRecord,
    UpgradeOption,
    acquisition_percentage,
    analyze_grade,
    average_competency_level,
    highest_grade_met,
)
from .rules import GRADE_REQUIREMENTS


def parse_compact_input(text: str) -> tuple[CompetencyRecord, int]:
    """Parse the six- or seven-value compact CLI format."""
    try:
        values = [int(value) for value in text.replace("|", " ").split()]
    except ValueError as error:
        raise ValueError("Wszystkie wartości muszą być liczbami całkowitymi.") from error

    if len(values) == 6:
        total_realized, level_0, level_1, level_2, level_3, target_grade = values
        levels = (level_0, level_1, level_2, level_3)
        if sum(levels) != total_realized:
            raise ValueError(
                "Gdy liczba zdobytych kompetencji różni się od wszystkich, "
                "podaj także attempted jako drugą wartość."
            )
        attempted = total_realized
    elif len(values) == 7:
        (
            total_realized,
            attempted,
            level_0,
            level_1,
            level_2,
            level_3,
            target_grade,
        ) = values
        levels = (level_0, level_1, level_2, level_3)
    else:
        raise ValueError("Podaj dokładnie 6 albo 7 liczb.")

    if target_grade not in GRADE_REQUIREMENTS:
        raise ValueError("Ocena docelowa musi mieścić się w zakresie 2-6.")

    try:
        record = CompetencyRecord(total_realized, attempted, *levels)
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


def _read_levels(total_realized: int) -> tuple[int, int, int, int]:
    while True:
        try:
            values = tuple(int(value) for value in input("Poziomy 0 1 2 3: ").split())
            if len(values) != 4 or any(value < 0 for value in values):
                raise ValueError
            if sum(values) > total_realized:
                print("Liczba zdobytych kompetencji nie może przekraczać wszystkich.")
                continue
            return values  # type: ignore[return-value]
        except ValueError:
            print("Wpisz cztery nieujemne liczby całkowite oddzielone spacjami.")


def _read_attempted(total_realized: int, acquired: int) -> int:
    while True:
        raw_value = input(f"Przystąpiono [{total_realized}]: ").strip()
        if not raw_value:
            return total_realized
        try:
            attempted = int(raw_value)
        except ValueError:
            print("Wpisz nieujemną liczbę całkowitą albo naciśnij Enter.")
            continue
        if attempted < acquired:
            print(
                "Liczba kompetencji, do których przystąpiono, nie może być "
                f"mniejsza niż liczba zdobytych ({acquired})."
            )
            continue
        if attempted > total_realized:
            print(
                "Liczba kompetencji, do których przystąpiono, nie może "
                f"przekraczać wszystkich kompetencji ({total_realized})."
            )
            continue
        return attempted


def _format_upgrade(option: UpgradeOption) -> str:
    parts = []
    is_combined = bool(option.acquisitions and option.upgrades)
    for level, count in option.acquisitions:
        if is_combined:
            noun = _polish_plural(
                count,
                "nową kompetencję",
                "nowe kompetencje",
                "nowych kompetencji",
            )
        else:
            noun = _polish_plural(
                count, "kompetencję", "kompetencje", "kompetencji"
            )
        parts.append(
            f"zdobądź {count} {noun} na poziomie co najmniej {level}"
        )
    for from_level, count in option.upgrades:
        noun = _polish_plural(count, "kompetencja", "kompetencje", "kompetencji")
        if is_combined:
            parts.append(f"popraw {count} {noun} z poziomu {from_level} na 3")
        else:
            parts.append(f"{count} {noun}: {from_level} → 3")
    separator = "\n→ " if is_combined else " oraz "
    return separator.join(parts)


def _polish_plural(count: int, singular: str, few: str, many: str) -> str:
    if count == 1:
        return singular
    if count % 100 not in (12, 13, 14) and count % 10 in (2, 3, 4):
        return few
    return many


def _read_interactively() -> tuple[CompetencyRecord, int]:
    total_realized = _read_positive_integer("Wszystkich kompetencji: ")
    levels = _read_levels(total_realized)
    acquired = sum(levels)
    attempted = _read_attempted(total_realized, acquired)
    target_grade = _read_bounded_integer("Cel: ", 2, 6)
    return CompetencyRecord(total_realized, attempted, *levels), target_grade


def run() -> None:
    print("NavigoGrade\n")
    print("Format:")
    print("wszystkie | poziom 0 | poziom 1 | poziom 2 | poziom 3 | cel")
    print("\nPrzykład:")
    print("12 | 0 | 1 | 3 | 8 | 6")
    print("\nJeśli nie wszystkie kompetencje są zdobyte:")
    print(
        "wszystkie | przystąpiono | poziom 0 | poziom 1 | "
        "poziom 2 | poziom 3 | cel"
    )
    print("\nPrzykład:")
    print("20 | 16 | 0 | 1 | 5 | 10 | 4\n")

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
    average = average_competency_level(record)
    current_grade = highest_grade_met(record)
    requirement = GRADE_REQUIREMENTS[target_grade]

    current_grade_text = str(current_grade) if current_grade is not None else "poniżej 2"
    average_text = f"{average:.2f}" if average is not None else "brak"
    print(f"\nOcena obecna: {current_grade_text}")
    print(f"Cel: {target_grade}")

    acquisition_mark = "✓" if analysis.acquisition_requirement_met else "✗"
    print(
        f"Zdobyte kompetencje: {record.acquired}/{record.total_realized} "
        f"({acquisition_percentage(record):.0f}%) {acquisition_mark}"
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
