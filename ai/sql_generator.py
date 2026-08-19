"""
sql_generator.py

Core strategy:

1. Deterministic SQL for critical school-data intents.
2. LLM SQL generation only where flexible interpretation is useful.
3. Student ownership is always enforced.
4. Exam aliases are handled centrally.
5. No hallucinated columns.
"""

import re

from ai.prompt import build_prompt
from ai.ollama_client import generate_sql as ollama_generate_sql


# =========================================================
# HELPERS
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
# SUBJECT SYNONYMS
# =========================================================

SUBJECT_SYNONYMS = {

    "mathematics": [
        "math",
        "maths",
        "mathematics",
        "math paper",
        "maths paper",
    ],

    "science": [
        "science",
        "sci",
        "science subject",
        "science paper",
    ],

    "social science": [
        "social science",
        "social sciences",
        "social studies",
        "sst",
        "s.s.t",
        "social studies paper",
    ],

    "english": [
        "english",
        "english language",
        "english paper",
    ],

    "hindi": [
        "hindi",
        "hindi language",
        "hindi paper",
    ],

    "computer science": [
        "computer science",
        "computer",
        "cs",
        "c.s.",
        "computers",
        "computer studies",
        "computer subject",
        "computer science subject",
    ],

    "physics": [
        "physics",
        "phy",
        "physics paper",
    ],

    "chemistry": [
        "chemistry",
        "chem",
        "chemistry paper",
    ],

    "biology": [
        "biology",
        "bio",
        "biology paper",
    ],
}


# =========================================================
# SUBJECT DETECTION
# =========================================================

def detect_subject(question: str):
    """
    Detect subject from natural language.

    Examples:

        "What did I score in Computer Science?"
        -> computer science

        "How much did I get in maths?"
        -> mathematics

        "My science marks?"
        -> science
    """

    if not question:
        return None

    query = question.lower().strip()

    # Normalize punctuation
    query = re.sub(r"[?!.:,;]", " ", query)
    query = re.sub(r"\s+", " ", query)

    # -----------------------------------------------------
    # First check longest phrases
    # -----------------------------------------------------

    candidates = []

    for canonical, synonyms in SUBJECT_SYNONYMS.items():

        for synonym in synonyms:

            synonym = synonym.lower()

            if re.search(
                rf"\b{re.escape(synonym)}\b",
                query
            ):
                candidates.append(
                    (len(synonym), canonical)
                )

    if not candidates:
        return None

    # Longest match wins
    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return candidates[0][1]


# =========================================================
# EXAM DETECTION
# =========================================================

EXAM_SYNONYMS = {

    "mid term": [
        "mid term",
        "midterm",
        "mid-term",
        "mid examination",
        "mid exam",
        "half yearly",
        "half-yearly",
        "half yearly examination",
    ],

    "final": [
        "final",
        "final exam",
        "final examination",
        "annual exam",
        "annual examination",
        "yearly exam",
        "year end exam",
    ],
}


def detect_exam(question: str):

    if not question:
        return None

    query = question.lower()

    candidates = []

    for canonical, synonyms in EXAM_SYNONYMS.items():

        for synonym in synonyms:

            if re.search(
                rf"\b{re.escape(synonym)}\b",
                query
            ):
                candidates.append(
                    (len(synonym), canonical)
                )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return candidates[0][1]


# =========================================================
# ADD SUBJECT FILTER
# =========================================================

