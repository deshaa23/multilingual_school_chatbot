"""
planner_validator.py

School Chatbot Query Planner + Validator

Main goals:
1. Deterministic routing for school-data queries.
2. Student-specific data -> SQL.
3. School policies / announcements / library -> RAG.
4. Normalize subjects consistently.
5. Correctly detect month/year for attendance.
6. Correctly distinguish marks from performance.
7. Prevent LLM / embedding router from overriding strong rules.
"""

import re
from datetime import datetime

from ai.intent_embedding import detect_intent


# =========================================================
# VALID VALUES
# =========================================================

VALID_INTENTS = {
    "marks",
    "attendance",
    "assignments",
    "timetable",
    "exams",
    "teacher",
    "profile",
    "fees",
    "performance",
    "school_policy",
    "announcement",
    "library",
    "unknown",
}

VALID_OPERATIONS = {
    "fetch",
    "compare",
    "analyze",
    "summarize",
}

VALID_QUERY_TYPES = {
    "information",
    "analysis",
    "comparison",
    "recommendation",
}

VALID_SOURCES = {
    "sql",
    "rag",
    "hybrid",
    "unknown",
}


# =========================================================
# VALID METRICS
# =========================================================

VALID_METRICS = {
    "",

    # -------------------------
    # MARKS
    # -------------------------
    "highest_score",
    "lowest_score",

    # -------------------------
    # PERFORMANCE
    # -------------------------
    "trend",
    "highest_subject",
    "lowest_subject",
    "highest_score",
    "lowest_score",
    "exam_comparison",
    "overall_performance",
    "subject_performance",
    "recommendation",
    "best_exam",
    "worst_exam",

    # -------------------------
    # ATTENDANCE
    # -------------------------
    "monthly_attendance",
    "attendance_trend",
    "attendance_summary",
    "attendance_percentage",
    "absent_days",
    "absent_dates",
    "present_days",
    "present_dates",
    "attendance_comparison",
    "attendance_eligibility",
    "late_days",
    "late_dates",

    # -------------------------
    # ASSIGNMENTS
    # -------------------------
    "assignment_summary",
    "upcoming_assignments",
    "overdue_assignments",
    "due_today",
    "due_tomorrow",
    "completed_assignments",
    "pending_assignments",
}


# =========================================================
# MONTHS
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
# WEEKDAYS
# =========================================================

WEEKDAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
}


# =========================================================
# SUBJECT SYNONYMS
# =========================================================

SUBJECT_SYNONYMS = {

    "mathematics": [
        "mathematics",
        "math",
        "maths",
        "math paper",
        "maths paper",
    ],

    "science": [
        "science",
        "sci",
        "science paper",
    ],

    "social science": [
        "social science",
        "social sciences",
        "social studies",
        "sst",
        "s.s.t",
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
        "computers",
        "cs",
        "c.s.",
        "computer studies",
        "computer subject",
        "computer science subject",
        "programming subject",
        "coding subject",
    ],

    "physics": [
        "physics",
        "phy",
    ],

    "chemistry": [
        "chemistry",
        "chem",
    ],

    "biology": [
        "biology",
        "bio",
    ],
}


# =========================================================
# SUBJECT NORMALIZATION
# =========================================================

SUBJECT_NORMALIZATION = {

    "math": "mathematics",
    "maths": "mathematics",
    "math paper": "mathematics",
    "maths paper": "mathematics",

    "sci": "science",

    "social studies": "social science",
    "social sciences": "social science",
    "sst": "social science",
    "s.s.t": "social science",

    "computer": "computer science",
    "computers": "computer science",
    "computer studies": "computer science",
    "computer subject": "computer science",
    "computer science subject": "computer science",
    "cs": "computer science",
    "c.s.": "computer science",

    "eng": "english",

    "hin": "hindi",

    "phy": "physics",

    "chem": "chemistry",

    "bio": "biology",
}


def normalize_subject(subject):
    """
    Convert user/LLM subject names to one canonical value.

    Examples:
        math -> mathematics
        maths -> mathematics
        sci -> science
        computer -> computer science
        cs -> computer science
        computer science -> computer science
    """

    if subject is None:
        return None

    value = str(subject).lower().strip()

    value = re.sub(
        r"\s+",
        " ",
        value
    )

    return SUBJECT_NORMALIZATION.get(
        value,
        value
    )


# =========================================================
# NORMALIZATION RULES
# =========================================================

NORMALIZATION_RULES = {

    # -------------------------
    # MARKS
    # -------------------------

    "scores": " marks ",
    "score": " marks ",
    "scored": " marks ",
    "grades": " marks ",
    "grade": " marks ",
    "results": " marks ",
    "result": " marks ",
    "percentage": " marks ",
    "percent": " marks ",

    # -------------------------
    # ASSIGNMENTS
    # -------------------------

    "homeworks": " assignment ",
    "homework": " assignment ",
    "classwork": " assignment ",
    "schoolwork": " assignment ",
    "school work": " assignment ",
    "tasks": " assignment ",
    "task": " assignment ",
    "projects": " assignment ",
    "project": " assignment ",
    "worksheets": " assignment ",
    "worksheet": " assignment ",

    # -------------------------
    # TIMETABLE
    # -------------------------

    "time table": " timetable ",
    "class schedule": " timetable ",
    "school schedule": " timetable ",
    "daily schedule": " timetable ",
    "period schedule": " timetable ",
    "class timings": " timetable ",
    "class timing": " timetable ",

    # -------------------------
    # ATTENDANCE
    # -------------------------

    "attendence": " attendance ",
    "presence rate": " attendance ",
    "present rate": " attendance ",
    "attendance rate": " attendance ",
    "absenteeism": " absence ",
    "missed classes": " absent ",
    "missed class": " absent ",
    "missed school": " absent ",

    # -------------------------
    # EXAMS
    # -------------------------

    "mid-term": " midterm ",
    "mid term": " midterm ",
    "midterm exam": " midterm ",
    "midterm examination": " midterm ",

    "final examination": " final exam ",
    "finals": " final exam ",

    "annual examination": " annual exam ",
    "annuals": " annual exam ",

    # -------------------------
    # INFORMAL
    # -------------------------

    "pls": " please ",
    "plz": " please ",
}


