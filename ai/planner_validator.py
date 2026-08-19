"""
planner_validator.py

School Chatbot Query Planner + Validator

Architecture:

USER QUERY
    ↓
LLM PLANNER
    ↓
NORMALIZATION
    ↓
HIGH-CONFIDENCE DETERMINISTIC GUARDRAILS
    ↓
SEMANTIC EMBEDDING ROUTER
    ↓
FINAL VALIDATED PLAN

Design goals
------------
1. Do NOT hard-code every possible sentence.
2. Use synonym families and semantic routing.
3. Deterministic rules override bad embedding classifications.
4. Personal school-data questions -> SQL.
5. Policy / announcement / library / general knowledge -> RAG.
6. Hybrid is reserved for queries requiring both SQL + RAG.
7. Student-specific queries always remain SQL.
8. Detect:
   - marks
   - exams
   - attendance
   - assignments
   - timetable
   - performance
   - teacher
   - profile
   - RAG
9. Detect useful metrics and constraints.
10. Normalize common user language before routing.
"""

import re

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

VALID_METRICS = {
    "",

    # Performance
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

    # Attendance
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

    # Assignments
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


# =========================================================
# SUBJECT SYNONYMS
#
# These are semantic hints, NOT database values.
# The SQL generator handles actual subject matching.
# =========================================================

SUBJECT_SYNONYMS = {

    "mathematics": [
        "math",
        "maths",
        "mathematics",
        "math paper",
        "maths paper",
        "math subject",
        "mathematics subject",
    ],

    "science": [
        "science",
        "sci",
        "science paper",
        "science subject",
    ],

    "social science": [
        "social science",
        "social sciences",
        "social studies",
        "sst",
        "s.s.t",
        "social studies paper",
        "social science paper",
    ],

    "english": [
        "english",
        "english language",
        "english paper",
        "english subject",
    ],

    "hindi": [
        "hindi",
        "hindi language",
        "hindi paper",
        "hindi subject",
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
        "programming",
        "coding subject",
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

    "history": [
        "history",
        "history subject",
        "history paper",
    ],

    "geography": [
        "geography",
        "geo",
        "geography paper",
    ],

    "civics": [
        "civics",
        "civics paper",
    ],

    "economics": [
        "economics",
        "eco",
        "economics paper",
    ],
}


# =========================================================
# GENERAL SYNONYM NORMALIZATION
#
# Important:
# This does NOT need to cover every sentence.
# Embeddings handle unseen paraphrases.
# =========================================================

NORMALIZATION_RULES = {

    # -----------------------------------------------------
    # MARKS
    # -----------------------------------------------------

    "scores": " marks ",
    "score": " marks ",
    "scored": " marks ",
    "scoring": " marks ",
    "marks obtained": " marks ",
    "grades": " marks ",
    "grade": " marks ",
    "results": " marks ",
    "result": " marks ",
    "percentage": " marks ",
    "percent": " marks ",
    "points": " marks ",

    # -----------------------------------------------------
    # ASSIGNMENTS
    # -----------------------------------------------------

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
    "coursework": " assignment ",

    # -----------------------------------------------------
    # TIMETABLE
    # -----------------------------------------------------

    "time table": " timetable ",
    "class schedule": " timetable ",
    "class schedules": " timetable ",
    "school schedule": " timetable ",
    "school schedules": " timetable ",
    "daily schedule": " timetable ",
    "daily routine": " timetable ",
    "period schedule": " timetable ",
    "period schedules": " timetable ",
    "lecture schedule": " timetable ",
    "class timings": " timetable ",
    "class timing": " timetable ",

    # -----------------------------------------------------
    # ATTENDANCE
    # -----------------------------------------------------

    "presence rate": " attendance ",
    "present rate": " attendance ",
    "attendance rate": " attendance ",
    "absenteeism": " absence ",
    "missed classes": " absent ",
    "missed class": " absent ",
    "missed school": " absent ",
    "miss school": " absent ",

    # -----------------------------------------------------
    # EXAMS
    # -----------------------------------------------------

    "mid-term": " midterm ",
    "mid term": " midterm ",
    "midterm exam": " midterm ",
    "midterm examination": " midterm ",

    "final examination": " final exam ",
    "finals": " final exam ",
    "annual examination": " annual exam ",
    "annuals": " annual exam ",

    "half-yearly": " half yearly exam ",
    "half yearly examination": " half yearly exam ",

    # -----------------------------------------------------
    # INFORMAL LANGUAGE
    # -----------------------------------------------------

    "pls": " please ",
    "plz": " please ",
    "ur": " your ",
    "u": " you ",
}


# =========================================================
# PERFORMANCE SYNONYMS
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
        "top scoring subject",
        "highest subject",
        "highest scoring subject",
        "subject with highest marks",
        "subject with highest score",
        "subject with best marks",
        "subject with best score",
        "subject where i scored highest",
        "subject where i got highest",
        "subject where i perform best",
        "subject i am best at",
        "which subject is best",
        "which subject is my best",
        "which subject am i best at",
        "which subject is strongest",
        "which subject am i strongest in",
        "where am i strongest",
        "what am i strongest in",
        "my strongest subject",
        "my best subject",
        "my highest scoring subject",
        "my highest marks subject",
        "highest score",
        "highest marks",
        "top score",
        "best score",
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
        "lowest performing subject",
        "subject with lowest marks",
        "subject with lowest score",
        "subject with worst marks",
        "subject with worst score",
        "subject where i scored lowest",
        "subject where i got lowest",
        "subject where i perform worst",
        "subject i am weak in",
        "which subject needs improvement",
        "which subject should i improve",
        "where am i weakest",
        "what am i weakest in",
        "my weakest subject",
        "my worst subject",
        "my lowest scoring subject",
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
        "growth in marks",
        "growth in performance",
        "progressing",
    ],

    "exam_comparison": [
        "compare exams",
        "compare examination",
        "compare examinations",
        "compare my exams",
        "compare my marks",
        "compare my scores",
        "compare my results",
        "exam comparison",
        "difference between exams",
        "difference between examinations",
        "mid term vs final",
        "midterm vs final",
        "final vs mid term",
        "final compared to mid term",
        "compare performance",
        "compare my performance",
        "how did i improve",
        "how much did i improve",
    ],

    "overall_performance": [
        "overall performance",
        "overall marks",
        "overall score",
        "overall result",
        "overall percentage",
        "total performance",
        "academic performance",
        "how am i performing",
        "how am i doing academically",
    ],
}


