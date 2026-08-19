"""
sql_generator.py

Deterministic SQL generator for School Chatbot.

Main goals:
1. Student ownership is ALWAYS enforced.
2. Critical school-data queries use deterministic SQL.
3. Subject aliases are normalized centrally.
4. Exam aliases are normalized centrally.
5. Attendance month/year filters are handled correctly.
6. Assignments, attendance, marks and performance do not depend
   on LLM-generated SQL.
7. LLM SQL is used only as a final fallback.
"""

import re
from datetime import datetime

from ai.prompt import build_prompt
from ai.ollama_client import generate_sql as ollama_generate_sql


# =========================================================
# CLEAN SQL
# =========================================================

def clean_sql(sql: str) -> str:

    if not sql:
        return ""

    sql = sql.replace("```sql", "")
    sql = sql.replace("```", "")
    sql = sql.strip()

    match = re.search(
        r"(SELECT[\s\S]*?;)",
        sql,
        re.IGNORECASE
    )

    if match:
        sql = match.group(1).strip()

    return sql


# =========================================================
# SUBJECT ALIASES
# =========================================================

SUBJECT_ALIASES = {

    "math": "mathematics",
    "maths": "mathematics",
    "mathematics": "mathematics",

    "science": "science",
    "sci": "science",

    "social science": "social science",
    "social sciences": "social science",
    "social studies": "social science",
    "sst": "social science",

    "english": "english",
    "eng": "english",

    "hindi": "hindi",
    "hin": "hindi",

    "computer": "computer science",
    "computers": "computer science",
    "computer science": "computer science",
    "computer studies": "computer science",
    "computer subject": "computer science",
    "comp science": "computer science",
    "cs": "computer science",
    "c.s.": "computer science",

    "physics": "physics",
    "phy": "physics",

    "chemistry": "chemistry",
    "chem": "chemistry",

    "biology": "biology",
    "bio": "biology",
}


# =========================================================
# SUBJECT DETECTION
# =========================================================

def detect_subject(question: str):

    if not question:
        return None

    q = question.lower().strip()

    q = re.sub(
        r"[?!.:,;]",
        " ",
        q
    )

    q = re.sub(
        r"\s+",
        " ",
        q
    )

    aliases = sorted(
        SUBJECT_ALIASES.keys(),
        key=len,
        reverse=True
    )

    for alias in aliases:

        if re.search(
            rf"\b{re.escape(alias)}\b",
            q
        ):

            return SUBJECT_ALIASES[alias]

    return None


# =========================================================
# SUBJECT SQL CONDITION
# =========================================================

def subject_condition(
    question: str,
    alias="sub"
):

    subject = detect_subject(question)

    if not subject:
        return ""

    if subject == "computer science":

        return f"""
AND LOWER(TRIM({alias}.subject_name))
    LIKE '%computer%science%'
""".strip()

    if subject == "social science":

        return f"""
AND LOWER(TRIM({alias}.subject_name))
    LIKE '%social%science%'
""".strip()

    safe_subject = (
        subject
        .replace("'", "''")
    )

    return f"""
AND LOWER(TRIM({alias}.subject_name))
    = LOWER('{safe_subject}')
""".strip()


# =========================================================
# EXAM DETECTION
# =========================================================

def detect_exam(question: str):

    if not question:
        return None

    q = question.lower()

    midterm_patterns = [
        "midterm",
        "mid term",
        "mid-term",
        "mid exam",
        "mid examination",
        "half yearly",
        "half-yearly",
        "half yearly examination",
        "term 1",
        "first term",
        "first semester",
        "semester 1",
    ]

    final_patterns = [
        "final",
        "finals",
        "final exam",
        "final examination",
        "annual",
        "annual exam",
        "annual examination",
        "year end",
        "year-end",
        "end term",
        "term 2",
        "second term",
        "second semester",
        "semester 2",
    ]

    for pattern in midterm_patterns:

        if pattern in q:
            return "midterm"

    for pattern in final_patterns:

        if pattern in q:
            return "final"

    return None


# =========================================================
# EXAM SQL CONDITION
# =========================================================