def normalize_for_routing(question: str) -> str:

    q = (
        question
        or ""
    ).lower().strip()

    q = q.replace(
        "’",
        "'"
    )

    q = re.sub(
        r"[!?.,;:]+",
        " ",
        q
    )

    # Longest phrases first
    rules = sorted(
        NORMALIZATION_RULES.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )

    for old, new in rules:
        q = q.replace(
            old,
            new
        )

    q = re.sub(
        r"\s+",
        " ",
        q
    )

    return q.strip()


# =========================================================
# PERFORMANCE PATTERNS
# =========================================================

PERFORMANCE_PATTERNS = {

    "highest_subject": [
        "strongest subject",
        "strongest",
        "best subject",
        "best performing subject",
        "best performing",
        "performing best",
        "performed best",
        "top subject",
        "top performing subject",
        "highest subject",
        "highest scoring subject",
        "subject with highest marks",
        "subject with highest score",
        "subject where i scored highest",
        "which subject is best",
        "which subject is my best",
        "which subject is strongest",
        "where am i strongest",
        "my strongest subject",
        "my best subject",
    ],

    "lowest_subject": [
        "weakest subject",
        "weak subject",
        "weakest",
        "worst subject",
        "worst performing subject",
        "performing worst",
        "performed worst",
        "lowest subject",
        "lowest scoring subject",
        "subject with lowest marks",
        "subject with lowest score",
        "which subject needs improvement",
        "which subject should i improve",
        "where am i weakest",
        "my weakest subject",
        "my worst subject",
    ],

    "trend": [
        "am i improving",
        "am i getting better",
        "getting better",
        "doing better",
        "improving",
        "improvement",
        "performance trend",
        "performance over time",
        "performance changing",
        "how is my performance changing",
        "how am i progressing",
        "my progress",
        "academic progress",
        "have i improved",
        "did i improve",
        "how have i improved",
        "show my performance trend",
    ],

    "exam_comparison": [
        "compare exams",
        "compare my exams",
        "compare my marks",
        "compare my scores",
        "exam comparison",
        "difference between exams",
        "mid term vs final",
        "midterm vs final",
        "final vs mid term",
        "final compared to mid term",
        "compare my performance",
        "how much did i improve",
        "how did i improve",
    ],

    "overall_performance": [
        "overall performance",
        "overall marks",
        "overall score",
        "overall result",
        "overall percentage",
        "total performance",
        "academic performance",
        "marks performance",
        "my marks performance",
        "how did i perform",
        "how did i perform overall",
        "how am i performing",
        "how am i doing",
        "how am i doing academically",
        "how well am i doing",
        "how well am i doing overall",
        "my performance",
    ],
}


# =========================================================
# ATTENDANCE WORDS
# =========================================================

ATTENDANCE_WORDS = [
    "attendance",
    "attendence",
    "attended",
    "present",
    "presence",
    "absent",
    "absence",
    "absentee",
    "absenteeism",
    "missed school",
    "miss school",
    "missed class",
    "miss class",
    "late attendance",
]


# =========================================================
# ASSIGNMENT WORDS
# =========================================================

ASSIGNMENT_WORDS = [
    "assignment",
    "assignments",
    "homework",
    "homeworks",
    "classwork",
    "schoolwork",
    "school work",
    "task",
    "tasks",
    "project",
    "projects",
    "worksheet",
    "worksheets",
    "coursework",
    "submission",
    "submissions",
]


# =========================================================
# TIMETABLE WORDS
# =========================================================

TIMETABLE_WORDS = [
    "timetable",
    "time table",
    "schedule",
    "routine",
    "period",
    "periods",
    "class timing",
    "class timings",
    "class schedule",
    "school schedule",
    "next class",
    "next period",
    "today's classes",
    "tomorrow's classes",
    "what class do i have",
    "which class do i have",
    "when is my class",
]


# =========================================================
# EXAM WORDS
# =========================================================

EXAM_WORDS = [
    "exam",
    "exams",
    "examination",
    "examinations",
    "test",
    "tests",
    "midterm",
    "mid term",
    "mid-year",
    "mid year",
    "final",
    "finals",
    "annual",
    "half yearly",
    "half-yearly",
    "semester",
    "term",
]


# =========================================================
# RAG WORDS
# =========================================================

RAG_POLICY_WORDS = [
    "policy",
    "policies",
    "rule",
    "rules",
    "regulation",
    "regulations",
    "guideline",
    "guidelines",
    "school policy",
    "school rule",
    "school rules",
    "leave policy",
    "attendance policy",
]


RAG_LIBRARY_WORDS = [
    "library policy",
    "library rules",
    "library fine",
    "library fines",
    "book return policy",
    "borrow book",
    "borrow books",
    "library membership",
    "library timing",
]


RAG_ANNOUNCEMENT_WORDS = [
    "announcement",
    "announcements",
    "notice",
    "notices",
    "circular",
    "circulars",
    "latest notice",
    "school notice",
    "school announcement",
    "school announcements",
]


# =========================================================
# HELPERS
# =========================================================

def contains_any(
    text: str,
    phrases
) -> bool:

    if not text:
        return False

    text = text.lower()

    for phrase in phrases:

        phrase = phrase.lower().strip()

        if phrase and phrase in text:
            return True

    return False


def regex_any(
    text: str,
    patterns
) -> bool:

    if not text:
        return False

    return any(
        re.search(
            pattern,
            text,
            re.IGNORECASE
        )
        for pattern in patterns
    )