# =========================================================
# ATTENDANCE SYNONYMS
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
    "missing school",
    "missed school",
    "miss school",
    "missed class",
    "miss class",
    "late",
    "lateness",
    "late attendance",
]


# =========================================================
# ASSIGNMENT SYNONYMS
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
    "work to do",
    "work pending",
]


# =========================================================
# TIMETABLE SYNONYMS
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
    "lecture",
    "lectures",
    "next class",
    "next lecture",
    "today's classes",
    "tomorrow's classes",
    "what class do i have",
    "which class do i have",
    "when is my class",
]


# =========================================================
# EXAM SYNONYMS
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
# RAG KEYWORDS
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
    "requirement",
    "requirements",
    "allowed",
    "not allowed",
    "permission",
    "school policy",
    "school rule",
    "school rules",
    "attendance requirement",
    "attendance criteria",
    "minimum attendance",
    "eligibility criteria",
]


RAG_LIBRARY_WORDS = [
    "library",
    "library rules",
    "library policy",
    "library fine",
    "library fines",
    "book fine",
    "book return policy",
    "borrow book",
    "borrow a book",
    "borrow books",
    "library membership",
    "library timing",
]


RAG_FEE_WORDS = [
    "fee policy",
    "fees policy",
    "school fees",
    "fee structure",
    "fees structure",
    "refund policy",
    "fee refund",
    "payment policy",
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
    "news from school",
]


# =========================================================
# HELPERS
# =========================================================

def contains_any(text: str, phrases) -> bool:

    if not text:
        return False

    text = text.lower()

    for phrase in phrases:

        phrase = phrase.lower().strip()

        if not phrase:
            continue

        if phrase in text:
            return True

    return False


def regex_any(text: str, patterns) -> bool:

    if not text:
        return False

    for pattern in patterns:

        if re.search(
            pattern,
            text,
            re.IGNORECASE
        ):
            return True

    return False