def enforce_subject_filter(
    sql: str,
    subject: str
):
    """
    Force subject filtering into generated SQL.

    This protects against the LLM returning all subjects
    when the user specifically asks about one subject.
    """

    if not sql or not subject:
        return sql

    sql_lower = sql.lower()

    # Already has subject filter
    if (
        "sub.subject_name" in sql_lower
        or "subject_name =" in sql_lower
        or "subject_name ilike" in sql_lower
        or "subject_name like" in sql_lower
    ):
        return sql

    # -----------------------------------------------------
    # If SQL already has WHERE
    # -----------------------------------------------------

    if re.search(r"\bwhere\b", sql, re.IGNORECASE):

        sql = re.sub(
            r"\bwhere\b",
            (
                "WHERE sub.subject_name ILIKE "
                f"'%{subject}%' AND "
            ),
            sql,
            count=1,
            flags=re.IGNORECASE
        )

    # -----------------------------------------------------
    # No WHERE
    # -----------------------------------------------------

    else:

        # Insert before GROUP BY / ORDER BY / LIMIT
        match = re.search(
            r"\b(group\s+by|order\s+by|limit)\b",
            sql,
            re.IGNORECASE
        )

        if match:

            position = match.start()

            sql = (
                sql[:position]
                + (
                    "WHERE sub.subject_name ILIKE "
                    f"'%{subject}%' "
                )
                + sql[position:]
            )

        else:

            sql = (
                sql.rstrip().rstrip(";")
                + (
                    " WHERE sub.subject_name ILIKE "
                    f"'%{subject}%'"
                )
                + ";"
            )

    return sql


# =========================================================
# ADD EXAM FILTER
# =========================================================

def enforce_exam_filter(
    sql: str,
    exam: str
):

    if not sql or not exam:
        return sql

    sql_lower = sql.lower()

    # We only add this if the SQL uses exams.
    if "join exams" not in sql_lower:
        return sql

    if (
        "exam_name" in sql_lower
        and (
            "ilike" in sql_lower
            or "=" in sql_lower
        )
    ):
        return sql

    if exam == "mid term":

        condition = (
            "e.exam_name ILIKE '%mid%'"
        )

    elif exam == "final":

        condition = (
            "e.exam_name ILIKE '%final%'"
        )

    else:
        return sql

    if re.search(r"\bwhere\b", sql, re.IGNORECASE):

        sql = re.sub(
            r"\bwhere\b",
            f"WHERE {condition} AND ",
            sql,
            count=1,
            flags=re.IGNORECASE
        )

    return sql


# =========================================================
# PERFORMANCE SQL
# =========================================================

def generate_performance_sql(
    question: str,
    intent: str,
    metric: str,
    student_id: int
):

    # -----------------------------------------------------
    # HIGHEST / STRONGEST SUBJECT
    # -----------------------------------------------------

    if (
        intent == "performance"
        and metric == "highest_subject"
    ):

        return f"""
        SELECT
            sub.subject_name,
            ROUND(
                SUM(m.marks_obtained) * 100.0
                / NULLIF(SUM(m.maximum_marks), 0),
                2
            ) AS percentage
        FROM marks m
        JOIN class_subjects cs
            ON m.class_subject_id = cs.class_subject_id
        JOIN subjects sub
            ON cs.subject_id = sub.subject_id
        JOIN exams e
            ON m.exam_id = e.exam_id
        WHERE m.student_id = {student_id}
        GROUP BY
            sub.subject_id,
            sub.subject_name
        ORDER BY percentage DESC;
        """.strip()

    # -----------------------------------------------------
    # LOWEST / WEAKEST SUBJECT
    # -----------------------------------------------------

    if (
        intent == "performance"
        and metric == "lowest_subject"
    ):

        return f"""
        SELECT
            sub.subject_name,
            ROUND(
                SUM(m.marks_obtained) * 100.0
                / NULLIF(SUM(m.maximum_marks), 0),
                2
            ) AS percentage
        FROM marks m
        JOIN class_subjects cs
            ON m.class_subject_id = cs.class_subject_id
        JOIN subjects sub
            ON cs.subject_id = sub.subject_id
        JOIN exams e
            ON m.exam_id = e.exam_id
        WHERE m.student_id = {student_id}
        GROUP BY
            sub.subject_id,
            sub.subject_name
        ORDER BY percentage ASC;
        """.strip()

    return None


# =========================================================
# MAIN SQL GENERATOR
# =========================================================

