"""
analyzer.py

Result Analyzer for School Chatbot.

Main goals:
1. Never invent information.
2. Deterministic answers for school-data queries.
3. Robust assignment handling.
4. Robust attendance handling.
5. Robust marks/performance handling.
6. Human-friendly formatting.
7. Ollama used only when deterministic formatting is not enough.
"""

import json
import ollama

from decimal import Decimal
from datetime import date, datetime


MODEL = "llama3:latest"


# =========================================================
# MAIN ANALYZER
# =========================================================

def analyze_results(
    question: str,
    plan: dict,
    results: list
) -> str:

    plan = plan or {}
    results = results or []

    metric = plan.get("metric", "")
    intent = plan.get("intent", "")

    print("\n========== ANALYZER ==========")
    print("Question:", question)
    print("Intent  :", intent)
    print("Metric  :", metric)
    print("Results :", results)
    print("==============================")

    # -----------------------------------------------------
    # NO RESULTS
    # -----------------------------------------------------

    if not results:

        return get_no_results_message(
            question,
            plan
        )

    # =====================================================
    # PERFORMANCE
    # =====================================================

    if metric == "exam_comparison":

        return compare_results(
            question,
            plan,
            results
        )

    if metric in {
        "trend",
        "highest_subject",
        "lowest_subject",
        "overall_performance",
        "best_exam",
        "worst_exam",
        "highest_score",
        "lowest_score"
    }:

        return analyze_performance(
            question,
            plan,
            results
        )

    if metric == "recommendation":

        return generate_recommendation(
            question,
            plan,
            results
        )

    # =====================================================
    # ATTENDANCE
    # =====================================================

    if intent == "attendance":

        return analyze_attendance(
            question,
            plan,
            results
        )

    # =====================================================
    # ASSIGNMENTS
    # =====================================================

    if intent == "assignments":

        return analyze_assignments(
            question,
            plan,
            results
        )

    # =====================================================
    # MARKS
    # =====================================================

    if intent == "marks":

        return analyze_marks(
            question,
            plan,
            results
        )

    # =====================================================
    # TIMETABLE
    # =====================================================

    if intent == "timetable":

        return analyze_timetable(
            question,
            plan,
            results
        )

    # =====================================================
    # EXAMS
    # =====================================================

    if intent == "exams":

        return analyze_exams(
            question,
            plan,
            results
        )

    # =====================================================
    # TEACHER
    # =====================================================

    if intent == "teacher":

        return analyze_teacher(
            question,
            plan,
            results
        )

    # =====================================================
    # PROFILE
    # =====================================================

    if intent == "profile":

        return analyze_profile(
            question,
            plan,
            results
        )

    # =====================================================
    # DEFAULT
    # =====================================================

    return analyze_generic(
        question,
        plan,
        results
    )


# =========================================================
# NO RESULTS MESSAGE
# =========================================================

def get_no_results_message(
    question: str,
    plan: dict
) -> str:

    intent = plan.get(
        "intent",
        ""
    )

    metric = plan.get(
        "metric",
        ""
    )

    if intent == "assignments":

        if metric in {
            "overdue",
            "overdue_assignments"
        }:

            return "You have no overdue assignments."

        if metric in {
            "today",
            "due_today"
        }:

            return "You have no assignments due today."

        if metric in {
            "tomorrow",
            "due_tomorrow"
        }:

            return "You have no assignments due tomorrow."

        return "No assignments found."

    if intent == "attendance":

        return "No attendance records found."

    if intent == "marks":

        return "No marks found for your query."

    if intent == "timetable":

        return "No timetable entries found."

    if intent == "exams":

        return "No exams found."

    if intent == "teacher":

        return "No teacher information found."

    return "I couldn't find any matching records."


# =========================================================
# DECIMAL / DATE CONVERSION
# =========================================================

def convert_decimals(obj):

    if isinstance(obj, Decimal):

        return float(obj)

    if isinstance(obj, (datetime, date)):

        return obj.isoformat()

    if isinstance(obj, list):

        return [
            convert_decimals(item)
            for item in obj
        ]

    if isinstance(obj, dict):

        return {
            key: convert_decimals(value)
            for key, value in obj.items()
        }

    return obj


# =========================================================
# SAFE INTEGER
# =========================================================

def safe_int(value):

    if value is None:

        return 0

    try:

        return int(value)

    except (
        TypeError,
        ValueError
    ):

        try:

            return int(float(value))

        except (
            TypeError,
            ValueError
        ):

            return 0


# =========================================================
# SAFE FLOAT
# =========================================================

