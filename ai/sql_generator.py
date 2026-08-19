"""
sql_generator.py

School Chatbot SQL Generator

Strategy
--------
1. Deterministic SQL for important school-data queries.
2. Natural-language synonyms are normalized centrally.
3. PostgreSQL is the source of truth for structured data.
4. LLM SQL generation is used only as a fallback.
5. Logged-in student ownership is always enforced.
6. Subject / exam / day / assignment terminology is normalized.
7. No duplicate generate_sql() definitions.
8. No undefined variables.
9. Supports:
   - Marks
   - Performance
   - Highest / lowest subject
   - Highest / lowest score
   - Attendance
   - Assignments
   - Timetable
   - Exams
"""

import re

from ai.prompt import build_prompt
from ai.ollama_client import generate_sql as ollama_generate_sql


# =========================================================
# GENERAL HELPERS
# =========================================================

def clean_sql(sql: str) -> str:
    """
    Clean LLM-generated SQL.
    """

    if not sql:
        return ""

    sql = sql.strip()

    # Remove markdown fences
    sql = re.sub(
        r"```sql",
        "",
        sql,
        flags=re.IGNORECASE
    )

    sql = sql.replace("```", "").strip()

    # Remove common prefixes
    sql = re.sub(
        r"^(sql\s*:?)",
        "",
        sql,
        flags=re.IGNORECASE
    ).strip()

    # Keep only SELECT statement
    match = re.search(
        r"(SELECT[\s\S]*?;)",
        sql,
        re.IGNORECASE
    )

    if match:
        sql = match.group(1).strip()

    return sql


def normalize_text(text: str) -> str:
    """
    Normalize natural-language input.

    This allows:
        mid-term
        mid term
        MIDTERM

    to become a consistent representation.
    """

    if not text:
        return ""

    text = text.lower().strip()

    # Normalize apostrophes
    text = text.replace("’", "'")

    # Hyphen -> space
    text = text.replace("-", " ")

    # Remove unnecessary punctuation
    text = re.sub(
        r"[?!.,:;()\[\]{}]",
        " ",
        text
    )

    # Collapse spaces
    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# =========================================================
# SUBJECT SYNONYMS
# =========================================================

SUBJECT_SYNONYMS = {

    "mathematics": [
        "mathematics",
        "math",
        "maths",
        "maths subject",
        "math subject",
        "math paper",
        "maths paper",
        "mathematics paper",
        "mathematical studies",
    ],

    "science": [
        "science",
        "sci",
        "science subject",
        "science paper",
        "general science",
    ],

    "social science": [
        "social science",
        "social sciences",
        "social studies",
        "social study",
        "sst",
        "s s t",
        "s.s.t",
        "social science subject",
        "social studies paper",
        "social science paper",
    ],

    "english": [
        "english",
        "eng",
        "english language",
        "english subject",
        "english paper",
        "language english",
    ],

    "hindi": [
        "hindi",
        "hin",
        "hindi language",
        "hindi subject",
        "hindi paper",
    ],

    "computer science": [
        "computer science",
        "computer studies",
        "computer study",
        "computer subject",
        "computer science subject",
        "computer science paper",
        "computer paper",
        "computers",
        "computer",
        "cs",
        "c s",
        "c.s",
        "comp science",
        "comp sci",
        "comp studies",
    ],

    "physics": [
        "physics",
        "phy",
        "physics subject",
        "physics paper",
    ],

    "chemistry": [
        "chemistry",
        "chem",
        "chemistry subject",
        "chemistry paper",
    ],

    "biology": [
        "biology",
        "bio",
        "biology subject",
        "biology paper",
    ],
}

# =========================================================
# SUBJECT NORMALIZATION
# =========================================================

SUBJECT_NORMALIZATION = {

    "math": "mathematics",
    "maths": "mathematics",
    "mathematics": "mathematics",

    "sci": "science",
    "science": "science",

    "social studies": "social science",
    "social sciences": "social science",
    "sst": "social science",
    "social science": "social science",

    "eng": "english",
    "english": "english",

    "hin": "hindi",
    "hindi": "hindi",

    "computer": "computer science",
    "computers": "computer science",
    "computer studies": "computer science",
    "comp science": "computer science",
    "cs": "computer science",
    "computer science": "computer science",

    "phy": "physics",
    "physics": "physics",

    "chem": "chemistry",
    "chemistry": "chemistry",

    "bio": "biology",
    "biology": "biology",
}