def make_plan(
    intent: str,
    *,
    query_type="information",
    operation="fetch",
    source="sql",
    constraints=None,
    context=None,
    metric="",
    analysis=False,
    comparison=False,
    confidence=1.0,
    reasoning=""
):

    return {
        "intent": intent,
        "query_type": query_type,
        "operation": operation,
        "source": source,
        "constraints": constraints or {},
        "context": context or {},
        "metric": metric,
        "analysis": analysis,
        "comparison": comparison,
        "confidence": confidence,
        "reasoning": reasoning,
    }


# =========================================================
# SUBJECT DETECTION
# =========================================================

def detect_subject(q: str):

    if not q:
        return None

    candidates = []

    for canonical, synonyms in SUBJECT_SYNONYMS.items():

        for synonym in synonyms:

            pattern = (
                rf"\b{re.escape(synonym.lower())}\b"
            )

            if re.search(
                pattern,
                q,
                re.IGNORECASE
            ):

                candidates.append(
                    (
                        len(synonym),
                        canonical
                    )
                )

    if not candidates:
        return None

    candidates.sort(
        key=lambda x: x[0],
        reverse=True
    )

    return normalize_subject(
        candidates[0][1]
    )


# =========================================================
# EXAM DETECTION
# =========================================================

def detect_exam_constraint(q: str):

    midterm_patterns = [
        r"\bmidterm\b",
        r"\bmid[- ]term\b",
        r"\bmid[- ]term exam\b",
        r"\bmid[- ]term examination\b",
        r"\bmid year\b",
        r"\bmid-year\b",
        r"\bhalf yearly\b",
        r"\bhalf-yearly\b",
        r"\bterm 1\b",
        r"\bfirst term\b",
        r"\bfirst semester\b",
        r"\bsemester 1\b",
    ]

    final_patterns = [
        r"\bfinal\b",
        r"\bfinals\b",
        r"\bfinal exam\b",
        r"\bfinal examination\b",
        r"\bannual exam\b",
        r"\bannual examination\b",
        r"\bend term\b",
        r"\bend-term\b",
        r"\bterm 2\b",
        r"\bsecond term\b",
        r"\bsecond semester\b",
        r"\bsemester 2\b",
    ]

    has_midterm = regex_any(
        q,
        midterm_patterns
    )

    has_final = regex_any(
        q,
        final_patterns
    )

    if has_midterm and has_final:

        return {
            "exam": [
                "midterm",
                "final"
            ],
            "comparison": True,
        }

    if has_midterm:

        return {
            "exam": "midterm",
            "comparison": False,
        }

    if has_final:

        return {
            "exam": "final",
            "comparison": False,
        }

    return {
        "exam": None,
        "comparison": False,
    }


# =========================================================
# MONTH/YEAR EXTRACTION
# =========================================================

def extract_month_year(q: str):

    if not q:
        return {
            "month": None,
            "year": None
        }

    q = q.lower()

    now = datetime.now()

    # -------------------------
    # THIS MONTH
    # -------------------------

    if (
        "this month" in q
        or "current month" in q
    ):

        return {
            "month": now.month,
            "year": now.year
        }

    # -------------------------
    # LAST MONTH
    # -------------------------

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

    # -------------------------
    # MONTH + YEAR
    # -------------------------

    month_pattern = "|".join(
        re.escape(x)
        for x in MONTH_MAP.keys()
    )

    match = re.search(
        rf"\b({month_pattern})\s+((?:19|20)\d{{2}})\b",
        q,
        re.IGNORECASE
    )

    if match:

        month_name = match.group(1).lower()

        return {
            "month": MONTH_MAP[month_name],
            "year": int(match.group(2))
        }

    # -------------------------
    # YEAR + MONTH
    # -------------------------

    match = re.search(
        rf"\b((?:19|20)\d{{2}})\s+({month_pattern})\b",
        q,
        re.IGNORECASE
    )

    if match:

        month_name = match.group(2).lower()

        return {
            "month": MONTH_MAP[month_name],
            "year": int(match.group(1))
        }

    # -------------------------
    # MONTH ONLY
    # -------------------------

    for month_name, number in MONTH_MAP.items():

        if re.search(
            rf"\b{re.escape(month_name)}\b",
            q
        ):

            return {
                "month": number,
                "year": None
            }

    return {
        "month": None,
        "year": None
    }


# =========================================================
# RAG DETECTION
# =========================================================

def detect_rag_intent(q: str):

    if contains_any(
        q,
        RAG_LIBRARY_WORDS
    ):
        return "library"

    if contains_any(
        q,
        RAG_ANNOUNCEMENT_WORDS
    ):
        return "announcement"

    if contains_any(
        q,
        RAG_POLICY_WORDS
    ):

        # Personal attendance should remain SQL.
        if contains_any(
            q,
            [
                "my attendance",
                "my absence",
                "my absences",
                "my present days",
                "my absent days",
            ]
        ):
            return None

        return "school_policy"

    return None


# =========================================================
# EXAM SCHEDULE DETECTION
# =========================================================

def is_exam_schedule_query(q: str):

    if not contains_any(
        q,
        EXAM_WORDS
    ):
        return False

    if contains_any(
        q,
        [
            "marks",
            "score",
            "scores",
            "scored",
            "grade",
            "result",
            "percentage",
            "obtained",
            "got",
        ]
    ):
        return False

    return contains_any(
        q,
        [
            "when",
            "date",
            "dates",
            "schedule",
            "start",
            "starts",
            "begin",
            "begins",
            "end",
            "ends",
            "timing",
            "calendar",
        ]
    )


# =========================================================
# ATTENDANCE DETECTION
# =========================================================

