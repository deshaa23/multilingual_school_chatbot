import json
import re

from langchain_ollama import ChatOllama


# Local LLM
llm = ChatOllama(
    model="llama3:latest",
    temperature=0
)


TOOL_ROUTER_PROMPT = """
You are an intent router for a school chatbot.

Choose the tool based on what the user wants to DO with their academic data.

TOOLS:

1. marks_tool

Use marks_tool when the user wants to RETRIEVE or VIEW their marks.

Examples:
- What are my marks?
- Show me my marks
- What did I score?
- Give me my marks
- Show my exam results
- What are my scores in Mathematics?
- How many marks did I get in Science?

Do NOT use marks_tool when the user asks for analysis, comparison,
improvement, ranking, recommendation, or advice based on marks.

2. performance_tool

Use performance_tool when the user wants ANALYSIS, COMPARISON,
INSIGHT, RANKING, or RECOMMENDATION based on academic performance.

Examples:
- How much did I improve?
- Did I improve from mid term to final?
- Which subject improved the most?
- Which subject is my strongest?
- Which subject is my weakest?
- Which subject should I focus on?
- Which subject needs more attention?
- Where am I performing poorly?
- What should I improve?
- Which subject am I best at?
- Which subject am I worst at?
- Compare my mid term and final marks.
- Am I doing better in finals?
- What are my strengths?
- What are my weaknesses?
- Based on my marks, what should I focus on?

IMPORTANT:

If the user asks for a recommendation, advice, comparison,
improvement, strength, weakness, ranking, or analysis,
use performance_tool even if the question contains words such as
"marks", "score", or "results".

3. attendance_tool

Use attendance_tool when the user asks about attendance,
presence, absence, attendance percentage, or attendance records.

Examples:
- What is my attendance?
- What is my attendance percentage?
- How many days was I absent?
- How many classes did I attend?
- Show my attendance.

4. timetable_tool

Use timetable_tool when the user asks about classes,
periods, schedule, timetable, or today's classes.

Examples:
- Show my timetable.
- What is my timetable?
- What classes do I have today?
- What is my schedule?
- What class do I have on Monday?
- Show Monday's timetable.
- What is my first period?
- What classes do I have tomorrow?

For timetable_tool, determine the day:

- Use the day name when the user specifies a day.
- Use null when the user asks for the complete timetable.

5. assignment_tool

Use assignment_tool when the user asks about assignments,
homework, pending work, or assignment deadlines.

Examples:
- Show my assignments.
- What assignments do I have?
- What homework do I have?
- Show my homework.
- What assignments are due?
- Which assignments are pending?
- Do I have any assignments?
- Show my upcoming assignments.
- What assignments are overdue?

For assignment_tool, determine the status:

- "pending" for pending/upcoming assignments.
- "overdue" for assignments whose due date has passed.
- null when the user simply wants to see assignments.

6. teacher_tool
   Use for:
   - class teacher
   - subject teacher
   - teacher information

7. profile_tool
   Use for:
   - profile
   - roll number
   - admission number
   - date of birth
   - student information

8. rag_tool
   Use for:
   - school-related informational questions
   - academic concepts
   - questions requiring information from the school knowledge base

9. general_chat
   Use for:
   - greetings
   - casual conversation
   - jokes
   - general conversation
   - questions unrelated to school data

Rules:

- Return ONLY valid JSON.
- Do not explain your decision.
- Select exactly ONE tool.
- Do not generate SQL.
- Do not answer the user's question.

Return exactly:

{{
    "tool": "tool_name",
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
    "lowest"
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

    # Remove markdown code fences if the LLM adds them
    content = re.sub(
        r"```json\s*|\s*```",
        "",
        content,
        flags=re.IGNORECASE
    ).strip()

    try:
        result = json.loads(content)

    except json.JSONDecodeError:

        print("Router returned invalid JSON.")

        return {
            "tool": "general_chat",
            "metric": None,
            "confidence": 0.0
        }

    tool = result.get("tool")
    metric = result.get("metric")

    # Validate selected tool
    if tool not in VALID_TOOLS:
        tool = "general_chat"
        metric = None
        confidence = 0.0

    else:
        # Validate metric
        if metric not in VALID_METRICS:
            metric = None

        # We don't depend on unreliable LLM confidence
        confidence = 1.0

    final_result = {
        "tool": tool,
        "metric": metric,
        "confidence": confidence
    }

    print("\n========== ROUTER RESULT ==========")
    print(final_result)
    print("===================================")

    return final_result