def normalize_subject(subject):

    if not subject:
        return None

    subject = str(subject).lower().strip()

    return SUBJECT_NORMALIZATION.get(
        subject,
        subject
    )

def detect_subject(question: str):
    """
    Detect subject from natural language.

    Longest phrase wins.

    Example:
        What did I score in computer science?
        -> computer science
    """

    query = normalize_text(question)

    if not query:
        return None

    candidates = []

    for canonical, synonyms in SUBJECT_SYNONYMS.items():

        for synonym in synonyms:

            synonym_normalized = normalize_text(
                synonym
            )

            if not synonym_normalized:
                continue

            pattern = (
                rf"(?<!\w)"
                rf"{re.escape(synonym_normalized)}"
                rf"(?!\w)"
            )

            if re.search(
                pattern,
                query
            ):

                candidates.append(
                    (
                        len(synonym_normalized),
                        canonical
                    )
                )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return candidates[0][1]


# =========================================================
# EXAM SYNONYMS
# =========================================================

EXAM_SYNONYMS = {

    "midterm": [
        "midterm",
        "mid term",
        "mid term exam",
        "mid term examination",
        "midterm exam",
        "midterm examination",
        "mid exam",
        "mid examination",
        "half yearly",
        "half yearly exam",
        "half yearly examination",
        "half yearly test",
        "first term",
        "first term exam",
        "first term examination",
        "term 1",
        "term one",
        "semester 1",
        "semester one",
        "first semester",
    ],

    "final": [
        "final",
        "finals",
        "final exam",
        "final exams",
        "final examination",
        "final examinations",
        "annual exam",
        "annual exams",
        "annual examination",
        "annual examinations",
        "yearly exam",
        "yearly examination",
        "year end exam",
        "year end examination",
        "end term",
        "end term exam",
        "end term examination",
        "second term",
        "second term exam",
        "second term examination",
        "term 2",
        "term two",
        "semester 2",
        "semester two",
        "second semester",
    ],
}


def detect_exam(question: str):
    """
    Detect exam type.

    Returns:
        midterm
        final
        None
    """

    query = normalize_text(question)

    if not query:
        return None

    candidates = []

    for canonical, synonyms in EXAM_SYNONYMS.items():

        for synonym in synonyms:

            synonym_normalized = normalize_text(
                synonym
            )

            pattern = (
                rf"(?<!\w)"
                rf"{re.escape(synonym_normalized)}"
                rf"(?!\w)"
            )

            if re.search(
                pattern,
                query
            ):

                candidates.append(
                    (
                        len(synonym_normalized),
                        canonical
                    )
                )

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return candidates[0][1]


# =========================================================
# QUESTION TYPE DETECTION
# =========================================================

def contains_any(
    question: str,
    words
) -> bool:

    query = normalize_text(
        question
    )

    for word in words:

        word = normalize_text(word)

        if re.search(
            rf"(?<!\w){re.escape(word)}(?!\w)",
            query
        ):
            return True

    return False


# =========================================================
# PERFORMANCE METRIC DETECTION
# =========================================================