def detect_attendance_plan(q: str):

    if not contains_any(
        q,
        ATTENDANCE_WORDS
    ):
        return None

    month_info = extract_month_year(q)

    constraints = {}

    if month_info["month"] is not None:

        constraints["month"] = (
            month_info["month"]
        )

    if month_info["year"] is not None:

        constraints["year"] = (
            month_info["year"]
        )

    # =====================================================
    # TREND
    # =====================================================

    if contains_any(
        q,
        [
            "attendance trend",
            "attendance over time",
            "attendance changing",
            "attendance improving",
            "attendance getting better",
            "attendance getting worse",
            "attendance progress",
            "is my attendance improving",
            "how has my attendance changed",
        ]
    ):

        return make_plan(
            "attendance",
            query_type="analysis",
            operation="analyze",
            metric="attendance_trend",
            constraints=constraints,
            analysis=True,
            confidence=1.0,
            reasoning="Detected attendance trend query."
        )

    # =====================================================
    # ELIGIBILITY
    # =====================================================

    if contains_any(
        q,
        [
            "eligible",
            "eligibility",
            "enough attendance",
            "attendance enough",
            "minimum attendance",
            "required attendance",
            "attendance requirement",
            "attendance shortage",
            "75%",
            "75 percent",
        ]
    ):

        return make_plan(
            "attendance",
            query_type="analysis",
            operation="analyze",
            metric="attendance_eligibility",
            constraints=constraints,
            analysis=True,
            confidence=1.0,
            reasoning="Detected attendance eligibility query."
        )

    # =====================================================
    # ABSENT DATES
    # =====================================================

    if regex_any(
        q,
        [
            r"\bwhen was i absent\b",
            r"\bwhen were i absent\b",
            r"\bwhich days.*absent\b",
            r"\bwhat days.*absent\b",
            r"\bdates.*absent\b",
            r"\babsent dates\b",
            r"\babsence dates\b",
            r"\bwhen did i miss\b",
            r"\bwhich days did i miss\b",
            r"\bwhat days did i miss\b",
            r"\bmissed days\b",
            r"\bdays i missed\b",
            r"\bdays i was absent\b",
        ]
    ):

        constraints["attendance"] = "absent"

        return make_plan(
            "attendance",
            metric="absent_dates",
            constraints=constraints,
            confidence=1.0,
            reasoning="Detected absent-date query."
        )

    # =====================================================
    # PRESENT DATES
    # =====================================================

    if regex_any(
        q,
        [
            r"\bwhen was i present\b",
            r"\bwhich days.*present\b",
            r"\bwhat days.*present\b",
            r"\bpresent dates\b",
            r"\bdays i attended\b",
            r"\bdays i was present\b",
            r"\bwhich days did i attend\b",
        ]
    ):

        constraints["attendance"] = "present"

        return make_plan(
            "attendance",
            metric="present_dates",
            constraints=constraints,
            confidence=1.0,
            reasoning="Detected present-date query."
        )

    # =====================================================
    # ABSENT COUNT
    # =====================================================

    if regex_any(
        q,
        [
            r"how many.*absen",
            r"number of absences",
            r"number of absent days",
            r"total absences",
            r"total absent days",
            r"count.*absence",
            r"count.*absent",
            r"how many days was i absent",
        ]
    ):

        return make_plan(
            "attendance",
            query_type="analysis",
            operation="analyze",
            metric="absent_days",
            constraints=constraints,
            analysis=True,
            confidence=1.0,
            reasoning="Detected absence-count query."
        )

    # =====================================================
    # PRESENT COUNT
    # =====================================================

    if regex_any(
        q,
        [
            r"how many.*present",
            r"how many.*attended",
            r"number of present days",
            r"total present days",
            r"count.*present days",
            r"days have i attended",
            r"number of days i attended",
            r"how many days did i attend",
        ]
    ):

        return make_plan(
            "attendance",
            query_type="analysis",
            operation="analyze",
            metric="present_days",
            constraints=constraints,
            analysis=True,
            confidence=1.0,
            reasoning="Detected present-day count query."
        )

    # =====================================================
    # MONTHLY ATTENDANCE
    # =====================================================

    if (
        month_info["month"] is not None
        or contains_any(
            q,
            [
                "monthly attendance",
                "attendance for the month",
                "attendance for this month",
                "attendance this month",
                "show my attendance",
                "show attendance",
                "attendance record",
                "attendance records",
            ]
        )
    ):

        return make_plan(
            "attendance",
            query_type="information",
            operation="fetch",
            metric="monthly_attendance",
            constraints=constraints,
            confidence=1.0,
            reasoning=(
                "Detected monthly attendance "
                "record query."
            )
        )

    # =====================================================
    # PERCENTAGE
    # =====================================================

    if regex_any(
        q,
        [
            r"\battendance percentage\b",
            r"\battendance percent\b",
            r"\battendance rate\b",
            r"\bwhat is my attendance\b",
            r"\bhow much attendance\b",
            r"\bhow good is my attendance\b",
            r"\bmy attendance\b",
            r"\battendance score\b",
        ]
    ):

        return make_plan(
            "attendance",
            query_type="analysis",
            operation="analyze",
            metric="attendance_percentage",
            constraints=constraints,
            analysis=True,
            confidence=1.0,
            reasoning="Detected attendance-percentage query."
        )

    # =====================================================
    # SUMMARY
    # =====================================================

    if contains_any(
        q,
        [
            "attendance summary",
            "attendance report",
            "attendance details",
            "present and absent",
            "present absent",
            "attendance overview",
            "attendance statistics",
            "attendance stats",
        ]
    ):

        return make_plan(
            "attendance",
            query_type="analysis",
            operation="analyze",
            metric="attendance_summary",
            constraints=constraints,
            analysis=True,
            confidence=1.0,
            reasoning="Detected attendance-summary query."
        )

    # =====================================================
    # COMPARISON
    # =====================================================

    if contains_any(
        q,
        [
            "compare my attendance",
            "attendance comparison",
            "compare attendance",
            "attendance compared",
            "compared to last month",
            "compared with last month",
            "this month vs last month",
        ]
    ):

        return make_plan(
            "attendance",
            query_type="comparison",
            operation="compare",
            metric="attendance_comparison",
            constraints=constraints,
            analysis=True,
            comparison=True,
            confidence=1.0,
            reasoning="Detected attendance comparison."
        )

    # =====================================================
    # LATE
    # =====================================================

    if contains_any(
        q,
        [
            "late days",
            "days i was late",
            "when was i late",
            "late attendance",
            "late to school",
            "late to class",
            "number of late days",
            "how many times was i late",
        ]
    ):

        constraints["attendance"] = "late"

        return make_plan(
            "attendance",
            metric="late_days",
            constraints=constraints,
            confidence=1.0,
            reasoning="Detected late-attendance query."
        )

    # =====================================================
    # DEFAULT ATTENDANCE
    # =====================================================

    # IMPORTANT:
    # "What is my attendance?" -> percentage
    #
    # "Show my attendance" -> monthly records

    if regex_any(
        q,
        [
            r"\bwhat is my attendance\b",
            r"\bhow much attendance do i have\b",
            r"\bwhat percentage.*attendance\b",
            r"\bmy attendance percentage\b",
        ]
    ):

        return make_plan(
            "attendance",
            query_type="analysis",
            operation="analyze",
            metric="attendance_percentage",
            constraints=constraints,
            analysis=True,
            confidence=1.0,
            reasoning="Detected attendance-percentage query."
        )

    return make_plan(
        "attendance",
        query_type="information",
        operation="fetch",
        metric="monthly_attendance",
        constraints=constraints,
        confidence=0.95,
        reasoning=(
            "Detected general attendance query; "
            "defaulting to monthly attendance records."
        )
    )


