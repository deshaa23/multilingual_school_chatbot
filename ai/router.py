import json
import re

from langchain_ollama import ChatOllama


llm = ChatOllama(
    model="llama3:latest",
    temperature=0
)


TOOL_ROUTER_PROMPT = """
You are an intent router for a school chatbot.

Choose exactly ONE tool based on what the student wants.

============================================================
PERSONAL DATA VS SCHOOL KNOWLEDGE
============================================================

If the question asks about the logged-in student's personal
academic information, use a database tool.

Personal/student data:
- marks
- performance
- attendance
- timetable
- assignments
- teacher information
- profile information

If the question asks about general school information or
information contained in school documents, use rag_tool.

Never use rag_tool to retrieve personal student data.
Never use SQL tools to answer school-policy/document questions.

TOOLS:

1. marks_tool
Use for retrieving marks/scores/results.

2. performance_tool

Use for analysis, comparison, improvement, strongest/weakest subject,
overall performance, average performance, or recommendations based on marks.

Examples:

"What is my overall performance?"
→ metric = "overall"

"What is my average?"
→ metric = "average"

"Which subject am I strongest in?"
→ metric = "highest"

"Which subject am I weakest in?"
→ metric = "lowest"

"Which subject should I improve?"
→ metric = "lowest"

"How can I improve my performance?"
→ metric = "improvement"

"Am I performing well?"
→ metric = "overall"

If no specific metric is requested:
→ metric = "overall"

3. attendance_tool
Use for attendance, presence, absence, attendance percentage,
attendance records, or attendance eligibility.

IMPORTANT:
Questions about attendance eligibility must use attendance_tool.

4. timetable_tool
Use for timetable, classes, periods, schedule, today's classes,
or a particular day's classes.

5. assignment_tool
Use for assignments, homework, pending work, upcoming work,
deadlines, or overdue assignments.

6. teacher_tool
Use for teacher information.

7. profile_tool
Use for student profile, roll number, admission number,
date of birth, or student information.

8. rag_tool

Use for information that must be answered from the school's
knowledge base, school documents, policies, rules, notices,
academic material, curriculum information, or other stored
school information.

Examples:

"What are the school uniform rules?"
→ rag_tool

"What are the rules for grades VI-X?"
→ rag_tool

"What is the school policy on attendance?"
→ rag_tool

"What is the admission procedure?"
→ rag_tool

"What are Newton's laws of motion?"
→ rag_tool

IMPORTANT:
If the question asks for the student's OWN data, never use rag_tool.

"My marks in Mathematics"
→ marks_tool

"My attendance"
→ attendance_tool

"My timetable"
→ timetable_tool

"My assignments"
→ assignment_tool

9. general_chat
Use for greetings, casual conversation, jokes, or unrelated questions.

============================================================
PARAMETER EXTRACTION
============================================================

For timetable questions:

Extract the requested day if explicitly mentioned.

Valid days:
- Monday
- Tuesday
- Wednesday
- Thursday
- Friday
- Saturday
- Sunday

Examples:

"What classes do I have on Monday?"
→ day = "Monday"

"Show Tuesday's timetable"
→ day = "Tuesday"

"What is my timetable?"
→ day = null

"What classes do I have today?"
→ day = "today"

If no specific day is mentioned:
→ day = null

For assignment questions:

Use status:

"pending", "upcoming", "due", "not completed"
→ status = "pending"

"overdue", "late"
→ status = "overdue"

Otherwise:
→ status = null

For marks questions:

Extract subject if explicitly mentioned.

Examples:
"What are my Mathematics marks?"
→ subject = "Mathematics"

"What did I score in Science?"
→ subject = "Science"

Otherwise:
→ subject = null

Extract exam if explicitly mentioned.

Examples:
"My final marks"
→ exam = "Final"

"My mid term marks"
→ exam = "Mid Term"

Otherwise:
→ exam = null

For attendance questions:

Extract metric when the user explicitly asks for a specific attendance-related value.

"What is my attendance percentage?"
→ metric = "attendance_percentage"

"What percentage of classes have I attended?"
→ metric = "attendance_percentage"

"How much attendance do I have?"
→ metric = "attendance_percentage"

"How many days was I absent?"
→ metric = "absent"

"How many classes did I miss?"
→ metric = "absent"

"Am I eligible based on my attendance?"
→ metric = "eligibility"

"Do I meet the attendance requirement?"
→ metric = "eligibility"

Otherwise:
→ metric = null

============================================================
IMPORTANT
============================================================

Do NOT answer the question.

Do NOT generate SQL.

Return ONLY valid JSON.

Return exactly this structure:

{{
    "tool": "tool_name",
    "subject": null,
    "exam": null,
    "day": null,
    "status": null,
    "metric": null,
    "confidence": 0.0
}}

User question:
{question}
"""


VALID_TOOLS = {
    "marks_tool",
    "attendance_tool",
    "performance_tool",
    "timetable_tool",
    "assignment_tool",
    "teacher_tool",
    "profile_tool",
    "rag_tool",
    "general_chat"
}


VALID_METRICS = {
    None,
    "highest",
    "lowest",
    "attendance_percentage",
    "absent",
    "eligibility",
    "overall",
    "average",
    "improvement"
}


VALID_DAYS = {
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "today"
}


VALID_STATUSES = {
    None,
    "pending",
    "overdue"
}


def route_query(question: str) -> dict:

    prompt = TOOL_ROUTER_PROMPT.format(
        question=question
    )

    response = llm.invoke(prompt)

    content = response.content.strip()

    print("\n========== ROUTER RAW RESPONSE ==========")
    print(content)
    print("==========================================")

    # --------------------------------------------------
    # Clean markdown code fences
    # --------------------------------------------------

    content = re.sub(
        r"```(?:json)?",
        "",
        content,
        flags=re.IGNORECASE
    ).strip()

    # --------------------------------------------------
    # Extract JSON object from LLM response
    # --------------------------------------------------

    match = re.search(
        r"\{[\s\S]*\}",
        content
    )

    if not match:

        print("Router returned invalid JSON.")

        return {
            "tool": "general_chat",
            "subject": None,
            "exam": None,
            "day": None,
            "status": None,
            "metric": None,
            "confidence": 0.0
        }

    json_text = match.group(0)

    try:
        result = json.loads(json_text)

    except json.JSONDecodeError as e:

        print("JSON parsing error:", e)
        print("Extracted JSON:", json_text)

        return {
            "tool": "general_chat",
            "subject": None,
            "exam": None,
            "day": None,
            "status": None,
            "metric": None,
            "confidence": 0.0
        }

    # --------------------------------------------------
    # Extract fields
    # --------------------------------------------------

    tool = result.get("tool")
    subject = result.get("subject")
    exam = result.get("exam")
    day = result.get("day")
    status = result.get("status")
    metric = result.get("metric")

    # --------------------------------------------------
    # Validate tool
    # --------------------------------------------------

    if tool not in VALID_TOOLS:

        tool = "general_chat"

        subject = None
        exam = None
        day = None
        status = None
        metric = None

        confidence = 0.0

    else:

        # Validate metric
        if metric not in VALID_METRICS:
            metric = None

        confidence = 1.0

    # --------------------------------------------------
    # Final result
    # --------------------------------------------------

    final_result = {
        "tool": tool,
        "subject": subject,
        "exam": exam,
        "day": day,
        "status": status,
        "metric": metric,
        "confidence": confidence
    }

    print("\n========== ROUTER RESULT ==========")
    print(final_result)
    print("===================================")

    return final_result