def detect_performance_metric(
    question: str,
    existing_metric=None
):
    """
    Converts many ways of asking performance questions
    into one deterministic metric.

    Examples:

        highest score
        best score
        maximum marks
        highest marks

        -> highest_score

        strongest subject
        best subject
        subject I am best at

        -> highest_subject
    """

    query = normalize_text(
        question
    )

    if existing_metric:
        return existing_metric

    # -----------------------------------------------------
    # HIGHEST SCORE
    # -----------------------------------------------------

    if contains_any(
        query,
        [
            "highest score",
            "highest marks",
            "maximum score",
            "maximum marks",
            "max score",
            "max marks",
            "best score",
            "best marks",
            "top score",
            "top marks",
            "most marks",
            "highest mark",
            "maximum mark",
            "best mark",
            "greatest score",
            "greatest marks",
        ]
    ):

        return "highest_score"

    # -----------------------------------------------------
    # LOWEST SCORE
    # -----------------------------------------------------

    if contains_any(
        query,
        [
            "lowest score",
            "lowest marks",
            "minimum score",
            "minimum marks",
            "min score",
            "min marks",
            "worst score",
            "worst marks",
            "least marks",
            "lowest mark",
            "minimum mark",
            "worst mark",
        ]
    ):

        return "lowest_score"

    # -----------------------------------------------------
    # HIGHEST SUBJECT
    # -----------------------------------------------------

    if contains_any(
        query,
        [
            "highest subject",
            "best subject",
            "strongest subject",
            "strong subject",
            "subject i am best at",
            "subject i'm best at",
            "subject i perform best in",
            "subject i performed best in",
            "best performing subject",
            "highest performing subject",
            "strongest performing subject",
            "top subject",
            "subject with highest percentage",
            "subject with best percentage",
        ]
    ):

        return "highest_subject"

    # -----------------------------------------------------
    # LOWEST SUBJECT
    # -----------------------------------------------------

    if contains_any(
        query,
        [
            "lowest subject",
            "weakest subject",
            "weak subject",
            "subject i am worst at",
            "subject i'm worst at",
            "subject i need to improve",
            "weakest performing subject",
            "lowest performing subject",
            "subject with lowest percentage",
            "subject with worst percentage",
        ]
    ):

        return "lowest_subject"

    # -----------------------------------------------------
    # TREND
    # -----------------------------------------------------

    if contains_any(
        query,
        [
            "performance trend",
            "marks trend",
            "score trend",
            "progress",
            "performance over time",
            "marks over time",
            "scores over time",
            "improvement",
            "improved",
            "getting better",
            "getting worse",
        ]
    ):

        return "trend"

    # -----------------------------------------------------
    # COMPARISON
    # -----------------------------------------------------

    if contains_any(
        query,
        [
            "compare exams",
            "compare my exams",
            "exam comparison",
            "compare marks",
            "compare scores",
            "compare midterm and final",
            "compare mid term and final",
            "difference between exams",
        ]
    ):

        return "exam_comparison"

    # -----------------------------------------------------
    # OVERALL
    # -----------------------------------------------------

    if contains_any(
        query,
        [
            "overall performance",
            "overall percentage",
            "overall score",
            "overall marks",
            "my percentage",
            "my overall result",
            "how am i performing",
            "how am i doing",
        ]
    ):

        return "overall_performance"

    return None


# =========================================================
# EXAM SQL CONDITION
# =========================================================

