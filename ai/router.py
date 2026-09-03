import json
import re
import ollama


ROUTER_MODEL = "llama3:latest"


# =============================================================
# ROUTE BUILDER
# =============================================================

def make_route(
    tool,
    confidence=1.0,
    subject=None,
    exam=None,
    day=None,
    status=None,
    metric=None
):
    return {
        "tool": tool,
        "subject": subject,
        "exam": exam,
        "day": day,
        "status": status,
        "metric": metric,
        "confidence": confidence
    }


# =============================================================
# SUBJECT NORMALIZATION
# =============================================================

def detect_subject(q: str):

    subject_map = {
        "social science": "Social Science",
        "social studies": "Social Science",

        "computer science": "Computer Science",

        "mathematics": "Mathematics",
        "maths": "Mathematics",
        "math": "Mathematics",

        "english": "English",

        "science": "Science",

        "computer": "Computer Science",
        "cs": "Computer Science",
        "sst": "Social Science",
    }

    for keyword in sorted(subject_map, key=len, reverse=True):

        if keyword in q:
            return subject_map[keyword]

    return None


# =============================================================
# RAG / SCHOOL INFORMATION
# =============================================================

def is_rag_question(q: str):
    """
    Detect questions asking about general school/institutional
    information rather than student-specific database data.
    """

    # ---------------------------------------------------------
    # Strong RAG phrases
    # ---------------------------------------------------------

    rag_phrases = [

        # Policies
        "school policy",
        "school policies",
        "school rule",
        "school rules",
        "school regulation",
        "school regulations",

        "attendance policy",
        "attendance policies",
        "attendance rule",
        "attendance rules",
        "attendance requirement",
        "attendance requirements",

        "leave policy",
        "leave policies",
        "leave rule",
        "leave rules",

        "exam policy",
        "exam policies",
        "examination policy",

        "grading policy",
        "grading system",
        "grading rules",

        "discipline policy",
        "discipline rules",

        "uniform policy",
        "uniform rules",

        "fee policy",
        "fee policies",

        "library policy",
        "library rules",

        "transport policy",
        "transport rules",

        # General school information
        "school information",
        "school guidelines",
        "school guideline",
        "school handbook",
        "school timings",
        "school timing",

        "about the school",
        "about school",

        "what are the school",
        "what is the school",

        "how does the school",
        "does the school",

        # Academic/general information
        "how is grading",
        "how are grades calculated",
        "how are marks calculated",
        "minimum attendance",
        "minimum percentage required",
        "percentage required for attendance",

        # FAQs
        "what documents are required",
        "what is required for admission",
        "admission process",
        "admission procedure",
        "school facilities",
        "school holidays",
        "holiday policy",
    ]

    if any(phrase in q for phrase in rag_phrases):
        return True

    return False


# =============================================================
# MAIN ROUTER
# =============================================================

def route_question(question: str) -> dict:

    q = (question or "").lower().strip()

    print("\n========== ROUTER QUESTION ==========")
    print(question)
    print("=====================================")

    # =========================================================
    # RAG / SCHOOL INFORMATION
    #
    # IMPORTANT:
    # This check comes BEFORE attendance/assignment/etc.
    #
    # Example:
    # "What is the school attendance policy?"
    #
    # MUST go to RAG, not attendance_tool.
    # =========================================================

    if is_rag_question(q):

        print("Deterministic route: rag_tool")

        return make_route(
            "rag_tool"
        )
        
        # =========================================================
    # CLASS RANK
    # =========================================================

    class_rank_keywords = [
        "class rank",
        "class ranking",
        "rank in class",
        "rank in my class",
        "my rank",
        "my class rank",
        "child rank",
        "child's rank",
        "child rank in class",
        "child's rank in class",
        "rank of my child",
        "position in class",
        "class position",
        "my position in class",
        "child position in class",
        "child's position in class",
    ]

    if any(keyword in q for keyword in class_rank_keywords):

        print("Deterministic route: marks_tool [class_rank]")

        return make_route(
            "marks_tool",
            metric="class_rank"
        )

    # =========================================================
