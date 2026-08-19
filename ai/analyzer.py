import json
import ollama
from decimal import Decimal

MODEL = "llama3:latest"


def analyze_results(question: str, plan: dict, results: list) -> str:
    """
    Main entry point for analysis.
    Routes to the appropriate analysis prompt.
    """

    if not results:
        return "I couldn't find enough data to analyze."

    operation = plan.get("operation", "")
    query_type = plan.get("query_type", "")
    
    metric = plan.get("metric", "")

    if metric == "exam_comparison":
        return compare_results(question, plan, results)

    elif metric == "trend":
        return analyze_performance(question, plan, results)

    elif metric == "highest_subject":
        return analyze_performance(question, plan, results)

    elif metric == "lowest_subject":
        return analyze_performance(question, plan, results)

    elif metric == "recommendation":
        return generate_recommendation(question, plan, results)
    
    elif metric == "overall_performance":
        return analyze_performance(question, plan, results)

    elif metric == "best_exam":
        return analyze_performance(question, plan, results)

    elif metric == "worst_exam":
        return analyze_performance(question, plan, results)
    
    elif metric == "attendance_summary":
        return analyze_attendance(question, plan, results)

    elif metric == "attendance_percentage":
        return analyze_attendance(question, plan, results)

    elif metric == "absent_days":
        return analyze_attendance(question, plan, results)

    elif metric == "late_days":
        return analyze_attendance(question, plan, results)

    elif metric == "attendance_trend":
        return analyze_attendance(question, plan, results)

    elif metric == "attendance_comparison":
        return analyze_attendance(question, plan, results)

    elif metric == "attendance_eligibility":
        return analyze_attendance(question, plan, results)
    
    elif metric == "absent_dates":
        return analyze_attendance(question, plan, results)

    elif metric == "present_dates":
        return analyze_attendance(question, plan, results)

# --------------------------------------------------------
# Compare
# --------------------------------------------------------
def convert_decimals(obj):
    if isinstance(obj, Decimal):
        return float(obj)

    if isinstance(obj, list):
        return [convert_decimals(item) for item in obj]

    if isinstance(obj, dict):
        return {
            key: convert_decimals(value)
            for key, value in obj.items()
        }

    return obj


def compare_results(question: str, plan: dict, results: list) -> str:

    prompt = f"""
You are an educational performance comparison assistant.

The user asked:
{question}

Execution Plan:
{json.dumps(plan, indent=2)}

Student Data:
{json.dumps(results, indent=2, default=str)}

Your task is ONLY to compare the student's Mid Term Examination
with the Final Examination.

STRICT RULES:

1. Compare ONLY subjects that have marks in BOTH exams.
2. For every subject, show:
   - Mid Term marks
   - Final marks
   - Difference = Final marks - Mid Term marks
3. If difference is positive, say "improved".
4. If difference is negative, say "declined".
5. If difference is zero, say "no change".
6. Do NOT mention strengths.
7. Do NOT mention weaknesses.
8. Do NOT give recommendations.
9. Do NOT give study advice.
10. Do NOT add an overall judgment unless it is directly supported by the data.
11. Do NOT invent missing marks.
12. Do NOT mention SQL, databases, execution plans, or AI.
13. Keep the answer concise.

Use this format:

Mid Term vs Final:

• Subject: Mid Term → Final (difference, status)
• Subject: Mid Term → Final (difference, status)

Example:
Mid Term vs Final:

• Mathematics: 84 → 79 (-5, declined)
• Science: 88 → 85 (-3, declined)
• English: 87 → 82 (-5, declined)

Return ONLY the comparison.
"""

    return call_llm(prompt)

# --------------------------------------------------------
# Analyze
# --------------------------------------------------------

def analyze_performance(question: str, plan: dict, results: list) -> str:

    prompt = f"""
You are an educational performance analyst.

Analyze the following student data.

Question:
{question}

Execution Plan:
{json.dumps(plan, indent=2)}

Data:
{json.dumps(results, indent=2, default=str)}

Instructions:

- Identify trends.
- Mention strengths.
- Mention weaknesses.
- Mention important observations.
- Do NOT invent information.
- Keep the answer under 150 words.

IMPORTANT

The execution plan has already determined the user's intent.

Trust the execution plan.

Do NOT reinterpret the question.

Analyze ONLY according to the execution plan.
"""

    return call_llm(prompt)