def exam_condition(
    exam_constraint,
    alias="e"
):
    """
    Convert normalized exam type into PostgreSQL condition.

    Supports both:
        "midterm"
        "final"

    and lists.
    """

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

        exam_type = normalize_text(
            str(exam_type)
        )

        # Normalize router variations
        if exam_type in {
            "mid term",
            "midterm",
            "mid",
            "half yearly",
            "term 1",
            "first term",
            "semester 1",
            "first semester",
        }:

            conditions.append(
                f"""
(
    LOWER({alias}.exam_name) LIKE '%mid%'
    OR LOWER({alias}.exam_name) LIKE '%half%'
    OR LOWER({alias}.exam_name) LIKE '%term 1%'
    OR LOWER({alias}.exam_name) LIKE '%term one%'
    OR LOWER({alias}.exam_name) LIKE '%first term%'
    OR LOWER({alias}.exam_name) LIKE '%semester 1%'
    OR LOWER({alias}.exam_name) LIKE '%semester one%'
    OR LOWER({alias}.exam_name) LIKE '%first semester%'
)
""".strip()
            )

        elif exam_type in {
            "final",
            "finals",
            "annual",
            "yearly",
            "end term",
            "term 2",
            "second term",
            "semester 2",
            "second semester",
        }:

            conditions.append(
                f"""
(
    LOWER({alias}.exam_name) LIKE '%final%'
    OR LOWER({alias}.exam_name) LIKE '%annual%'
    OR LOWER({alias}.exam_name) LIKE '%yearly%'
    OR LOWER({alias}.exam_name) LIKE '%end term%'
    OR LOWER({alias}.exam_name) LIKE '%term 2%'
    OR LOWER({alias}.exam_name) LIKE '%term two%'
    OR LOWER({alias}.exam_name) LIKE '%second term%'
    OR LOWER({alias}.exam_name) LIKE '%semester 2%'
    OR LOWER({alias}.exam_name) LIKE '%semester two%'
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
# SUBJECT SQL CONDITION
# =========================================================

def subject_condition(
    question: str,
    alias="sub"
):
    """
    Generate safe subject filtering.

    Example:
        Computer Science
        -> LOWER(sub.subject_name) LIKE '%computer%science%'
    """

    subject = detect_subject(
        question
    )

    if not subject:
        return ""

    if subject == "computer science":

        return f"""
AND (
    LOWER({alias}.subject_name) LIKE '%computer%science%'
    OR LOWER({alias}.subject_name) = 'computer'
    OR LOWER({alias}.subject_name) = 'computers'
)
""".strip()

    if subject == "social science":

        return f"""
AND (
    LOWER({alias}.subject_name) LIKE '%social%science%'
    OR LOWER({alias}.subject_name) LIKE '%social%stud%'
    OR LOWER({alias}.subject_name) = 'sst'
)
""".strip()

    return (
        f"\nAND LOWER({alias}.subject_name) "
        f"LIKE '%{subject}%'"
    )


# =========================================================
# MONTH CONDITION
# =========================================================

MONTH_NAMES = {
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


def detect_month(question: str):
    """
    Detect month from natural language.
    """

    query = normalize_text(
        question
    )

    for name, number in MONTH_NAMES.items():

        if re.search(
            rf"(?<!\w){re.escape(name)}(?!\w)",
            query
        ):
            return number

    # Numeric month
    match = re.search(
        r"\bmonth\s+(\d{1,2})\b",
        query
    )

    if match:

        month = int(
            match.group(1)
        )

        if 1 <= month <= 12:
            return month

    return None


def month_condition(
    month,
    alias="a"
):

    if not month:
        return ""

    try:
        month = int(
            month
        )
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
# ATTENDANCE METRIC
# =========================================================

def detect_attendance_metric(
    question: str,
    existing_metric=None
):

    if existing_metric:
        return existing_metric

    query = normalize_text(
        question
    )

    # Absent dates
    if contains_any(
        query,
        [
            "absent dates",
            "dates i was absent",
            "days i was absent",
            "when was i absent",
            "when i was absent",
            "which days was i absent",
            "which days i was absent",
            "my absences",
            "absent days",
        ]
    ):

        # If "how many" -> count
        if contains_any(
            query,
            [
                "how many",
                "number of",
                "count",
                "total",
            ]
        ):
            return "absent_days"

        return "absent_dates"

    # Present dates
    if contains_any(
        query,
        [
            "present dates",
            "dates i was present",
            "days i was present",
            "when was i present",
            "which days was i present",
            "my present days",
        ]
    ):

        return "present_dates"

    # Late
    if contains_any(
        query,
        [
            "late",
            "tardy",
            "late days",
            "days i was late",
            "when was i late",
        ]
    ):

        if contains_any(
            query,
            [
                "when",
                "which days",
                "dates",
            ]
        ):
            return "late_dates"

        return "late_days"

    # Percentage / summary
    if contains_any(
        query,
        [
            "attendance percentage",
            "attendance percent",
            "attendance %",
            "percentage attendance",
            "my attendance",
            "attendance",
            "present percentage",
            "attendance rate",
            "attendance ratio",
            "how regular am i",
            "how regular",
        ]
    ):

        return "attendance_percentage"

    # Trend
    if contains_any(
        query,
        [
            "attendance trend",
            "attendance over time",
            "attendance history",
            "attendance progress",
            "monthly attendance",
        ]
    ):

        return "attendance_trend"

    return None


# =========================================================
# ASSIGNMENT SCOPE
# =========================================================

def detect_assignment_scope(
    question: str,
    existing_scope=None
):

    if existing_scope:
        return existing_scope

    query = normalize_text(
        question
    )

    if contains_any(
        query,
        [
            "overdue",
            "late assignment",
            "missed assignment",
            "past due",
            "deadline passed",
        ]
    ):
        return "overdue"

    if contains_any(
        query,
        [
            "today",
            "due today",
            "for today",
        ]
    ):
        return "today"

    if contains_any(
        query,
        [
            "tomorrow",
            "due tomorrow",
            "for tomorrow",
        ]
    ):
        return "tomorrow"

    if contains_any(
        query,
        [
            "upcoming",
            "next assignments",
            "future assignments",
            "pending assignments",
            "remaining assignments",
            "assignments due soon",
        ]
    ):
        return "upcoming"

    return None


# =========================================================
# TIMETABLE DAY
# =========================================================

DAY_SYNONYMS = {

    "monday": [
        "monday",
        "mon",
    ],

    "tuesday": [
        "tuesday",
        "tue",
        "tues",
    ],

    "wednesday": [
        "wednesday",
        "wed",
    ],

    "thursday": [
        "thursday",
        "thu",
        "thur",
        "thurs",
    ],

    "friday": [
        "friday",
        "fri",
    ],

    "saturday": [
        "saturday",
        "sat",
    ],

    "sunday": [
        "sunday",
        "sun",
    ],
}


def detect_timetable_day(
    question: str,
    existing_day=None
):

    if existing_day:
        return str(
            existing_day
        ).lower()

    query = normalize_text(
        question
    )

    if contains_any(
        query,
        [
            "today",
            "todays",
            "today's",
            "current day",
        ]
    ):
        return "today"

    if contains_any(
        query,
        [
            "tomorrow",
            "tomorrows",
            "tomorrow's",
        ]
    ):
        return "tomorrow"

    if contains_any(
        query,
        [
            "next class",
            "upcoming class",
            "next period",
            "upcoming period",
            "what class is next",
            "which class is next",
        ]
    ):
        return "next"

    for canonical, synonyms in DAY_SYNONYMS.items():

        for synonym in synonyms:

            if re.search(
                rf"(?<!\w){re.escape(synonym)}(?!\w)",
                query
            ):
                return canonical

    return None


def timetable_day_condition(
    day,
    alias="t"
):

    if not day:
        return ""

    day = normalize_text(
        str(day)
    )

    if day == "today":

        return f"""
AND LOWER(TRIM({alias}.day_of_week))
    =
    LOWER(TRIM(
        TO_CHAR(
            CURRENT_DATE,
            'Day'
        )
    ))
""".strip()

    if day == "tomorrow":

        return f"""
AND LOWER(TRIM({alias}.day_of_week))
    =
    LOWER(TRIM(
        TO_CHAR(
            CURRENT_DATE + INTERVAL '1 day',
            'Day'
        )
    ))
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
    metric: str,
    student_id: int,
    exam_constraint=None
):

    exam_filter = exam_condition(
        exam_constraint,
        "e"
    )

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

    # -----------------------------------------------------
    # HIGHEST INDIVIDUAL SCORE
    # -----------------------------------------------------

    if metric == "highest_score":

        return f"""
SELECT
    sub.subject_name,
    e.exam_name,
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
    m.marks_obtained DESC,
    percentage DESC

LIMIT 1;
""".strip()

    # -----------------------------------------------------
    # LOWEST INDIVIDUAL SCORE
    # -----------------------------------------------------

    if metric == "lowest_score":

        return f"""
SELECT
    sub.subject_name,
    e.exam_name,
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
    m.marks_obtained ASC,
    percentage ASC

LIMIT 1;
""".strip()

    # -----------------------------------------------------
    # PERFORMANCE TREND
    # -----------------------------------------------------

    if metric == "trend":

        return f"""
SELECT
    e.exam_id,
    e.exam_name,
    e.start_date,

    ROUND(
        SUM(m.marks_obtained) * 100.0
        /
        NULLIF(
            SUM(m.maximum_marks),
            0
        ),
        2
    ) AS percentage

FROM marks m

JOIN exams e
    ON m.exam_id =
       e.exam_id

WHERE m.student_id =
      {student_id}

{exam_filter}

GROUP BY
    e.exam_id,
    e.exam_name,
    e.start_date

ORDER BY
    e.start_date ASC;
""".strip()

    # -----------------------------------------------------
    # EXAM COMPARISON
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # OVERALL PERFORMANCE
    # -----------------------------------------------------

    if metric == "overall_performance":

        return f"""
SELECT
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

JOIN exams e
    ON m.exam_id =
       e.exam_id

WHERE m.student_id =
      {student_id}

{exam_filter};
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
    """
    Main SQL generation entry point.

    Flow:

        User question
              ↓
        Normalize plan
              ↓
        Detect synonyms
              ↓
        Deterministic SQL
              ↓
        LLM fallback
    """

    if not isinstance(
        plan,
        dict
    ):
        plan = {}

    if not isinstance(
        current_user,
        dict
    ):
        current_user = {}

    # =====================================================
    # USER
    # =====================================================

    student_id = current_user.get(
        "student_id"
    )

    # =====================================================
    # PLAN
    # =====================================================

    intent = str(
        plan.get(
            "intent",
            ""
        )
    ).lower().strip()

    metric = plan.get(
        "metric"
    )

    constraints = plan.get(
        "constraints",
        {}
    )

    if not isinstance(
        constraints,
        dict
    ):
        constraints = {}

    # =====================================================
    # NATURAL LANGUAGE NORMALIZATION
    # =====================================================

    detected_subject = detect_subject(
        question
    )

    detected_exam = detect_exam(
        question
    )

    # If planner didn't detect exam, detect it here.
    if not constraints.get(
        "exam"
    ) and detected_exam:

        constraints["exam"] = detected_exam

    # Subject is useful even if planner didn't detect it.
    if detected_subject:

        constraints.setdefault(
            "subject",
            detected_subject
        )

    # =====================================================
    # PERFORMANCE METRIC
    # =====================================================

    if intent == "performance":

        metric = detect_performance_metric(
            question,
            metric
        )

        plan["metric"] = metric

    # =====================================================
    # ATTENDANCE METRIC
    # =====================================================

    if intent == "attendance":

        metric = detect_attendance_metric(
            question,
            metric
        )

        plan["metric"] = metric

        if not constraints.get(
            "month"
        ):

            detected_month = detect_month(
                question
            )

            if detected_month:

                constraints["month"] = (
                    detected_month
                )

    # =====================================================
    # ASSIGNMENT SCOPE
    # =====================================================

    if intent == "assignments":

        assignment_scope = detect_assignment_scope(
            question,
            constraints.get(
                "assignment_scope"
            )
        )

        constraints[
            "assignment_scope"
        ] = assignment_scope

    # =====================================================
    # TIMETABLE DAY
    # =====================================================

    if intent == "timetable":

        timetable_day = detect_timetable_day(
            question,
            constraints.get(
                "day"
            )
        )

        constraints["day"] = timetable_day

    # =====================================================
    # SECURITY
    # =====================================================

    student_required_intents = {
        "marks",
        "attendance",
        "assignments",
        "timetable",
        "performance",
    }

    if intent in student_required_intents:

        if not student_id:

            raise ValueError(
                "Student profile could not be identified."
            )

    # =====================================================
    # DEBUG
    # =====================================================

    print(
        "\n=========================================="
    )

    print(
        "QUESTION:",
        question
    )

    print(
        "INTENT:",
        intent
    )

    print(
        "METRIC:",
        metric
    )

    print(
        "SUBJECT:",
        detected_subject
    )

    print(
        "EXAM:",
        detected_exam
    )

    print(
        "CONSTRAINTS:",
        constraints
    )

    print(
        "STUDENT ID:",
        student_id
    )

    print(
        "=========================================="
    )

    # =====================================================
    # PERFORMANCE
    # =====================================================

    if intent == "performance":

        sql = generate_performance_sql(
            metric=metric,
            student_id=student_id,
            exam_constraint=constraints.get(
                "exam"
            )
        )

        if sql:

            print(
                "\n===== DETERMINISTIC PERFORMANCE SQL ====="
            )

            print(sql)

            print(
                "=========================================="
            )

            return sql

    # =====================================================
    # MARKS
    # =====================================================

    if intent == "marks":

        # -------------------------------------------------
        # GET SUBJECT
        # -------------------------------------------------

        subject = normalize_subject(
            constraints.get("subject")
            or plan.get("context", {}).get("subject")
        )

        exam = constraints.get("exam")

        if not subject:
            raise ValueError(
                "Subject is required for marks query."
            )

        # -------------------------------------------------
        # SUBJECT NORMALIZATION
        # -------------------------------------------------

        subject_map = {

            "math": "mathematics",
            "maths": "mathematics",
            "mathematics": "mathematics",

            "science": "science",
            "sci": "science",

            "social studies": "social science",
            "social sciences": "social science",
            "social science": "social science",
            "sst": "social science",

            "english": "english",
            "eng": "english",

            "hindi": "hindi",
            "hin": "hindi",

            "computer": "computer science",
            "computers": "computer science",
            "computer studies": "computer science",
            "computer subject": "computer science",
            "computer science": "computer science",
            "comp science": "computer science",
            "cs": "computer science",

            "physics": "physics",
            "phy": "physics",

            "chemistry": "chemistry",
            "chem": "chemistry",

            "biology": "biology",
            "bio": "biology",
        }

        subject = str(subject).lower().strip()

        subject = subject_map.get(
            subject,
            subject
        )

        # -------------------------------------------------
        # SUBJECT CONDITION
        # -------------------------------------------------

        if subject == "computer science":

            subject_condition = """