def safe_float(value):

    if value is None:

        return None

    try:

        return float(value)

    except (
        TypeError,
        ValueError
    ):

        return None


# =========================================================
# FORMAT DATE
# =========================================================

def format_date(
    value,
    format_string="%Y-%m-%d"
):

    if value is None:

        return None

    if hasattr(
        value,
        "strftime"
    ):

        return value.strftime(
            format_string
        )

    text = str(value)

    # ISO timestamp
    if "T" in text:

        text = text.split("T")[0]

    return text


# =========================================================
# PERFORMANCE COMPARISON
# =========================================================

def compare_results(
    question: str,
    plan: dict,
    results: list
) -> str:

    prompt = f"""
You are an educational performance comparison assistant.

User question:
{question}

Student data:
{json.dumps(
    convert_decimals(results),
    indent=2,
    default=str
)}

Task:
Compare the student's examination results.

Rules:
1. Use ONLY the provided data.
2. Never invent missing marks.
3. Compare only examinations that actually exist.
4. Show actual marks obtained.
5. If maximum marks are available, you may show them.
6. Calculate Final - Mid Term only when both values exist.
7. Positive = improved.
8. Negative = declined.
9. Zero = no change.
10. Do not mention SQL, database, AI or internal systems.
11. Keep the answer concise.
12. Use simple English.

Return only the answer.
"""

    return call_llm(prompt)


# =========================================================
# PERFORMANCE ANALYSIS
# =========================================================

def analyze_performance(
    question: str,
    plan: dict,
    results: list
) -> str:

    metric = plan.get(
        "metric",
        ""
    )

    # =====================================================
    # HIGHEST SUBJECT
    # =====================================================

    if metric in {
        "highest_subject",
        "best_subject"
    }:

        rows = []

        for row in results:

            subject = row.get(
                "subject_name"
            )

            percentage = safe_float(
                row.get("percentage")
            )

            if subject is None:
                continue

            if percentage is None:
                continue

            rows.append(
                (
                    str(subject),
                    percentage
                )
            )

        if not rows:

            return (
                "I couldn't determine "
                "your strongest subject."
            )

        best_percentage = max(
            x[1]
            for x in rows
        )

        best_subjects = [
            x[0]
            for x in rows
            if x[1] == best_percentage
        ]

        if len(best_subjects) == 1:

            return (
                f"Your strongest subject is "
                f"{best_subjects[0]} with "
                f"{best_percentage:.2f}%."
            )

        return (
            "Your strongest subjects are "
            + ", ".join(best_subjects)
            + f" with {best_percentage:.2f}%."
        )

    # =====================================================
    # LOWEST SUBJECT
    # =====================================================

    if metric in {
        "lowest_subject",
        "weakest_subject"
    }:

        rows = []

        for row in results:

            subject = row.get(
                "subject_name"
            )

            percentage = safe_float(
                row.get("percentage")
            )

            if subject is None:
                continue

            if percentage is None:
                continue

            rows.append(
                (
                    str(subject),
                    percentage
                )
            )

        if not rows:

            return (
                "I couldn't determine "
                "your weakest subject."
            )

        lowest_percentage = min(
            x[1]
            for x in rows
        )

        lowest_subjects = [
            x[0]
            for x in rows
            if x[1] == lowest_percentage
        ]

        if len(lowest_subjects) == 1:

            return (
                f"Your lowest-performing subject is "
                f"{lowest_subjects[0]} with "
                f"{lowest_percentage:.2f}%."
            )

        return (
            "Your lowest-performing subjects are "
            + ", ".join(lowest_subjects)
            + f" with {lowest_percentage:.2f}%."
        )

    # =====================================================
    # HIGHEST SCORE
    # =====================================================

    if metric == "highest_score":

        row = results[0]

        subject = row.get(
            "subject_name",
            "Unknown subject"
        )

        marks = row.get(
            "marks_obtained"
        )

        maximum = row.get(
            "maximum_marks"
        )

        percentage = safe_float(
            row.get("percentage")
        )

        if percentage is not None:

            return (
                f"Your highest score is in "
                f"{subject}: "
                f"{marks}/{maximum} "
                f"({percentage:.2f}%)."
            )

        return (
            f"Your highest score is in "
            f"{subject}: "
            f"{marks}/{maximum}."
        )

    # =====================================================
    # LOWEST SCORE
    # =====================================================

    if metric == "lowest_score":

        row = results[0]

        subject = row.get(
            "subject_name",
            "Unknown subject"
        )

        marks = row.get(
            "marks_obtained"
        )

        maximum = row.get(
            "maximum_marks"
        )

        percentage = safe_float(
            row.get("percentage")
        )

        if percentage is not None:

            return (
                f"Your lowest score is in "
                f"{subject}: "
                f"{marks}/{maximum} "
                f"({percentage:.2f}%)."
            )

        return (
            f"Your lowest score is in "
            f"{subject}: "
            f"{marks}/{maximum}."
        )

    # =====================================================
    # TREND
    # =====================================================

    if metric == "trend":

        return analyze_marks_trend(
            results
        )

    # =====================================================
    # GENERIC PERFORMANCE
    # =====================================================

    prompt = f"""
You are an educational performance assistant.

Question:
{question}

Student data:
{json.dumps(
    convert_decimals(results),
    indent=2,
    default=str
)}

Metric:
{metric}

Rules:
- Use ONLY the provided data.
- Never invent marks.
- Never invent percentages.
- Do not mention SQL or databases.
- Do not mention AI.
- Use simple English.
- Answer the question directly.
- Keep the response below 150 words.

Return only the answer.
"""

    return call_llm(prompt)