# ATTENDANCE
# =========================================================

    attendance_keywords = [
    "attendance",
    "attendence",
    "present",
    "absent",
    "absence",
    "attendance percentage",
    "attendance requirement",
    "attendance eligibility",
    "eligible based on attendance",
    "how many days was i absent",
    "how many days was i present",
    ]

# ---------------------------------------------------------
# MONTHLY ATTENDANCE
# ---------------------------------------------------------

    attendance_month_phrases = [
        "this month attendance",
        "my attendance this month",
        "attendance this month",
        "monthly attendance",
        "attendance for this month",
        "how is my attendance this month",
        "what is my attendance this month",
        "what was my attendance this month",
        "how much attendance this month",
    ]

    if any(phrase in q for phrase in attendance_month_phrases):

        print("Deterministic route: attendance_tool [monthly]")

        return make_route(
            "attendance_tool",
            metric="monthly"
        )


# ---------------------------------------------------------
# GENERAL ATTENDANCE
# ---------------------------------------------------------

    if any(keyword in q for keyword in attendance_keywords):

        print("Deterministic route: attendance_tool")

        return make_route(
            "attendance_tool"
        )

    # =========================================================
    # ASSIGNMENTS
    # =========================================================

    assignment_keywords = [
        "assignment",
        "assignments",
        "homework",
        "homeworks",
        "pending assignment",
        "pending assignments",
        "submitted assignment",
        "submitted assignments",
        "submission",
        "submissions",
        "deadline",
        "due date",
        "due assignment",
        "assignment deadline",
        "assignment due",
        "my homework",
        "my assignments",
    ]

    if any(keyword in q for keyword in assignment_keywords):

        print("Deterministic route: assignment_tool")

        return make_route(
            "assignment_tool"
        )

    # =========================================================
    # TIMETABLE
    # =========================================================

    timetable_keywords = [
        "timetable",
        "time table",
        "my schedule",
        "class schedule",
        "class today",
        "classes today",
        "class tomorrow",
        "classes tomorrow",
        "period",
        "periods",
        "when is my class",
        "when is mathematics class",
        "when is maths class",
        "when is science class",
        "when is english class",
    ]

    if any(keyword in q for keyword in timetable_keywords):

        subject = detect_subject(q)

        print("Deterministic route: timetable_tool")

        return make_route(
            "timetable_tool",
            subject=subject
        )

    # =========================================================
    # TEACHER
    # =========================================================

    teacher_keywords = [
        "class teacher",
        "class tutor",
        "homeroom teacher",
        "home room teacher",
        "who is my teacher",
        "who is the teacher",
        "teacher of my class",
        "my class teacher",
    ]

    if any(keyword in q for keyword in teacher_keywords):

        print("Deterministic route: teacher_tool")

        return make_route(
            "teacher_tool"
        )

    # =========================================================
    # PROFILE
    # =========================================================

    profile_keywords = [
        "my profile",
        "student profile",
        "my roll number",
        "roll number",
        "roll no",
        "my admission number",
        "admission number",
        "admission no",
        "date of birth",
        "dob",
        "student name",
        "child name",
        "my name",
    ]

    if any(keyword in q for keyword in profile_keywords):

        print("Deterministic route: profile_tool")

        return make_route(
            "profile_tool"
        )

    # =========================================================
    # MARKS - IMPROVEMENT
    # =========================================================

    improvement_keywords = [
        "did i improve",
        "have i improved",
        "am i improving",
        "my improvement",
        "improvement in my marks",
        "improved my marks",
        "how much did i improve",
        "how much have i improved",
        "compare my marks",
        "compare my results",
        "compare my exams",
        "performance improved",
        "performance improvement",
    ]

    if any(keyword in q for keyword in improvement_keywords):

        print("Deterministic route: marks_tool [improvement]")

        return make_route(
            "marks_tool",
            metric="improvement"
        )

    # =========================================================
    # MARKS - WEAKEST SUBJECT
    # =========================================================

    weakest_keywords = [
        "weakest subject",
        "weak subject",
        "lowest marks",
        "lowest score",
        "lowest scoring subject",
        "subject with lowest marks",
        "subject with the lowest marks",
        "which subject am i weakest in",
        "which subject am i weak in",
    ]

    if any(keyword in q for keyword in weakest_keywords):

        print("Deterministic route: marks_tool [weakest]")

        return make_route(
            "marks_tool",
            metric="weakest"
        )

    # =========================================================
    # MARKS - STRONGEST SUBJECT
    # =========================================================

    strongest_keywords = [
        "strongest subject",
        "best subject",
        "highest marks",
        "highest score",
        "highest scoring subject",
        "subject with highest marks",
        "subject with the highest marks",
    ]

    if any(keyword in q for keyword in strongest_keywords):

        print("Deterministic route: marks_tool [strongest]")

        return make_route(
            "marks_tool",
            metric="strongest"
        )

    # =========================================================
    # MARKS - FOCUS / IMPROVEMENT ADVICE
    # =========================================================

    focus_keywords = [
        "which subject should i focus",
        "which subject should i focus on",
        "what subject should i focus",
        "what subject should i focus on",
        "where should i focus",
        "what should i focus on",
        "subject to focus",
        "subject should i work on",
        "which subject should i work on",
        "which subject should i improve",
        "how to improve my marks",
        "how can i improve my marks",
        "how to improve",
        "how can i improve",
        "what should i improve",
        "where can i improve",
    ]

    if any(keyword in q for keyword in focus_keywords):

        print("Deterministic route: marks_tool [focus]")

        return make_route(
            "marks_tool",
            metric="focus"
        )

    # =========================================================
    # MARKS - SUBJECT FOLLOW-UP
    # =========================================================

    subject = detect_subject(q)

    followup_mark_phrases = [
        "what about",
        "how about",
        "tell me about",
        "and ",
    ]

    if subject and any(
        phrase in q
        for phrase in followup_mark_phrases
    ):

        print(
            f"Deterministic route: marks_tool "
            f"[subject follow-up: {subject}]"
        )

        return make_route(
            "marks_tool",
            subject=subject,
            metric="subject_analysis"
        )

    # =========================================================
    # MARKS / EXAMS
    # =========================================================

    marks_keywords = [
        "my marks",
        "my mark",
        "my score",
        "my scores",
        "my result",
        "my results",
        "my grade",
        "my grades",
        "my exam",
        "my examination",

        "marks",
        "mark",
        "score",
        "scores",
        "result",
        "results",
        "grade",
        "grades",
        "exam",
        "examination",
        "mid term",
        "midterm",
        "final exam",
        "final examination",
        "how did i score",
        "how did i perform",
        "my performance",
    ]

    if any(keyword in q for keyword in marks_keywords):

        print("Deterministic route: marks_tool")

        return make_route(
            "marks_tool",
            subject=subject
        )

    # =========================================================
    # LLM FALLBACK
    # =========================================================

    router_prompt = f"""
You are a strict JSON router for a school assistant.

Choose exactly ONE tool.

AVAILABLE TOOLS:

attendance_tool
assignment_tool
timetable_tool
teacher_tool
profile_tool
marks_tool
rag_tool
general_chat

IMPORTANT ROUTING RULES:

1. STUDENT-SPECIFIC DATA

Questions asking about the student's own records MUST use
the appropriate SQL tool.

Examples:

"My attendance?"
"How many days was I absent?"
"What are my marks?"
"What is my result?"
"When is my maths class?"
"Who is my class teacher?"
"What assignments are pending?"

2. RAG / SCHOOL INFORMATION

Questions asking about school policies, rules, procedures,
guidelines, handbook information, or general school
information MUST use rag_tool.

Examples:

"What is the school attendance policy?"
"What is the minimum attendance requirement?"
"What is the leave policy?"
"What are the school rules?"
"What is the grading policy?"
"What are the school timings?"
"What documents are required for admission?"

IMPORTANT:

"attendance policy" is NOT the student's attendance record.

"What is my attendance?"
    -> attendance_tool

"What is the school attendance policy?"
    -> rag_tool

3. MARKS

Questions about marks, scores, results, exams, performance,
improvement, weakest subjects, strongest subjects, or which
subject to focus on MUST use marks_tool.

4. TIMETABLE

Questions about classes, timetable, schedule, periods, or
when a class occurs MUST use timetable_tool.

5. TEACHER

Questions about the student's class teacher MUST use
teacher_tool.

6. PROFILE

Questions about the student's profile, name, roll number,
admission number, or date of birth MUST use profile_tool.

7. ASSIGNMENTS

Questions about assignments, homework, submissions, or
deadlines MUST use assignment_tool.

8. GENERAL CHAT

Only normal conversational questions that do not require
school data or documents should use general_chat.

Return ONLY valid JSON.

Do not write explanations.
Do not use markdown.
Do not use code fences.

Required JSON:

{{
    "tool": "tool_name",
    "subject": null,
    "exam": null,
    "day": null,
    "status": null,
    "metric": null,
    "confidence": 1.0
}}

Possible metrics:

- improvement
- weakest
- strongest
- focus
- subject_analysis
- null
- class_rank

USER QUESTION:

{question}
"""

    try:

        response = ollama.chat(
            model=ROUTER_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": router_prompt
                }
            ],
            options={
                "temperature": 0
            }
        )

        raw = response["message"]["content"].strip()

        print("\n========== ROUTER RAW RESPONSE ==========")
        print(raw)
        print("==========================================")

        parsed = extract_router_json(raw)

        if parsed is None:

            print("Router returned invalid JSON.")

            fallback = deterministic_fallback(question)

            if fallback:
                return fallback

            return make_route(
                "general_chat",
                confidence=0.0
            )

        # =====================================================
        # VALIDATE TOOL
        # =====================================================

        valid_tools = {
            "attendance_tool",
            "assignment_tool",
            "timetable_tool",
            "teacher_tool",
            "profile_tool",
            "marks_tool",
            "rag_tool",
            "general_chat"
        }

        if parsed.get("tool") not in valid_tools:

            print("Router selected invalid tool.")

            parsed["tool"] = "general_chat"

        # =====================================================
        # NORMALIZE SUBJECT
        # =====================================================

        if parsed.get("subject"):

            normalized_subject = detect_subject(
                str(parsed["subject"]).lower()
            )

            if normalized_subject:
                parsed["subject"] = normalized_subject

        # =====================================================
        # DEFAULT VALUES
        # =====================================================

        parsed.setdefault("subject", None)
        parsed.setdefault("exam", None)
        parsed.setdefault("day", None)
        parsed.setdefault("status", None)
        parsed.setdefault("metric", None)
        parsed.setdefault("confidence", 0.0)

        return parsed

    except Exception as e:

        print("Router error:", e)

        fallback = deterministic_fallback(question)

        if fallback:
            return fallback

        return make_route(
            "general_chat",
            confidence=0.0
        )