AND (
    LOWER(TRIM(sub.subject_name)) LIKE '%computer%science%'
)
"""

        elif subject == "social science":

            subject_condition = """
AND (
    LOWER(TRIM(sub.subject_name)) LIKE '%social%science%'
)
"""

        else:

            subject_condition = f"""
AND LOWER(TRIM(sub.subject_name)) =
    LOWER(TRIM('{subject}'))
"""

        # -------------------------------------------------
        # EXAM CONDITION
        #
        # IMPORTANT:
        # Only add this when the user actually specified
        # an exam.
        # -------------------------------------------------

        exam_condition_sql = ""

        if exam:

            exam_value = str(
                exam
            ).lower().strip()

            # ---------------------------------------------
            # MID TERM
            # ---------------------------------------------

            if exam_value in {
                "midterm",
                "mid term",
                "mid-term",
                "mid examination",
                "mid exam",
                "half yearly",
                "half-yearly",
            }:

                exam_condition_sql = """
AND (
    LOWER(TRIM(e.exam_name)) LIKE '%mid%'
    OR LOWER(TRIM(e.exam_name)) LIKE '%half%'
    OR LOWER(TRIM(e.exam_name)) LIKE '%term 1%'
    OR LOWER(TRIM(e.exam_name)) LIKE '%first term%'
    OR LOWER(TRIM(e.exam_name)) LIKE '%first semester%'
)
"""

            # ---------------------------------------------
            # FINAL
            # ---------------------------------------------

            elif exam_value in {
                "final",
                "finals",
                "annual",
                "yearly",
                "annual exam",
                "annual examination",
            }:

                exam_condition_sql = """
