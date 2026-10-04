from __future__ import annotations

import csv
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from student_performance_analysis import (
    DATA_FILE,
    SUBJECT_FIELDS,
    calculate_overall,
    format_report,
    generate_analysis,
    grade_for,
    load_students,
)


REQUIRED_FIELDS = [
    "Student ID",
    "Name",
    "Gender",
    "Class",
    *SUBJECT_FIELDS,
    "Attendance",
    "AssignmentScore",
]


class StudentPerformanceApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Student Performance Analyser")
        self.root.geometry("1100x760")
        self.root.minsize(850, 620)
        self.root.configure(bg="#f4f7fb")
        self.rows: list[dict[str, str]] = []
        self.analysis: dict = {}
        self.search_var = tk.StringVar()
        self.class_var = tk.StringVar(value="All classes")

        self._configure_style()
        self._build_layout()
        if DATA_FILE.exists():
            self.load_file(DATA_FILE)
        else:
            self.status.configure(text="No data loaded. Open a CSV file or add a student to begin.")

    def _configure_style(self):
        style = ttk.Style()
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("TFrame", background="#f4f7fb")
        style.configure("Card.TFrame", background="#ffffff", borderwidth=1, relief="solid")
        style.configure("TLabel", background="#f4f7fb", foreground="#192338", font=("Segoe UI", 10))
        style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"), foreground="#17294d")
        style.configure("Subtitle.TLabel", foreground="#718096", font=("Segoe UI", 10))
        style.configure("CardTitle.TLabel", background="#ffffff", foreground="#64748b", font=("Segoe UI", 9))
        style.configure("CardValue.TLabel", background="#ffffff", foreground="#263f79", font=("Segoe UI", 21, "bold"))
        style.configure("TButton", padding=(11, 7), font=("Segoe UI", 9))
        style.map("TButton", background=[("active", "#e8edfa")], foreground=[("active", "#263f79")])
        style.configure("Accent.TButton", padding=(12, 7), font=("Segoe UI", 9, "bold"))
        style.map(
            "Accent.TButton",
            background=[("active", "#3e62d5"), ("!disabled", "#4d72e8")],
            foreground=[("!disabled", "#ffffff")],
        )
        style.configure("Treeview", rowheight=34, font=("Segoe UI", 10), background="#ffffff", fieldbackground="#ffffff")
        style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#f1f4fa",
            foreground="#475569",
            padding=(8, 9),
        )
        style.map("Treeview", background=[("selected", "#e7edff")], foreground=[("selected", "#1f3263")])

    def _build_layout(self):
        page = ttk.Frame(self.root, padding=(28, 24))
        page.pack(fill="both", expand=True)

        header = ttk.Frame(page)
        header.pack(fill="x", pady=(0, 16))
        title_block = ttk.Frame(header)
        title_block.pack(side="left")
        ttk.Label(title_block, text="Student Performance Analyser", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            title_block,
            text="Class results, attendance, and subject insights",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(3, 0))
        actions = ttk.Frame(header)
        actions.pack(side="right", anchor="center")
        ttk.Button(actions, text="Open CSV", command=self.open_csv).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Add student", command=self.add_student).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Save CSV", command=self.save_csv).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Export report", style="Accent.TButton", command=self.export_report).pack(side="left")

        self.cards_frame = ttk.Frame(page)
        self.cards_frame.pack(fill="x", pady=(0, 16))
        self.card_values = {}
        for index, (key, label) in enumerate(
            [
                ("students", "STUDENTS"),
                ("average", "CLASS AVERAGE"),
                ("pass_rate", "PASS RATE"),
                ("top", "TOP PERFORMER"),
            ]
        ):
            card = ttk.Frame(self.cards_frame, style="Card.TFrame", padding=(16, 13))
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0))
            self.cards_frame.columnconfigure(index, weight=1, uniform="cards")
            ttk.Label(card, text=label, style="CardTitle.TLabel").pack(anchor="w")
            value = ttk.Label(card, text="-", style="CardValue.TLabel")
            value.pack(anchor="w", pady=(7, 0))
            self.card_values[key] = value

        charts = ttk.Frame(page)
        charts.pack(fill="x", pady=(0, 14))
        subject_card = ttk.Frame(charts, style="Card.TFrame", padding=14)
        subject_card.pack(side="left", fill="both", expand=True, padx=(0, 8))
        ttk.Label(subject_card, text="Subject averages", style="CardTitle.TLabel").pack(anchor="w")
        self.subject_chart = tk.Canvas(subject_card, height=150, background="#ffffff", highlightthickness=0)
        self.subject_chart.pack(fill="both", expand=True, pady=(8, 0))
        self.subject_chart.bind("<Configure>", lambda _event: self._draw_subject_chart())

        grade_card = ttk.Frame(charts, style="Card.TFrame", padding=14)
        grade_card.pack(side="left", fill="both", expand=True, padx=(8, 0))
        ttk.Label(grade_card, text="Grade distribution", style="CardTitle.TLabel").pack(anchor="w")
        self.grade_chart = tk.Canvas(grade_card, height=150, background="#ffffff", highlightthickness=0)
        self.grade_chart.pack(fill="both", expand=True, pady=(8, 0))
        self.grade_chart.bind("<Configure>", lambda _event: self._draw_grade_chart())

        list_header = ttk.Frame(page)
        list_header.pack(fill="x", pady=(0, 8))
        ttk.Label(list_header, text="Students", font=("Segoe UI", 14, "bold")).pack(side="left")
        filters = ttk.Frame(list_header)
        filters.pack(side="right")
        ttk.Label(filters, text="Class").pack(side="left", padx=(0, 6))
        self.class_filter = ttk.Combobox(
            filters,
            textvariable=self.class_var,
            state="readonly",
            width=14,
            values=["All classes"],
        )
        self.class_filter.pack(side="left", padx=(0, 12))
        self.class_filter.bind("<<ComboboxSelected>>", lambda _event: self._populate_students())
        ttk.Label(filters, text="Search").pack(side="left", padx=(0, 6))
        search = ttk.Entry(filters, textvariable=self.search_var, width=22)
        search.pack(side="left")
        self.search_var.trace_add("write", lambda *_args: self._populate_students())

        table_frame = ttk.Frame(page, style="Card.TFrame", padding=8)
        table_frame.pack(fill="both", expand=True)
        columns = ("id", "name", "class", "average", "grade", "attendance")
        self.student_table = ttk.Treeview(table_frame, columns=columns, show="headings")
        headings = {
            "id": ("Student ID", 110),
            "name": ("Name", 220),
            "class": ("Class", 100),
            "average": ("Average", 130),
            "grade": ("Grade", 100),
            "attendance": ("Attendance", 150),
        }
        for column, (heading, width) in headings.items():
            self.student_table.heading(column, text=heading)
            self.student_table.column(column, width=width, anchor="w" if column in ("id", "name") else "center")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.student_table.yview)
        self.student_table.configure(yscrollcommand=scrollbar.set)
        self.student_table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.student_table.tag_configure("alternate", background="#f8fafc")
        self.status = ttk.Label(page, text="", style="Subtitle.TLabel")
        self.status.pack(anchor="w", pady=(8, 0))

    @staticmethod
    def _validate_rows(rows: list[dict[str, str]]):
        if not rows:
            raise ValueError("The selected CSV does not contain any student records.")

        for row_number, row in enumerate(rows, start=2):
            missing = [field for field in REQUIRED_FIELDS if not row.get(field)]
            if missing:
                raise ValueError(f"Row {row_number} is missing values for: {', '.join(missing)}.")
            for field in [*SUBJECT_FIELDS, "Attendance", "AssignmentScore"]:
                try:
                    value = float(row[field])
                except ValueError as error:
                    raise ValueError(f"Row {row_number} has an invalid number in '{field}'.") from error
                if not 0 <= value <= 100:
                    raise ValueError(f"Row {row_number}: '{field}' must be between 0 and 100.")

    def open_csv(self):
        path = filedialog.askopenfilename(
            title="Open student data",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if path:
            self.load_file(Path(path))

    def add_student(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add student")
        dialog.transient(self.root)
        dialog.resizable(False, False)
        dialog.grab_set()

        form = ttk.Frame(dialog, padding=18)
        form.pack(fill="both", expand=True)
        entries = {}
        for index, field in enumerate(REQUIRED_FIELDS):
            row, column = divmod(index, 2)
            ttk.Label(form, text=field).grid(row=row, column=column * 2, sticky="w", padx=(0, 8), pady=5)
            entry = ttk.Entry(form, width=24)
            entry.grid(row=row, column=column * 2 + 1, sticky="ew", padx=(0, 14), pady=5)
            entries[field] = entry

        def submit():
            row = {field: entry.get().strip() for field, entry in entries.items()}
            try:
                self._validate_rows([row])
                updated_rows = [*self.rows, row]
                updated_analysis = generate_analysis(updated_rows)
            except (ValueError, KeyError) as error:
                messagebox.showerror("Could not add student", str(error), parent=dialog)
                return

            self.rows = updated_rows
            self.analysis = updated_analysis
            dialog.destroy()
            self._update_dashboard("Manual entry")

        actions = ttk.Frame(form)
        actions.grid(row=(len(REQUIRED_FIELDS) + 1) // 2, column=0, columnspan=4, sticky="e", pady=(12, 0))
        ttk.Button(actions, text="Cancel", command=dialog.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Add student", style="Accent.TButton", command=submit).pack(side="left")
        entries[REQUIRED_FIELDS[0]].focus_set()

    def load_file(self, path: Path):
        try:
            rows = load_students(path)
            self._validate_rows(rows)
            analysis = generate_analysis(rows)
        except (OSError, csv.Error, UnicodeError, ValueError, KeyError) as error:
            messagebox.showerror("Could not load student data", str(error), parent=self.root)
            self.status.configure(text=f"No data loaded from {path.name}. Open a valid CSV file or add a student.")
            return

        self.rows = rows
        self.analysis = analysis
        self._update_dashboard(path)

    def _update_dashboard(self, source: Path | str):
        best = self.analysis["best_student"]
        best_score = calculate_overall(best)
        self.card_values["students"].configure(text=str(self.analysis["total_students"]))
        self.card_values["average"].configure(text=f"{self.analysis['average_score']:.1f}%")
        self.card_values["pass_rate"].configure(text=f"{self.analysis['pass_rate']:.0f}%")
        self.card_values["top"].configure(text=f"{best['Name']} - {best_score:.1f}%")

        classes = sorted({row["Class"] for row in self.rows}, key=lambda value: (not value.isdigit(), value))
        current = self.class_var.get()
        options = ["All classes", *classes]
        self.class_filter.configure(values=options)
        self.class_var.set(current if current in options else "All classes")
        self._populate_students()
        self._draw_subject_chart()
        self._draw_grade_chart()
        self.status.configure(text=f"Data source: {source}")

    def _populate_students(self):
        if not hasattr(self, "student_table"):
            return
        query = self.search_var.get().strip().casefold()
        selected_class = self.class_var.get()
        visible = [
            row
            for row in self.rows
            if (selected_class == "All classes" or row["Class"] == selected_class)
            and (not query or query in row["Name"].casefold() or query in row["Student ID"].casefold())
        ]
        visible.sort(key=lambda row: row["Name"].casefold())
        self.student_table.delete(*self.student_table.get_children())
        for index, row in enumerate(visible):
            average = calculate_overall(row)
            self.student_table.insert(
                "",
                "end",
                values=(
                    row["Student ID"],
                    row["Name"],
                    row["Class"],
                    f"{average:.1f}%",
                    grade_for(average),
                    f"{float(row['Attendance']):.0f}%",
                ),
                tags=("alternate",) if index % 2 else (),
            )

    def _draw_subject_chart(self):
        canvas = self.subject_chart
        canvas.delete("all")
        if not self.analysis:
            return
        width = max(canvas.winfo_width(), 300)
        row_height = 33
        label_width = 72
        right_space = 42
        bar_width = max(width - label_width - right_space, 90)
        for index, (subject, average) in enumerate(self.analysis["subject_averages"].items()):
            y = 12 + index * row_height
            canvas.create_text(0, y + 9, text=subject, anchor="w", fill="#475569", font=("Segoe UI", 9))
            canvas.create_rectangle(
                label_width,
                y,
                label_width + bar_width,
                y + 18,
                fill="#e8eef7",
                outline="",
            )
            canvas.create_rectangle(
                label_width,
                y,
                label_width + bar_width * average / 100,
                y + 18,
                fill="#4f7cff",
                outline="",
            )
            canvas.create_text(
                width - 2,
                y + 9,
                text=f"{average:.1f}%",
                anchor="e",
                fill="#172554",
                font=("Segoe UI", 9, "bold"),
            )

    def _draw_grade_chart(self):
        canvas = self.grade_chart
        canvas.delete("all")
        if not self.analysis:
            return
        width = max(canvas.winfo_width(), 300)
        height = max(canvas.winfo_height(), 140)
        distribution = self.analysis["grade_distribution"]
        max_count = max(distribution.values(), default=0) or 1
        slot = width / len(distribution)
        chart_height = height - 35
        colors = {"A": "#22a06b", "B": "#4f7cff", "C": "#f2a93b", "D": "#ed7b55", "F": "#d64c4c"}
        for index, (grade, count) in enumerate(distribution.items()):
            bar_height = chart_height * count / max_count
            center = slot * index + slot / 2
            canvas.create_text(center, height - 12, text=grade, fill="#475569", font=("Segoe UI", 9, "bold"))
            canvas.create_rectangle(
                center - 17,
                chart_height - bar_height + 3,
                center + 17,
                chart_height + 3,
                fill=colors[grade],
                outline="",
            )
            canvas.create_text(center, max(chart_height - bar_height - 9, 8), text=str(count), fill="#172554")

    def export_report(self):
        path = filedialog.asksaveasfilename(
            title="Export analysis report",
            defaultextension=".txt",
            initialfile="analysis_report.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            Path(path).write_text(format_report(self.analysis), encoding="utf-8")
        except OSError as error:
            messagebox.showerror("Could not export report", str(error), parent=self.root)
            return
        messagebox.showinfo("Report exported", f"Report saved to:\n{path}", parent=self.root)

    def save_csv(self):
        if not self.rows:
            messagebox.showerror("No student data", "Add a student or open a CSV file before saving.", parent=self.root)
            return
        path = filedialog.asksaveasfilename(
            title="Save student data",
            defaultextension=".csv",
            initialfile="students.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with Path(path).open("w", encoding="utf-8", newline="") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=REQUIRED_FIELDS)
                writer.writeheader()
                writer.writerows(self.rows)
        except OSError as error:
            messagebox.showerror("Could not save student data", str(error), parent=self.root)
            return
        self.status.configure(text=f"Student data saved to: {path}")
        messagebox.showinfo("Student data saved", f"Data saved to:\n{path}", parent=self.root)


def main():
    root = tk.Tk()
    StudentPerformanceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
