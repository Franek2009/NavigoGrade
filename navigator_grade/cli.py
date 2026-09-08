from .calculator import (
    CompetencyRecord,
    UpgradeOption,
    acquisition_percentage,
    analyze_grade,
    average_competency_level,
    highest_grade_met,
)
from .rules import GRADE_REQUIREMENTS


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
            values = tuple(int(value) for value in input("Poziomy [0 1 2 3]: ").split())
            if len(values) != 4 or any(value < 0 for value in values):
                raise ValueError
            if sum(values) > total_realized:
                print("Liczba zdobytych kompetencji nie może przekraczać wszystkich.")
                continue
            return values  # type: ignore[return-value]
        except ValueError:
            print("Wpisz cztery nieujemne liczby całkowite oddzielone spacjami.")


def _format_upgrade(option: UpgradeOption) -> str:
    parts = []
    for from_level, count in option.upgrades:
        noun = "kompetencję" if count == 1 else "kompetencje"
        parts.append(f"{count} {noun} z poziomu {from_level} na 3")
    return " oraz ".join(parts)


def run() -> None:
    print("NavigoGrade\n")
    total_realized = _read_positive_integer("Liczba kompetencji: ")
    levels = _read_levels(total_realized)
    acquired = sum(levels)

    if acquired == total_realized:
        attempted = acquired
    else:
        attempted = _read_bounded_integer(
            f"Liczba kompetencji, do których przystąpiono [{acquired}-{total_realized}]: ",
            acquired,
            total_realized,
        )

    target_grade = _read_bounded_integer("Cel: ", 2, 6)
    record = CompetencyRecord(total_realized, attempted, *levels)
    analysis = analyze_grade(target_grade, record)
    average = average_competency_level(record)
    current_grade = highest_grade_met(record)
    requirement = GRADE_REQUIREMENTS[target_grade]

    current_grade_text = str(current_grade) if current_grade is not None else "poniżej 2"
    average_text = f"{average:.2f}" if average is not None else "brak"
    print(f"\nObecnie: {current_grade_text}")
    print(
        f"Zdobyte: {record.acquired}/{record.total_realized} "
        f"({acquisition_percentage(record):.0f}%)"
    )
    print(f"Średnia: {average_text}")
    print(f"\nDo oceny {target_grade}:")

    acquisition_mark = "✓" if analysis.acquisition_requirement_met else "✗"
    print(
        f"{acquisition_mark} wymagane "
        f"{requirement.minimum_acquisition_percentage:g}% kompetencji"
    )
    if analysis.average_requirement_met is not None:
        average_mark = "✓" if analysis.average_requirement_met else "✗"
        print(
            f"{average_mark} wymagana średnia "
            f"{requirement.minimum_average_level:.2f}"
        )

    if analysis.additional_acquired_needed:
        competency_word = (
            "dodatkowej kompetencji"
            if analysis.additional_acquired_needed == 1
            else "dodatkowych kompetencji"
        )
        print(
            f"\nBrakuje zdobycia {analysis.additional_acquired_needed} "
            f"{competency_word}."
        )

    if analysis.missing_level_points:
        print(f"\nBrakuje: {analysis.missing_level_points} punktów poziomu.")
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