def generate_sql(
    question: str,
    plan: dict,
    user_context: dict
):

    student_id = user_context.get(
        "student_id"
    )

    intent = plan.get(
        "intent"
    )

    metric = plan.get(
        "metric"
    )

    # =====================================================
    # PERFORMANCE QUERIES
    # =====================================================

    if (
        intent == "performance"
        and metric in [
            "highest_subject",
            "lowest_subject",
        ]
    ):

        if not student_id:
            raise ValueError(
                "Student ID is required for performance queries."
            )

        performance_sql = generate_performance_sql(
            question,
            intent,
            metric,
            student_id
        )

        if performance_sql:
            return performance_sql

    # =====================================================
    # NORMAL LLM SQL GENERATION
    # =====================================================

    prompt = build_prompt(
        question,
        plan,
        user_context
    )

    sql = ollama_generate_sql(
        prompt
    )

    if not sql:
        raise ValueError(
            "SQL generator returned an empty query."
        )

    sql = sql.strip()

    # Remove markdown code blocks
    sql = re.sub(
        r"```sql",
        "",
        sql,
        flags=re.IGNORECASE
    )

    sql = sql.replace(
        "```",
        ""
    ).strip()

    # =====================================================
    # SUBJECT FILTER
    # =====================================================

    subject = detect_subject(
        question
    )

    print(
        "\nDetected Subject:",
        subject
    )

    if (
        subject
        and intent in [
            "marks",
            "performance"
        ]
    ):

        sql = enforce_subject_filter(
            sql,
            subject
        )

    # =====================================================
    # EXAM FILTER
    # =====================================================

    exam = detect_exam(
        question
    )

    print(
        "Detected Exam:",
        exam
    )

    if exam and intent == "marks":

        sql = enforce_exam_filter(
            sql,
            exam
        )

    print(
        "\n===== FINAL GENERATED SQL ====="
    )

    print(sql)

    print(
        "================================"
    )

    return sql


# =========================================================
# EXAM FILTER
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

        if exam_type == "final":

            conditions.append(
                f"""
                (
                    LOWER({alias}.exam_name) LIKE '%final%'
                    OR LOWER({alias}.exam_name) LIKE '%annual%'
                    OR LOWER({alias}.exam_name) LIKE '%end term%'
                    OR LOWER({alias}.exam_name) LIKE '%term 2%'
                    OR LOWER({alias}.exam_name) LIKE '%second term%'
                    OR LOWER({alias}.exam_name) LIKE '%second semester%'
                )
                """
            )

        elif exam_type == "midterm":

            conditions.append(
                f"""
                (
                    LOWER({alias}.exam_name) LIKE '%mid%'
                    OR LOWER({alias}.exam_name) LIKE '%half%'
                    OR LOWER({alias}.exam_name) LIKE '%term 1%'
                    OR LOWER({alias}.exam_name) LIKE '%first term%'
                    OR LOWER({alias}.exam_name) LIKE '%first semester%'
                )
                """
            )

    if not conditions:
        return ""

    return (
        "\nAND (\n"
        +
        "\nOR\n".join(
            conditions
        )
        +
        "\n)"
    )


# =========================================================
# MONTH FILTER
# =========================================================

def month_condition(
    month,
    alias="a"
):

    if not month:
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

    return (
        f"\nAND EXTRACT("
        f"MONTH FROM {alias}.attendance_date"
        f") = {month}"
    )


# =========================================================
# SUBJECT FILTER
# =========================================================

SUBJECT_ALIASES = {

    "math": "mathematics",
    "maths": "mathematics",

    "sci": "science",

    "social studies": "social science",
    "sst": "social science",

    "cs": "computer science",
    "computer": "computer science",

    "comp science": "computer science",

    "phy": "physics",
    "chem": "chemistry",
    "bio": "biology",

    "eng": "english",
    "hin": "hindi",

}


def detect_subject_pattern(question: str):

    q = question.lower()

    # Longer names first.
    aliases = sorted(
        list(SUBJECT_ALIASES.keys())
        + list(SUBJECT_ALIASES.values()),
        key=len,
        reverse=True
    )

    for subject in aliases:

        if re.search(
            rf"\b{re.escape(subject)}\b",
            q
        ):

            canonical = SUBJECT_ALIASES.get(
                subject,
                subject
            )

            return canonical

    return None