def exam_condition(
    exam_constraint,
    alias="e"
):

    if not exam_constraint:
        return ""

    if isinstance(
        exam_constraint,
        str
    ):
        exam_constraint = [
            exam_constraint
        ]

    conditions = []

    for exam_type in exam_constraint:

        exam_type = (
            str(exam_type)
            .lower()
            .strip()
        )

        if exam_type in {
            "midterm",
            "mid term",
            "mid-term",
        }:

            conditions.append(
                f"""
(
    LOWER({alias}.exam_name) LIKE '%mid%'
    OR LOWER({alias}.exam_name) LIKE '%half%'
    OR LOWER({alias}.exam_name) LIKE '%term 1%'
    OR LOWER({alias}.exam_name) LIKE '%first term%'
    OR LOWER({alias}.exam_name) LIKE '%first semester%'
)
""".strip()
            )

        elif exam_type == "final":

            conditions.append(
                f"""
(
    LOWER({alias}.exam_name) LIKE '%final%'
    OR LOWER({alias}.exam_name) LIKE '%annual%'
    OR LOWER({alias}.exam_name) LIKE '%year end%'
    OR LOWER({alias}.exam_name) LIKE '%end term%'
    OR LOWER({alias}.exam_name) LIKE '%term 2%'
    OR LOWER({alias}.exam_name) LIKE '%second term%'
    OR LOWER({alias}.exam_name) LIKE '%second semester%'
)
""".strip()
            )

    if not conditions:
        return ""

    return (
        "\nAND (\n"
        + "\nOR\n".join(conditions)
        + "\n)"
    )


# =========================================================
# MONTH MAP
# =========================================================

MONTH_MAP = {

    "january": 1,
    "jan": 1,

    "february": 2,
    "feb": 2,

    "march": 3,
    "mar": 3,

    "april": 4,
    "apr": 4,

    "may": 5,

    "june": 6,
    "jun": 6,

    "july": 7,
    "jul": 7,

    "august": 8,
    "aug": 8,

    "september": 9,
    "sep": 9,
    "sept": 9,

    "october": 10,
    "oct": 10,

    "november": 11,
    "nov": 11,

    "december": 12,
    "dec": 12,
}


# =========================================================
# EXTRACT MONTH/YEAR FROM QUESTION
# =========================================================

def extract_month_from_question(question: str):

    if not question:
        return None

    q = question.lower().strip()

    now = datetime.now()

    # -----------------------------------------------------
    # THIS MONTH
    # -----------------------------------------------------

    if (
        "this month" in q
        or "current month" in q
    ):

        return {
            "month": now.month,
            "year": now.year
        }

    # -----------------------------------------------------
    # LAST MONTH
    # -----------------------------------------------------

    if (
        "last month" in q
        or "previous month" in q
    ):

        if now.month == 1:

            return {
                "month": 12,
                "year": now.year - 1
            }

        return {
            "month": now.month - 1,
            "year": now.year
        }

    # -----------------------------------------------------
    # MONTH + YEAR
    # Example: June 2026
    # -----------------------------------------------------

    month_pattern = "|".join(
        re.escape(x)
        for x in MONTH_MAP.keys()
    )

    match = re.search(
        rf"\b({month_pattern})\s+((?:19|20)\d{{2}})\b",
        q
    )

    if match:

        month_name = match.group(1)
        year = int(match.group(2))

        return {
            "month": MONTH_MAP[month_name],
            "year": year
        }

    # -----------------------------------------------------
    # YEAR + MONTH
    # Example: 2026 June
    # -----------------------------------------------------

    match = re.search(
        rf"\b((?:19|20)\d{{2}})\s+({month_pattern})\b",
        q
    )

    if match:

        year = int(match.group(1))
        month_name = match.group(2)

        return {
            "month": MONTH_MAP[month_name],
            "year": year
        }

    # -----------------------------------------------------
    # MONTH ONLY
    # Example: attendance in June
    # -----------------------------------------------------

    for month_name, month_number in MONTH_MAP.items():

        if re.search(
            rf"\b{re.escape(month_name)}\b",
            q
        ):

            return {
                "month": month_number,
                "year": None
            }

    return None


# =========================================================
# MONTH CONDITION
# =========================================================