# =========================================================
# PERFORMANCE DETECTION
# =========================================================

def detect_performance_plan(q: str):

    # =====================================================
    # HIGHEST SCORE
    # =====================================================

    if contains_any(
        q,
        [
            "highest score",
            "highest marks",
            "maximum score",
            "maximum marks",
            "top score",
            "top marks",
            "most marks",
        ]
    ):

        return make_plan(
            "marks",
            metric="highest_score",
            query_type="information",
            operation="fetch",
            source="sql",
            confidence=1.0,
            reasoning="Detected highest-score query."
        )

    # =====================================================
    # LOWEST SCORE
    # =====================================================

    if contains_any(
        q,
        [
            "lowest score",
            "lowest marks",
            "minimum score",
            "minimum marks",
            "least marks",
        ]
    ):

        return make_plan(
            "marks",
            metric="lowest_score",
            query_type="information",
            operation="fetch",
            source="sql",
            confidence=1.0,
            reasoning="Detected lowest-score query."
        )

    # =====================================================
    # SPECIFIC SUBJECT CHECK
    # =====================================================

    specific_subject = detect_subject(q)

    specific_subject_query = (
        specific_subject is not None
        and regex_any(
            q,
            [
                r"\bwhat.*marks.*in\b",
                r"\bwhat.*score.*in\b",
                r"\bhow much.*in\b",
                r"\bmarks.*for\b",
                r"\bscore.*for\b",
                r"\bhow did i do in\b",
                r"\bwhat did i get in\b",
                r"\bwhat did i score in\b",
            ]
        )
    )

    # =====================================================
    # STRONGEST SUBJECT
    # =====================================================

    if contains_any(
        q,
        PERFORMANCE_PATTERNS[
            "highest_subject"
        ]
    ):

        if not specific_subject_query:

            return make_plan(
                "performance",
                query_type="analysis",
                operation="analyze",
                source="sql",
                metric="highest_subject",
                analysis=True,
                confidence=1.0,
                reasoning=(
                    "Detected strongest/highest-performing "
                    "subject query."
                )
            )

    # =====================================================
    # WEAKEST SUBJECT
    # =====================================================

    if contains_any(
        q,
        PERFORMANCE_PATTERNS[
            "lowest_subject"
        ]
    ):

        if not specific_subject_query:

            return make_plan(
                "performance",
                query_type="analysis",
                operation="analyze",
                source="sql",
                metric="lowest_subject",
                analysis=True,
                confidence=1.0,
                reasoning=(
                    "Detected weakest/lowest-performing "
                    "subject query."
                )
            )

    # =====================================================
    # EXAM COMPARISON
    # =====================================================

    exam_info = detect_exam_constraint(q)

    comparison_words = [
        "compare",
        "comparison",
        "compared",
        "versus",
        " vs ",
        "difference",
        "improvement",
        "improved",
    ]

    if (
        exam_info["comparison"]
        or (
            exam_info["exam"] is not None
            and contains_any(
                q,
                comparison_words
            )
        )
        or contains_any(
            q,
            PERFORMANCE_PATTERNS[
                "exam_comparison"
            ]
        )
    ):

        constraints = {}

        if exam_info["exam"]:
            constraints["exam"] = (
                exam_info["exam"]
            )

        return make_plan(
            "performance",
            query_type="comparison",
            operation="compare",
            source="sql",
            constraints=constraints,
            metric="exam_comparison",
            analysis=True,
            comparison=True,
            confidence=1.0,
            reasoning="Detected exam-performance comparison."
        )

    # =====================================================
    # OVERALL PERFORMANCE
    # =====================================================

    if contains_any(
        q,
        PERFORMANCE_PATTERNS[
            "overall_performance"
        ]
    ):

        return make_plan(
            "performance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="overall_performance",
            analysis=True,
            confidence=1.0,
            reasoning="Detected overall-performance query."
        )

    # =====================================================
    # TREND
    # =====================================================

    if contains_any(
        q,
        PERFORMANCE_PATTERNS[
            "trend"
        ]
    ):

        return make_plan(
            "performance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="trend",
            analysis=True,
            confidence=1.0,
            reasoning="Detected performance-trend query."
        )

    return None