AND (
    LOWER(TRIM(e.exam_name)) LIKE '%final%'
    OR LOWER(TRIM(e.exam_name)) LIKE '%annual%'
    OR LOWER(TRIM(e.exam_name)) LIKE '%year end%'
    OR LOWER(TRIM(e.exam_name)) LIKE '%end term%'
    OR LOWER(TRIM(e.exam_name)) LIKE '%term 2%'
    OR LOWER(TRIM(e.exam_name)) LIKE '%second term%'
    OR LOWER(TRIM(e.exam_name)) LIKE '%second semester%'
)
"""

        # -------------------------------------------------
        # FINAL DETERMINISTIC MARKS QUERY
        # -------------------------------------------------

        sql = f"""
SELECT
    sub.subject_name,
    e.exam_name,
    m.marks_obtained,
    m.maximum_marks

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

{subject_condition}

{exam_condition_sql}

ORDER BY
    e.start_date ASC NULLS LAST;
""".strip()

        # -------------------------------------------------
        # SAFETY CHECK
        # -------------------------------------------------

        if not sql:

            raise ValueError(
                "SQL generator returned an empty query."
            )

        if not re.match(
            r"^\s*SELECT\b",
            sql,
            re.IGNORECASE
        ):

            raise ValueError(
                "Generated SQL is not a SELECT query."
            )

        # -------------------------------------------------
        # DEBUG
        # -------------------------------------------------

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

        month_filter = month_condition(
            constraints.get(
                "month"
            ),
            "a"
        )

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

AND LOWER(TRIM(a.status)) =
    'absent'

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

AND LOWER(TRIM(a.status)) =
    'present'

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

AND LOWER(TRIM(a.status)) =
    'absent'

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

AND LOWER(TRIM(a.status)) =
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

            return f"""