def month_condition(
    month,
    alias="a",
    year=None
):

    if month is None:
        return ""

    try:

        month = int(month)

    except (
        TypeError,
        ValueError
    ):

        return ""

    if not 1 <= month <= 12:
        return ""

    condition = (
        f"\nAND EXTRACT("
        f"MONTH FROM {alias}.attendance_date"
        f") = {month}"
    )

    # -----------------------------------------------------
    # YEAR FILTER
    # -----------------------------------------------------

    if year is not None:

        try:

            year = int(year)

            condition += (
                f"\nAND EXTRACT("
                f"YEAR FROM {alias}.attendance_date"
                f") = {year}"
            )

        except (
            TypeError,
            ValueError
        ):

            pass

    return condition


# =========================================================
# ATTENDANCE MONTH RESOLUTION
# =========================================================

def resolve_attendance_month(
    question,
    constraints
):

    constraints = constraints or {}

    month = constraints.get(
        "month"
    )

    year = constraints.get(
        "year"
    )

    extracted = (
        extract_month_from_question(
            question
        )
    )

    # Planner constraint first.
    if month is None and extracted:

        month = extracted.get(
            "month"
        )

    if year is None and extracted:

        year = extracted.get(
            "year"
        )

    return month, year


# =========================================================
# DAY CONDITION
# =========================================================

def timetable_day_condition(
    day,
    alias="t"
):

    if not day:
        return ""

    day = (
        str(day)
        .lower()
        .strip()
    )

    if day == "today":

        return f"""
AND LOWER(TRIM({alias}.day_of_week))
    =
    LOWER(TRIM(TO_CHAR(CURRENT_DATE, 'Day')))
""".strip()

    if day == "tomorrow":

        return f"""
AND LOWER(TRIM({alias}.day_of_week))
    =
    LOWER(
        TRIM(
            TO_CHAR(
                CURRENT_DATE + INTERVAL '1 day',
                'Day'
            )
        )
    )
""".strip()

    if day == "next":

        return f"""
AND (
    LOWER(TRIM({alias}.day_of_week))
        =
        LOWER(
            TRIM(
                TO_CHAR(
                    CURRENT_DATE,
                    'Day'
                )
            )
        )

    AND {alias}.start_time >= CURRENT_TIME
)
""".strip()

    weekdays = {
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    }

    if day in weekdays:

        return (
            f"\nAND LOWER(TRIM({alias}.day_of_week)) "
            f"= '{day}'"
        )

    return ""


# =========================================================
# PERFORMANCE SQL
# =========================================================

def generate_performance_sql(
    metric,
    student_id,
    exam_filter=""
):

    # -----------------------------------------------------
    # HIGHEST SCORE
    # -----------------------------------------------------

    if metric == "highest_score":

        return f"""
SELECT
    sub.subject_name,
    e.exam_name,
    e.start_date,
    m.marks_obtained,
    m.maximum_marks,

    ROUND(
        m.marks_obtained * 100.0
        /
        NULLIF(
            m.maximum_marks,
            0
        ),
        2
    ) AS percentage

FROM marks m

JOIN class_subjects cs
    ON m.class_subject_id =
       cs.class_subject_id

JOIN subjects sub
    ON cs.subject_id =
       sub.subject_id

LEFT JOIN exams e
    ON m.exam_id =
       e.exam_id

WHERE m.student_id =
      {student_id}

{exam_filter}

ORDER BY
    percentage DESC,
    e.start_date DESC NULLS LAST

LIMIT 1;
""".strip()

    # -----------------------------------------------------
    # LOWEST SCORE
    # -----------------------------------------------------

    if metric == "lowest_score":

        return f"""
SELECT
    sub.subject_name,
    e.exam_name,
    e.start_date,
    m.marks_obtained,
    m.maximum_marks,

    ROUND(
        m.marks_obtained * 100.0
        /
        NULLIF(
            m.maximum_marks,
            0
        ),
        2
    ) AS percentage

FROM marks m

JOIN class_subjects cs
    ON m.class_subject_id =
       cs.class_subject_id

JOIN subjects sub
    ON cs.subject_id =
       sub.subject_id

LEFT JOIN exams e
    ON m.exam_id =
       e.exam_id

WHERE m.student_id =
      {student_id}

{exam_filter}

ORDER BY
    percentage ASC,
    e.start_date ASC NULLS LAST

LIMIT 1;
""".strip()

    # -----------------------------------------------------
    # HIGHEST SUBJECT
    # -----------------------------------------------------

    if metric == "highest_subject":

        return f"""
SELECT
    sub.subject_name,

    ROUND(
        SUM(m.marks_obtained) * 100.0
        /
        NULLIF(
            SUM(m.maximum_marks),
            0
        ),
        2
    ) AS percentage,

    SUM(m.marks_obtained)
        AS total_obtained,

    SUM(m.maximum_marks)
        AS total_maximum

FROM marks m

JOIN class_subjects cs
    ON m.class_subject_id =
       cs.class_subject_id

JOIN subjects sub
    ON cs.subject_id =
       sub.subject_id

JOIN exams e
    ON m.exam_id =
       e.exam_id

WHERE m.student_id =
      {student_id}

{exam_filter}

GROUP BY
    sub.subject_id,
    sub.subject_name

ORDER BY
    percentage DESC

LIMIT 1;
""".strip()

    # -----------------------------------------------------
    # LOWEST SUBJECT
    # -----------------------------------------------------

    if metric == "lowest_subject":

        return f"""
SELECT
    sub.subject_name,

    ROUND(
        SUM(m.marks_obtained) * 100.0
        /
        NULLIF(
            SUM(m.maximum_marks),
            0
        ),
        2
    ) AS percentage,

    SUM(m.marks_obtained)
        AS total_obtained,

    SUM(m.maximum_marks)
        AS total_maximum

FROM marks m

JOIN class_subjects cs
    ON m.class_subject_id =
       cs.class_subject_id

JOIN subjects sub
    ON cs.subject_id =
       sub.subject_id

JOIN exams e
    ON m.exam_id =
       e.exam_id

WHERE m.student_id =
      {student_id}

{exam_filter}

GROUP BY
    sub.subject_id,
    sub.subject_name

ORDER BY
    percentage ASC

LIMIT 1;
""".strip()

    return None


