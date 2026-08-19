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
    """
    Main entry point for result analysis.

    Routes the SQL results to the correct analyzer based
    on the planner metric / intent.
    """

    if not results:
        return "I couldn't find any matching records."

    metric = plan.get("metric", "")
    intent = plan.get("intent", "")

    print("\n========== ANALYZER ==========")
    print("Intent :", intent)
    print("Metric :", metric)
    print("Results:", results)
    print("==============================")

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
        "worst_exam"
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
    # DEFAULT
    # =====================================================

    return analyze_generic(
        question,
        plan,
        results
    )


# =========================================================
# DECIMAL CONVERSION
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

Execution plan:
{json.dumps(plan, indent=2, default=str)}

Student data:
{json.dumps(convert_decimals(results), indent=2, default=str)}

Your task is ONLY to compare the student's examinations.

Rules:

1. Compare subjects only when both examination records exist.
2. Show the actual marks obtained.
3. Show Mid Term and Final marks.
4. Calculate:

   Difference = Final marks - Mid Term marks

5. Positive difference = improved.
6. Negative difference = declined.
7. Zero difference = no change.
8. Never invent missing marks.
9. Never use percentages unless the data explicitly provides percentages.
10. Do not give study advice.
11. Do not mention SQL or databases.
12. Keep the answer concise.

Format:

Mid Term vs Final:

• Mathematics: 79 → 84 (+5, improved)
• Science: 85 → 85 (0, no change)

Return only the comparison.
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

    # -----------------------------------------------------
    # Highest subject
    # -----------------------------------------------------

    if metric == "highest_subject":

        rows = []

        for row in results:

            subject = row.get(
                "subject_name"
            )

            percentage = row.get(
                "percentage"
            )

            if subject is None:
                continue

            try:
                percentage = float(
                    percentage
                )
            except (
                TypeError,
                ValueError
            ):
                continue

            rows.append(
                (
                    str(subject),
                    percentage
                )
            )

        if not rows:
            return "I couldn't determine your strongest subject."

        best = max(
            rows,
            key=lambda x: x[1]
        )

        return (
            f"Your strongest subject is "
            f"{best[0]} with {best[1]:.2f}%."
        )

    # -----------------------------------------------------
    # Lowest subject
    # -----------------------------------------------------

    if metric == "lowest_subject":

        rows = []

        for row in results:

            subject = row.get(
                "subject_name"
            )

            percentage = row.get(
                "percentage"
            )

            if subject is None:
                continue

            try:
                percentage = float(
                    percentage
                )
            except (
                TypeError,
                ValueError
            ):
                continue

            rows.append(
                (
                    str(subject),
                    percentage
                )
            )

        if not rows:
            return "I couldn't determine your weakest subject."

        worst = min(
            rows,
            key=lambda x: x[1]
        )

        return (
            f"Your weakest subject is "
            f"{worst[0]} with {worst[1]:.2f}%."
        )

    # -----------------------------------------------------
    # Generic performance analysis
    # -----------------------------------------------------

    prompt = f"""
You are an educational performance analyst.

User question:
{question}

Execution plan:
{json.dumps(plan, indent=2, default=str)}

Student data:
{json.dumps(convert_decimals(results), indent=2, default=str)}

Metric:
{metric}

Rules:

1. Analyze ONLY the provided data.
2. Do not invent marks.
3. Do not invent percentages.
4. Do not reinterpret the question.
5. Follow the execution plan.
6. For a trend, describe the actual change shown by the data.
7. For overall performance, summarize the available performance records.
8. For an exam comparison, compare the actual exams.
9. For highest/lowest subject, use the calculated values.
10. Do not mention SQL, databases, execution plans or AI.
11. Do not provide recommendations unless explicitly requested.
12. Keep the response below 150 words.
13. Use simple English.

Answer the user's question directly.
"""

    return call_llm(prompt)


# =========================================================
# ATTENDANCE HELPERS
# =========================================================