def analyze_attendance(question: str, plan: dict, results: list) -> str:

    if not results:
        return "No attendance records found."

    metric = plan.get("metric", "")

    present = 0
    absent = 0
    late = 0

    for r in results:
        status = str(r["status"]).lower().strip()

        if status == "present":
            present += 1
        elif status == "absent":
            absent += 1
        elif status == "late":
            late += 1

    total = present + absent + late

    if total == 0:
        return "No attendance records found."

    # -------------------------------------------------
    # SUMMARY
    # -------------------------------------------------

    if metric == "attendance_summary":

        return (
            f"Attendance summary:\n"
            f"• Present: {present} days\n"
            f"• Absent: {absent} days\n"
            f"• Late: {late} days\n"
            f"• Total recorded days: {total}"
        )

    # -------------------------------------------------
    # PERCENTAGE
    # -------------------------------------------------

    elif metric == "attendance_percentage":

        attended = present + late
        percentage = (attended / total) * 100

        return (
            f"Your attendance is {percentage:.2f}% "
            f"({attended} out of {total} days)."
        )

    # -------------------------------------------------
    # ABSENT DAYS
    # -------------------------------------------------

    elif metric == "absent_days":

        return f"You were absent for {absent} day(s)."
    
    # -------------------------------------------------
    # ABSENT DATES
    # -------------------------------------------------

    elif metric == "absent_dates":

        dates = []

        for r in results:
            date_value = r["attendance_date"]

            if hasattr(date_value, "strftime"):
                date_value = date_value.strftime("%Y-%m-%d")
            else:
                date_value = str(date_value)[:10]

            dates.append(date_value)

        if not dates:
            return "You have no absent days recorded."

        if len(dates) == 1:
            return f"You were absent on {dates[0]}."

        return (
            "You were absent on:\n"
            + "\n".join(f"• {date}" for date in dates)
        )
        
        # -------------------------------------------------
    # PRESENT DATES
    # -------------------------------------------------

    elif metric == "present_dates":

        dates = []

        for r in results:
            date_value = r["attendance_date"]

            if hasattr(date_value, "strftime"):
                date_value = date_value.strftime("%Y-%m-%d")
            else:
                date_value = str(date_value)[:10]

            dates.append(date_value)

        if not dates:
            return "You have no present days recorded."

        if len(dates) == 1:
            return f"You were present on {dates[0]}."

        return (
            "You were present on:\n"
            + "\n".join(f"• {date}" for date in dates)
        )
    
    
    # -------------------------------------------------
    # LATE DAYS
    # -------------------------------------------------

    elif metric == "late_days":

        return f"You were late on {late} day(s)."

    # -------------------------------------------------
    # ELIGIBILITY
    # -------------------------------------------------

    elif metric == "attendance_eligibility":

        attended = present + late
        percentage = (attended / total) * 100

        if percentage >= 75:
            return (
                f"Your attendance is {percentage:.2f}%, "
                f"so you meet the 75% attendance requirement."
            )
        else:
            return (
                f"Your attendance is {percentage:.2f}%, "
                f"which is below the 75% requirement."
            )

    # -------------------------------------------------
    # TREND
    # -------------------------------------------------

    elif metric == "attendance_trend":

        if len(results) < 2:
            return "There is not enough attendance data to determine a trend."

        midpoint = len(results) // 2

        first_half = results[:midpoint]
        second_half = results[midpoint:]

        def calculate_percentage(records):

            p = sum(
                1 for r in records
                if str(r["status"]).lower() == "present"
            )

            l = sum(
                1 for r in records
                if str(r["status"]).lower() == "late"
            )

            if not records:
                return 0

            return ((p + l) / len(records)) * 100

        first_percentage = calculate_percentage(first_half)
        second_percentage = calculate_percentage(second_half)

        difference = second_percentage - first_percentage

        if difference > 0:
            return (
                f"Your attendance is improving. "
                f"It increased from {first_percentage:.2f}% "
                f"to {second_percentage:.2f}%."
            )

        elif difference < 0:
            return (
                f"Your attendance has declined. "
                f"It decreased from {first_percentage:.2f}% "
                f"to {second_percentage:.2f}%."
            )

        else:
            return (
                f"Your attendance has remained stable at "
                f"{second_percentage:.2f}%."
            )

    # -------------------------------------------------
    # COMPARISON
    # -------------------------------------------------

    elif metric == "attendance_comparison":

        from datetime import datetime

        dated_results = []

        for r in results:
            date_value = r["attendance_date"]

            if isinstance(date_value, str):
                date_value = datetime.strptime(
                    date_value[:10],
                    "%Y-%m-%d"
                ).date()

            dated_results.append((date_value, r["status"]))

        if len(dated_results) < 2:
            return "There is not enough attendance data for comparison."

        dated_results.sort(key=lambda x: x[0])

        midpoint = len(dated_results) // 2

        first_period = dated_results[:midpoint]
        second_period = dated_results[midpoint:]

        def period_percentage(records):

            if not records:
                return 0

            attended = sum(
                1
                for _, status in records
                if str(status).lower() in ["present", "late"]
            )

            return (attended / len(records)) * 100

        first_percentage = period_percentage(first_period)
        second_percentage = period_percentage(second_period)

        difference = second_percentage - first_percentage

        if difference > 0:
            status = "improved"
        elif difference < 0:
            status = "declined"
        else:
            status = "remained the same"

        return (
            f"Attendance {status}: "
            f"{first_percentage:.2f}% → "
            f"{second_percentage:.2f}% "
            f"({difference:+.2f}%)."
        )

    return "I couldn't determine your attendance information."

# --------------------------------------------------------
# Recommendation
# --------------------------------------------------------

def generate_recommendation(question: str, plan: dict, results: list) -> str:

    prompt = f"""
You are an educational mentor.

Use ONLY the data below.

Question:
{question}

Execution Plan:
{json.dumps(plan, indent=2)}

Data:
{json.dumps(convert_decimals(results), indent=2)}

Instructions:

- Suggest areas of improvement.
- Recommend subjects to focus on.
- Keep recommendations practical.
- Do NOT invent information.
- Keep the answer under 150 words.

IMPORTANT

The execution plan has already determined the user's intent.

Trust the execution plan.

Do NOT reinterpret the question.

Analyze ONLY according to the execution plan.
"""

    return call_llm(prompt)

# --------------------------------------------------------
# Common Ollama Call
# --------------------------------------------------------

def call_llm(prompt: str) -> str:

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are an AI educational analyst.

Only analyze the provided data.

Never invent information.

Never mention SQL, databases or AI.

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

    return response["message"]["content"].strip()