# =========================================================
# MARKS TREND
# =========================================================

def analyze_marks_trend(
    results: list
) -> str:

    if not results:

        return "No marks found."

    lines = [
        "Performance trend:"
    ]

    for row in results:

        subject = row.get(
            "subject_name",
            "Unknown subject"
        )

        exam = row.get(
            "exam_name",
            "Exam"
        )

        marks = row.get(
            "marks_obtained"
        )

        maximum = row.get(
            "maximum_marks"
        )

        lines.append(
            f"• {subject} - {exam}: "
            f"{marks}/{maximum}"
        )

    return "\n".join(lines)


# =========================================================
# ATTENDANCE STATUS
# =========================================================

def normalize_status(status):

    if status is None:

        return ""

    return str(
        status
    ).strip().lower()


# =========================================================
# ATTENDANCE DATE
# =========================================================

def format_attendance_date(value):

    if value is None:

        return "Unknown date"

    if hasattr(
        value,
        "strftime"
    ):

        return value.strftime(
            "%d %b %Y"
        )

    text = str(value)

    if "T" in text:

        text = text.split("T")[0]

    return text[:10]


# =========================================================
# ATTENDANCE COUNTS
# =========================================================

def get_attendance_counts(
    results
):

    present = 0
    absent = 0
    late = 0

    for row in results:

        status = normalize_status(
            row.get("status")
        )

        if status == "present":

            present += 1

        elif status == "absent":

            absent += 1

        elif status == "late":

            late += 1

    return present, absent, late


# =========================================================
# ATTENDANCE ANALYZER
# =========================================================