# =========================================================
# ASSIGNMENT DETECTION
# =========================================================

def detect_assignment_plan(q: str):

    if not contains_any(
        q,
        ASSIGNMENT_WORDS
    ):
        return None

    # =====================================================
    # OVERDUE
    # =====================================================

    if contains_any(
        q,
        [
            "overdue",
            "over due",
            "late assignment",
            "late assignments",
            "past due",
            "past deadline",
            "missed deadline",
            "deadline passed",
        ]
    ):

        return make_plan(
            "assignments",
            constraints={
                "assignment_scope": "overdue"
            },
            metric="overdue_assignments",
            confidence=1.0,
            reasoning="Detected overdue-assignment query."
        )

    # =====================================================
    # TODAY
    # =====================================================

    if contains_any(
        q,
        [
            "due today",
            "today's assignment",
            "assignments today",
            "homework today",
            "task today",
            "work due today",
        ]
    ):

        return make_plan(
            "assignments",
            constraints={
                "assignment_scope": "today"
            },
            metric="due_today",
            confidence=1.0,
            reasoning="Detected assignments due today."
        )

    # =====================================================
    # TOMORROW
    # =====================================================

    if contains_any(
        q,
        [
            "due tomorrow",
            "tomorrow's assignment",
            "assignments tomorrow",
            "homework tomorrow",
            "task tomorrow",
        ]
    ):

        return make_plan(
            "assignments",
            constraints={
                "assignment_scope": "tomorrow"
            },
            metric="due_tomorrow",
            confidence=1.0,
            reasoning="Detected assignments due tomorrow."
        )

    # =====================================================
    # COMPLETED
    # =====================================================

    if contains_any(
        q,
        [
            "completed assignments",
            "finished assignments",
            "submitted assignments",
            "completed homework",
            "finished homework",
        ]
    ):

        return make_plan(
            "assignments",
            metric="completed_assignments",
            confidence=1.0,
            reasoning="Detected completed-assignment query."
        )

    # =====================================================
    # PENDING / UPCOMING
    # =====================================================

    if contains_any(
        q,
        [
            "upcoming assignment",
            "upcoming assignments",
            "next assignment",
            "next assignments",
            "what do i have to submit",
            "what do i need to submit",
            "what should i submit",
            "pending assignment",
            "pending assignments",
            "assignments due",
            "homework due",
            "work pending",
        ]
    ):

        return make_plan(
            "assignments",
            constraints={
                "assignment_scope": "upcoming"
            },
            metric="upcoming_assignments",
            confidence=1.0,
            reasoning="Detected pending/upcoming assignment query."
        )

    # =====================================================
    # DEFAULT
    # =====================================================

    return make_plan(
        "assignments",
        metric="assignment_summary",
        confidence=0.95,
        reasoning="Detected assignment/homework query."
    )


# =========================================================
# TIMETABLE
# =========================================================

def detect_timetable_plan(q: str):

    if not contains_any(
        q,
        TIMETABLE_WORDS
    ):
        return None

    if is_exam_schedule_query(q):
        return None

    constraints = {}

    for day in WEEKDAYS:

        if re.search(
            rf"\b{day}\b",
            q
        ):

            constraints["day"] = day
            break

    if "today" in q:
        constraints["day"] = "today"

    if "tomorrow" in q:
        constraints["day"] = "tomorrow"

    if contains_any(
        q,
        [
            "next class",
            "next period",
            "next lecture",
        ]
    ):

        constraints["day"] = "next"

    return make_plan(
        "timetable",
        constraints=constraints,
        confidence=1.0,
        reasoning="Detected timetable query."
    )


# =========================================================
# MARKS
# =========================================================

def detect_marks_plan(q: str):

    marks_words = [
        "marks",
        "mark",
        "score",
        "scores",
        "scored",
        "grade",
        "grades",
        "result",
        "results",
        "percentage",
        "percent",
        "obtained",
        "got",
        "how much did i get",
        "what did i get",
        "what did i score",
        "my score",
        "my marks",
        "my result",
    ]

    if not contains_any(
        q,
        marks_words
    ):
        return None

    # Performance gets priority.
    performance_plan = detect_performance_plan(q)

    if performance_plan:
        return performance_plan

    constraints = {}

    exam_info = detect_exam_constraint(q)

    if exam_info["exam"]:
        constraints["exam"] = (
            exam_info["exam"]
        )

    context = {}

    subject = detect_subject(q)

    if subject:
        context["subject"] = normalize_subject(
            subject
        )

    return make_plan(
        "marks",
        constraints=constraints,
        context=context,
        confidence=1.0,
        reasoning="Detected marks/score/result query."
    )


# =========================================================
# TEACHER
# =========================================================

def detect_teacher_plan(q: str):

    if not contains_any(
        q,
        [
            "teacher",
            "teachers",
            "who teaches",
            "who is my teacher",
            "who teaches me",
            "subject teacher",
            "instructor",
            "faculty",
        ]
    ):
        return None

    context = {}

    subject = detect_subject(q)

    if subject:
        context["subject"] = normalize_subject(
            subject
        )

    return make_plan(
        "teacher",
        context=context,
        confidence=1.0,
        reasoning="Detected teacher query."
    )


# =========================================================
# PROFILE
# =========================================================

def detect_profile_plan(q: str):

    if not contains_any(
        q,
        [
            "my profile",
            "my details",
            "my information",
            "my student details",
            "my student information",
            "my class",
            "which class am i in",
            "what class am i in",
            "my section",
            "my roll number",
            "my admission number",
            "my admission",
            "my personal details",
        ]
    ):
        return None

    return make_plan(
        "profile",
        confidence=1.0,
        reasoning="Detected student-profile query."
    )


