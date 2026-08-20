# ai/planner.py

import json
import re
import ollama

from ai.semantic_router import semantic_route


MODEL = "llama3:latest"


# =========================================================
# CLEAN JSON
# =========================================================

def _extract_json(text: str):

    text = text.strip()

    # Remove markdown fences
    text = re.sub(
        r"```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"```\s*$",
        "",
        text
    )

    # Find JSON object
    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL
    )

    if not match:
        raise ValueError(
            "Planner did not return valid JSON."
        )

    return json.loads(
        match.group(0)
    )


# =========================================================
# PLAN QUERY
# =========================================================

def plan_query(question: str):

    # -----------------------------------------------------
    # STEP 1
    # Embedding-based semantic routing
    # -----------------------------------------------------

    semantic = semantic_route(
        question
    )

    print(
        "\n===== SEMANTIC ROUTER ====="
    )

    print(
        semantic
    )

    print(
        "===========================\n"
    )

    # -----------------------------------------------------
    # STEP 2
    # LLM semantic understanding
    # -----------------------------------------------------

    prompt = f"""
You are the semantic router for a multilingual school chatbot.

The chatbot has two main data sources:

1. SQL
   PostgreSQL contains personalized structured data:
   - student marks
   - exam results
   - attendance
   - assignments
   - timetable
   - teachers
   - student profile
   - class information

2. RAG
   ChromaDB contains school documents:
   - school policies
   - exam rules
   - exam schedules
   - assignment guidelines
   - attendance rules
   - school information
   - academic guidelines

3. HYBRID
   Use hybrid when the question needs BOTH:
   - personalized database information
   - school document/policy information

IMPORTANT:
Do NOT classify based only on exact keywords.
Understand the meaning of the question.

SEMANTIC ROUTER HINT:

{json.dumps(semantic, indent=2)}

USER QUESTION:

{question}

---------------------------------------------------------
INTENTS
---------------------------------------------------------

marks:
Questions asking for actual marks, scores, results or grades.

performance:
Questions analyzing academic performance.

attendance:
Questions asking about the student's attendance.

assignments:
Questions asking about the student's assignments/homework.

timetable:
Questions asking about the student's classes/schedule.

teacher:
Questions about teachers.

profile:
Questions about the student's own profile.

class:
Questions about the student's class/section.

rag:
General school/document/policy/instruction questions.

---------------------------------------------------------
METRICS
---------------------------------------------------------

Use metric only when applicable.

Possible metrics:

highest_subject
lowest_subject
highest_score
lowest_score
trend
exam_comparison
none

Examples:

"Which is my strongest subject?"
→ intent = performance
→ metric = highest_subject
→ source = sql

"What is my weakest subject?"
→ intent = performance
→ metric = lowest_subject
→ source = sql

"What is my highest score?"
→ intent = performance
→ metric = highest_score
→ source = sql

"Am I improving?"
→ intent = performance
→ metric = trend
→ source = sql

"Compare my mid term and final exams."
→ intent = performance
→ metric = exam_comparison
→ source = sql

---------------------------------------------------------
SOURCE RULES
---------------------------------------------------------

Use SQL for personalized data.

Use RAG for school/document knowledge.

Examples:

"What is my attendance?"
→ SQL

"What is the minimum attendance required?"
→ RAG

"Show my assignments."
→ SQL

"How should assignments be submitted?"
→ RAG

"Show my timetable."
→ SQL

"What are the school timetable rules?"
→ RAG

"When are the exams?"
→ RAG

"What did I score in mathematics?"
→ SQL

"Is my attendance below the school's required minimum?"
→ HYBRID

"Which assignment is due and what is the submission policy?"
→ HYBRID

---------------------------------------------------------
IMPORTANT
---------------------------------------------------------

A question containing words like:

exam
score
result
attendance
assignment
class
schedule

does NOT automatically mean SQL.

Understand what the user actually wants.

---------------------------------------------------------
OUTPUT
---------------------------------------------------------

Return ONLY JSON.

Schema:

{{
    "intent": "...",
    "source": "sql|rag|hybrid",
    "metric": "highest_subject|lowest_subject|highest_score|lowest_score|trend|exam_comparison|none",
    "subject": null,
    "exam": null,
    "day": null,
    "confidence": 0.0,
    "reason": "short explanation"
}}

Do not return markdown.
Do not return extra text.
"""

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        format="json"
    )

    content = response["message"]["content"]

    plan = _extract_json(
        content
    )

    # -----------------------------------------------------
    # Defaults
    # -----------------------------------------------------

    plan.setdefault(
        "intent",
        semantic["intent"]
    )

    plan.setdefault(
        "source",
        "sql"
    )

    plan.setdefault(
        "metric",
        "none"
    )

    plan.setdefault(
        "subject",
        None
    )

    plan.setdefault(
        "exam",
        None
    )

    plan.setdefault(
        "day",
        None
    )

    plan.setdefault(
        "confidence",
        0.5
    )

    plan.setdefault(
        "reason",
        ""
    )

    # -----------------------------------------------------
    # Normalize
    # -----------------------------------------------------

    plan["intent"] = str(
        plan["intent"]
    ).lower().strip()

    plan["source"] = str(
        plan["source"]
    ).lower().strip()

    plan["metric"] = str(
        plan["metric"]
    ).lower().strip()
    
    # -----------------------------------------------------
    # POLICY / GENERAL SCHOOL KNOWLEDGE OVERRIDE
    # -----------------------------------------------------
#
# IMPORTANT:
# "what is school attendance policy"
# is NOT the student's attendance.
#
# It must go to RAG.
#
# Examples:
#   what is school attendance policy -> RAG
#   what are attendance rules -> RAG
#   what is minimum attendance required -> RAG
#
# But:
#   what is my attendance -> SQL
#   what is my attendance percentage -> SQL
# -----------------------------------------------------

    question_lower = question.lower().strip()

    policy_phrases = [
    "attendance policy",
    "attendance rule",
    "attendance rules",
    "attendance requirement",
    "attendance requirements",
    "minimum attendance",
    "required attendance",
    "school attendance",
    "attendance guidelines",

    "exam policy",
    "exam rules",
    "exam guidelines",
    "examination policy",
    "examination rules",

    "assignment policy",
    "assignment rules",
    "assignment guidelines",

    "school policy",
    "school policies",
    "school rules",
    "school guidelines",

    "submission policy",
    "submission rules",
    "submission guidelines"
    ]

    personal_attendance_phrases = [
    "my attendance",
    "my attendance record",
    "my attendance records",
    "my attendance percentage",
    "my attendance status",
    "my present days",
    "my absent days",
    "how many days was i present",
    "how many days was i absent"
    ]

    is_policy_query = any(
    phrase in question_lower
    for phrase in policy_phrases
    )

    is_personal_attendance_query = any(
    phrase in question_lower
    for phrase in personal_attendance_phrases
    )

    if (
    is_policy_query
    and not is_personal_attendance_query
    ):

        print(
            "\n===== POLICY OVERRIDE ====="
        )

        print(
            "Policy/general school knowledge detected."
        )

        print(
            "Original planner intent:",
            plan["intent"]
        )

        print(
            "Original planner source:",
            plan["source"]
        )

        plan["intent"] = "rag"
        plan["source"] = "rag"
        plan["metric"] = "none"

        print(
            "Forced intent: rag"
        )

        print(
            "Forced source: rag"
        )

        print(
            "============================"
        )

    # -----------------------------------------------------
    # DETECT LATEST / PREVIOUS EXAM
    # -----------------------------------------------------

    question_lower = question.lower()

    if (
        "latest" in question_lower
        or "most recent" in question_lower
        or "recent exam" in question_lower
    ):
        plan["exam"] = "latest"

    elif (
        "previous" in question_lower
        or "last exam" in question_lower
    ):
        plan["exam"] = "previous"

    try:
        plan["confidence"] = float(
            plan["confidence"]
        )
    except Exception:
        plan["confidence"] = 0.5

    return plan