# =========================================================
# MAIN SQL GENERATOR
# =========================================================

def generate_sql(
    question: str,
    plan: dict,
    current_user: dict
):

    current_user = current_user or {}
    plan = plan or {}

    student_id = current_user.get(
        "student_id"
    )

    intent = plan.get(
        "intent",
        ""
    )

    metric = plan.get(
        "metric",
        ""
    )

    constraints = plan.get(
        "constraints",
        {}
    ) or {}

    context = plan.get(
        "context",
        {}
    ) or {}

    # =====================================================
    # SECURITY
    # =====================================================

    protected_intents = {
        "marks",
        "attendance",
        "assignments",
        "timetable",
        "exams",
        "performance",
        "teacher",
        "profile",
    }

    if intent in protected_intents:

        if not student_id:

            raise ValueError(
                "Student profile could not be identified."
            )

    # =====================================================
    # PERFORMANCE
    # =====================================================

    if intent == "performance":

        exam_filter = exam_condition(
            constraints.get("exam"),
            "e"
        )

        sql = generate_performance_sql(
            metric,
            student_id,
            exam_filter
        )

        if sql:

            print(
                "\n===== PERFORMANCE SQL ====="
            )

            print(sql)

            print(
                "==========================="
            )

            return clean_sql(sql)

        # -------------------------------------------------
        # TREND
        # -------------------------------------------------

        if metric == "trend":

            return f"""
SELECT
    sub.subject_name,
    e.exam_name,
    e.start_date,
    m.marks_obtained,
    m.maximum_marks

FROM marks m

JOIN class_subjects cs
    ON m.class_subject_id =
       cs.class_subject_id

JOIN subjects sub
    ON cs.subject_id =
       sub.subject_id

JOIN exams e
    ON m.exam_id =
       e.exam_id

WHERE m.student_id =
      {student_id}

{exam_filter}

ORDER BY
    e.start_date ASC,
    sub.subject_name ASC;
""".strip()

        # -------------------------------------------------
        # EXAM COMPARISON
        # -------------------------------------------------

        if metric == "exam_comparison":

            return f"""
SELECT
    sub.subject_name,
    e.exam_name,
    e.start_date,
    m.marks_obtained,
    m.maximum_marks

FROM marks m

JOIN class_subjects cs
    ON m.class_subject_id =
       cs.class_subject_id

JOIN subjects sub
    ON cs.subject_id =
       sub.subject_id

JOIN exams e
    ON m.exam_id =
       e.exam_id

WHERE m.student_id =
      {student_id}

{exam_filter}

ORDER BY
    e.start_date ASC,
    sub.subject_name ASC;
""".strip()

        # -------------------------------------------------
        # OVERALL PERFORMANCE
        # -------------------------------------------------

        if metric == "overall_performance":

            return f"""
SELECT
    sub.subject_name,
    e.exam_name,
    e.start_date,
    m.marks_obtained,
    m.maximum_marks,

    ROUND(
        m.marks_obtained * 100.0
        /
        NULLIF(
            m.maximum_marks,
            0
        ),
        2
    ) AS percentage

FROM marks m

JOIN class_subjects cs
    ON m.class_subject_id =
       cs.class_subject_id

JOIN subjects sub
    ON cs.subject_id =
       sub.subject_id

JOIN exams e
    ON m.exam_id =
       e.exam_id

WHERE m.student_id =
      {student_id}

{exam_filter}

ORDER BY
    e.start_date ASC,
    sub.subject_name ASC;
""".strip()

    # =====================================================
    # MARKS
    # =====================================================

    if intent == "marks":

        subject = (
            constraints.get("subject")
            or context.get("subject")
            or detect_subject(question)
        )

        if subject:

            subject = SUBJECT_ALIASES.get(
                str(subject).lower().strip(),
                str(subject).lower().strip()
            )

        # -------------------------------------------------
        # SUBJECT FILTER
        # -------------------------------------------------

        subject_filter = ""

        if subject:

            if subject == "computer science":

                subject_filter = """
AND LOWER(TRIM(sub.subject_name))
    LIKE '%computer%science%'
""".strip()

            elif subject == "social science":

                subject_filter = """
AND LOWER(TRIM(sub.subject_name))
    LIKE '%social%science%'
""".strip()

            else:

                safe_subject = (
                    subject
                    .replace("'", "''")
                )

                subject_filter = (
                    "\nAND LOWER(TRIM(sub.subject_name)) "
                    f"= LOWER('{safe_subject}')"
                )

        # -------------------------------------------------
        # EXAM
        # -------------------------------------------------

        exam_filter = exam_condition(
            constraints.get("exam"),
            "e"
        )

        sql = f"""
SELECT
    sub.subject_name,
    e.exam_name,
    e.start_date,
    m.marks_obtained,
    m.maximum_marks,

    ROUND(
        m.marks_obtained * 100.0
        /
        NULLIF(
            m.maximum_marks,
            0
        ),
        2
    ) AS percentage

FROM marks m

JOIN class_subjects cs
    ON m.class_subject_id =
       cs.class_subject_id

JOIN subjects sub
    ON cs.subject_id =
       sub.subject_id

LEFT JOIN exams e
    ON m.exam_id =
       e.exam_id

WHERE m.student_id =
      {student_id}

{subject_filter}

{exam_filter}

ORDER BY
    e.start_date ASC NULLS LAST,
    sub.subject_name ASC;
""".strip()

        print(
            "\n===== DETERMINISTIC MARKS SQL ====="
        )

        print(sql)

        print(
            "==================================="
        )

        return clean_sql(sql)

    # =====================================================
    # ATTENDANCE
    # =====================================================

    if intent == "attendance":

        month, year = resolve_attendance_month(
            question,
            constraints
        )

        print(
            "\n===== ATTENDANCE FILTER ====="
        )

        print("Question:", question)
        print("Month:", month)
        print("Year:", year)
        print("Metric:", metric)
        print("Constraints:", constraints)

        print(
            "=============================="
        )

        month_filter = month_condition(
            month,
            "a",
            year
        )

        # -------------------------------------------------
        # MONTHLY ATTENDANCE
        #
        # "Show my attendance"
        # "Show attendance"
        # "Show my attendance for June"
        # "My attendance in June 2026"
        # -------------------------------------------------

        if metric in {
            "",
            "monthly_attendance",
        }:

            # No explicit month:
            # use current month.

            if month is None:

                monthly_filter = """
AND DATE_TRUNC(
    'month',
    a.attendance_date
)
=
DATE_TRUNC(
    'month',
    CURRENT_DATE
)
""".strip()

            else:

                monthly_filter = (
                    month_filter
                )

            sql = f"""
SELECT
    a.attendance_date,
    a.status

FROM attendance a

WHERE a.student_id =
      {student_id}

{monthly_filter}

ORDER BY
    a.attendance_date ASC;
""".strip()

            print(
                "\n===== MONTHLY ATTENDANCE SQL ====="
            )

            print(sql)

            print(
                "=================================="
            )

            return clean_sql(sql)

        # -------------------------------------------------
        # ABSENT DATES
        # -------------------------------------------------

        if metric == "absent_dates":

            return f"""
SELECT
    a.attendance_date,
    a.status

FROM attendance a

WHERE a.student_id =
      {student_id}

AND LOWER(
    TRIM(a.status)
) = 'absent'

{month_filter}

ORDER BY
    a.attendance_date ASC;
""".strip()

        # -------------------------------------------------
        # PRESENT DATES
        # -------------------------------------------------

        if metric == "present_dates":

            return f"""
SELECT
    a.attendance_date,
    a.status

FROM attendance a

WHERE a.student_id =
      {student_id}

AND LOWER(
    TRIM(a.status)
) = 'present'

{month_filter}

ORDER BY
    a.attendance_date ASC;
""".strip()

        # -------------------------------------------------
        # ABSENT COUNT
        # -------------------------------------------------

        if metric == "absent_days":

            return f"""
SELECT
    COUNT(*) AS absent_days

FROM attendance a

WHERE a.student_id =
      {student_id}

AND LOWER(
    TRIM(a.status)
) = 'absent'

{month_filter};
""".strip()

        # -------------------------------------------------
        # PRESENT COUNT
        # -------------------------------------------------

        if metric == "present_days":

            return f"""
SELECT
    COUNT(*) AS present_days

FROM attendance a

WHERE a.student_id =
      {student_id}

AND LOWER(
    TRIM(a.status)
) = 'present'

{month_filter};
""".strip()

        # -------------------------------------------------
        # LATE
        # -------------------------------------------------

        if metric in {
            "late_days",
            "late_dates",
        }:

            if metric == "late_days":

                return f"""
SELECT
    COUNT(*) AS late_days

FROM attendance a

WHERE a.student_id =
      {student_id}

AND LOWER(
    TRIM(a.status)
) = 'late'

{month_filter};
""".strip()

            return f"""
SELECT
    a.attendance_date,
    a.status

FROM attendance a

WHERE a.student_id =
      {student_id}

AND LOWER(
    TRIM(a.status)
) = 'late'

{month_filter}

ORDER BY
    a.attendance_date ASC;
""".strip()

        # -------------------------------------------------
        # ATTENDANCE PERCENTAGE
        # -------------------------------------------------

        if metric == "attendance_percentage":

            return f"""
SELECT

    COUNT(*) AS total_days,

    COUNT(*) FILTER (
        WHERE LOWER(
            TRIM(a.status)
        ) = 'present'
    ) AS present_days,

    COUNT(*) FILTER (
        WHERE LOWER(
            TRIM(a.status)
        ) = 'absent'
    ) AS absent_days,

    COUNT(*) FILTER (
        WHERE LOWER(
            TRIM(a.status)
        ) = 'late'
    ) AS late_days,

    ROUND(

        (
            COUNT(*) FILTER (
                WHERE LOWER(
                    TRIM(a.status)
                ) IN (
                    'present',
                    'late'
                )
            ) * 100.0
        )
        /
        NULLIF(
            COUNT(*),
            0
        ),

        2

    ) AS attendance_percentage

FROM attendance a

WHERE a.student_id =
      {student_id}

{month_filter};
""".strip()

        # -------------------------------------------------
        # ATTENDANCE SUMMARY
        # -------------------------------------------------

        if metric == "attendance_summary":

            return f"""
SELECT

    COUNT(*) AS total_days,

    COUNT(*) FILTER (
        WHERE LOWER(
            TRIM(a.status)
        ) = 'present'
    ) AS present_days,

    COUNT(*) FILTER (
        WHERE LOWER(
            TRIM(a.status)
        ) = 'absent'
    ) AS absent_days,

    COUNT(*) FILTER (
        WHERE LOWER(
            TRIM(a.status)
        ) = 'late'
    ) AS late_days,

    ROUND(

        (
            COUNT(*) FILTER (
                WHERE LOWER(
                    TRIM(a.status)
                ) IN (
                    'present',
                    'late'
                )
            ) * 100.0
        )
        /
        NULLIF(
            COUNT(*),
            0
        ),

        2

    ) AS attendance_percentage

FROM attendance a

WHERE a.student_id =
      {student_id}

{month_filter};
""".strip()

        # -------------------------------------------------
        # ELIGIBILITY
        # -------------------------------------------------

        if metric == "attendance_eligibility":

            return f"""
SELECT

    COUNT(*) AS total_days,

    COUNT(*) FILTER (
        WHERE LOWER(
            TRIM(a.status)
        ) IN (
            'present',
            'late'
        )
    ) AS attended_days,

    ROUND(

        (
            COUNT(*) FILTER (
                WHERE LOWER(
                    TRIM(a.status)
                ) IN (
                    'present',
                    'late'
                )
            ) * 100.0
        )
        /
        NULLIF(
            COUNT(*),
            0
        ),

        2

    ) AS attendance_percentage

FROM attendance a

WHERE a.student_id =
      {student_id}

{month_filter};
""".strip()

        # -------------------------------------------------
        # ATTENDANCE TREND
        # -------------------------------------------------

        if metric == "attendance_trend":

            return f"""
SELECT

    DATE_TRUNC(
        'month',
        a.attendance_date
    ) AS month,

    COUNT(*) AS total_days,

    COUNT(*) FILTER (
        WHERE LOWER(
            TRIM(a.status)
        ) = 'present'
    ) AS present_days,

    COUNT(*) FILTER (
        WHERE LOWER(
            TRIM(a.status)
        ) = 'absent'
    ) AS absent_days,

    COUNT(*) FILTER (
        WHERE LOWER(
            TRIM(a.status)
        ) = 'late'
    ) AS late_days,

    ROUND(

        (
            COUNT(*) FILTER (
                WHERE LOWER(
                    TRIM(a.status)
                ) IN (
                    'present',
                    'late'
                )
            ) * 100.0
        )
        /
        NULLIF(
            COUNT(*),
            0
        ),

        2

    ) AS attendance_percentage

FROM attendance a

WHERE a.student_id =
      {student_id}

GROUP BY
    DATE_TRUNC(
        'month',
        a.attendance_date
    )

ORDER BY
    month ASC;
""".strip()

        # -------------------------------------------------
        # ATTENDANCE COMPARISON
        # -------------------------------------------------

        if metric == "attendance_comparison":

            return f"""
SELECT

    DATE_TRUNC(
        'month',
        a.attendance_date
    ) AS month,

    COUNT(*) AS total_days,

    COUNT(*) FILTER (
        WHERE LOWER(
            TRIM(a.status)
        ) IN (
            'present',
            'late'
        )
    ) AS attended_days,

    COUNT(*) FILTER (
        WHERE LOWER(
            TRIM(a.status)
        ) = 'absent'
    ) AS absent_days,

    ROUND(

        (
            COUNT(*) FILTER (
                WHERE LOWER(
                    TRIM(a.status)
                ) IN (
                    'present',
                    'late'
                )
            ) * 100.0
        )
        /
        NULLIF(
            COUNT(*),
            0
        ),

        2

    ) AS attendance_percentage

FROM attendance a

WHERE a.student_id =
      {student_id}

GROUP BY
    DATE_TRUNC(
        'month',
        a.attendance_date
    )

ORDER BY
    month ASC;
""".strip()

    # =====================================================
    # ASSIGNMENTS
    # =====================================================

    if intent == "assignments":

        scope = constraints.get(
            "assignment_scope"
        )

        extra_condition = ""

        # -------------------------------------------------
        # OVERDUE
        # -------------------------------------------------

        if scope == "overdue":

            extra_condition = """
AND a.due_date < CURRENT_DATE
""".strip()

        # -------------------------------------------------
        # TODAY
        # -------------------------------------------------

        elif scope == "today":

            extra_condition = """
AND a.due_date = CURRENT_DATE
""".strip()

        # -------------------------------------------------
        # TOMORROW
        # -------------------------------------------------

        elif scope == "tomorrow":

            extra_condition = """
AND a.due_date =
    CURRENT_DATE + INTERVAL '1 day'
""".strip()

        # -------------------------------------------------
        # UPCOMING / PENDING
        # -------------------------------------------------

        elif scope in {
            "upcoming",
            "pending",
        }:

            extra_condition = """
AND a.due_date >= CURRENT_DATE
""".strip()

        # -------------------------------------------------
        # COMPLETED
        # -------------------------------------------------

        elif scope == "completed":

            # Adjust this only if your assignments table
            # uses a different completion column.
            extra_condition = """
AND LOWER(
    COALESCE(a.status, '')
) IN (
    'completed',
    'submitted',
    'done'
)
""".strip()

        # -------------------------------------------------
        # SUBJECT
        # -------------------------------------------------

        subject_filter = subject_condition(
            question,
            "sub"
        )

        sql = f"""
SELECT

    sub.subject_name,
    a.title,
    a.description,
    a.assigned_date,
    a.due_date

FROM students st

JOIN class_subjects cs
    ON st.class_id =
       cs.class_id

JOIN assignments a
    ON cs.class_subject_id =
       a.class_subject_id

JOIN subjects sub
    ON cs.subject_id =
       sub.subject_id

WHERE st.student_id =
      {student_id}

{extra_condition}

{subject_filter}

ORDER BY
    a.due_date ASC NULLS LAST,
    sub.subject_name ASC;
""".strip()

        print(
            "\n===== ASSIGNMENTS SQL ====="
        )

        print(sql)

        print(
            "==========================="
        )

        return clean_sql(sql)

    # =====================================================
    # TIMETABLE
    # =====================================================

    if intent == "timetable":

        day = constraints.get(
            "day"
        )

        day_filter = timetable_day_condition(
            day,
            "t"
        )

        timetable_subject_filter = subject_condition(
            question,
            "s"
        )

        next_limit = ""

        if day == "next":

            next_limit = """
LIMIT 1
""".strip()

        return f"""
SELECT

    t.day_of_week,
    t.start_time,
    t.end_time,
    t.room_number,
    t.period_number,
    s.subject_name

FROM students st

JOIN class_subjects cs
    ON st.class_id =
       cs.class_id

JOIN timetable t
    ON cs.class_subject_id =
       t.class_subject_id

JOIN subjects s
    ON cs.subject_id =
       s.subject_id

WHERE st.student_id =
      {student_id}

{day_filter}

{timetable_subject_filter}

ORDER BY

    CASE LOWER(
        TRIM(t.day_of_week)
    )

        WHEN 'monday' THEN 1
        WHEN 'tuesday' THEN 2
        WHEN 'wednesday' THEN 3
        WHEN 'thursday' THEN 4
        WHEN 'friday' THEN 5
        WHEN 'saturday' THEN 6
        WHEN 'sunday' THEN 7

    END,

    t.start_time

{next_limit};
""".strip()

    # =====================================================
    # EXAMS
    # =====================================================

    if intent == "exams":

        exam_filter = exam_condition(
            constraints.get("exam"),
            "e"
        )

        return f"""
SELECT

    e.exam_name,
    e.academic_year,
    e.start_date,
    e.end_date

FROM exams e

WHERE 1 = 1

{exam_filter}

ORDER BY
    e.start_date ASC;
""".strip()

    # =====================================================
    # TEACHER
    # =====================================================

    if intent == "teacher":

        teacher_subject_filter = subject_condition(
            question,
            "sub"
        )

        return f"""
SELECT DISTINCT

    t.first_name,
    t.last_name,
    t.email,
    sub.subject_name

FROM students st

JOIN class_subjects cs
    ON st.class_id =
       cs.class_id

JOIN subjects sub
    ON cs.subject_id =
       sub.subject_id

JOIN teachers t
    ON cs.teacher_id =
       t.teacher_id

WHERE st.student_id =
      {student_id}

{teacher_subject_filter}

ORDER BY
    sub.subject_name,
    t.last_name,
    t.first_name;
""".strip()

    # =====================================================
    # PROFILE
    # =====================================================

    if intent == "profile":

        return f"""
SELECT
    s.student_id,
    s.first_name,
    s.last_name,
    s.roll_number,
    s.date_of_birth,
    s.gender,
    s.admission_date,
    c.class_name,
    c.section,
    c.academic_year

FROM students s

JOIN classes c
    ON s.class_id =
       c.class_id

WHERE s.student_id =
      {student_id};
""".strip()

    # =====================================================
    # FALLBACK LLM SQL
    # =====================================================

    prompt = build_prompt(
        question,
        plan,
        current_user
    )

    sql = ollama_generate_sql(
        prompt
    )

    if not sql:

        raise ValueError(
            "SQL generator returned an empty query."
        )

    return clean_sql(sql)