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
from .cli import _format_future_actions
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
    outlook = future_outlook(target_grade, record)
    lines = [
        "Obecnie",
        f"Ocena: {current_text}",
        f"Zdobyte kompetencje: {record.acquired}/{record.evaluated}",
        f"Procent zdobytych: {percentage_text}",
        f"Średnia poziomu: {average_text}",
        "",
        "Cel",
        f"Ocena docelowa: {target_grade}",
        (
            "✓ Wymagany procent kompetencji jest spełniony"
            if analysis.acquisition_requirement_met is True
            else "✗ Wymagany procent kompetencji nie jest spełniony"
            if analysis.acquisition_requirement_met is False
            else "— Procent kompetencji: brak danych"
        ),
    ]
    if analysis.average_requirement_met is not None:
        mark = "✓" if analysis.average_requirement_met else "✗"
        lines.append(
            f"{mark} Wymagana średnia: {requirement.minimum_average_level:.2f}"
        )

    lines.extend(["", "Jak osiągnąć"])
    if grade_requirements_met(target_grade, record):
        lines.append(f"✓ Spełniasz wymagania na ocenę {target_grade}.")
    elif outlook.target_plan is None:
        lines.append("✗ Brak możliwego planu końcowego.")
    else:
        lines.extend(_format_future_actions(outlook.target_plan))

    lines.extend(["", "Jak utrzymać"])
    if not outlook.target_currently_met:
        lines.append("— Ta sekcja będzie dostępna po osiągnięciu celu.")
    elif record.remaining_future == 0:
        lines.append("✓ Nie pozostały żadne przyszłe kompetencje.")
    elif outlook.target_plan is None:
        lines.append("✗ Brak możliwego planu utrzymania oceny.")
    else:
        lines.append(f"Z pozostałych {record.remaining_future} kompetencji wystarczy:")
        for level, count in enumerate(outlook.target_plan.future_levels):
            if count:
                lines.append(f"→ {count} × poziom {level}")

    lines.extend(["", "Do następnej oceny"])
    if outlook.next_grade is None:
        lines.append("✓ To najwyższa dostępna ocena.")
    elif outlook.next_grade_plan is None:
        lines.append(f"✗ Ocena {outlook.next_grade} nie jest osiągalna.")
    else:
        lines.append(f"Ocena {outlook.next_grade}:")
        next_analysis = outlook.next_grade_analysis
        if next_analysis.additional_acquired_needed:
            lines.append(
                f"→ Brakuje {next_analysis.additional_acquired_needed} "
                "zdobytych kompetencji obecnie"
            )
        if next_analysis.missing_level_points:
            lines.append(
                f"→ Brakuje {next_analysis.missing_level_points} punktów poziomu obecnie"
            )
        lines.extend(_format_future_actions(outlook.next_grade_plan))
    return "\n".join(lines)


class NavigoGradeApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("NavigoGrade")
        self.root.minsize(560, 620)

        container = ttk.Frame(root, padding=20)
        container.grid(sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(3, weight=1)

        ttk.Label(container, text="NavigoGrade", font=("TkDefaultFont", 18, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        ttk.Label(
            container, text="Sprawdź ocenę i zobacz najprostszy plan działania"
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 14))

        form = ttk.LabelFrame(container, text="Dane", padding=12)
        form.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 14))
        form.columnconfigure(1, weight=1)

        labels = (
            "Wszystkich kompetencji",
            "Poziom 0",
            "Poziom 1",
            "Poziom 2",
            "Poziom 3",
        )
        self.entries: list[ttk.Entry] = []
        for row, label in enumerate(labels, start=1):
            ttk.Label(form, text=label).grid(
                row=row, column=0, sticky="w", padx=(0, 12), pady=3
            )
            entry = ttk.Entry(form)
            entry.grid(row=row, column=1, sticky="ew", pady=3)
            self.entries.append(entry)

        ttk.Label(form, text="Cel").grid(
            row=6, column=0, sticky="w", padx=(0, 12), pady=3
        )
        self.target = ttk.Combobox(
            form, values=tuple(GRADE_REQUIREMENTS), state="readonly"
        )
        self.target.set("6")
        self.target.grid(row=6, column=1, sticky="ew", pady=3)

        ttk.Button(form, text="Oblicz", command=self.calculate).grid(
            row=7, column=0, columnspan=2, pady=(12, 0)
        )

        self.results = tk.Text(
            container, wrap="word", height=22, state="disabled", padx=12, pady=10
        )
        self.results.grid(row=3, column=0, columnspan=2, sticky="nsew")
        self.results.tag_configure(
            "heading", font=("TkDefaultFont", 12, "bold"), spacing1=8
        )
        self.results.tag_configure("success", foreground="#18733c")
        self.results.tag_configure("failure", foreground="#b3261e")
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
        for heading in (
            "Obecnie", "Cel", "Jak osiągnąć", "Jak utrzymać", "Do następnej oceny"
        ):
            start = self.results.search(heading, "1.0", stopindex=tk.END)
            if start:
                self.results.tag_add("heading", start, f"{start} lineend")
        position = "1.0"
        while True:
            position = self.results.search("✓", position, stopindex=tk.END)
            if not position:
                break
            self.results.tag_add("success", position, f"{position} lineend")
            position = f"{position}+1c"
        position = "1.0"
        while True:
            position = self.results.search("✗", position, stopindex=tk.END)
            if not position:
                break
            self.results.tag_add("failure", position, f"{position} lineend")
            position = f"{position}+1c"
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