# =============================================================
# JSON EXTRACTION
# =============================================================

def extract_router_json(raw_response: str):

    if not raw_response:
        return None

    raw_response = raw_response.strip()

    # ---------------------------------------------------------
    # DIRECT JSON
    # ---------------------------------------------------------

    try:

        data = json.loads(raw_response)

        if isinstance(data, dict) and "tool" in data:
            return data

    except (json.JSONDecodeError, TypeError):

        pass

    # ---------------------------------------------------------
    # REMOVE MARKDOWN CODE FENCES
    # ---------------------------------------------------------

    cleaned = re.sub(
        r"```(?:json)?",
        "",
        raw_response,
        flags=re.IGNORECASE
    )

    cleaned = cleaned.replace("```", "").strip()

    try:

        data = json.loads(cleaned)

        if isinstance(data, dict) and "tool" in data:
            return data

    except (json.JSONDecodeError, TypeError):

        pass

    # ---------------------------------------------------------
    # FIND JSON OBJECT INSIDE RESPONSE
    # ---------------------------------------------------------

    match = re.search(
        r"\{[\s\S]*\}",
        cleaned
    )

    if match:

        try:

            data = json.loads(match.group(0))

            if isinstance(data, dict) and "tool" in data:
                return data

        except json.JSONDecodeError:

            pass

    return None


