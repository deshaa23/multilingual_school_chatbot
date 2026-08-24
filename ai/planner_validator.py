"""
planner_validator.py

Deterministic validator and fallback planner for School Chatbot.

Main goals:
1. Protect correct planner intent from semantic/BGE mistakes.
2. Detect attendance queries deterministically.
3. Detect assignment queries deterministically.
4. Detect assignment subject/title/scope.
5. Detect performance queries deterministically.
6. Detect marks, timetable, teacher and profile queries.
7. Detect month/year/day/exam constraints.
8. Normalize invalid planner output.
9. Keep the output compatible with sql_generator.py and analyzer.py.
10. Make natural-language queries work reliably.
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
    "teacher",
    "profile",
    "fees",
    "performance",
    "school_policy",
    "announcement",
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

    # -----------------------------------------------------
    # PERFORMANCE
    # -----------------------------------------------------

    "trend",
    "highest_score",
    "lowest_score",
    "highest_subject",
    "lowest_subject",
    "exam_comparison",
    "overall_performance",
    "subject_performance",
    "recommendation",
    "best_exam",
    "worst_exam",
    "performance_report",

    # -----------------------------------------------------
    # ASSIGNMENTS
    # -----------------------------------------------------

    "assignment_list",
    "pending_assignments",
    "completed_assignments",
    "overdue_assignments",
    "assignment_due",

    # -----------------------------------------------------
    # ATTENDANCE
    # -----------------------------------------------------

    "monthly_attendance",
    "attendance_trend",
    "attendance_summary",
    "attendance_percentage",
    "attendance_eligibility",

    "absent_days",
    "absent_dates",
    "when_absent",

    "present_days",
    "present_dates",

    "late_days",
    "late_dates",

    "attendance_comparison",

    "subject_attendance",
    "attendance_by_subject",
}


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
# GENERAL HELPERS
# =========================================================

def contains_any(
    question: str,
    phrases: list[str]
) -> bool:

    if not question:
        return False

    return any(
        phrase in question
        for phrase in phrases
    )


def normalize_question(
    question: str
) -> str:

    if not question:
        return ""

    q = str(question).lower().strip()

    q = re.sub(
        r"\s+",
        " ",
        q
    )

    return q


def safe_dict(value):

    if isinstance(value, dict):
        return value

    return {}


def make_plan(
    intent,
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

def detect_subject(
    question: str
):

    q = normalize_question(question)

    if not q:
        return None

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
# ASSIGNMENT SUBJECT DETECTION
# =========================================================

def detect_assignment_subject(
    question: str
):

    return detect_subject(question)


# =========================================================
# ASSIGNMENT TITLE DETECTION
# =========================================================

def extract_assignment_title(
    question: str
):
    """
    Examples:

    What is due date for Python Basics assignment?
        -> Python Basics

    What is the due date of Python Basics assignment?
        -> Python Basics

    When is Python Basics assignment due?
        -> Python Basics

    Tell me about Python Basics assignment
        -> Python Basics

    What is my chemistry assignment?
        -> chemistry assignment
    """

    q = normalize_question(question)

    if not q:
        return None

    q = re.sub(
        r"[?!.]+$",
        "",
        q
    ).strip()

    patterns = [

        # due date for Python Basics assignment
        r"due\s+date\s+(?:for|of)\s+(.+?)\s+assignment\b",

        # what is the due date for Python Basics assignment
        r"what\s+is\s+(?:the\s+)?due\s+date\s+(?:for|of)\s+(.+?)\s+assignment\b",

        # when is Python Basics assignment due
        r"when\s+is\s+(.+?)\s+assignment\s+due\b",

        # when will Python Basics assignment be due
        r"when\s+will\s+(.+?)\s+assignment\s+be\s+due\b",

        # tell me about Python Basics assignment
        r"tell\s+me\s+about\s+(.+?)\s+assignment\b",

        # show Python Basics assignment
        r"(?:show|find|get)\s+(?:my\s+)?(.+?)\s+assignment\b",

        # details of Python Basics assignment
        r"(?:details|information|info)\s+(?:about|for|of)\s+(.+?)\s+assignment\b",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            q,
            re.IGNORECASE
        )

        if not match:
            continue

        title = match.group(1).strip()

        title = re.sub(
            r"^(my|the)\s+",
            "",
            title,
            flags=re.IGNORECASE
        ).strip()

        if not title:
            return None

        # If title is only a subject, do not treat it
        # as assignment title.
        canonical_subject = detect_subject(title)

        if canonical_subject:
            normalized_title = re.sub(
                r"\s+",
                " ",
                title.lower()
            )

            subject_aliases = [
                alias
                for alias, canonical
                in SUBJECT_ALIASES.items()
                if canonical == canonical_subject
            ]

            if normalized_title in subject_aliases:
                return None

        return title

    return None


# =========================================================
# ASSIGNMENT SCOPE
# =========================================================

def detect_assignment_scope(
    question: str
):
    """
    Detect assignment date scope.

    Returns:

        overdue
        today
        tomorrow
        upcoming
        None
    """

    q = normalize_question(question)

    if not q:
        return None

    # -----------------------------------------------------
    # OVERDUE
    # -----------------------------------------------------

    overdue_phrases = [
        "overdue assignment",
        "overdue assignments",
        "overdue homework",
        "late assignment",
        "late assignments",
        "missed assignment deadline",
        "missed assignment deadlines",
        "assignments past due",
        "assignments that are overdue",
    ]

    if contains_any(
        q,
        overdue_phrases
    ):
        return "overdue"

    # -----------------------------------------------------
    # TODAY
    # -----------------------------------------------------

    today_phrases = [
        "assignment due today",
        "assignments due today",
        "what is due today",
        "what are due today",
        "due today",
        "today's assignment",
        "todays assignment",
        "today assignments",
    ]

    if contains_any(
        q,
        today_phrases
    ):
        return "today"

    # -----------------------------------------------------
    # TOMORROW
    # -----------------------------------------------------

    tomorrow_phrases = [
        "assignment due tomorrow",
        "assignments due tomorrow",
        "what is due tomorrow",
        "what are due tomorrow",
        "due tomorrow",
        "tomorrow's assignment",
        "tomorrows assignment",
        "tomorrow assignments",
    ]

    if contains_any(
        q,
        tomorrow_phrases
    ):
        return "tomorrow"

    # -----------------------------------------------------
    # UPCOMING
    # -----------------------------------------------------

    upcoming_phrases = [
        "upcoming assignments",
        "upcoming assignment",
        "future assignments",
        "future assignment",
        "next assignments",
        "next assignment",
        "assignments coming up",
        "assignment coming up",
        "what assignments are coming",
        "what is coming up",
    ]

    if contains_any(
        q,
        upcoming_phrases
    ):
        return "upcoming"

    return None


# =========================================================
# ASSIGNMENT PHRASES
# =========================================================

ASSIGNMENT_GENERAL_PHRASES = [
    "assignment",
    "assignments",
    "homework",
    "homeworks",
    "home work",
]


ASSIGNMENT_PENDING_PHRASES = [
    "pending assignment",
    "pending assignments",
    "pending homework",
    "incomplete assignment",
    "incomplete assignments",
    "unfinished assignment",
    "unfinished assignments",
    "assignments i need to complete",
    "assignments to complete",
]


ASSIGNMENT_COMPLETED_PHRASES = [
    "completed assignment",
    "completed assignments",
    "finished assignment",
    "finished assignments",
    "submitted assignment",
    "submitted assignments",
]


ASSIGNMENT_OVERDUE_PHRASES = [
    "overdue assignment",
    "overdue assignments",
    "overdue homework",
    "late assignment",
    "late assignments",
    "missed assignment deadline",
    "missed assignment deadlines",
    "assignments past due",
]


ASSIGNMENT_DUE_PHRASES = [
    "due date",
    "due dates",
    "deadline",
    "deadlines",
    "when is my assignment due",
    "when are my assignments due",
    "when is the assignment due",
    "when are the assignments due",
    "when is my homework due",
    "when are my homework due",
]


# =========================================================
# ATTENDANCE PHRASES
# =========================================================

ABSENT_PHRASES = [
    "when was i absent",
    "when were i absent",
    "which days was i absent",
    "which day was i absent",
    "what days was i absent",
    "what day was i absent",
    "dates i was absent",
    "date i was absent",
    "days i was absent",
    "day i was absent",
    "my absent dates",
    "my absence dates",
    "my absent days",
    "my absence days",
    "when did i miss school",
    "when did i miss class",
    "when did i miss",
    "which days did i miss school",
    "which days did i miss",
    "which day did i miss",
    "days did i miss",
    "days i missed",
    "show my absent dates",
    "show me my absent dates",
    "show my absences",
]


PRESENT_PHRASES = [
    "when was i present",
    "which days was i present",
    "which day was i present",
    "what days was i present",
    "what day was i present",
    "dates i was present",
    "date i was present",
    "days i was present",
    "present dates",
    "show my present dates",
    "show me my present dates",
]


ATTENDANCE_GENERAL_PHRASES = [
    "attendance",
    "attendance record",
    "attendance records",
    "present",
    "absent",
    "absence",
    "absences",
    "missed school",
    "miss school",
    "missed class",
    "miss class",
]


# =========================================================
# ATTENDANCE DETECTION
# =========================================================

def detect_attendance_plan(
    question: str
):

    q = normalize_question(question)

    if not q:
        return None

    # -----------------------------------------------------
    # ABSENT DATES
    # -----------------------------------------------------

    if contains_any(
        q,
        ABSENT_PHRASES
    ):

        return make_plan(
            intent="attendance",
            query_type="information",
            operation="fetch",
            source="sql",
            constraints={
                "attendance": "missing"
            },
            metric="absent_dates",
            confidence=1.0,
            reasoning=(
                "The user wants to know the dates "
                "on which they were absent."
            ),
        )

    # -----------------------------------------------------
    # PRESENT DATES
    # -----------------------------------------------------

    if contains_any(
        q,
        PRESENT_PHRASES
    ):

        return make_plan(
            intent="attendance",
            query_type="information",
            operation="fetch",
            source="sql",
            constraints={
                "attendance": "present"
            },
            metric="present_dates",
            confidence=1.0,
            reasoning=(
                "The user wants to know the dates "
                "on which they were present."
            ),
        )

    # -----------------------------------------------------
    # LATE DATES
    # -----------------------------------------------------

    late_date_phrases = [
        "when was i late",
        "which days was i late",
        "what days was i late",
        "days i was late",
        "dates i was late",
        "late dates",
        "show my late dates",
    ]

    if contains_any(
        q,
        late_date_phrases
    ):

        return make_plan(
            intent="attendance",
            query_type="information",
            operation="fetch",
            source="sql",
            constraints={
                "attendance": "late"
            },
            metric="late_dates",
            confidence=1.0,
            reasoning=(
                "The user wants to know the dates "
                "on which they were late."
            ),
        )

    # -----------------------------------------------------
    # ABSENCE COUNT
    # -----------------------------------------------------

    absence_count_phrases = [
        "how many days was i absent",
        "how many days have i been absent",
        "number of absences",
        "how many absences",
        "how many days absent",
        "count my absences",
        "total absences",
        "number of days absent",
    ]

    if contains_any(
        q,
        absence_count_phrases
    ):

        return make_plan(
            intent="attendance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            constraints={
                "attendance": "missing"
            },
            metric="absent_days",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants the number of days "
                "they were absent."
            ),
        )

    # -----------------------------------------------------
    # PRESENT COUNT
    # -----------------------------------------------------

    present_count_phrases = [
        "how many days was i present",
        "how many days have i attended",
        "how many days did i attend",
        "number of present days",
        "number of days present",
        "count my present days",
        "total present days",
    ]

    if contains_any(
        q,
        present_count_phrases
    ):

        return make_plan(
            intent="attendance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            constraints={
                "attendance": "present"
            },
            metric="present_days",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants the number of days "
                "they were present."
            ),
        )

    # -----------------------------------------------------
    # LATE COUNT
    # -----------------------------------------------------

    late_count_phrases = [
        "how many days was i late",
        "how many times was i late",
        "number of late days",
        "number of days late",
        "count my late days",
        "total late days",
    ]

    if contains_any(
        q,
        late_count_phrases
    ):

        return make_plan(
            intent="attendance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            constraints={
                "attendance": "late"
            },
            metric="late_days",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants the number of days "
                "they were late."
            ),
        )

    # -----------------------------------------------------
    # ATTENDANCE PERCENTAGE
    # -----------------------------------------------------

    percentage_phrases = [
        "attendance percentage",
        "attendance percent",
        "what percentage of attendance",
        "what is my attendance",
        "my attendance rate",
        "attendance rate",
        "how much attendance do i have",
        "how much attendance have i got",
    ]

    if contains_any(
        q,
        percentage_phrases
    ):

        return make_plan(
            intent="attendance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="attendance_percentage",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants to know "
                "their attendance percentage."
            ),
        )

    # -----------------------------------------------------
    # ATTENDANCE ELIGIBILITY
    # -----------------------------------------------------

    eligibility_phrases = [
        "eligible with my attendance",
        "am i eligible",
        "do i have enough attendance",
        "is my attendance enough",
        "75% attendance",
        "75 percent attendance",
        "attendance requirement",
        "eligible for exam",
        "eligible to sit",
    ]

    if contains_any(
        q,
        eligibility_phrases
    ):

        return make_plan(
            intent="attendance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="attendance_eligibility",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants to check "
                "attendance eligibility."
            ),
        )

    # -----------------------------------------------------
    # ATTENDANCE COMPARISON
    # -----------------------------------------------------

    comparison_phrases = [
        "compare my attendance",
        "compare attendance",
        "attendance comparison",
        "attendance compared",
        "compare this month with last month",
        "compare last month",
        "compared with last month",
        "compared to last month",
    ]

    if contains_any(
        q,
        comparison_phrases
    ):

        return make_plan(
            intent="attendance",
            query_type="comparison",
            operation="analyze",
            source="sql",
            metric="attendance_comparison",
            analysis=True,
            comparison=True,
            confidence=1.0,
            reasoning=(
                "The user wants to compare attendance."
            ),
        )
        
    # =========================================================
    # ATTENDANCE VALIDATION
    # =========================================================

    q_lower = question.lower().strip()

    # ---------------------------------------------------------
    # POLICY / GENERAL KNOWLEDGE MUST STAY RAG
    # ---------------------------------------------------------

    policy_keywords = [
        "policy",
        "rule",
        "rules",
        "required",
        "requirement",
        "minimum",
        "school policy",
        "school rule",
        "guideline",
        "guidelines",
        "what does the school say",
        "what is the school",
    ]

    is_attendance_policy = (
        "attendance" in q_lower
        and any(keyword in q_lower for keyword in policy_keywords)
    )

    if is_attendance_policy:

        plan = {
            "intent": "rag",
            "query_type": "information",
            "operation": "fetch",
            "source": "rag",
            "constraints": {},
            "context": {},
            "metric": "none",
            "analysis": False,
            "comparison": False,
            "confidence": 1.0,
            "reasoning": "The user is asking about school attendance policy/rules."
        }

        print("\n===== VALIDATED RAG POLICY PLAN =====")
        print(plan)
        print("=====================================\n")

        return plan

    # -----------------------------------------------------
    # ATTENDANCE TREND
    # -----------------------------------------------------

    trend_phrases = [
        "is my attendance improving",
        "am i improving my attendance",
        "attendance improving",
        "attendance getting better",
        "attendance trend",
        "attendance over time",
        "attendance progress",
        "how is my attendance changing",
    ]

    if contains_any(
        q,
        trend_phrases
    ):

        return make_plan(
            intent="attendance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="attendance_trend",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants to analyze "
                "their attendance trend."
            ),
        )

    # -----------------------------------------------------
    # ATTENDANCE SUMMARY
    # -----------------------------------------------------

    summary_phrases = [
        "attendance summary",
        "attendance record summary",
        "present absent",
        "how many days was i present and absent",
        "how many days present and absent",
        "attendance details",
        "attendance report",
        "my attendance details",
    ]

    if contains_any(
        q,
        summary_phrases
    ):

        return make_plan(
            intent="attendance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="attendance_summary",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants a summary "
                "of their attendance."
            ),
        )

    # -----------------------------------------------------
    # SUBJECT-WISE ATTENDANCE
    # -----------------------------------------------------

    subject_attendance_phrases = [
        "attendance by subject",
        "subject wise attendance",
        "subject-wise attendance",
        "attendance for each subject",
        "attendance in each subject",
        "my attendance for each subject",
    ]

    if contains_any(
        q,
        subject_attendance_phrases
    ):

        return make_plan(
            intent="attendance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="subject_attendance",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants attendance "
                "broken down by subject."
            ),
        )

    # -----------------------------------------------------
    # GENERAL ATTENDANCE
    # -----------------------------------------------------

    if contains_any(
        q,
        ATTENDANCE_GENERAL_PHRASES
    ):

        return make_plan(
            intent="attendance",
            query_type="information",
            operation="fetch",
            source="sql",
            metric="monthly_attendance",
            confidence=1.0,
            reasoning=(
                "The user is asking "
                "about attendance."
            ),
        )

    return None


# =========================================================
# ASSIGNMENT DETECTION
# =========================================================

def detect_assignment_plan(
    question: str
):

    q = normalize_question(question)

    if not q:
        return None

    subject = detect_assignment_subject(q)
    title = extract_assignment_title(q)
    scope = detect_assignment_scope(q)

# =====================================================
# IMPORTANT: SUBJECT IS NOT ASSIGNMENT TITLE
# =====================================================

    if subject and title:

        normalized_subject = re.sub(
            r"\s+",
            " ",
            str(subject).lower().strip()
        )

        normalized_title = re.sub(
            r"\s+",
            " ",
            str(title).lower().strip()
        )

    # Remove trailing "assignment" / "assignments"
        normalized_title = re.sub(
            r"\s+assignments?$",
            "",
            normalized_title
        ).strip()

    # Example:
    # "what is chemistry assignment"
    #
    # subject = chemistry
    # title   = chemistry
    #
    # Therefore title MUST be removed.

        if normalized_title == normalized_subject:
            title = None
    constraints = {}
    context = {}

    # -----------------------------------------------------
    # SUBJECT
    # -----------------------------------------------------

    if subject:
        constraints["subject"] = subject
        context["subject"] = subject

    # -----------------------------------------------------
    # TITLE
    # -----------------------------------------------------

    if title:
        constraints["assignment_title"] = title

    # -----------------------------------------------------
    # SCOPE
    # -----------------------------------------------------

    if scope:
        constraints["assignment_scope"] = scope

    # -----------------------------------------------------
    # OVERDUE
    # -----------------------------------------------------

    if contains_any(
        q,
        ASSIGNMENT_OVERDUE_PHRASES
    ):

        return make_plan(
            intent="assignments",
            query_type="information",
            operation="fetch",
            source="sql",
            constraints={
                **constraints,
                "assignment_scope": "overdue",
            },
            context=context,
            metric="overdue_assignments",
            confidence=1.0,
            reasoning=(
                "The user wants to see "
                "overdue assignments."
            ),
        )

    # -----------------------------------------------------
    # PENDING
    # -----------------------------------------------------

    if contains_any(
        q,
        ASSIGNMENT_PENDING_PHRASES
    ):

        return make_plan(
            intent="assignments",
            query_type="information",
            operation="fetch",
            source="sql",
            constraints={
                **constraints,
                "assignment_scope": "upcoming",
            },
            context=context,
            metric="pending_assignments",
            confidence=1.0,
            reasoning=(
                "The user wants assignments "
                "that still need attention."
            ),
        )

    # -----------------------------------------------------
    # COMPLETED
    # -----------------------------------------------------

    if contains_any(
        q,
        ASSIGNMENT_COMPLETED_PHRASES
    ):

        return make_plan(
            intent="assignments",
            query_type="information",
            operation="fetch",
            source="sql",
            constraints=constraints,
            context=context,
            metric="completed_assignments",
            confidence=1.0,
            reasoning=(
                "The user wants completed "
                "or submitted assignments."
            ),
        )

    # -----------------------------------------------------
    # TODAY
    # -----------------------------------------------------

    if scope == "today":

        return make_plan(
            intent="assignments",
            query_type="information",
            operation="fetch",
            source="sql",
            constraints={
                **constraints,
                "assignment_scope": "today",
            },
            context=context,
            metric="assignment_due",
            confidence=1.0,
            reasoning=(
                "The user wants assignments "
                "due today."
            ),
        )

    # -----------------------------------------------------
    # TOMORROW
    # -----------------------------------------------------

    if scope == "tomorrow":

        return make_plan(
            intent="assignments",
            query_type="information",
            operation="fetch",
            source="sql",
            constraints={
                **constraints,
                "assignment_scope": "tomorrow",
            },
            context=context,
            metric="assignment_due",
            confidence=1.0,
            reasoning=(
                "The user wants assignments "
                "due tomorrow."
            ),
        )

    # -----------------------------------------------------
    # UPCOMING
    # -----------------------------------------------------

    if scope == "upcoming":

        return make_plan(
            intent="assignments",
            query_type="information",
            operation="fetch",
            source="sql",
            constraints={
                **constraints,
                "assignment_scope": "upcoming",
            },
            context=context,
            metric="assignment_list",
            confidence=1.0,
            reasoning=(
                "The user wants upcoming assignments."
            ),
        )

    # -----------------------------------------------------
    # SPECIFIC ASSIGNMENT / DUE DATE
    # -----------------------------------------------------

    if title:

        return make_plan(
            intent="assignments",
            query_type="information",
            operation="fetch",
            source="sql",
            constraints=constraints,
            context=context,
            metric="assignment_due",
            confidence=1.0,
            reasoning=(
                "The user is asking about "
                "a specific assignment."
            ),
        )

    # -----------------------------------------------------
    # DUE DATE
    # -----------------------------------------------------

    if contains_any(
        q,
        ASSIGNMENT_DUE_PHRASES
    ):

        return make_plan(
            intent="assignments",
            query_type="information",
            operation="fetch",
            source="sql",
            constraints=constraints,
            context=context,
            metric="assignment_due",
            confidence=1.0,
            reasoning=(
                "The user wants assignment "
                "due-date information."
            ),
        )

    # -----------------------------------------------------
    # GENERAL ASSIGNMENT
    # -----------------------------------------------------

    if contains_any(
        q,
        ASSIGNMENT_GENERAL_PHRASES
    ):

        return make_plan(
            intent="assignments",
            query_type="information",
            operation="fetch",
            source="sql",
            constraints=constraints,
            context=context,
            metric="assignment_list",
            confidence=1.0,
            reasoning=(
                "The user wants information "
                "about assignments."
            ),
        )

    return None


# =========================================================
# PERFORMANCE DETECTION
# =========================================================

def detect_performance_plan(
    question: str,
    existing_metric=None
):

    q = normalize_question(question)

    if not q:
        return None
    
    # =====================================================
    # FULL PERFORMANCE REPORT
    # =====================================================

    if contains_any(
        q,
        [
            "how did i perform",
            "how did i perform overall",
            "how am i performing",
            "how am i doing",
            "how am i doing academically",
            "how well am i doing",
            "how well am i doing overall",
            "give me my performance report",
            "give me a performance report",
            "show my performance report",
            "my performance report",
        ]
    ):
        return make_plan(
        intent="performance",
        query_type="analysis",
        operation="analyze",
        source="sql",
        metric="performance_report",
        analysis=True,
        comparison=True,
        confidence=1.0,
        reasoning=(
            "Detected request for a complete performance report "
            "including exam comparison, strongest subject, "
            "weakest subject, and overall trend."
        )
    )
    
    # =========================================================
    # SUBJECT FOCUS / IMPROVEMENT OVERRIDE
    # =========================================================

    focus_phrases = [
        "which subject should i focus on",
        "which subject should i focus",
        "what subject should i focus on",
        "what subject should i focus",
        "subject should i focus on",
        "focus on which subject",
        "which subject to focus on",

        "which subject should i improve",
        "what subject should i improve",
        "which subject needs improvement",
        "what should i improve",
        "where do i need improvement",
        "where am i weak",

        "weakest subject",
        "worst subject",
        "lowest subject",
        "lowest marks",

        # Important: recommendation based on marks
        "focus based on my marks",
        "focus based on marks",
        "improve based on my marks",
        "improve based on marks",
        "subject based on my marks",
    ]

    if any(phrase in q for phrase in focus_phrases):
        return make_plan(
            intent="performance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="lowest_subject",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "Detected subject-focus/improvement query "
                "based on student marks."
            )
        )

    performance_words = [
        "performance",
        "performing",
        "strongest subject",
        "strong subject",
        "best subject",
        "weakest subject",
        "weak subject",
        "worst subject",
        "highest marks",
        "lowest marks",
        "highest score",
        "lowest score",
        "improving",
        "getting better",
        "progress",
        "trend",
        "compare exams",
        "compare my exams",
        "exam comparison",
        "recommend",
        "recommendation",
        "how can i improve",
        "what should i study",
    ]

    has_performance_language = contains_any(
        q,
        performance_words
    )

    # Exam comparison can also be recognized
    # without the word performance.
    has_midterm = any(
        phrase in q
        for phrase in [
            "midterm",
            "mid term",
            "mid-term",
            "mid exam",
            "mid examination",
            "half yearly",
            "half-yearly",
            "term 1",
            "first term",
            "first semester",
            "semester 1",
        ]
    )

    has_final = any(
        phrase in q
        for phrase in [
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
    )

    if not has_performance_language and not (
        has_midterm and has_final
    ):
        return None
    
    # ==========================================
    # SUBJECT TO IMPROVE / FOCUS ON
    # ==========================================

    focus_phrases = [
    "which subject should i focus on",
    "which subject should i focus",
    "what subject should i focus on",
    "what subject should i focus",
    "subject should i focus on",
    "focus on which subject",
    "which subject to focus on",
    "which subject should i improve",
    "what subject should i improve",
    "which subject needs improvement",
    "what should i improve",
    "where do i need improvement",
    "where am i weak",
    "weakest subject",
    "worst subject",
    "lowest subject",
    "lowest marks",
    ]
    if any(phrase in q for phrase in focus_phrases):
        return make_plan(
        intent="performance",
        query_type="analysis",
        operation="analyze",
        source="sql",
        metric="lowest_subject",
        analysis=True,
        confidence=1.0,
        reasoning=(
            "The user wants to identify the subject "
            "that needs the most improvement."
        ),
    )

    # -----------------------------------------------------
    # RECOMMENDATION
    # -----------------------------------------------------

    recommendation_phrases = [
        "recommend",
        "recommendation",
        "study recommendation",
        "what should i study",
        "what should i improve",
        "how can i improve",
        "where should i improve",
        "what do i need to improve",
    ]

    if contains_any(
        q,
        recommendation_phrases
    ):

        return make_plan(
            intent="performance",
            query_type="recommendation",
            operation="analyze",
            source="sql",
            metric="recommendation",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants recommendations "
                "based on academic performance."
            ),
        )
        
     # =====================================================
    # FULL PERFORMANCE REPORT
    # =====================================================
    if contains_any(
        q,
        [
            "how did i perform",
            "how did i perform overall",
            "how am i performing",
            "how am i doing",
            "how am i doing academically",
            "how well am i doing",
            "how well am i doing overall",
            "give me my performance report",
            "give me a performance report",
            "show my performance report",
            "my performance report",
        ]
    ):
        return make_plan(
            "performance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="performance_report",
            analysis=True,
            comparison=True,
            confidence=1.0,
            reasoning=(
                "Detected request for a complete performance "
                "report including exam comparison, strongest "
                "subject, and weakest subject."
            )
        )


    # -----------------------------------------------------
    # LOWEST SUBJECT
    # -----------------------------------------------------

    lowest_phrases = [
    "weakest subject",
    "weak subject",
    "worst subject",
    "lowest subject",
    "lowest marks",
    "lowest score",
    "subject with lowest marks",
    "subject with the lowest marks",
    "which subject has my lowest marks",
    "which is my worst subject",

    "needs improvement",
    "which subject needs improvement",
    "which subject should i improve",
    "what subject should i improve",
    "where do i need improvement",
    "where am i weak",
    "what should i improve",

    # IMPORTANT
    "which subject should i focus on",
    "subject should i focus on",
    "focus based on my marks",
    "focus on which subject",
]


    if contains_any(q,lowest_phrases):

        return make_plan(
            intent="performance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="lowest_subject",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants to identify "
                "their weakest subject."
                "that needs improvement."
            ),
        )

    # -----------------------------------------------------
    # HIGHEST SUBJECT
    # -----------------------------------------------------

    highest_subject_phrases = [
        "strongest subject",
    "strong subject",
    "best subject",
    "highest subject",
    "subject with highest marks",
    "subject with the highest marks",
    "highest marks in which subject",
    "which subject has my highest marks",
    "which subject is my best",
    "which is my best subject",
    ]

    if contains_any(q,highest_subject_phrases):

        return make_plan(
            intent="performance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="highest_subject",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants to identify "
                "their strongest subject."
            ),
        )

    # -----------------------------------------------------
    # EXAM COMPARISON
    # -----------------------------------------------------

    comparison_words = [
        "compare",
        "compared",
        "comparison",
        "vs",
        "versus",
        "improve",
        "improved",
        "declined",
        "change",
    ]

    if (
        has_midterm
        and has_final
        and contains_any(
            q,
            comparison_words
        )
    ):

        return make_plan(
            intent="performance",
            query_type="comparison",
            operation="analyze",
            source="sql",
            constraints={
                "exam": [
                    "midterm",
                    "final",
                ]
            },
            metric="exam_comparison",
            analysis=True,
            comparison=True,
            confidence=1.0,
            reasoning=(
                "The user wants to compare "
                "Mid Term and Final performance."
            ),
        )

    # If both exams are explicitly mentioned,
    # comparison is normally intended.
    if has_midterm and has_final:

        return make_plan(
            intent="performance",
            query_type="comparison",
            operation="analyze",
            source="sql",
            constraints={
                "exam": [
                    "midterm",
                    "final",
                ]
            },
            metric="exam_comparison",
            analysis=True,
            comparison=True,
            confidence=1.0,
            reasoning=(
                "Both Mid Term and Final "
                "examinations were mentioned."
            ),
        )

    # -----------------------------------------------------
    # TREND
    # -----------------------------------------------------

    trend_phrases = [
        "performance trend",
        "performance over time",
        "am i improving",
        "am i getting better",
        "is my performance improving",
        "my progress",
        "academic progress",
        "performance progress",
        "trend in my marks",
        "trend in my scores",
        "compare my performance",
        "how am i improving",
    ]

    if contains_any(
        q,
        trend_phrases
    ):

        return make_plan(
            intent="performance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="trend",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants to analyze "
                "performance over time."
            ),
        )

    # -----------------------------------------------------
    # HIGHEST SCORE
    # -----------------------------------------------------

    highest_score_phrases = [
        "highest score",
        "highest marks",
        "maximum marks",
        "my highest score",
        "my highest marks",
        "what is my highest score",
    ]

    if contains_any(
        q,
        highest_score_phrases
    ):

        return make_plan(
            intent="performance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="highest_score",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants to find "
                "their highest score."
            ),
        )

    # -----------------------------------------------------
    # LOWEST SCORE
    # -----------------------------------------------------

    lowest_score_phrases = [
        "lowest score",
        "lowest marks",
        "minimum marks",
        "my lowest score",
        "my lowest marks",
        "what is my lowest score",
    ]

    if contains_any(
        q,
        lowest_score_phrases
    ):

        return make_plan(
            intent="performance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="lowest_score",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants to find "
                "their lowest score."
            ),
        )

    # -----------------------------------------------------
    # BEST EXAM
    # -----------------------------------------------------

    best_exam_phrases = [
        "best exam",
        "which exam did i do best",
        "which exam was my best",
        "exam where i scored highest",
    ]

    if contains_any(
        q,
        best_exam_phrases
    ):

        return make_plan(
            intent="performance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="best_exam",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants to identify "
                "their best examination."
            ),
        )

    # -----------------------------------------------------
    # WORST EXAM
    # -----------------------------------------------------

    worst_exam_phrases = [
        "worst exam",
        "which exam did i do worst",
        "which exam was my worst",
        "exam where i scored lowest",
    ]

    if contains_any(
        q,
        worst_exam_phrases
    ):

        return make_plan(
            intent="performance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="worst_exam",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user wants to identify "
                "their worst examination."
            ),
        )

    # -----------------------------------------------------
    # SUBJECT PERFORMANCE
    # -----------------------------------------------------

    subject = detect_subject(q)

    if subject and any(
        word in q
        for word in [
            "performance",
            "marks",
            "score",
            "result",
            "grade",
        ]
    ):

        return make_plan(
            intent="marks",
            query_type="information",
            operation="fetch",
            source="sql",
            constraints={
                "subject": subject
            },
            context={
                "subject": subject
            },
            metric="subject_performance",
            confidence=1.0,
            reasoning=(
                "The user wants performance "
                "information for a specific subject."
            ),
        )
    
    # =========================================================
    # PERFORMANCE TREND / IMPROVEMENT
    # =========================================================

    performance_trend_phrases = [
        "am i improving",
        "is my performance improving",
        "am i getting better",
        "is my performance getting better",
        "am i doing better",
        "did i improve",
        "did i improve in exams",
        "have i improved",
        "have i been improving",
        "am i performing better",
        "performance trend",
        "my performance over time",
        "my progress",
        "how is my performance changing",
    ]

    if contains_any(q, performance_trend_phrases):

        return make_plan(
            intent="performance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="trend",
            analysis=True,
            comparison=False,
            confidence=1.0,
            reasoning=(
                "The user wants to know whether "
                "their exam performance is improving over time."
            ),
        )
    
    # -----------------------------------------------------
    # GENERAL PERFORMANCE
    # -----------------------------------------------------

    if has_performance_language:

        return make_plan(
            intent="performance",
            query_type="analysis",
            operation="analyze",
            source="sql",
            metric="overall_performance",
            analysis=True,
            confidence=1.0,
            reasoning=(
                "The user is asking about "
                "overall academic performance."
            ),
        )

    return None

def enforce_marks_constraints(question: str, plan: dict) -> dict:

    q = question.lower().strip()

    if plan.get("intent") != "marks":
        return plan

    constraints = plan.get("constraints", {}) or {}

    # =================================================
    # LATEST MARKS
    # =================================================

    if (
        "latest marks" in q
        or "latest mark" in q
        or "latest exam marks" in q
        or "most recent marks" in q
        or "most recent mark" in q
    ):

        constraints["exam"] = "latest"
        plan["exam"] = "latest"

        if not plan.get("metric"):
            plan["metric"] = "overall_performance"

    # =================================================
    # FINAL MARKS
    # =================================================

    elif (
        "final marks" in q
        or "final exam marks" in q
        or "final examination marks" in q
    ):

        constraints["exam"] = "final"
        plan["exam"] = "final"

    # =================================================
    # MID TERM MARKS
    # =================================================

    elif (
        "mid term marks" in q
        or "midterm marks" in q
        or "mid term exam marks" in q
    ):

        constraints["exam"] = "midterm"
        plan["exam"] = "midterm"

    # =================================================
    # PREVIOUS MARKS
    # =================================================

    elif (
        "previous marks" in q
        or "previous exam marks" in q
        or "previous exam" in q
    ):

        constraints["exam"] = "previous"
        plan["exam"] = "previous"

    plan["constraints"] = constraints

    return plan


# =========================================================
# GENERAL EXPLICIT INTENT
# =========================================================

def detect_explicit_intent(
    question: str
):

    q = normalize_question(question)

    if not q:
        return None

    # -----------------------------------------------------
    # ATTENDANCE
    # -----------------------------------------------------

    attendance_words = [
        "attendance",
        "absent",
        "absence",
        "present",
        "missed school",
        "miss school",
        "missed class",
        "miss class",
    ]

    if any(
        word in q
        for word in attendance_words
    ):
        return "attendance"

    # -----------------------------------------------------
    # ASSIGNMENTS
    # -----------------------------------------------------

    assignment_words = [
        "assignment",
        "assignments",
        "homework",
        "home work",
        "submission",
        "submissions",
        "due date",
        "deadline",
    ]

    if any(
        word in q
        for word in assignment_words
    ):
        return "assignments"

    # -----------------------------------------------------
    # TIMETABLE
    # -----------------------------------------------------

    timetable_words = [
        "timetable",
        "time table",
        "schedule",
        "class schedule",
        "classes today",
        "class today",
        "period",
        "periods",
        "what class",
        "which class",
    ]

    if any(
        word in q
        for word in timetable_words
    ):
        return "timetable"

    # -----------------------------------------------------
    # TEACHER
    # -----------------------------------------------------

    teacher_words = [
        "teacher",
        "teachers",
        "who teaches",
        "who is my teacher",
        "faculty",
        "subject teacher",
    ]

    if any(
        word in q
        for word in teacher_words
    ):
        return "teacher"

    # -----------------------------------------------------
    # PROFILE
    # -----------------------------------------------------

    profile_words = [
        "my profile",
        "my details",
        "my information",
        "student details",
        "student information",
        "who am i",
        "my student details",
    ]

    if any(
        word in q
        for word in profile_words
    ):
        return "profile"

    # -----------------------------------------------------
    # FEES
    # -----------------------------------------------------

    fees_words = [
        "fee",
        "fees",
        "payment",
        "payments",
        "tuition",
        "school fee",
    ]

    if any(
        word in q
        for word in fees_words
    ):
        return "fees"

    # -----------------------------------------------------
    # ANNOUNCEMENTS
    # -----------------------------------------------------

    announcement_words = [
        "announcement",
        "announcements",
        "notice",
        "notices",
        "circular",
        "circulars",
        "latest notice",
    ]

    if any(
        word in q
        for word in announcement_words
    ):
        return "announcement"

    # -----------------------------------------------------
    # SCHOOL POLICY
    # -----------------------------------------------------

    policy_words = [
        "school policy",
        "policy",
        "uniform",
        "library rules",
        "transport rules",
        "holiday policy",
        "school rules",
        "rules",
    ]

    if any(
        word in q
        for word in policy_words
    ):
        return "school_policy"

    # -----------------------------------------------------
    # MARKS
    # -----------------------------------------------------

    marks_words = [
        "marks",
        "mark",
        "score",
        "scores",
        "result",
        "results",
        "grade",
        "grades",
        "exam marks",
        "test marks",
        "my result",
        "my results",
    ]

    if any(
        word in q
        for word in marks_words
    ):
        return "marks"

    return None


# =========================================================
# EXAM DETECTION
# =========================================================

def detect_exam_constraints(
    question: str
):

    q = normalize_question(question)

    has_midterm = any(
        phrase in q
        for phrase in [
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
    )

    has_final = any(
        phrase in q
        for phrase in [
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
    )

    if has_midterm and has_final:
        return [
            "midterm",
            "final",
        ]

    if has_midterm:
        return "midterm"

    if has_final:
        return "final"

    return None


# =========================================================
# MONTH/YEAR DETECTION
# =========================================================

def detect_month_year(
    question: str
):

    q = normalize_question(question)

    if not q:
        return None, None

    # -----------------------------------------------------
    # CURRENT MONTH
    # -----------------------------------------------------

    if (
        "this month" in q
        or "current month" in q
    ):
        from datetime import datetime

        now = datetime.now()

        return now.month, now.year

    # -----------------------------------------------------
    # LAST MONTH
    # -----------------------------------------------------

    if (
        "last month" in q
        or "previous month" in q
    ):
        from datetime import datetime

        now = datetime.now()

        if now.month == 1:
            return 12, now.year - 1

        return now.month - 1, now.year

    month_pattern = "|".join(
        re.escape(
            name
        )
        for name in MONTH_MAP.keys()
    )

    # -----------------------------------------------------
    # June 2026
    # -----------------------------------------------------

    match = re.search(
        rf"\b({month_pattern})\s+((?:19|20)\d{{2}})\b",
        q
    )

    if match:

        month_name = match.group(1)
        year = int(match.group(2))

        return (
            MONTH_MAP[month_name],
            year
        )

    # -----------------------------------------------------
    # 2026 June
    # -----------------------------------------------------

    match = re.search(
        rf"\b((?:19|20)\d{{2}})\s+({month_pattern})\b",
        q
    )

    if match:

        year = int(match.group(1))
        month_name = match.group(2)

        return (
            MONTH_MAP[month_name],
            year
        )

    # -----------------------------------------------------
    # MONTH ONLY
    # -----------------------------------------------------

    for month_name, month_number in MONTH_MAP.items():

        if re.search(
            rf"\b{re.escape(month_name)}\b",
            q
        ):

            return (
                month_number,
                None
            )

    return None, None


# =========================================================
# DAY DETECTION
# =========================================================

def detect_day(
    question: str
):

    q = normalize_question(question)

    if not q:
        return None

    if "today" in q:
        return "today"

    if "tomorrow" in q:
        return "tomorrow"

    # "next class", "next period"
    if any(
        phrase in q
        for phrase in [
            "next class",
            "next period",
            "what is next",
            "what's next",
        ]
    ):
        return "next"

    weekdays = {
        "monday",
        "tuesday",
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
    }

    for day in weekdays:

        if re.search(
            rf"\b{day}\b",
            q
        ):
            return day

    return None


# =========================================================
# FALLBACK PLAN
# =========================================================

def build_fallback_plan(
    question: str
):

    q = normalize_question(question)

    print("\n===== FALLBACK PLAN BUILDER =====")
    print("Question:", question)

    # =====================================================
    # 1. ATTENDANCE
    # =====================================================

    attendance_plan = detect_attendance_plan(q)

    if attendance_plan is not None:

        month, year = detect_month_year(q)

        if month is not None:
            attendance_plan["constraints"]["month"] = month

        if year is not None:
            attendance_plan["constraints"]["year"] = year

        print("\n===== FALLBACK ATTENDANCE PLAN =====")
        print(attendance_plan)
        print("====================================\n")

        return attendance_plan

    # =====================================================
    # 2. ASSIGNMENTS
    # =====================================================

    assignment_plan = detect_assignment_plan(q)

    if assignment_plan is not None:

        month, year = detect_month_year(q)

        if month is not None:
            assignment_plan["constraints"]["month"] = month

        if year is not None:
            assignment_plan["constraints"]["year"] = year

        print("\n===== FALLBACK ASSIGNMENT PLAN =====")
        print(assignment_plan)
        print("====================================\n")

        return assignment_plan

    # =====================================================
    # 3. PERFORMANCE
    # =====================================================
    
    
    
    performance_plan = detect_performance_plan(q)

    if performance_plan is not None:

        exam = detect_exam_constraints(q)

        if exam is not None:
            performance_plan["constraints"]["exam"] = exam

        print("\n===== FALLBACK PERFORMANCE PLAN =====")
        print(performance_plan)
        print("====================================\n")

        return performance_plan

    # =====================================================
    # 4. GENERAL EXPLICIT INTENT
    # =====================================================

    explicit_intent = detect_explicit_intent(q)

    if explicit_intent:

        plan = make_plan(
            intent=explicit_intent,
            query_type="information",
            operation="fetch",
            source="sql",
            confidence=1.0,
            reasoning=(
                "Explicit rule-based intent detection."
            ),
        )

        # -------------------------------------------------
        # MARKS
        # -------------------------------------------------

        if explicit_intent == "marks":

            subject = detect_subject(q)

            if subject:

                plan["constraints"]["subject"] = subject
                plan["context"]["subject"] = subject

        # -------------------------------------------------
        # TIMETABLE
        # -------------------------------------------------

        elif explicit_intent == "timetable":

            day = detect_day(q)

            if day:
                plan["constraints"]["day"] = day

            subject = detect_subject(q)

            if subject:
                plan["context"]["subject"] = subject

        # -------------------------------------------------
        # TEACHER
        # -------------------------------------------------

        elif explicit_intent == "teacher":

            subject = detect_subject(q)

            if subject:
                plan["constraints"]["subject"] = subject
                plan["context"]["subject"] = subject

        # -------------------------------------------------
        # SCHOOL POLICY
        # -------------------------------------------------

        elif explicit_intent == "school_policy":

            plan["source"] = "rag"

        print("\n===== FALLBACK EXPLICIT PLAN =====")
        print(plan)
        print("==================================\n")

        return plan

    # =====================================================
    # 5. SEMANTIC FALLBACK
    # =====================================================

    try:

        semantic_intent, semantic_score, scores = (
            detect_intent(q)
        )

    except Exception as exc:

        print(
            "Semantic intent detection failed:",
            exc
        )

        semantic_intent = "unknown"
        semantic_score = 0.0
        scores = {}

    print("\n===== FALLBACK SEMANTIC INTENT =====")
    print("Query:", q)
    print("Embedding Intent:", semantic_intent)
    print("Embedding Score:", semantic_score)
    print("All Scores:", scores)
    print("====================================\n")

    if (
        semantic_intent in VALID_INTENTS
        and semantic_score >= 0.75
    ):
        intent = semantic_intent
    else:
        intent = "unknown"

    source = "sql"

    if intent == "school_policy":
        source = "rag"

    if intent == "performance":
        source = "hybrid"

    plan = make_plan(
        intent=intent,
        source=source,
        confidence=float(
            semantic_score or 0.0
        ),
        reasoning=(
            "Semantic fallback intent detection."
        ),
    )

    return plan


# =========================================================
# MERGE CONSTRAINTS
# =========================================================

def merge_constraints(
    original,
    detected
):

    original = (
        original
        if isinstance(original, dict)
        else {}
    )

    detected = (
        detected
        if isinstance(detected, dict)
        else {}
    )

    merged = dict(original)

    for key, value in detected.items():

        if value is None:
            continue

        if (
            isinstance(value, dict)
            and isinstance(
                merged.get(key),
                dict
            )
        ):

            merged[key] = {
                **merged[key],
                **value,
            }

        else:

            merged[key] = value

    return merged


# =========================================================
# MAIN VALIDATOR
# =========================================================

def validate_plan(
    plan: dict,
    question: str = ""
):

    if not isinstance(plan, dict):
        plan = {}

    q = normalize_question(question)

    # =====================================================
    # IMPORTANT PRIORITY ORDER
    #
    # 1. Attendance
    # 2. Assignments
    # 3. Performance
    # 4. Existing valid planner intent
    # 5. General explicit intent
    # 6. Semantic fallback
    #
    # This prevents BGE from changing obvious queries.
    # =====================================================

    # =====================================================
    # ATTENDANCE
    # =====================================================

    attendance_plan = detect_attendance_plan(q)

    if attendance_plan is not None:

        existing_constraints = safe_dict(
            plan.get("constraints")
        )

        attendance_plan["constraints"] = (
            merge_constraints(
                existing_constraints,
                attendance_plan["constraints"]
            )
        )

        month, year = detect_month_year(q)

        if month is not None:
            attendance_plan["constraints"]["month"] = month

        if year is not None:
            attendance_plan["constraints"]["year"] = year

        print("\n===== VALIDATED ATTENDANCE PLAN =====")
        print(attendance_plan)
        print("=====================================\n")

        return attendance_plan

    # =====================================================
    # ASSIGNMENTS
    # =====================================================

    assignment_plan = detect_assignment_plan(q)

    if assignment_plan is not None:

        existing_constraints = safe_dict(
            plan.get("constraints")
        )

        existing_context = safe_dict(
            plan.get("context")
        )

        assignment_plan["constraints"] = (
            merge_constraints(
                existing_constraints,
                assignment_plan["constraints"]
            )
        )

        assignment_plan["context"] = (
            merge_constraints(
                existing_context,
                assignment_plan["context"]
            )
        )

        month, year = detect_month_year(q)

        if month is not None:
            assignment_plan["constraints"]["month"] = month

        if year is not None:
            assignment_plan["constraints"]["year"] = year

        print("\n===== VALIDATED ASSIGNMENT PLAN =====")
        print(assignment_plan)
        print("=====================================\n")

        return assignment_plan

    # =====================================================
    # PERFORMANCE
    # =====================================================

    performance_plan = detect_performance_plan(q)

    if performance_plan is not None:

        existing_constraints = safe_dict(
            plan.get("constraints")
        )

        performance_plan["constraints"] = (
            merge_constraints(
                existing_constraints,
                performance_plan["constraints"]
            )
        )

        print("\n===== VALIDATED PERFORMANCE PLAN =====")
        print(performance_plan)
        print("======================================\n")

        return performance_plan

    # =====================================================
    # EXISTING PLANNER INTENT
    # =====================================================

    intent = str(
        plan.get(
            "intent",
            ""
        )
    ).lower().strip()

    # =====================================================
    # SEMANTIC INTENT
    # =====================================================

    try:

        semantic_intent, semantic_score, scores = (
            detect_intent(q)
        )

    except Exception as exc:

        print(
            "Semantic detection failed:",
            exc
        )

        semantic_intent = "unknown"
        semantic_score = 0.0
        scores = {}

    print("\n===== SEMANTIC INTENT =====")
    print("Query:", q)
    print("Embedding Intent:", semantic_intent)
    print("Embedding Score:", semantic_score)
    print("All Scores:", scores)
    print("===========================\n")

    # -----------------------------------------------------
    # ONLY USE SEMANTIC INTENT IF PLANNER INTENT
    # IS INVALID.
    # -----------------------------------------------------

    if (
        intent not in VALID_INTENTS
        or intent == "unknown"
    ):

        if (
            semantic_intent in VALID_INTENTS
            and semantic_score >= 0.75
        ):

            intent = semantic_intent

        else:

            explicit_intent = (
                detect_explicit_intent(q)
            )

            if explicit_intent:
                intent = explicit_intent
            else:
                intent = "unknown"

    plan["intent"] = intent

    # =====================================================
    # DEFAULT CONTAINERS
    # =====================================================

    constraints = plan.get(
        "constraints",
        {}
    )

    context = plan.get(
        "context",
        {}
    )

    if not isinstance(
        constraints,
        dict
    ):
        constraints = {}

    if not isinstance(
        context,
        dict
    ):
        context = {}

    plan["constraints"] = constraints
    plan["context"] = context

    # =====================================================
    # MONTH/YEAR
    # =====================================================

    month, year = detect_month_year(q)

    if month is not None:
        constraints["month"] = month

    if year is not None:
        constraints["year"] = year

    # =====================================================
    # EXAM
    # =====================================================

    exam = detect_exam_constraints(q)

    if exam is not None:
        constraints["exam"] = exam

    # =====================================================
    # SUBJECT
    # =====================================================

    subject = detect_subject(q)

    if subject:

        # Do not blindly add subject to all intents.
        if intent in {
            "marks",
            "assignments",
            "teacher",
            "timetable",
            "attendance",
        }:

            constraints.setdefault(
                "subject",
                subject
            )

            context.setdefault(
                "subject",
                subject
            )

    # =====================================================
    # DAY
    # =====================================================

    day = detect_day(q)

    if (
        day is not None
        and intent == "timetable"
    ):

        constraints["day"] = day

    # =====================================================
    # PERFORMANCE
    # =====================================================

    if intent == "performance":

        plan["operation"] = "analyze"
        plan["query_type"] = "analysis"
        plan["source"] = "hybrid"
        plan["analysis"] = True
        
        # =========================================================
        # GENERIC PERFORMANCE REPORT OVERRIDE
        # =========================================================

        generic_performance_phrases = [
            "how did i perform",
            "how did i do",
            "how am i performing",
            "how is my performance",
            "how was my performance",
            "my overall performance",
            "overall performance",
            "tell me about my performance",
            "give me my performance",
            "performance report",
            "performance summary"
        ]

        if any(
            phrase in q.lower()
            for phrase in generic_performance_phrases
        ):
            return make_plan(
                "performance",
                source="hybrid",
                metric="performance_report",
                subject=None,
                exam=None,
                day=None,
                confidence= 0.95,
                reasoning="compare performance across examinations",
                constraints={},
                context={},
                operation="analyze",
                query_type="analysis",
                analysis=True,
                comparison=True
            )

        # -------------------------------------------------
        # LOWEST SUBJECT
        # -------------------------------------------------

        if any(
            phrase in q
            for phrase in [
                "weakest subject",
                "weak subject",
                "worst subject",
                "lowest subject",
                "subject with lowest marks",
                "subject with the lowest marks",
                "lowest marks in which subject",
                "which subject has my lowest marks",
                "which subject is my worst",
                "which is my worst subject",

                "needs improvement",
                "which subject needs improvement",
                "which subject should i improve",
                "where do i need improvement",
                "where am i weak",
                "what should i improve",
                "what subject should i improve",

                # NEW
                "which subject should i focus on",
                "subject should i focus on",
                "focus based on my marks",
            ]
        ):

            plan["metric"] = "lowest_subject"

        # -------------------------------------------------
        # HIGHEST SUBJECT
        # -------------------------------------------------

        elif any(
            phrase in q
            for phrase in [
                "strongest subject",
                "strong subject",
                "best subject",
                "highest subject",
                "highest marks in which subject",
                "subject with highest marks",
                "which subject has my highest marks",
            ]
        ):

            plan["metric"] = "highest_subject"

        # -------------------------------------------------
        # RECOMMENDATION
        # -------------------------------------------------

        elif any(
            phrase in q
            for phrase in [
                "recommend",
                "recommendation",
                "what should i study",
                "what should i improve",
                "how can i improve",
                "where should i improve",
            ]
        ):

            plan["metric"] = "recommendation"
            plan["query_type"] = "recommendation"

        # -------------------------------------------------
        # EXAM COMPARISON
        # -------------------------------------------------

        elif (
            isinstance(
                exam,
                list
            )
            and len(exam) == 2
            and any(
                word in q
                for word in [
                    "compare",
                    "comparison",
                    "compared",
                    "vs",
                    "versus",
                    "improve",
                    "change",
                ]
            )
        ):

            plan["metric"] = "exam_comparison"
            plan["comparison"] = True
            plan["query_type"] = "comparison"

        # -------------------------------------------------
        # TREND
        # -------------------------------------------------

        elif any(
            phrase in q
            for phrase in [
                "trend",
                "progress",
                "improving",
                "getting better",
                "performance over time",
                "compare my performance",
            ]
        ):

            plan["metric"] = "trend"

        # -------------------------------------------------
        # DEFAULT
        # -------------------------------------------------

        else:

            plan["metric"] = (
                plan.get("metric")
                if plan.get("metric")
                in VALID_METRICS
                else "overall_performance"
            )

        if (
            not plan.get("confidence")
            or plan.get("confidence", 0) < 0.5
        ):

            plan["confidence"] = 0.9

    # =====================================================
    # MARKS
    # =====================================================

    elif intent == "marks":

        plan["operation"] = "fetch"
        plan["query_type"] = "information"
        plan["source"] = "sql"
        plan["analysis"] = False

        # If the question is actually asking for
        # highest/lowest performance, convert it.
        if any(
            phrase in q
            for phrase in [
                "highest marks",
                "highest score",
                "strongest subject",
                "best subject",
                "lowest marks",
                "lowest score",
                "weakest subject",
                "worst subject",
            ]
        ):

            performance = detect_performance_plan(q)

            if performance:

                return performance

        if plan.get(
            "metric"
        ) not in VALID_METRICS:

            plan["metric"] = ""

    # =====================================================
    # ATTENDANCE
    # =====================================================

    elif intent == "attendance":

        plan["source"] = "sql"

        if not plan.get("metric"):
            plan["metric"] = "monthly_attendance"

    # =====================================================
    # ASSIGNMENTS
    # =====================================================

    elif intent == "assignments":

        plan["source"] = "sql"

        if not plan.get("metric"):
            plan["metric"] = "assignment_list"

    # =====================================================
    # TIMETABLE
    # =====================================================

    elif intent == "timetable":

        plan["source"] = "sql"

    # =====================================================
    # TEACHER
    # =====================================================

    elif intent == "teacher":

        plan["source"] = "sql"

    # =====================================================
    # PROFILE
    # =====================================================

    elif intent == "profile":

        plan["source"] = "sql"

    # =====================================================
    # FEES
    # =====================================================

    elif intent == "fees":

        plan["source"] = "sql"

    # =====================================================
    # ANNOUNCEMENT
    # =====================================================

    elif intent == "announcement":

        plan["source"] = "sql"

    # =====================================================
    # SCHOOL POLICY
    # =====================================================

    elif intent == "school_policy":

        plan["source"] = "rag"

    # =====================================================
    # UNKNOWN
    # =====================================================

    elif intent == "unknown":

        plan["source"] = "unknown"

    # =====================================================
    # VALIDATE OPERATION
    # =====================================================

    if (
        plan.get("operation")
        not in VALID_OPERATIONS
    ):

        if plan.get("analysis"):
            plan["operation"] = "analyze"
        else:
            plan["operation"] = "fetch"

    # =====================================================
    # VALIDATE QUERY TYPE
    # =====================================================

    if (
        plan.get("query_type")
        not in VALID_QUERY_TYPES
    ):

        if plan.get("comparison"):
            plan["query_type"] = "comparison"

        elif plan.get("analysis"):
            plan["query_type"] = "analysis"

        else:
            plan["query_type"] = "information"

    # =====================================================
    # VALIDATE SOURCE
    # =====================================================

    if (
        plan.get("source")
        not in VALID_SOURCES
    ):

        if intent == "school_policy":
            plan["source"] = "rag"

        elif intent == "performance":
            plan["source"] = "hybrid"

        else:
            plan["source"] = "sql"

    # =====================================================
    # VALIDATE METRIC
    # =====================================================

    if (
        plan.get("metric")
        not in VALID_METRICS
    ):

        plan["metric"] = ""

    # =====================================================
    # DEFAULT FIELDS
    # =====================================================

    plan.setdefault(
        "constraints",
        {}
    )

    plan.setdefault(
        "context",
        {}
    )

    plan.setdefault(
        "analysis",
        False
    )

    plan.setdefault(
        "comparison",
        False
    )

    plan.setdefault(
        "confidence",
        0.0
    )

    plan.setdefault(
        "reasoning",
        ""
    )

    # =====================================================
    # FORCE ANALYSIS FLAGS
    # =====================================================

    if plan.get("metric") in {
        "trend",
        "highest_score",
        "lowest_score",
        "highest_subject",
        "lowest_subject",
        "exam_comparison",
        "overall_performance",
        "subject_performance",
        "recommendation",
        "best_exam",
        "worst_exam",

        "attendance_trend",
        "attendance_summary",
        "attendance_percentage",
        "attendance_eligibility",
        "absent_days",
        "present_days",
        "late_days",
        "attendance_comparison",
        "subject_attendance",
        "attendance_by_subject",
    }:

        plan["analysis"] = True

    if plan.get(
        "metric"
    ) == "exam_comparison":

        plan["comparison"] = True
        plan["query_type"] = "comparison"
        plan["operation"] = "analyze"
        
    # =====================================================
    # ENFORCE MARKS CONSTRAINTS
    # =====================================================

# Detect latest exam questions
    if plan.get("intent") == "marks":
        q = question.lower().strip()

        latest_keywords = [
            "latest marks",
            "latest mark",
            "latest exam marks",
            "latest exam",
            "most recent marks",
            "most recent mark",
            "most recent exam",
            "recent marks",
            "recent mark",
            "recent exam"
        ]

        if any(keyword in q for keyword in latest_keywords):
            plan["constraints"]["exam"] = "latest"

            print(
                "===== LATEST EXAM DETECTED ====="
            )
            print(
                "Question:",
                question
            )
            print(
                "Constraint:",
                plan["constraints"]["exam"]
            )
            print(
                "================================"
            )

    plan = enforce_marks_constraints(
        question,
        plan
    )
    
    if (plan.get("intent") == "performance" and any(
        phrase in q
        for phrase in [
            "which subject should i improve",
            "which subject needs improvement",
            "what subject should i improve",
            "where am i weak",
            "what should i improve",
            "focus on",
            "which subject should i focus on",
            "subject should i focus on",
            "focus based on my marks"
        ]
    )
):
        plan["metric"] = "lowest_subject"

    # =====================================================
    # FINAL DEBUG
    # =====================================================
    print("\n========== FINAL PLAN ==========")
    print(plan)
    print("Intent:", plan.get("intent"))
    print("Metric:", plan.get("metric"))
    print("Constraints:", plan.get("constraints"))
    print("Context:", plan.get("context"))
    print("Confidence:", plan.get("confidence"))
    print("================================\n")

    return plan


# =========================================================
# OPTIONAL ALIAS
# =========================================================

def planner_validator(
    plan: dict,
    question: str = ""
):

    return validate_plan(
        plan,
        question
    )