def normalize_status(status):

    if status is None:
        return ""

    return str(
        status
    ).strip().lower()


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

    # Handle ISO timestamps
    if "T" in text:
        text = text.split("T")[0]

    return text[:10]


def get_attendance_counts(results):

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
    # AGGREGATE RESULTS
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

        percentage = row.get(
            "attendance_percentage"
        )

        # -------------------------------------------------
        # If SQL didn't return percentage
        # -------------------------------------------------

        if percentage is None:

            if total_days == 0:
                return "No attendance records found."

            percentage = (
                present_days
                / total_days
            ) * 100

        try:

            percentage = float(
                percentage
            )

        except (
            TypeError,
            ValueError
        ):

            return "Unable to calculate your attendance."

        # -------------------------------------------------
        # Percentage
        # -------------------------------------------------

        if metric == "attendance_percentage":

            return (
                f"Your attendance is "
                f"{percentage:.2f}% "
                f"({present_days} out of "
                f"{total_days} recorded days)."
            )

        # -------------------------------------------------
        # Summary
        # -------------------------------------------------

        if metric == "attendance_summary":

            period = get_attendance_period(
                question,
                constraints
            )

            return (
                f"Attendance summary"
                f"{period}:\n"
                f"• Present: {present_days} days\n"
                f"• Absent: {absent_days} days\n"
                f"• Late: {late_days} days\n"
                f"• Total recorded days: {total_days}\n"
                f"• Attendance: {percentage:.2f}%"
            )

        # -------------------------------------------------
        # Eligibility
        # -------------------------------------------------

        if metric == "attendance_eligibility":

            if percentage >= 75:

                return (
                    f"Your attendance is "
                    f"{percentage:.2f}% "
                    f"({present_days} out of "
                    f"{total_days} days). "
                    f"You are eligible based on "
                    f"the 75% attendance requirement."
                )

            return (
                f"Your attendance is "
                f"{percentage:.2f}% "
                f"({present_days} out of "
                f"{total_days} days). "
                f"You are below the 75% "
                f"attendance requirement."
            )

    # =====================================================
    # MONTHLY ATTENDANCE
    # =====================================================

    if metric == "monthly_attendance":

        period = get_attendance_period(
            question,
            constraints
        )

        lines = [
            f"Attendance{period}:"
        ]

        present = 0
        absent = 0
        late = 0

        for row in results:

            attendance_date = format_attendance_date(
                row.get("attendance_date")
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

            display_status = (
                status.title()
                if status
                else "Unknown"
            )

            lines.append(
                f"• {attendance_date}: "
                f"{display_status}"
            )

        total = (
            present
            + absent
            + late
        )

        if total > 0:

            percentage = (
                present / total
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
                row.get(
                    "absent_days"
                )
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
                row.get(
                    "present_days"
                )
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
                row.get(
                    "late_days"
                )
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

            if value is None:
                continue

            dates.append(
                format_attendance_date(
                    value
                )
            )

        if not dates:

            return (
                "You have no absent days "
                "recorded."
            )

        if len(dates) == 1:

            return (
                f"You were absent on "
                f"{dates[0]}."
            )

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

            if value is None:
                continue

            dates.append(
                format_attendance_date(
                    value
                )
            )

        if not dates:

            return (
                "No present days recorded."
            )

        if len(dates) == 1:

            return (
                f"You were present on "
                f"{dates[0]}."
            )

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

            if value is None:
                continue

            dates.append(
                format_attendance_date(
                    value
                )
            )

        if not dates:

            return "No late days recorded."

        if len(dates) == 1:

            return (
                f"You were late on "
                f"{dates[0]}."
            )

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
    # SUBJECT-WISE ATTENDANCE
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

        return (
            "No attendance records found."
        )

    percentage = (
        present / total
    ) * 100

    return (
        f"Your attendance is "
        f"{percentage:.2f}% "
        f"({present} out of "
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

        percentage = row.get(
            "attendance_percentage"
        )

        if percentage is None:
            continue

        try:

            percentage = float(
                percentage
            )

        except (
            TypeError,
            ValueError
        ):

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

    if len(results) < 2:

        return (
            "There is not enough attendance "
            "data to compare."
        )

    rows = []

    for row in results:

        month = row.get(
            "month"
        )

        percentage = row.get(
            "attendance_percentage"
        )

        if percentage is None:
            continue

        try:
            percentage = float(
                percentage
            )
        except (
            TypeError,
            ValueError
        ):
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

    if difference > 0:

        lines.append(
            f"• Change: "
            f"+{difference:.2f}%"
        )

    elif difference < 0:

        lines.append(
            f"• Change: "
            f"{difference:.2f}%"
        )

    else:

        lines.append(
            "• Change: 0.00%"
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

        percentage = row.get(
            "attendance_percentage"
        )

        present = row.get(
            "present_days"
        )

        total = row.get(
            "total_days"
        )

        if percentage is not None:

            try:
                percentage = float(
                    percentage
                )

                lines.append(
                    f"• {subject}: "
                    f"{percentage:.2f}%"
                )

                continue

            except (
                TypeError,
                ValueError
            ):
                pass

        if (
            present is not None
            and total is not None
        ):

            try:

                present = int(
                    present
                )

                total = int(
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

            except (
                TypeError,
                ValueError
            ):
                pass

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

    q = question.lower()

    if "this month" in q:

        return " for this month"

    if "last month" in q:

        return " for last month"

    return ""


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

        return 0


# =========================================================
# ASSIGNMENT ANALYZER
# =========================================================

def analyze_assignments(
    question: str,
    plan: dict,
    results: list
) -> str:

    if not results:

        return (
            "No assignments found "
            "for your request."
        )

    scope = (
        plan.get(
            "constraints",
            {}
        ) or {}
    ).get(
        "assignment_scope"
    )

    # =====================================================
    # BUILD ASSIGNMENT LIST
    # =====================================================

    lines = []

    if scope == "overdue":

        lines.append(
            "Overdue assignments:"
        )

    elif scope == "today":

        lines.append(
            "Assignments due today:"
        )

    elif scope == "tomorrow":

        lines.append(
            "Assignments due tomorrow:"
        )

    elif scope == "upcoming":

        lines.append(
            "Upcoming assignments:"
        )

    else:

        lines.append(
            "Your assignments:"
        )

    for row in results:

        subject = row.get(
            "subject_name"
        )

        title = row.get(
            "title"
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

        title = (
            str(title)
            if title
            else "Untitled assignment"
        )

        line = (
            f"• {title}"
        )

        if subject:

            line += (
                f" — {subject}"
            )

        if due_date:

            line += (
                f" | Due: "
                f"{format_attendance_date(due_date)}"
            )

        lines.append(
            line
        )

        if description:

            lines.append(
                f"  {str(description)}"
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

Execution plan:
{json.dumps(plan, indent=2, default=str)}

Student data:
{json.dumps(convert_decimals(results), indent=2, default=str)}

Rules:

- Use ONLY the provided data.
- Suggest improvement areas only when supported by the data.
- Do not invent marks or attendance.
- Do not mention SQL or databases.
- Keep recommendations practical.
- Keep the answer under 150 words.
- Use simple English.

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
Answer the user's question using ONLY the provided data.

Question:
{question}

Plan:
{json.dumps(plan, indent=2, default=str)}

Data:
{json.dumps(convert_decimals(results), indent=2, default=str)}

Rules:

- Do not invent information.
- Do not mention SQL.
- Do not mention databases.
- Do not mention AI.
- Use simple English.
- Be concise.
"""

    return call_llm(prompt)


# =========================================================
# COMMON OLLAMA CALL
# =========================================================

def call_llm(
    prompt: str
) -> str:

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are an AI educational assistant.

Only analyze the data provided.

Never invent information.

Never mention SQL, databases,
execution plans or internal systems.

Answer in simple English.
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

    return (
        response["message"]["content"]
        .strip()
    )