def subject_condition(
    question: str,
    alias="s"
):

    subject = detect_subject_pattern(
        question
    )

    if not subject:
        return ""

    if subject == "computer science":

        return (
            f"\nAND LOWER({alias}.subject_name) "
            f"LIKE '%computer%science%'"
        )

    if subject == "social science":

        return (
            f"\nAND LOWER({alias}.subject_name) "
            f"LIKE '%social%science%'"
        )

    return (
        f"\nAND LOWER({alias}.subject_name) "
        f"LIKE '%{subject}%'"
    )


# =========================================================
# DAY FILTER
# =========================================================

def timetable_day_condition(
    day,
    alias="t"
):

    if not day:
        return ""

    day = str(day).lower()

    if day == "today":

        return f"""
AND LOWER(t.day_of_week) =
    LOWER(TRIM(TO_CHAR(CURRENT_DATE, 'Day')))
"""

    if day == "tomorrow":

        return f"""
AND LOWER(t.day_of_week) =
    LOWER(TRIM(TO_CHAR(CURRENT_DATE + INTERVAL '1 day', 'Day')))
"""

    if day == "next":

        return f"""
AND (
    LOWER(t.day_of_week) =
        LOWER(TRIM(TO_CHAR(CURRENT_DATE, 'Day')))
    AND t.start_time >= CURRENT_TIME
)
"""

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
            f"\nAND LOWER({alias}.day_of_week) "
            f"= '{day}'"
        )

    return ""


# =========================================================
# GENERATE SQL
# =========================================================

def generate_sql(
    question: str,
    plan: dict,
    current_user: dict
):

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

    # =====================================================
    # SECURITY
    # =====================================================

    if intent in {
        "marks",
        "attendance",
        "assignments",
        "timetable",
        "exams",
        "performance",
    }:

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

        # -------------------------------------------------
        # HIGHEST / LOWEST SCORE
        # -------------------------------------------------

        if metric == "highest_score":
            return f"""
SELECT
    sub.subject_name,
    e.exam_name,
    e.start_date,
    m.marks_obtained,
    m.maximum_marks,
    ROUND(m.marks_obtained * 100.0 / NULLIF(m.maximum_marks, 0), 2) AS percentage
FROM marks m
JOIN class_subjects cs ON m.class_subject_id = cs.class_subject_id
JOIN subjects sub ON cs.subject_id = sub.subject_id
LEFT JOIN exams e ON m.exam_id = e.exam_id
WHERE m.student_id = {student_id}
ORDER BY percentage DESC, e.start_date DESC NULLS LAST
LIMIT 1;
""".strip()

        if metric == "lowest_score":
            return f"""
SELECT
    sub.subject_name,
    e.exam_name,
    e.start_date,
    m.marks_obtained,
    m.maximum_marks,
    ROUND(m.marks_obtained * 100.0 / NULLIF(m.maximum_marks, 0), 2) AS percentage
FROM marks m
JOIN class_subjects cs ON m.class_subject_id = cs.class_subject_id
JOIN subjects sub ON cs.subject_id = sub.subject_id
LEFT JOIN exams e ON m.exam_id = e.exam_id
WHERE m.student_id = {student_id}
ORDER BY percentage ASC, e.start_date ASC NULLS LAST
LIMIT 1;
""".strip()

        # -------------------------------------------------
        # HIGHEST / STRONGEST SUBJECT
        # -------------------------------------------------

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

    SUM(m.marks_obtained) AS total_obtained,
    SUM(m.maximum_marks) AS total_maximum

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
    percentage DESC;
""".strip()

        # -------------------------------------------------
        # LOWEST / WEAKEST SUBJECT
        # -------------------------------------------------

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

    SUM(m.marks_obtained) AS total_obtained,
    SUM(m.maximum_marks) AS total_maximum

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
    percentage ASC;
""".strip()

        # -------------------------------------------------
        # PERFORMANCE TREND
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
    ON m.class_subject_id = cs.class_subject_id
