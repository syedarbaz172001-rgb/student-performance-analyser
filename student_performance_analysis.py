from __future__ import annotations

import csv
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent / "data" / "students.csv"
OUTPUT_FILE = Path(__file__).resolve().parent / "analysis_report.txt"
SUBJECT_FIELDS = ["Maths", "Science", "English", "History"]


def load_students(path: Path):
    with path.open("r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def calculate_overall(row):
    scores = [float(row[field]) for field in SUBJECT_FIELDS]
    return round(sum(scores) / len(scores), 2)


def grade_for(score):
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def generate_analysis(rows):
    total_students = len(rows)
    subject_averages = {subject: 0.0 for subject in SUBJECT_FIELDS}
    attendance_groups = {"Excellent (>= 90)": 0, "Good (75-89)": 0, "Needs Attention (< 75)": 0}
    grade_distribution = {grade: 0 for grade in ["A", "B", "C", "D", "F"]}

    if total_students == 0:
        return {
            "total_students": 0,
            "average_score": 0.0,
            "best_student": None,
            "weakest_student": None,
            "pass_rate": 0.0,
            "subject_averages": subject_averages,
            "gender_averages": {},
            "attendance_groups": attendance_groups,
            "grade_distribution": grade_distribution,
        }

    overall_scores = [calculate_overall(row) for row in rows]
    average_score = round(sum(overall_scores) / total_students, 2)
    best_student = max(rows, key=calculate_overall)
    weakest_student = min(rows, key=calculate_overall)
    pass_count = sum(1 for score in overall_scores if score >= 50)
    pass_rate = round((pass_count / total_students) * 100, 2) if total_students else 0.0

    for subject in SUBJECT_FIELDS:
        values = [float(row[subject]) for row in rows]
        subject_averages[subject] = round(sum(values) / len(values), 2)

    gender_summary = {}
    for row in rows:
        gender = row["Gender"]
        gender_summary.setdefault(gender, {"count": 0, "total": 0.0})
        gender_summary[gender]["count"] += 1
        gender_summary[gender]["total"] += calculate_overall(row)

    gender_averages = {
        gender: round(data["total"] / data["count"], 2)
        for gender, data in gender_summary.items()
    }

    for row in rows:
        attendance = float(row["Attendance"])
        if attendance >= 90:
            attendance_groups["Excellent (>= 90)"] += 1
        elif attendance >= 75:
            attendance_groups["Good (75-89)"] += 1
        else:
            attendance_groups["Needs Attention (< 75)"] += 1

    for score in overall_scores:
        grade_distribution[grade_for(score)] += 1

    return {
        "total_students": total_students,
        "average_score": average_score,
        "best_student": best_student,
        "weakest_student": weakest_student,
        "pass_rate": pass_rate,
        "subject_averages": subject_averages,
        "gender_averages": gender_averages,
        "attendance_groups": attendance_groups,
        "grade_distribution": grade_distribution,
    }


def format_report(analysis):
    if not analysis or analysis["total_students"] == 0:
        return (
            "Student Performance Analyser\n"
            "===========================\n\n"
            "No student data is available.\n"
        )

    lines = [
        "Student Performance Analyser",
        "===========================",
        "",
        f"Total Students: {analysis['total_students']}",
        f"Average Overall Score: {analysis['average_score']}%",
        f"Pass Rate: {analysis['pass_rate']}%",
        "",
        "Top Performer:",
        f"- {analysis['best_student']['Name']} ({analysis['best_student']['Class']}): {calculate_overall(analysis['best_student'])}%",
        "",
        "Lowest Performer:",
        f"- {analysis['weakest_student']['Name']} ({analysis['weakest_student']['Class']}): {calculate_overall(analysis['weakest_student'])}%",
        "",
        "Subject-wise Average Scores:",
    ]

    for subject, average in analysis["subject_averages"].items():
        lines.append(f"- {subject}: {average}%")

    lines.extend(["", "Gender-wise Average Performance:"])
    for gender, average in analysis["gender_averages"].items():
        lines.append(f"- {gender}: {average}%")

    lines.extend(["", "Attendance Distribution:"])
    for label, count in analysis["attendance_groups"].items():
        lines.append(f"- {label}: {count} students")

    lines.extend(["", "Grade Distribution:"])
    for grade, count in analysis["grade_distribution"].items():
        lines.append(f"- Grade {grade}: {count} students")

    return "\n".join(lines) + "\n"


def main():
    if not DATA_FILE.exists():
        print(f"No student data file found at {DATA_FILE}. Add a CSV file or import data before running analysis.")
        return

    rows = load_students(DATA_FILE)
    if not rows:
        print(f"The student dataset at {DATA_FILE} is empty.")
        return

    analysis = generate_analysis(rows)
    report = format_report(analysis)
    OUTPUT_FILE.write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
