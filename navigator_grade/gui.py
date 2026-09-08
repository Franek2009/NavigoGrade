"""Tkinter interface for NavigoGrade."""

from __future__ import annotations

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:
    tk = None
    messagebox = None
    ttk = None

from .calculator import (
    CompetencyRecord,
    acquisition_percentage,
    analyze_grade,
    average_competency_level,
    grade_requirements_met,
    highest_grade_met,
    future_outlook,
)
from .cli import _format_future_outlook, _format_upgrade, _polish_plural
from .rules import GRADE_REQUIREMENTS


def parse_gui_input(
    total_text: str,
    level_texts: tuple[str, str, str, str],
    target_text: str,
) -> tuple[CompetencyRecord, int]:
    """Convert GUI field text into the existing domain model."""
    total_overall = int(total_text.strip())
    levels = tuple(int(text.strip()) if text.strip() else 0 for text in level_texts)
    target_grade = int(target_text.strip())
    if target_grade not in GRADE_REQUIREMENTS:
        raise ValueError("target grade must be from 2 to 6")
    return CompetencyRecord(total_overall, *levels), target_grade


def format_results(record: CompetencyRecord, target_grade: int) -> str:
    """Format calculator results for the GUI without creating any widgets."""
    analysis = analyze_grade(target_grade, record)
    average = average_competency_level(record)
    current_grade = highest_grade_met(record)
    requirement = GRADE_REQUIREMENTS[target_grade]

    current_text = str(current_grade) if current_grade is not None else "poniżej 2"
    average_text = f"{average:.2f}" if average is not None else "brak"
    percentage = acquisition_percentage(record)
    percentage_text = f"{percentage:.2f}%" if percentage is not None else "brak danych"
    lines = [
        f"Ocena obecna: {current_text}",
        f"Zdobyte kompetencje: {record.acquired}/{record.evaluated}",
        f"Procent zdobytych: {percentage_text}",
        f"Średnia poziomu: {average_text}",
        "",
        f"Wymagania na ocenę {target_grade}:",
        (
            "✓ procent zdobytych kompetencji"
            if analysis.acquisition_requirement_met is True
            else "✗ procent zdobytych kompetencji"
            if analysis.acquisition_requirement_met is False
            else "— procent zdobytych kompetencji: brak danych"
        ),
    ]
    if analysis.average_requirement_met is not None:
        mark = "✓" if analysis.average_requirement_met else "✗"
        lines.append(
            f"{mark} średnia co najmniej {requirement.minimum_average_level:.2f}"
        )

    lines.extend(["", "Co trzeba poprawić"])
    if grade_requirements_met(target_grade, record):
        lines.append(f"Spełniasz wymagania na ocenę {target_grade}.")
        lines.extend(
            ["", _format_future_outlook(future_outlook(target_grade, record), record.remaining_future)]
        )
        return "\n".join(lines)

    if analysis.additional_acquired_needed:
        noun = _polish_plural(
            analysis.additional_acquired_needed,
            "dodatkową kompetencję",
            "dodatkowe kompetencje",
            "dodatkowych kompetencji",
        )
        lines.append(
            f"Zdobądź {analysis.additional_acquired_needed} {noun}."
        )
    if analysis.missing_level_points:
        noun = "punktu" if analysis.missing_level_points == 1 else "punktów"
        lines.append(f"Brakuje {analysis.missing_level_points} {noun} poziomu.")

    for index, option in enumerate(analysis.upgrade_options):
        label = "Najprościej" if index == 0 else "Alternatywnie"
        formatted = _format_upgrade(option).replace("\n→ ", "\n  → ")
        lines.append(f"{label}:\n  → {formatted}")

    if analysis.average_requirement_met is False and average is None:
        lines.append("Nie można obliczyć średniej bez podjętych kompetencji.")
    lines.extend(
        ["", _format_future_outlook(future_outlook(target_grade, record), record.remaining_future)]
    )
    return "\n".join(lines)


class NavigoGradeApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("NavigoGrade")
        self.root.minsize(560, 620)

        container = ttk.Frame(root, padding=16)
        container.grid(sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(9, weight=1)

        ttk.Label(container, text="NavigoGrade", font=("TkDefaultFont", 18, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )

        labels = (
            "Wszystkich kompetencji",
            "Poziom 0",
            "Poziom 1",
            "Poziom 2",
            "Poziom 3",
        )
        self.entries: list[ttk.Entry] = []
        for row, label in enumerate(labels, start=1):
            ttk.Label(container, text=label).grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=3
            )
            entry = ttk.Entry(container)
            entry.grid(row=row, column=1, sticky="ew", pady=3)
            self.entries.append(entry)

        ttk.Label(container, text="Cel").grid(
            row=7, column=0, sticky="w", padx=(0, 12), pady=3
        )
        self.target = ttk.Combobox(
            container, values=tuple(GRADE_REQUIREMENTS), state="readonly"
        )
        self.target.set("6")
        self.target.grid(row=7, column=1, sticky="ew", pady=3)

        ttk.Button(container, text="Oblicz", command=self.calculate).grid(
            row=8, column=0, columnspan=2, pady=12
        )

        self.results = tk.Text(container, wrap="word", height=20, state="disabled")
        self.results.grid(row=9, column=0, columnspan=2, sticky="nsew")
        self.entries[0].focus_set()

    def calculate(self) -> None:
        try:
            record, target_grade = parse_gui_input(
                self.entries[0].get(),
                tuple(entry.get() for entry in self.entries[1:]),
                self.target.get(),
            )
            result = format_results(record, target_grade)
        except (TypeError, ValueError) as error:
            messagebox.showerror(
                "Nieprawidłowe dane",
                "Wpisz nieujemne liczby całkowite i sprawdź zależności między "
                f"polami.\n\nSzczegóły: {error}",
                parent=self.root,
            )
            return

        self.results.configure(state="normal")
        self.results.delete("1.0", tk.END)
        self.results.insert("1.0", result)
        self.results.configure(state="disabled")


def main() -> None:
    if tk is None:
        raise SystemExit(
            "Tkinter nie jest dostępny. Zainstaluj obsługę Tk dla używanej "
            "wersji Pythona."
        )
    root = tk.Tk()
    NavigoGradeApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