JOIN subjects sub
    ON cs.subject_id = sub.subject_id
JOIN exams e
    ON m.exam_id = e.exam_id

WHERE m.student_id = {student_id}
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
    sub.subject_name;
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
    m.maximum_marks

FROM marks m
JOIN class_subjects cs
    ON m.class_subject_id = cs.class_subject_id
JOIN subjects sub
    ON cs.subject_id = sub.subject_id
JOIN exams e
    ON m.exam_id = e.exam_id

WHERE m.student_id = {student_id}
{exam_filter}

ORDER BY
    e.start_date ASC,
    sub.subject_name ASC;
""".strip()

    # =====================================================
    # MARKS — FULLY DETERMINISTIC
    # =====================================================

    if intent == "marks":
        subject = (
            constraints.get("subject")
            or plan.get("context", {}).get("subject")
            or detect_subject(question)
        )

        # Normalize subject names once.
        subject_aliases = {
            "math": "mathematics",
            "maths": "mathematics",
            "sci": "science",
            "social studies": "social science",
            "social sciences": "social science",
            "sst": "social science",
            "computer": "computer science",
            "computers": "computer science",
            "computer studies": "computer science",
            "comp science": "computer science",
            "cs": "computer science",
            "c.s.": "computer science",
            "eng": "english",
            "hin": "hindi",
            "phy": "physics",
            "chem": "chemistry",
            "bio": "biology",
        }

        if subject:
            subject = subject_aliases.get(
                str(subject).lower().strip(),
                str(subject).lower().strip()
            )

        subject_condition = ""
        if subject:
            if subject == "computer science":
                subject_condition = (
                    "\nAND LOWER(TRIM(sub.subject_name)) "
                    "LIKE '%computer%science%'"
                )
            elif subject == "social science":
                subject_condition = (
                    "\nAND LOWER(TRIM(sub.subject_name)) "
                    "LIKE '%social%science%'"
                )
            else:
                safe_subject = subject.replace("'", "''")
                subject_condition = (
                    "\nAND LOWER(TRIM(sub.subject_name)) = "
                    f"LOWER('{safe_subject}')"
                )

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
    m.maximum_marks

FROM marks m

JOIN class_subjects cs
    ON m.class_subject_id = cs.class_subject_id

JOIN subjects sub
    ON cs.subject_id = sub.subject_id

LEFT JOIN exams e
    ON m.exam_id = e.exam_id

WHERE m.student_id = {student_id}
{subject_condition}
{exam_filter}

ORDER BY
    e.start_date ASC NULLS LAST,
    sub.subject_name ASC;
""".strip()

        print("\n===== DETERMINISTIC MARKS SQL =====")
        print(sql)
        print("===================================")
        return clean_sql(sql)

    # =====================================================
    # ATTENDANCE
    # =====================================================

    if intent == "attendance":

        # -------------------------------------------------
        # ABSENT DATES
        # -------------------------------------------------

        if metric == "absent_dates":

            month_filter = month_condition(
                constraints.get("month"),
                "a"
            )

            return f"""
SELECT
    a.attendance_date,
    a.status

FROM attendance a

WHERE a.student_id =
      {student_id}

AND LOWER(a.status) =
    'absent'

{month_filter}

ORDER BY
    a.attendance_date ASC;
""".strip()

        # -------------------------------------------------
        # PRESENT DATES
        # -------------------------------------------------

        if metric == "present_dates":

            month_filter = month_condition(
                constraints.get("month"),
                "a"
            )

            return f"""
SELECT
    a.attendance_date,
    a.status

FROM attendance a

WHERE a.student_id =
      {student_id}

AND LOWER(a.status) =
    'present'

{month_filter}

ORDER BY
    a.attendance_date ASC;
""".strip()

        # -------------------------------------------------
        # ABSENT COUNT
        # -------------------------------------------------

        if metric == "absent_days":

            month_filter = month_condition(
                constraints.get("month"),
                "a"
            )

            return f"""
SELECT
    COUNT(*) AS absent_days

FROM attendance a

WHERE a.student_id =
      {student_id}

AND LOWER(a.status) =
    'absent'

{month_filter};
""".strip()

        # -------------------------------------------------
        # PRESENT COUNT
        # -------------------------------------------------

        if metric == "present_days":

            month_filter = month_condition(
                constraints.get("month"),
                "a"
            )

            return f"""
SELECT
    COUNT(*) AS present_days

FROM attendance a

WHERE a.student_id =
      {student_id}

AND LOWER(a.status) =
    'present'

{month_filter};
""".strip()

        # -------------------------------------------------
        # ATTENDANCE PERCENTAGE
        # -------------------------------------------------

        if metric in {
            "attendance_percentage",
            "attendance_summary",
            "attendance_eligibility",
        }:

            month_filter = month_condition(
                constraints.get("month"),
                "a"
            )

            return f"""
SELECT

    COUNT(*) AS total_days,

    COUNT(*) FILTER (
        WHERE LOWER(a.status) =
              'present'
    ) AS present_days,

    COUNT(*) FILTER (
        WHERE LOWER(a.status) =
              'absent'
    ) AS absent_days,

    COUNT(*) FILTER (
        WHERE LOWER(a.status) =
              'late'
    ) AS late_days,

    ROUND(
        COUNT(*) FILTER (
            WHERE LOWER(a.status) =
                  'present'
        ) * 100.0
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
        # LATE
        # -------------------------------------------------

        if metric in {
            "late_days",
            "late_dates",
        }:

            return f"""