def normalize_for_routing(question: str) -> str:
    """
    Normalize only for routing.

    Original question is NEVER modified for SQL generation.
    """

    q = (
        question
        or ""
    ).lower().strip()

    # Normalize punctuation first.
    q = q.replace(
        "’",
        "'"
    )

    q = re.sub(
        r"[!?.,;:]+",
        " ",
        q
    )

    # Longer phrases first.
    rules = sorted(
        NORMALIZATION_RULES.items(),
        key=lambda item: len(item[0]),
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
                q
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

    return candidates[0][1]


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
        r"\bhalf yearly exam\b",
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
# RAG DETECTION
# =========================================================

def detect_rag_intent(q: str):

    # -----------------------------------------------------
    # Library
    # -----------------------------------------------------

    if contains_any(
        q,
        RAG_LIBRARY_WORDS
    ):

        return "library"

    # -----------------------------------------------------
    # Fees
    # -----------------------------------------------------

    if contains_any(
        q,
        RAG_FEE_WORDS
    ):

        return "fees"

    # -----------------------------------------------------
    # Announcements
    # -----------------------------------------------------

    if contains_any(
        q,
        RAG_ANNOUNCEMENT_WORDS
    ):

        return "announcement"

    # -----------------------------------------------------
    # Policy
    # -----------------------------------------------------

    if contains_any(
        q,
        RAG_POLICY_WORDS
    ):

        # Personal attendance calculation
        # should remain SQL.

        personal_attendance = (
            contains_any(
                q,
                [
                    "my attendance",
                    "my absence",
                    "my absences",
                    "my present days",
                    "my absent days",
                ]
            )
        )

        if not personal_attendance:
            return "school_policy"

    return None


# =========================================================
# EXAM SCHEDULE DETECTION
# =========================================================

def is_exam_schedule_query(q: str) -> bool:

    if not contains_any(
        q,
        EXAM_WORDS
    ):
        return False

    schedule_words = [
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
        "timetable",
        "when is",
        "when are",
    ]

    # If asking marks, it is not a schedule query.
    marks_words = [
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

    if contains_any(
        q,
        marks_words
    ):
        return False

    return contains_any(
        q,
        schedule_words
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

    # -----------------------------------------------------
    # TREND
    # -----------------------------------------------------

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
        ]
    ):

        return make_plan(
            "attendance",
            query_type="analysis",
            operation="analyze",
            metric="attendance_trend",
            analysis=True,
            confidence=1.0,
            reasoning="Detected attendance trend query."
        )

    # -----------------------------------------------------
    # ELIGIBILITY
    # -----------------------------------------------------

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
            analysis=True,
            confidence=1.0,
            reasoning="Detected attendance eligibility query."
        )

    # -----------------------------------------------------
    # ABSENT DATES
    # -----------------------------------------------------

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
            r"\bwhich days was i absent\b",
        ]
    ):

        return make_plan(
            "attendance",
            metric="absent_dates",
            constraints={
                "attendance": "absent"
            },
            confidence=1.0,
            reasoning="Detected absent-date query."
        )

    # -----------------------------------------------------
    # PRESENT DATES
    # -----------------------------------------------------

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

        return make_plan(
            "attendance",
            metric="present_dates",
            constraints={
                "attendance": "present"
            },
            confidence=1.0,
            reasoning="Detected present-date query."
        )

    # -----------------------------------------------------
    # ABSENT COUNT
    # -----------------------------------------------------

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
        ]
    ):

        return make_plan(
            "attendance",
            query_type="analysis",
            operation="analyze",
            metric="absent_days",
            analysis=True,
            confidence=1.0,
            reasoning="Detected absence-count query."
        )

    # -----------------------------------------------------
    # PRESENT COUNT
    # -----------------------------------------------------

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
        ]
    ):

        return make_plan(
            "attendance",
            query_type="analysis",
            operation="analyze",
            metric="present_days",
            analysis=True,
            confidence=1.0,
            reasoning="Detected present-day count query."
        )

    # -----------------------------------------------------
    # PERCENTAGE
    # -----------------------------------------------------

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
            analysis=True,
            confidence=1.0,
            reasoning="Detected attendance-percentage query."
        )

    # -----------------------------------------------------
    # SUMMARY
    # -----------------------------------------------------

    if contains_any(
        q,
        [
            "attendance summary",
            "attendance report",
            "attendance record",
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
            analysis=True,
            confidence=1.0,
            reasoning="Detected attendance-summary query."
        )

    # -----------------------------------------------------
    # COMPARISON
    # -----------------------------------------------------

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
            analysis=True,
            comparison=True,
            confidence=1.0,
            reasoning="Detected attendance comparison."
        )

    # -----------------------------------------------------
    # LATE
    # -----------------------------------------------------

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

        return make_plan(
            "attendance",
            metric="late_days",
            constraints={
                "attendance": "late"
            },
            confidence=1.0,
            reasoning="Detected late-attendance query."
        )

    # -----------------------------------------------------
    # GENERAL ATTENDANCE
    # -----------------------------------------------------

    return make_plan(
        "attendance",
        confidence=0.95,
        reasoning="Detected general attendance query."
    )