# =========================================================
# PERSONAL FEES
# =========================================================

def detect_fee_plan(q: str):

    if not contains_any(
        q,
        [
            "my fees",
            "my fee",
            "fee pending",
            "fees pending",
            "fee paid",
            "fees paid",
            "have i paid my fees",
            "how much fee is pending",
            "how much fees is pending",
        ]
    ):
        return None

    # IMPORTANT:
    # These are PERSONAL student data.
    # Therefore SQL, NOT RAG.

    return make_plan(
        "fees",
        source="sql",
        confidence=1.0,
        reasoning="Detected personal student-fee query."
    )


# =========================================================
# SEMANTIC ROUTER
# =========================================================

def semantic_route(q: str):

    try:

        (
            semantic_intent,
            semantic_score,
            scores
        ) = detect_intent(q)

        print(
            "\n===== SEMANTIC INTENT ====="
        )

        print(
            "Query:",
            q
        )

        print(
            "Embedding Intent:",
            semantic_intent
        )

        print(
            "Embedding Score:",
            semantic_score
        )

        print(
            "All Scores:",
            scores
        )

        print(
            "===========================\n"
        )

        return (
            semantic_intent,
            float(semantic_score),
            scores
        )

    except Exception as e:

        print(
            "Semantic router error:",
            e
        )

        return (
            "unknown",
            0.0,
            {}
        )


# =========================================================
# SOURCE ROUTING
# =========================================================

def source_for_intent(intent: str):

    if intent in {
        "school_policy",
        "announcement",
        "library",
    }:
        return "rag"

    if intent in {
        "marks",
        "attendance",
        "assignments",
        "timetable",
        "exams",
        "performance",
        "teacher",
        "profile",
        "fees",
    }:
        return "sql"

    return "unknown"


# =========================================================
# NORMALIZE LLM PLAN
# =========================================================

def normalize_llm_plan(plan: dict):

    if not isinstance(
        plan,
        dict
    ):
        plan = {}

    intent = str(
        plan.get(
            "intent",
            "unknown"
        )
        or "unknown"
    ).lower().strip()

    metric = str(
        plan.get(
            "metric",
            ""
        )
        or ""
    ).lower().strip()

    source = str(
        plan.get(
            "source",
            ""
        )
        or ""
    ).lower().strip()

    operation = str(
        plan.get(
            "operation",
            ""
        )
        or ""
    ).lower().strip()

    query_type = str(
        plan.get(
            "query_type",
            ""
        )
        or ""
    ).lower().strip()

    if intent not in VALID_INTENTS:
        intent = "unknown"

    if metric not in VALID_METRICS:
        metric = ""

    if source not in VALID_SOURCES:
        source = ""

    if operation not in VALID_OPERATIONS:
        operation = ""

    if query_type not in VALID_QUERY_TYPES:
        query_type = ""

    plan["intent"] = intent
    plan["metric"] = metric
    plan["source"] = source
    plan["operation"] = operation
    plan["query_type"] = query_type

    if not isinstance(
        plan.get("constraints"),
        dict
    ):
        plan["constraints"] = {}

    if not isinstance(
        plan.get("context"),
        dict
    ):
        plan["context"] = {}

    return plan


# =========================================================
# APPLY COMMON CONSTRAINTS
# =========================================================

def apply_common_constraints(
    plan: dict,
    q: str
):

    constraints = plan.setdefault(
        "constraints",
        {}
    )

    # =====================================================
    # MONTH + YEAR
    # =====================================================

    if plan.get("intent") == "attendance":

        month_info = extract_month_year(q)

        if (
            constraints.get("month") is None
            and month_info["month"] is not None
        ):

            constraints["month"] = (
                month_info["month"]
            )

        if (
            constraints.get("year") is None
            and month_info["year"] is not None
        ):

            constraints["year"] = (
                month_info["year"]
            )

    # =====================================================
    # TIMETABLE DAY
    # =====================================================

    if plan.get("intent") == "timetable":

        for day in WEEKDAYS:

            if re.search(
                rf"\b{day}\b",
                q
            ):

                constraints["day"] = day
                break

        if "today" in q:
            constraints["day"] = "today"

        elif "tomorrow" in q:
            constraints["day"] = "tomorrow"

        elif contains_any(
            q,
            [
                "next class",
                "next period",
                "next lecture",
            ]
        ):
            constraints["day"] = "next"

    # =====================================================
    # EXAM
    # =====================================================

    if plan.get("intent") in {
        "marks",
        "performance",
        "exams",
    }:

        exam_info = detect_exam_constraint(q)

        if exam_info["exam"]:

            constraints["exam"] = (
                exam_info["exam"]
            )

    plan["constraints"] = constraints

    return plan


# =========================================================
# MAIN VALIDATOR
# =========================================================