SELECT

    COUNT(*) AS total_days,

    COUNT(*) FILTER (
        WHERE LOWER(TRIM(a.status)) =
              'present'
    ) AS present_days,

    COUNT(*) FILTER (
        WHERE LOWER(TRIM(a.status)) =
              'absent'
    ) AS absent_days,

    COUNT(*) FILTER (
        WHERE LOWER(TRIM(a.status)) =
              'late'
    ) AS late_days,

    ROUND(
        COUNT(*) FILTER (
            WHERE LOWER(TRIM(a.status)) =
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

AND LOWER(TRIM(a.status)) =
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
        WHERE LOWER(TRIM(a.status)) =
              'present'
    ) AS present_days,

    COUNT(*) FILTER (
        WHERE LOWER(TRIM(a.status)) =
              'absent'
    ) AS absent_days,

    COUNT(*) FILTER (
        WHERE LOWER(TRIM(a.status)) =
              'late'
    ) AS late_days,

    ROUND(
        COUNT(*) FILTER (
            WHERE LOWER(TRIM(a.status)) =
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
        # DEFAULT
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
""".strip()

        elif scope == "today":

            extra_condition = """
AND a.due_date = CURRENT_DATE
""".strip()

        elif scope == "tomorrow":

            extra_condition = """
AND a.due_date =
    CURRENT_DATE + INTERVAL '1 day'
""".strip()

        elif scope == "upcoming":

            extra_condition = """
AND a.due_date >= CURRENT_DATE
""".strip()

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

        # -------------------------------------------------
        # NEXT CLASS
        # -------------------------------------------------

        if day == "next":

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

AND (
    (
        LOWER(TRIM(t.day_of_week))
        =
        LOWER(TRIM(
            TO_CHAR(
                CURRENT_DATE,
                'Day'
            )
        ))
        AND t.start_time >= CURRENT_TIME
    )
    OR
    LOWER(TRIM(t.day_of_week))
        =
        LOWER(TRIM(
            TO_CHAR(
                CURRENT_DATE + INTERVAL '1 day',
                'Day'
            )
        ))
)

ORDER BY
    CASE
        WHEN LOWER(TRIM(t.day_of_week))
             =
             LOWER(TRIM(
                 TO_CHAR(
                     CURRENT_DATE,
                     'Day'
                 )
             ))
        THEN 0
        ELSE 1
    END,

    t.start_time

LIMIT 1;
""".strip()

        # -------------------------------------------------
        # NORMAL TIMETABLE
        # -------------------------------------------------

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

ORDER BY
    CASE LOWER(TRIM(t.day_of_week))
        WHEN 'monday' THEN 1
        WHEN 'tuesday' THEN 2
        WHEN 'wednesday' THEN 3
        WHEN 'thursday' THEN 4
        WHEN 'friday' THEN 5
        WHEN 'saturday' THEN 6
        WHEN 'sunday' THEN 7
    END,

    t.start_time;
""".strip()

    # =====================================================
    # EXAMS
    # =====================================================

    if intent == "exams":

        exam_filter = exam_condition(
            constraints.get(
                "exam"
            ),
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
    # FALLBACK LLM
    # =====================================================

    print(
        "\n===== FALLBACK LLM SQL ====="
    )

    prompt = build_prompt(
        question,
        plan,
        current_user
    )

    sql = ollama_generate_sql(
        prompt
    )

    sql = clean_sql(
        sql
    )

    if not sql:

        raise ValueError(
            "SQL generator returned an empty query."
        )

    # Safety
    if not re.match(
        r"^\s*SELECT\b",
        sql,
        re.IGNORECASE
    ):

        raise ValueError(
            "Generated SQL is not a SELECT query."
        )

    print(sql)

    print(
        "============================"
    )

    return sql