def analyze_attendance(
    question: str,
    plan: dict,
    results: list
) -> str:

    if not results:

        return "No attendance records found."

    metric = plan.get(
        "metric",
        ""
    )

    constraints = plan.get(
        "constraints",
        {}
    ) or {}

    print("\n========== ATTENDANCE ANALYZER ==========")
    print("Question:", question)
    print("Metric:", metric)
    print("Constraints:", constraints)
    print("Results:", results)
    print("=========================================")

    # =====================================================
    # AGGREGATE ATTENDANCE
    # =====================================================

    if metric in {
        "attendance_percentage",
        "attendance_summary",
        "attendance_eligibility"
    }:

        row = results[0]

        total_days = safe_int(
            row.get("total_days")
        )

        present_days = safe_int(
            row.get("present_days")
        )

        absent_days = safe_int(
            row.get("absent_days")
        )

        late_days = safe_int(
            row.get("late_days")
        )

        percentage = safe_float(
            row.get(
                "attendance_percentage"
            )
        )

        if percentage is None:

            if total_days == 0:

                return "No attendance records found."

            percentage = (
                (present_days + late_days)
                / total_days
            ) * 100

        # -------------------------------------------------
        # PERCENTAGE
        # -------------------------------------------------

        if metric == "attendance_percentage":

            return (
                f"Your attendance is "
                f"{percentage:.2f}% "
                f"({present_days + late_days} out of "
                f"{total_days} recorded days)."
            )

        # -------------------------------------------------
        # SUMMARY
        # -------------------------------------------------

        if metric == "attendance_summary":

            period = get_attendance_period(
                question,
                constraints
            )

            return (
                f"Attendance summary{period}:\n"
                f"• Present: {present_days} days\n"
                f"• Absent: {absent_days} days\n"
                f"• Late: {late_days} days\n"
                f"• Total recorded days: {total_days}\n"
                f"• Attendance: {percentage:.2f}%"
            )

        # -------------------------------------------------
        # ELIGIBILITY
        # -------------------------------------------------

        if metric == "attendance_eligibility":

            if percentage >= 75:

                return (
                    f"Your attendance is "
                    f"{percentage:.2f}%. "
                    f"You meet the 75% attendance "
                    f"requirement."
                )

            return (
                f"Your attendance is "
                f"{percentage:.2f}%. "
                f"You are below the 75% attendance "
                f"requirement."
            )

    # =====================================================
    # MONTHLY ATTENDANCE
    # =====================================================

    if metric in {
        "",
        "monthly_attendance"
    }:

        lines = [
            f"Attendance{get_attendance_period(question, constraints)}:"
        ]

        present = 0
        absent = 0
        late = 0

        for row in results:

            attendance_date = (
                format_attendance_date(
                    row.get(
                        "attendance_date"
                    )
                )
            )

            status = normalize_status(
                row.get("status")
            )

            if status == "present":

                present += 1

            elif status == "absent":

                absent += 1

            elif status == "late":

                late += 1

            lines.append(
                f"• {attendance_date}: "
                f"{status.title() if status else 'Unknown'}"
            )

        total = (
            present
            + absent
            + late
        )

        if total:

            percentage = (
                (present + late)
                / total
            ) * 100

            lines.append("")
            lines.append(
                f"Summary: {present} present, "
                f"{absent} absent, "
                f"{late} late."
            )

            lines.append(
                f"Attendance: "
                f"{percentage:.2f}%"
            )

        return "\n".join(lines)

    # =====================================================
    # ABSENT DAYS
    # =====================================================

    if metric == "absent_days":

        row = results[0]

        if "absent_days" in row:

            count = safe_int(
                row.get("absent_days")
            )

            return (
                f"You were absent for "
                f"{count} day(s)."
            )

        _, absent, _ = (
            get_attendance_counts(
                results
            )
        )

        return (
            f"You were absent for "
            f"{absent} day(s)."
        )

    # =====================================================
    # PRESENT DAYS
    # =====================================================

    if metric == "present_days":

        row = results[0]

        if "present_days" in row:

            count = safe_int(
                row.get("present_days")
            )

            return (
                f"You attended school for "
                f"{count} day(s)."
            )

        present, _, _ = (
            get_attendance_counts(
                results
            )
        )

        return (
            f"You attended school for "
            f"{present} day(s)."
        )

    # =====================================================
    # LATE DAYS
    # =====================================================

    if metric == "late_days":

        row = results[0]

        if "late_days" in row:

            count = safe_int(
                row.get("late_days")
            )

            return (
                f"You were late for "
                f"{count} day(s)."
            )

        _, _, late = (
            get_attendance_counts(
                results
            )
        )

        return (
            f"You were late for "
            f"{late} day(s)."
        )

    # =====================================================
    # ABSENT DATES
    # =====================================================

    if metric in {
        "absent_dates",
        "when_absent"
    }:

        dates = []

        for row in results:

            value = row.get(
                "attendance_date"
            )

            if value is not None:

                dates.append(
                    format_attendance_date(
                        value
                    )
                )

        if not dates:

            return "You have no absent days recorded."

        return (
            "You were absent on:\n"
            + "\n".join(
                f"• {d}"
                for d in dates
            )
        )

    # =====================================================
    # PRESENT DATES
    # =====================================================

    if metric == "present_dates":

        dates = []

        for row in results:

            value = row.get(
                "attendance_date"
            )

            if value is not None:

                dates.append(
                    format_attendance_date(
                        value
                    )
                )

        if not dates:

            return "No present days recorded."

        return (
            "You were present on:\n"
            + "\n".join(
                f"• {d}"
                for d in dates
            )
        )

    # =====================================================
    # LATE DATES
    # =====================================================

    if metric == "late_dates":

        dates = []

        for row in results:

            value = row.get(
                "attendance_date"
            )

            if value is not None:

                dates.append(
                    format_attendance_date(
                        value
                    )
                )

        if not dates:

            return "No late days recorded."

        return (
            "You were late on:\n"
            + "\n".join(
                f"• {d}"
                for d in dates
            )
        )

    # =====================================================
    # ATTENDANCE TREND
    # =====================================================

    if metric in {
        "attendance_trend",
        "trend",
        "improving",
        "change"
    }:

        return analyze_attendance_trend(
            results
        )

    # =====================================================
    # ATTENDANCE COMPARISON
    # =====================================================

    if metric == "attendance_comparison":

        return analyze_attendance_comparison(
            results
        )

    # =====================================================
    # SUBJECT ATTENDANCE
    # =====================================================

    if metric in {
        "subject_attendance",
        "attendance_by_subject"
    }:

        return analyze_subject_attendance(
            results
        )

    # =====================================================
    # FALLBACK
    # =====================================================

    present, absent, late = (
        get_attendance_counts(
            results
        )
    )

    total = (
        present
        + absent
        + late
    )

    if total == 0:

        return "No attendance records found."

    percentage = (
        (present + late)
        / total
    ) * 100

    return (
        f"Your attendance is "
        f"{percentage:.2f}% "
        f"({present + late} out of "
        f"{total} recorded days)."
    )