# =========================================================
# PERFORMANCE DETECTION
# =========================================================

def detect_performance_plan(q: str):

    # -----------------------------------------------------
    # HIGHEST SUBJECT
    # -----------------------------------------------------

    if contains_any(
        q,
        PERFORMANCE_PATTERNS["highest_subject"]
    ):

        # A specific-subject question such as:
        #
        # "What score did I get in Computer Science?"
        #
        # should remain a marks query.

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

    # -----------------------------------------------------
    # LOWEST SUBJECT
    # -----------------------------------------------------

    if contains_any(
        q,
        PERFORMANCE_PATTERNS["lowest_subject"]
    ):

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
                ]
            )
        )

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

    # -----------------------------------------------------
    # OVERALL PERFORMANCE
    # -----------------------------------------------------

    if contains_any(
        q,
        PERFORMANCE_PATTERNS["overall_performance"]
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

    # -----------------------------------------------------
    # EXAM COMPARISON
    # -----------------------------------------------------

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
        "better",
        "change",
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
            constraints["exam"] = exam_info["exam"]

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

    # -----------------------------------------------------
    # PERFORMANCE TREND
    # -----------------------------------------------------

    if contains_any(
        q,
        PERFORMANCE_PATTERNS["trend"]
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

    # -----------------------------------------------------
    # OVERDUE
    # -----------------------------------------------------

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
            "missed deadlines",
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

    # -----------------------------------------------------
    # TODAY
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # TOMORROW
    # -----------------------------------------------------

    if contains_any(
        q,
        [
            "due tomorrow",
            "tomorrow's assignment",
            "assignments tomorrow",
            "homework tomorrow",
            "task tomorrow",
            "work due tomorrow",
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

    # -----------------------------------------------------
    # UPCOMING / PENDING
    # -----------------------------------------------------

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
            "work i need to complete",
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
            reasoning="Detected upcoming/pending assignment query."
        )

    # -----------------------------------------------------
    # COMPLETED
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # DEFAULT
    # -----------------------------------------------------

    return make_plan(
        "assignments",
        metric="assignment_summary",
        confidence=0.95,
        reasoning="Detected assignment/homework query."
    )


# =========================================================
# TIMETABLE DETECTION
# =========================================================

def detect_timetable_plan(q: str):

    if not contains_any(
        q,
        TIMETABLE_WORDS
    ):
        return None

    # Exam schedule must go to exams.
    if is_exam_schedule_query(q):
        return None

    constraints = {}

    # -----------------------------------------------------
    # DAY
    # -----------------------------------------------------

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
        reasoning="Detected timetable/class-schedule query."
    )


# =========================================================
# MARKS DETECTION
# =========================================================

# =========================================================
# MARKS DETECTION
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

    if not contains_any(q, marks_words):
        return None

    # -----------------------------------------------------
    # Do not steal performance queries
    # -----------------------------------------------------

    performance_plan = detect_performance_plan(q)

    if performance_plan:
        return performance_plan

    # -----------------------------------------------------
    # DETECT SUBJECT
    # -----------------------------------------------------

    subject = detect_subject(q)

    # -----------------------------------------------------
    # DETECT EXAM
    # -----------------------------------------------------

    exam_info = detect_exam_constraint(q)

    # -----------------------------------------------------
    # BUILD CONSTRAINTS
    # -----------------------------------------------------

    constraints = {}

    if subject:
        constraints["subject"] = subject

    if exam_info.get("exam"):
        constraints["exam"] = exam_info["exam"]

    # -----------------------------------------------------
    # CONTEXT
    # -----------------------------------------------------

    context = {}

    if subject:
        context["subject"] = subject

    # -----------------------------------------------------
    # FINAL PLAN
    # -----------------------------------------------------

    return make_plan(
        "marks",
        constraints=constraints,
        context=context,
        confidence=1.0,
        reasoning="Detected marks/score/result query."
    )

# =========================================================
# TEACHER DETECTION
# =========================================================

def detect_teacher_plan(q: str):

    teacher_words = [
        "teacher",
        "teachers",
        "who teaches",
        "who is my teacher",
        "who teaches me",
        "subject teacher",
        "subject instructor",
        "instructor",
        "faculty",
        "sir",
        "madam",
        "ma'am",
    ]

    if not contains_any(
        q,
        teacher_words
    ):
        return None

    context = {}

    subject = detect_subject(q)

    if subject:
        context["subject"] = subject

    return make_plan(
        "teacher",
        context=context,
        confidence=1.0,
        reasoning="Detected teacher/faculty query."
    )


# =========================================================
# PROFILE DETECTION
# =========================================================

def detect_profile_plan(q: str):

    profile_words = [
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
        "my admission",
        "my personal details",
    ]

    if not contains_any(
        q,
        profile_words
    ):
        return None

    return make_plan(
        "profile",
        confidence=1.0,
        reasoning="Detected student-profile query."
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
        "fees",
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
    }:
        return "sql"

    return "unknown"


# =========================================================
# NORMALIZE EXISTING LLM PLAN
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

    # -----------------------------------------------------
    # MONTH
    # -----------------------------------------------------

    for month, number in MONTH_MAP.items():

        if re.search(
            rf"\b{month}\b",
            q
        ):

            constraints["month"] = number
            break

    # -----------------------------------------------------
    # WEEKDAY
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # EXAM
    # -----------------------------------------------------

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
    """
    Final query router.

    Priority:

    1. RAG-specific deterministic rules
    2. Exam schedule
    3. Attendance
    4. Performance
    5. Assignments
    6. Timetable
    7. Teacher
    8. Profile
    9. Marks
    10. LLM plan
    11. Embedding router
    12. Unknown

    This prevents embeddings from incorrectly changing
    high-confidence deterministic classifications.
    """

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

        final_plan = make_plan(
            rag_intent,
            source="rag",
            confidence=1.0,
            reasoning=(
                "Deterministic RAG guardrail detected "
                "a policy, announcement, fee, or "
                "library query."
            )
        )

        print(
            "\n===== FINAL PLAN ====="
        )

        print(
            final_plan
        )

        return final_plan

    # =====================================================
    # 2. EXAM SCHEDULE
    # =====================================================

    if is_exam_schedule_query(q):

        exam_info = detect_exam_constraint(
            q
        )

        constraints = {}

        if exam_info["exam"]:
            constraints["exam"] = (
                exam_info["exam"]
            )

        final_plan = make_plan(
            "exams",
            source="sql",
            constraints=constraints,
            confidence=1.0,
            reasoning=(
                "Detected exam schedule/date/timing "
                "query."
            )
        )

        return final_plan

    # =====================================================
    # 3. ATTENDANCE
    # =====================================================

    attendance_plan = detect_attendance_plan(
        q
    )

    if attendance_plan:

        attendance_plan = apply_common_constraints(
            attendance_plan,
            q
        )

        return attendance_plan

    # =====================================================
    # 4. PERFORMANCE
    # =====================================================

    performance_plan = detect_performance_plan(
        q
    )

    if performance_plan:

        performance_plan = apply_common_constraints(
            performance_plan,
            q
        )

        return performance_plan

    # =====================================================
    # 5. ASSIGNMENTS
    # =====================================================

    assignment_plan = detect_assignment_plan(
        q
    )

    if assignment_plan:

        assignment_plan = apply_common_constraints(
            assignment_plan,
            q
        )

        # Preserve subject information.
        subject = detect_subject(q)

        if subject:

            assignment_plan.setdefault(
                "context",
                {}
            )["subject"] = subject

        return assignment_plan

    # =====================================================
    # 6. TIMETABLE
    # =====================================================

    timetable_plan = detect_timetable_plan(
        q
    )

    if timetable_plan:

        timetable_plan = apply_common_constraints(
            timetable_plan,
            q
        )

        subject = detect_subject(q)

        if subject:

            timetable_plan.setdefault(
                "context",
                {}
            )["subject"] = subject

        return timetable_plan

    # =====================================================
    # 7. TEACHER
    # =====================================================

    teacher_plan = detect_teacher_plan(
        q
    )

    if teacher_plan:

        return teacher_plan

    # =====================================================
    # 8. PROFILE
    # =====================================================

    profile_plan = detect_profile_plan(
        q
    )

    if profile_plan:

        return profile_plan

    # =====================================================
    # 9. MARKS
    # =====================================================

    marks_plan = detect_marks_plan(
        q
    )

    if marks_plan:

        marks_plan = apply_common_constraints(
            marks_plan,
            q
        )

        return marks_plan

    # =====================================================
    # 10. LLM PLAN
    # =====================================================

    llm_intent = plan.get(
        "intent",
        "unknown"
    )

    llm_metric = plan.get(
        "metric",
        ""
    )

    # -----------------------------------------------------
    # Normalize common LLM metric mistakes
    # -----------------------------------------------------

    metric_aliases = {

        "highest": "highest_subject",
        "highest_score": "highest_subject",
        "highest_marks": "highest_subject",
        "best": "highest_subject",
        "strongest": "highest_subject",
        "top": "highest_subject",

        "lowest": "lowest_subject",
        "lowest_score": "lowest_subject",
        "lowest_marks": "lowest_subject",
        "weakest": "lowest_subject",
        "worst": "lowest_subject",

        "progress": "trend",
        "improvement": "trend",
        "performance_trend": "trend",

        "compare": "exam_comparison",
        "comparison": "exam_comparison",
    }

    if llm_metric in metric_aliases:

        llm_metric = metric_aliases[
            llm_metric
        ]

        plan["metric"] = llm_metric

    # -----------------------------------------------------
    # If LLM already gave a valid high-confidence plan,
    # retain it ONLY if deterministic routing found nothing.
    # -----------------------------------------------------

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

        # Source must match the actual intent.
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

        # Add subject context when available.
        subject = detect_subject(q)

        if subject:

            plan.setdefault(
                "context",
                {}
            )["subject"] = subject

        print(
            "\n===== USING VALIDATED LLM PLAN ====="
        )

        print(
            plan
        )

        return plan

    # =====================================================
    # 11. SEMANTIC EMBEDDING ROUTER
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

        intent = semantic_intent

        source = source_for_intent(
            intent
        )

        final_plan = make_plan(
            intent,
            query_type=(
                "analysis"
                if intent == "performance"
                else "information"
            ),
            operation=(
                "analyze"
                if intent == "performance"
                else "fetch"
            ),
            source=source,
            confidence=semantic_score,
            analysis=(
                intent == "performance"
            ),
            reasoning=(
                "Semantic embedding routing was used "
                "after deterministic guardrails."
            )
        )

        # -------------------------------------------------
        # Semantic performance correction
        # -------------------------------------------------

        if intent == "performance":

            # Re-run deterministic metric detection.
            metric_plan = detect_performance_plan(
                q
            )

            if metric_plan:

                final_plan.update(
                    metric_plan
                )

        # -------------------------------------------------
        # Subject
        # -------------------------------------------------

        subject = detect_subject(q)

        if subject:

            final_plan.setdefault(
                "context",
                {}
            )["subject"] = subject

        # -------------------------------------------------
        # Constraints
        # -------------------------------------------------

        final_plan = apply_common_constraints(
            final_plan,
            q
        )

        return final_plan

    # =====================================================
    # 12. UNKNOWN
    # =====================================================

    unknown_plan = make_plan(
        "unknown",
        source="unknown",
        confidence=semantic_score,
        reasoning=(
            "No deterministic rule or sufficiently "
            "confident semantic route matched."
        )
    )

    print(
        "\n===== UNKNOWN PLAN ====="
    )

    print(
        unknown_plan
    )

    return unknown_plan


# =========================================================
# FALLBACK PLAN
# =========================================================

def build_fallback_plan(
    question: str
):
    """
    Used when the LLM planner completely fails.

    This intentionally uses the same deterministic
    validator instead of maintaining another separate
    set of routing rules.
    """

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