SELECT
    a.attendance_date,
    a.status

FROM attendance a

WHERE a.student_id =
      {student_id}

AND LOWER(a.status) =
    'late'

ORDER BY
    a.attendance_date ASC;
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
        WHERE LOWER(a.status) =
              'present'
    ) AS present_days,

    COUNT(*) FILTER (
        WHERE LOWER(a.status) =
              'absent'
    ) AS absent_days,

    ROUND(
        COUNT(*) FILTER (
            WHERE LOWER(a.status) =
                  'present'
        ) * 100.0
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
        # DEFAULT ATTENDANCE
        # -------------------------------------------------

        return f"""
SELECT
    a.attendance_date,
    a.status

FROM attendance a

WHERE a.student_id =
      {student_id}

ORDER BY
    a.attendance_date ASC;
""".strip()

    # =====================================================
    # ASSIGNMENTS
    # =====================================================

    if intent == "assignments":

        scope = constraints.get(
            "assignment_scope"
        )

        extra_condition = ""

        if scope == "overdue":

            extra_condition = """
AND a.due_date < CURRENT_DATE
"""

        elif scope == "today":

            extra_condition = """
AND a.due_date = CURRENT_DATE
"""

        elif scope == "tomorrow":

            extra_condition = """
AND a.due_date =
    CURRENT_DATE + INTERVAL '1 day'
"""

        elif scope == "upcoming":

            extra_condition = """
AND a.due_date >= CURRENT_DATE
"""

        subject_filter = subject_condition(
            question,
            "sub"
        )

        return f"""
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
    a.due_date ASC,
    sub.subject_name ASC;
""".strip()

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
            next_limit = "\nLIMIT 1"

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
    CASE LOWER(t.day_of_week)
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
        teacher_subject_filter = subject_condition(question, "sub")
        return f"""
SELECT DISTINCT
    t.first_name,
    t.last_name,
    t.email,
    sub.subject_name
FROM students st
JOIN class_subjects cs ON st.class_id = cs.class_id
JOIN subjects sub ON cs.subject_id = sub.subject_id
JOIN teachers t ON cs.teacher_id = t.teacher_id
WHERE st.student_id = {student_id}
{teacher_subject_filter}
ORDER BY sub.subject_name, t.last_name, t.first_name;
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

    return clean_sql(
        sql
    )