# =========================================================
# ATTENDANCE TREND
# =========================================================

def analyze_attendance_trend(
    results: list
) -> str:

    trend_data = []

    for row in results:

        month = row.get(
            "month"
        )

        percentage = safe_float(
            row.get(
                "attendance_percentage"
            )
        )

        if percentage is None:

            continue

        if hasattr(
            month,
            "strftime"
        ):

            month_name = month.strftime(
                "%B %Y"
            )

        else:

            month_name = str(
                month
            )

        trend_data.append(
            (
                month_name,
                percentage
            )
        )

    if len(trend_data) < 2:

        return (
            "There is not enough attendance "
            "data to determine a trend."
        )

    first_month, first_percentage = (
        trend_data[0]
    )

    last_month, last_percentage = (
        trend_data[-1]
    )

    difference = (
        last_percentage
        - first_percentage
    )

    if difference > 0:

        status = "improving"

    elif difference < 0:

        status = "declining"

    else:

        status = "unchanged"

    return (
        f"Your attendance is {status}.\n"
        f"• {first_month}: "
        f"{first_percentage:.2f}%\n"
        f"• {last_month}: "
        f"{last_percentage:.2f}%\n"
        f"• Change: "
        f"{difference:+.2f}%"
    )


# =========================================================
# ATTENDANCE COMPARISON
# =========================================================

def analyze_attendance_comparison(
    results: list
) -> str:

    rows = []

    for row in results:

        month = row.get(
            "month"
        )

        percentage = safe_float(
            row.get(
                "attendance_percentage"
            )
        )

        if percentage is None:

            continue

        if hasattr(
            month,
            "strftime"
        ):

            month = month.strftime(
                "%B %Y"
            )

        rows.append(
            (
                str(month),
                percentage
            )
        )

    if len(rows) < 2:

        return (
            "There is not enough attendance "
            "data to compare."
        )

    lines = [
        "Attendance comparison:"
    ]

    for month, percentage in rows:

        lines.append(
            f"• {month}: "
            f"{percentage:.2f}%"
        )

    difference = (
        rows[-1][1]
        - rows[0][1]
    )

    lines.append(
        f"• Change: "
        f"{difference:+.2f}%"
    )

    return "\n".join(lines)


# =========================================================
# SUBJECT ATTENDANCE
# =========================================================

def analyze_subject_attendance(
    results: list
) -> str:

    if not results:

        return (
            "No subject-wise attendance "
            "records found."
        )

    lines = [
        "Subject-wise attendance:"
    ]

    for row in results:

        subject = row.get(
            "subject_name",
            "Unknown subject"
        )

        percentage = safe_float(
            row.get(
                "attendance_percentage"
            )
        )

        present = row.get(
            "present_days"
        )

        total = row.get(
            "total_days"
        )

        if percentage is not None:

            lines.append(
                f"• {subject}: "
                f"{percentage:.2f}%"
            )

            continue

        if (
            present is not None
            and total is not None
        ):

            present = safe_int(
                present
            )

            total = safe_int(
                total
            )

            percentage = (
                present / total * 100
                if total
                else 0
            )

            lines.append(
                f"• {subject}: "
                f"{percentage:.2f}% "
                f"({present}/{total})"
            )

            continue

        lines.append(
            f"• {subject}: "
            "Attendance data available"
        )

    return "\n".join(lines)


# =========================================================
# ATTENDANCE PERIOD
# =========================================================

def get_attendance_period(
    question: str,
    constraints: dict
) -> str:

    constraints = constraints or {}

    month = constraints.get(
        "month"
    )

    year = constraints.get(
        "year"
    )

    if month:

        month_names = [
            "",
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December"
        ]

        try:

            month_number = int(
                month
            )

            if 1 <= month_number <= 12:

                name = month_names[
                    month_number
                ]

                if year:

                    return (
                        f" for {name} "
                        f"{year}"
                    )

                return (
                    f" for {name}"
                )

        except (
            TypeError,
            ValueError
        ):

            pass

    q = (
        question
        .lower()
        .strip()
    )

    if "this month" in q:

        return " for this month"

    if "last month" in q:

        return " for last month"

    return ""