# =============================================================
# DETERMINISTIC FALLBACK
# =============================================================

def deterministic_fallback(question: str):

    q = (question or "").lower().strip()

    # =========================================================
    # RAG
    # =========================================================

    if is_rag_question(q):

        return make_route(
            "rag_tool"
        )
        
        
    # =========================================================
    # CLASS RANK
    # =========================================================

    class_rank_keywords = [
        "class rank",
        "class ranking",
        "rank in class",
        "rank in my class",
        "my rank",
        "my class rank",
        "child rank",
        "child's rank",
        "child rank in class",
        "child's rank in class",
        "rank of my child",
        "position in class",
        "class position",
        "my position in class",
        "child position in class",
        "child's position in class",
    ]

    if any(keyword in q for keyword in class_rank_keywords):

        print("Deterministic route: marks_tool [class_rank]")

        return make_route(
            "marks_tool",
            metric="class_rank"
        )

    # =========================================================
    # ATTENDANCE
    # =========================================================

    if any(
        keyword in q
        for keyword in [
            "my attendance",
            "attendance percentage",
            "attendance record",
            "attendance status",
            "absent",
            "absence",
            "present",
            "check my attendance",
            "show my attendance",
            "tell me my attendance"
        ]
    ) or q == "attendance":

        return make_route(
            "attendance_tool"
        )

    # =========================================================
    # ASSIGNMENTS
    # =========================================================

    if any(
        keyword in q
        for keyword in [
            "assignment",
            "assignments",
            "homework",
            "pending assignment",
            "submission",
            "deadline",
            "due date"
        ]
    ):

        return make_route(
            "assignment_tool"
        )

    # =========================================================
    # TIMETABLE
    # =========================================================

    if any(
        keyword in q
        for keyword in [
            "timetable",
            "time table",
            "schedule",
            "class today",
            "classes today",
            "class tomorrow",
            "classes tomorrow",
            "period",
            "periods"
        ]
    ):

        return make_route(
            "timetable_tool",
            subject=detect_subject(q)
        )

    # =========================================================
    # TEACHER
    # =========================================================

    if any(
        keyword in q
        for keyword in [
            "class teacher",
            "class tutor",
            "homeroom teacher",
            "home room teacher",
            "who is my teacher",
            "teacher of my class",
            "my class teacher"
        ]
    ):

        return make_route(
            "teacher_tool"
        )

    # =========================================================
    # PROFILE
    # =========================================================

    if any(
        keyword in q
        for keyword in [
            "my profile",
            "student profile",
            "roll number",
            "roll no",
            "admission number",
            "admission no",
            "date of birth",
            "dob",
            "student name",
            "child name",
            "my name"
        ]
    ):

        return make_route(
            "profile_tool"
        )

    # =========================================================
    # IMPROVEMENT
    # =========================================================

    if any(
        keyword in q
        for keyword in [
            "did i improve",
            "have i improved",
            "am i improving",
            "compare my marks",
            "compare my results",
            "how much did i improve",
            "improvement"
        ]
    ):

        return make_route(
            "marks_tool",
            metric="improvement"
        )

    # =========================================================
    # WEAKEST
    # =========================================================

    if any(
        keyword in q
        for keyword in [
            "weakest subject",
            "weak subject",
            "lowest marks",
            "lowest score"
        ]
    ):

        return make_route(
            "marks_tool",
            metric="weakest"
        )

    # =========================================================
    # STRONGEST
    # =========================================================

    if any(
        keyword in q
        for keyword in [
            "strongest subject",
            "best subject",
            "highest marks",
            "highest score"
        ]
    ):

        return make_route(
            "marks_tool",
            metric="strongest"
        )

    # =========================================================
    # FOCUS
    # =========================================================

    if any(
        keyword in q
        for keyword in [
            "how to improve",
            "how can i improve",
            "improve my marks",
            "which subject should i focus",
            "what should i improve",
            "where should i focus"
        ]
    ):

        return make_route(
            "marks_tool",
            metric="focus"
        )

    # =========================================================
    # SUBJECT FOLLOW-UP
    # =========================================================

    subject = detect_subject(q)

    if subject and any(
        phrase in q
        for phrase in [
            "what about",
            "how about",
            "tell me about",
            "and "
        ]
    ):

        return make_route(
            "marks_tool",
            subject=subject,
            metric="subject_analysis"
        )

    # =========================================================
    # MARKS
    # =========================================================

    if any(
        keyword in q
        for keyword in [
            "marks",
            "mark",
            "score",
            "scores",
            "result",
            "results",
            "grade",
            "grades",
            "exam",
            "examination"
        ]
    ):

        return make_route(
            "marks_tool",
            subject=subject
        )

    return None