def validate_plan(
    plan: dict,
    question: str = ""
):

    original_q = (
        question
        or ""
    ).strip()

    q = normalize_for_routing(
        original_q
    )

    plan = normalize_llm_plan(
        plan
    )

    print(
        "\n========== QUERY ROUTING =========="
    )

    print(
        "Original:",
        original_q
    )

    print(
        "Normalized:",
        q
    )

    print(
        "LLM Intent:",
        plan.get("intent")
    )

    print(
        "LLM Metric:",
        plan.get("metric")
    )

    print(
        "===================================\n"
    )

    # =====================================================
    # 1. RAG
    # =====================================================

    rag_intent = detect_rag_intent(q)

    if rag_intent:

        return make_plan(
            rag_intent,
            source="rag",
            confidence=1.0,
            reasoning=(
                "Deterministic RAG guardrail detected "
                "a school policy, announcement, or library query."
            )
        )

    # =====================================================
    # 2. EXAM SCHEDULE
    # =====================================================

    if is_exam_schedule_query(q):

        exam_info = detect_exam_constraint(q)

        constraints = {}

        if exam_info["exam"]:

            constraints["exam"] = (
                exam_info["exam"]
            )

        return make_plan(
            "exams",
            source="sql",
            constraints=constraints,
            confidence=1.0,
            reasoning="Detected exam schedule query."
        )

    # =====================================================
    # 3. ATTENDANCE
    # =====================================================

    attendance_plan = detect_attendance_plan(q)

    if attendance_plan:

        return apply_common_constraints(
            attendance_plan,
            q
        )

    # =====================================================
    # 4. PERFORMANCE
    # =====================================================

    performance_plan = detect_performance_plan(q)

    if performance_plan:

        return apply_common_constraints(
            performance_plan,
            q
        )

    # =====================================================
    # 5. ASSIGNMENTS
    # =====================================================

    assignment_plan = detect_assignment_plan(q)

    if assignment_plan:

        assignment_plan = (
            apply_common_constraints(
                assignment_plan,
                q
            )
        )

        subject = detect_subject(q)

        if subject:

            assignment_plan.setdefault(
                "context",
                {}
            )["subject"] = normalize_subject(
                subject
            )

        return assignment_plan

    # =====================================================
    # 6. TIMETABLE
    # =====================================================

    timetable_plan = detect_timetable_plan(q)

    if timetable_plan:

        timetable_plan = (
            apply_common_constraints(
                timetable_plan,
                q
            )
        )

        subject = detect_subject(q)

        if subject:

            timetable_plan.setdefault(
                "context",
                {}
            )["subject"] = normalize_subject(
                subject
            )

        return timetable_plan

    # =====================================================
    # 7. TEACHER
    # =====================================================

    teacher_plan = detect_teacher_plan(q)

    if teacher_plan:

        return teacher_plan

    # =====================================================
    # 8. PROFILE
    # =====================================================

    profile_plan = detect_profile_plan(q)

    if profile_plan:

        return profile_plan

    # =====================================================
    # 9. FEES
    # =====================================================

    fee_plan = detect_fee_plan(q)

    if fee_plan:

        return fee_plan

    # =====================================================
    # 10. MARKS
    # =====================================================

    marks_plan = detect_marks_plan(q)

    if marks_plan:

        return apply_common_constraints(
            marks_plan,
            q
        )

    # =====================================================
    # 11. VALIDATED LLM PLAN
    # =====================================================

    llm_intent = plan.get(
        "intent",
        "unknown"
    )

    llm_metric = plan.get(
        "metric",
        ""
    )

    metric_aliases = {

        "highest":
            "highest_subject",

        "best":
            "highest_subject",

        "strongest":
            "highest_subject",

        "top":
            "highest_subject",

        "lowest":
            "lowest_subject",

        "weakest":
            "lowest_subject",

        "worst":
            "lowest_subject",

        "progress":
            "trend",

        "improvement":
            "trend",

        "performance_trend":
            "trend",

        "compare":
            "exam_comparison",

        "comparison":
            "exam_comparison",
    }

    if llm_metric in metric_aliases:

        llm_metric = metric_aliases[
            llm_metric
        ]

        plan["metric"] = llm_metric

    if (
        llm_intent in VALID_INTENTS
        and llm_intent != "unknown"
        and float(
            plan.get(
                "confidence",
                0
            )
            or 0
        ) >= 0.75
    ):

        plan["source"] = (
            source_for_intent(
                llm_intent
            )
        )

        if llm_intent == "performance":

            plan["query_type"] = (
                "comparison"
                if plan.get("metric")
                == "exam_comparison"
                else "analysis"
            )

            plan["operation"] = (
                "compare"
                if plan.get("metric")
                == "exam_comparison"
                else "analyze"
            )

            plan["analysis"] = True

        else:

            plan["query_type"] = (
                "information"
            )

            plan["operation"] = (
                "fetch"
            )

            plan["analysis"] = False

        plan = apply_common_constraints(
            plan,
            q
        )

        subject = detect_subject(q)

        if subject:

            plan.setdefault(
                "context",
                {}
            )["subject"] = normalize_subject(
                subject
            )

        return plan

    # =====================================================
    # 12. SEMANTIC ROUTER
    # =====================================================

    (
        semantic_intent,
        semantic_score,
        scores
    ) = semantic_route(q)

    if (
        semantic_intent in VALID_INTENTS
        and semantic_intent != "unknown"
        and semantic_score >= 0.55
    ):

        final_plan = make_plan(
            semantic_intent,
            query_type=(
                "analysis"
                if semantic_intent == "performance"
                else "information"
            ),
            operation=(
                "analyze"
                if semantic_intent == "performance"
                else "fetch"
            ),
            source=source_for_intent(
                semantic_intent
            ),
            confidence=semantic_score,
            analysis=(
                semantic_intent
                == "performance"
            ),
            reasoning=(
                "Semantic embedding routing was used "
                "after deterministic guardrails."
            )
        )

        if semantic_intent == "performance":

            metric_plan = (
                detect_performance_plan(q)
            )

            if metric_plan:

                final_plan.update(
                    metric_plan
                )

        subject = detect_subject(q)

        if subject:

            final_plan.setdefault(
                "context",
                {}
            )["subject"] = normalize_subject(
                subject
            )

        final_plan = apply_common_constraints(
            final_plan,
            q
        )

        return final_plan

    # =====================================================
    # 13. UNKNOWN
    # =====================================================

    return make_plan(
        "unknown",
        source="unknown",
        confidence=semantic_score,
        reasoning=(
            "No deterministic rule or sufficiently "
            "confident semantic route matched."
        )
    )


# =========================================================
# FALLBACK PLAN
# =========================================================

def build_fallback_plan(
    question: str
):

    print(
        "\nNo valid LLM plan found."
    )

    print(
        "Using deterministic + semantic fallback."
    )

    return validate_plan(
        {},
        question
    )