# =========================================================
# ASSIGNMENT DATE FORMAT
# =========================================================

def format_assignment_date(
    value
):

    if value is None:

        return "Not specified"

    if hasattr(
        value,
        "strftime"
    ):

        return value.strftime(
            "%d %b %Y"
        )

    text = str(value)

    if "T" in text:

        text = text.split("T")[0]

    return text


# =========================================================
# ASSIGNMENT ANALYZER
# =========================================================

def analyze_assignments(
    question: str,
    plan: dict,
    results: list
) -> str:

    if not results:

        return "No assignments found."

    print("\n===== ASSIGNMENT ANALYZER =====")
    print("Question:", question)
    print("Metric:", plan.get("metric", ""))
    print("Constraints:", plan.get("constraints", {}))
    print("Results:", results)
    print("===============================")

    metric = plan.get(
        "metric",
        ""
    )

    constraints = (
        plan.get(
            "constraints",
            {}
        )
        or {}
    )

    # =====================================================
    # SPECIFIC ASSIGNMENT
    # =====================================================

    if len(results) == 1:

        return format_single_assignment(
            results[0],
            question
        )

    # =====================================================
    # DUE DATE QUERY
    # =====================================================

    if is_due_date_question(
        question
    ):

        return format_due_dates(
            results
        )

    # =====================================================
    # UPCOMING
    # =====================================================

    if metric in {
        "upcoming",
        "upcoming_assignments"
    }:

        return format_assignment_list(
            results,
            title="Upcoming assignments:"
        )

    # =====================================================
    # OVERDUE
    # =====================================================

    if metric in {
        "overdue",
        "overdue_assignments"
    }:

        return format_assignment_list(
            results,
            title="Overdue assignments:"
        )

    # =====================================================
    # TODAY
    # =====================================================

    if metric in {
        "today",
        "due_today"
    }:

        return format_assignment_list(
            results,
            title="Assignments due today:"
        )

    # =====================================================
    # TOMORROW
    # =====================================================

    if metric in {
        "tomorrow",
        "due_tomorrow"
    }:

        return format_assignment_list(
            results,
            title="Assignments due tomorrow:"
        )

    # =====================================================
    # COUNT
    # =====================================================

    if metric in {
        "count",
        "assignment_count",
        "number"
    }:

        return (
            f"You have {len(results)} "
            f"assignment(s)."
        )

    # =====================================================
    # GENERAL LIST
    # =====================================================

    return format_assignment_list(
        results,
        title="Assignments:"
    )


# =========================================================
# SINGLE ASSIGNMENT FORMAT
# =========================================================

def format_single_assignment(
    row: dict,
    question: str = ""
) -> str:

    subject = row.get(
        "subject_name"
    )

    title = row.get(
        "title",
        "Assignment"
    )

    description = row.get(
        "description"
    )

    assigned_date = row.get(
        "assigned_date"
    )

    due_date = row.get(
        "due_date"
    )

    lines = [
        str(title)
    ]

    if subject:

        lines.append(
            f"Subject: {subject}"
        )

    if description:

        lines.append(
            f"Description: {description}"
        )

    if assigned_date:

        lines.append(
            f"Assigned Date: "
            f"{format_assignment_date(assigned_date)}"
        )

    if due_date:

        lines.append(
            f"Due Date: "
            f"{format_assignment_date(due_date)}"
        )

    return "\n".join(lines)


# =========================================================
# DUE DATE QUESTION DETECTION
# =========================================================

def is_due_date_question(
    question: str
) -> bool:

    if not question:

        return False

    q = question.lower()

    patterns = [
        "due date",
        "when is",
        "when's",
        "when is it due",
        "when is this due",
        "deadline",
        "due on",
        "due by"
    ]

    return any(
        pattern in q
        for pattern in patterns
    )


# =========================================================
# FORMAT DUE DATES
# =========================================================

def format_due_dates(
    results: list
) -> str:

    if not results:

        return "No assignments found."

    lines = [
        "Assignment due dates:"
    ]

    for row in results:

        title = row.get(
            "title",
            "Assignment"
        )

        subject = row.get(
            "subject_name"
        )

        due_date = row.get(
            "due_date"
        )

        text = f"• {title}"

        if subject:

            text += (
                f" ({subject})"
            )

        if due_date:

            text += (
                f": {format_assignment_date(due_date)}"
            )

        else:

            text += ": No due date specified"

        lines.append(text)

    return "\n".join(lines)


# =========================================================
# FORMAT ASSIGNMENT LIST
# =========================================================

def format_assignment_list(
    results: list,
    title: str = "Assignments:"
) -> str:

    if not results:

        return "No assignments found."

    lines = [
        title
    ]

    for row in results:

        assignment_title = row.get(
            "title",
            "Assignment"
        )

        subject = row.get(
            "subject_name"
        )

        description = row.get(
            "description"
        )

        due_date = row.get(
            "due_date"
        )

        text = f"• {assignment_title}"

        if subject:

            text += (
                f" — {subject}"
            )

        if due_date:

            text += (
                f" — Due: "
                f"{format_assignment_date(due_date)}"
            )

        if description:

            text += (
                f"\n  {description}"
            )

        lines.append(text)

    return "\n".join(lines)


# =========================================================
# MARKS ANALYZER
# =========================================================

def analyze_marks(
    question: str,
    plan: dict,
    results: list
) -> str:

    if not results:

        return "No marks found."

    # -----------------------------------------------------
    # Single result
    # -----------------------------------------------------

    if len(results) == 1:

        row = results[0]

        subject = row.get(
            "subject_name",
            ""
        )

        exam = row.get(
            "exam_name"
        )

        marks = row.get(
            "marks_obtained"
        )

        maximum = row.get(
            "maximum_marks"
        )

        percentage = safe_float(
            row.get("percentage")
        )

        text = ""

        if subject:

            text += subject

        if exam:

            text += (
                f" — {exam}"
            )

        if marks is not None:

            text += (
                f": {marks}/{maximum}"
            )

        if percentage is not None:

            text += (
                f" ({percentage:.2f}%)"
            )

        return text.strip()

    # -----------------------------------------------------
    # Multiple marks
    # -----------------------------------------------------

    lines = [
        "Marks:"
    ]

    for row in results:

        subject = row.get(
            "subject_name",
            "Subject"
        )

        exam = row.get(
            "exam_name"
        )

        marks = row.get(
            "marks_obtained"
        )

        maximum = row.get(
            "maximum_marks"
        )

        percentage = safe_float(
            row.get("percentage")
        )

        text = f"• {subject}"

        if exam:

            text += (
                f" — {exam}"
            )

        if marks is not None:

            text += (
                f": {marks}/{maximum}"
            )

        if percentage is not None:

            text += (
                f" ({percentage:.2f}%)"
            )

        lines.append(text)

    return "\n".join(lines)


# =========================================================
# TIMETABLE ANALYZER
# =========================================================

def analyze_timetable(
    question: str,
    plan: dict,
    results: list
) -> str:

    if not results:

        return "No timetable entries found."

    lines = [
        "Timetable:"
    ]

    for row in results:

        day = row.get(
            "day_of_week",
            ""
        )

        subject = row.get(
            "subject_name",
            "Unknown subject"
        )

        start = row.get(
            "start_time"
        )

        end = row.get(
            "end_time"
        )

        room = row.get(
            "room_number"
        )

        period = row.get(
            "period_number"
        )

        text = f"• {subject}"

        if day:

            text += (
                f" — {day}"
            )

        if start and end:

            text += (
                f", {start} - {end}"
            )

        if period:

            text += (
                f", Period {period}"
            )

        if room:

            text += (
                f", Room {room}"
            )

        lines.append(text)

    return "\n".join(lines)


# =========================================================
# EXAM ANALYZER
# =========================================================

def analyze_exams(
    question: str,
    plan: dict,
    results: list
) -> str:

    if not results:

        return "No exams found."

    if len(results) == 1:

        row = results[0]

        exam_name = row.get(
            "exam_name",
            "Exam"
        )

        academic_year = row.get(
            "academic_year"
        )

        start_date = row.get(
            "start_date"
        )

        end_date = row.get(
            "end_date"
        )

        lines = [
            str(exam_name)
        ]

        if academic_year:

            lines.append(
                f"Academic Year: {academic_year}"
            )

        if start_date:

            lines.append(
                f"Start Date: "
                f"{format_assignment_date(start_date)}"
            )

        if end_date:

            lines.append(
                f"End Date: "
                f"{format_assignment_date(end_date)}"
            )

        return "\n".join(lines)

    lines = [
        "Exams:"
    ]

    for row in results:

        name = row.get(
            "exam_name",
            "Exam"
        )

        start = row.get(
            "start_date"
        )

        end = row.get(
            "end_date"
        )

        text = f"• {name}"

        if start:

            text += (
                f": {format_assignment_date(start)}"
            )

            if end:

                text += (
                    f" - "
                    f"{format_assignment_date(end)}"
                )

        lines.append(text)

    return "\n".join(lines)


# =========================================================
# TEACHER ANALYZER
# =========================================================

def analyze_teacher(
    question: str,
    plan: dict,
    results: list
) -> str:

    if not results:

        return "No teacher information found."

    lines = [
        "Teacher information:"
    ]

    seen = set()

    for row in results:

        first_name = row.get(
            "first_name",
            ""
        )

        last_name = row.get(
            "last_name",
            ""
        )

        email = row.get(
            "email"
        )

        subject = row.get(
            "subject_name"
        )

        name = (
            f"{first_name} {last_name}"
        ).strip()

        key = (
            name,
            email,
            subject
        )

        if key in seen:

            continue

        seen.add(key)

        text = f"• {name}"

        if subject:

            text += (
                f" — {subject}"
            )

        if email:

            text += (
                f" — {email}"
            )

        lines.append(text)

    return "\n".join(lines)


# =========================================================
# PROFILE ANALYZER
# =========================================================

def analyze_profile(
    question: str,
    plan: dict,
    results: list
) -> str:

    if not results:

        return "Student profile not found."

    row = results[0]

    student_id = row.get(
        "student_id"
    )

    first_name = row.get(
        "first_name",
        ""
    )

    last_name = row.get(
        "last_name",
        ""
    )

    roll_number = row.get(
        "roll_number"
    )

    class_name = row.get(
        "class_name"
    )

    section = row.get(
        "section"
    )

    academic_year = row.get(
        "academic_year"
    )

    dob = row.get(
        "date_of_birth"
    )

    gender = row.get(
        "gender"
    )

    admission_date = row.get(
        "admission_date"
    )

    lines = [
        "Student Profile:"
    ]

    if first_name or last_name:

        lines.append(
            f"• Name: "
            f"{first_name} {last_name}".strip()
        )

    if student_id:

        lines.append(
            f"• Student ID: {student_id}"
        )

    if class_name:

        text = (
            f"• Class: {class_name}"
        )

        if section:

            text += (
                f" - {section}"
            )

        lines.append(text)

    if roll_number:

        lines.append(
            f"• Roll Number: {roll_number}"
        )

    if academic_year:

        lines.append(
            f"• Academic Year: {academic_year}"
        )

    if dob:

        lines.append(
            f"• Date of Birth: "
            f"{format_assignment_date(dob)}"
        )

    if gender:

        lines.append(
            f"• Gender: {gender}"
        )

    if admission_date:

        lines.append(
            f"• Admission Date: "
            f"{format_assignment_date(admission_date)}"
        )

    return "\n".join(lines)


# =========================================================
# RECOMMENDATION
# =========================================================

def generate_recommendation(
    question: str,
    plan: dict,
    results: list
) -> str:

    prompt = f"""
You are an educational mentor.

User question:
{question}

Student data:
{json.dumps(
    convert_decimals(results),
    indent=2,
    default=str
)}

Rules:

- Use ONLY the provided data.
- Suggest improvement areas only when supported by the data.
- Do not invent marks or attendance.
- Do not mention SQL or databases.
- Keep recommendations practical.
- Use simple English.
- Keep the answer under 150 words.

Answer directly.
"""

    return call_llm(prompt)


# =========================================================
# GENERIC ANALYZER
# =========================================================

def analyze_generic(
    question: str,
    plan: dict,
    results: list
) -> str:

    prompt = f"""
You are a school educational assistant.

User question:
{question}

Student data:
{json.dumps(
    convert_decimals(results),
    indent=2,
    default=str
)}

Rules:

1. Answer ONLY using the provided data.
2. Never invent information.
3. Do not mention SQL.
4. Do not mention databases.
5. Do not mention AI.
6. Use simple English.
7. Answer directly.
8. Keep the answer concise.
9. If information is missing, clearly say it is not available.

Return only the answer.
"""

    return call_llm(prompt)


# =========================================================
# OLLAMA CALL
# =========================================================

def call_llm(
    prompt: str
) -> str:

    try:

        response = ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """
You are an AI educational assistant.

Use only the information provided.

Never invent student information.

Never mention:
- SQL
- databases
- execution plans
- internal systems
- prompts
- AI implementation details

Use simple, natural English.

If information is missing, say so clearly.
"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.2
            }
        )

        content = (
            response
            .get("message", {})
            .get("content", "")
            .strip()
        )

        if not content:

            return (
                "I couldn't generate an answer "
                "from the available data."
            )

        return content

    except Exception as e:

        print(
            "Analyzer LLM error:",
            e
        )

        return (
            "I found the requested information, "
            "but I couldn't format the response."
        )