from ai.tools.tool_executor import execute_tool
from rag.rag_pipeline import rag_answer
from ai.router import route_question


def process_query(
    question: str,
    student_id: int,
    language: str = "ENGLISH",
    original_question: str = None
):
    """
    Main chatbot pipeline.

    Flow:

        User Question
              ↓
           Router
              ↓
       ┌──────┴──────┐
       ↓             ↓
    SQL Tools      RAG Tool
       ↓             ↓
    Database      Chroma
       ↓             ↓
       └──────┬──────┘
              ↓
          Tool Result
    """

    if original_question is None:
        original_question = question

    # ==========================================
    # 1. ROUTE THE QUESTION
    # ==========================================

    route = route_question(question)

    tool_name = route["tool"]

    print("\n========== ROUTING ==========")
    print(f"Question  : {question}")
    print(f"Tool      : {tool_name}")
    print(f"Metric    : {route.get('metric')}")
    print(f"Subject   : {route.get('subject')}")
    print(f"Exam      : {route.get('exam')}")
    print(f"Day       : {route.get('day')}")
    print(f"Status    : {route.get('status')}")
    print(f"Confidence: {route.get('confidence')}")
    print("=============================")

    # ==========================================
    # 2. GENERAL CHAT
    # ==========================================

    if tool_name == "general_chat":

        return {
            "type": "general_chat",
            "success": True,
            "message": "General chat"
        }

    # ==========================================
    # 3. RAG
    # ==========================================

    if tool_name == "rag_tool":

        print("\n========== RAG TOOL ==========")
        print("English Question :", question)
        print("Original Question:", original_question)
        print("Language         :", language)
        print("==============================")

        answer = rag_answer(
            english_question=question,
            original_question=question,
            language="ENGLISH"
        )

        return {
            "type": "rag",
            "success": True,
            "answer": answer
        }

    # ==========================================
    # 4. SQL / DATABASE TOOLS
    # ==========================================

    print("\n========== SQL TOOL ==========")
    print("Tool:", tool_name)
    print("==============================")

    result = execute_tool(
        tool_name=tool_name,
        student_id=student_id,
        subject=route.get("subject"),
        exam=route.get("exam"),
        day=route.get("day"),
        status=route.get("status"),
        metric=route.get("metric")
    )

    return result

import json
import re


def extract_router_json(raw_response: str, question: str = ""):

    if not raw_response:
        return None

    raw_response = raw_response.strip()

    # =========================================================
    # 1. DIRECT JSON
    # =========================================================

    try:
        data = json.loads(raw_response)

        if isinstance(data, dict) and "tool" in data:
            return data

    except (json.JSONDecodeError, TypeError):
        pass

    # =========================================================
    # 2. REMOVE MARKDOWN CODE FENCES
    # =========================================================

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

    # =========================================================
    # 3. FIND JSON OBJECT INSIDE RESPONSE
    # =========================================================

    match = re.search(
        r"\{[\s\S]*?\}",
        cleaned
    )

    if match:

        try:

            data = json.loads(match.group(0))

            if isinstance(data, dict) and "tool" in data:
                return data

        except json.JSONDecodeError:
            pass

    # =========================================================
    # 4. DETERMINISTIC FALLBACK
    # =========================================================
    # If LLM ignores JSON completely, identify the tool
    # directly from the user's question.
    # =========================================================

    q = (question or "").lower().strip()

    # ---------------------------------------------------------
    # ASSIGNMENTS
    # ---------------------------------------------------------

    assignment_keywords = [
        "assignment",
        "assignments",
        "homework",
        "homeworks",
        "task",
        "tasks",
        "due assignment",
        "assignment deadline",
        "assignment due"
    ]

    if any(keyword in q for keyword in assignment_keywords):

        return {
            "tool": "assignment_tool",
            "subject": None,
            "exam": None,
            "day": None,
            "status": None,
            "metric": None,
            "confidence": 1.0
        }

    # ---------------------------------------------------------
    # ATTENDANCE
    # ---------------------------------------------------------

    attendance_keywords = [
        "attendance",
        "attendence",
        "absent",
        "absence",
        "present",
        "attendance percentage"
    ]

    if any(keyword in q for keyword in attendance_keywords):

        return {
            "tool": "attendance_tool",
            "subject": None,
            "exam": None,
            "day": None,
            "status": None,
            "metric": None,
            "confidence": 1.0
        }

    # ---------------------------------------------------------
    # TIMETABLE
    # ---------------------------------------------------------

    timetable_keywords = [
        "timetable",
        "time table",
        "schedule",
        "class schedule",
        "classes today",
        "classes tomorrow"
    ]

    if any(keyword in q for keyword in timetable_keywords):

        return {
            "tool": "timetable_tool",
            "subject": None,
            "exam": None,
            "day": None,
            "status": None,
            "metric": None,
            "confidence": 1.0
        }

    # ---------------------------------------------------------
    # MARKS
    # ---------------------------------------------------------

    marks_keywords = [
        "marks",
        "mark",
        "score",
        "scores",
        "grade",
        "grades",
        "result",
        "results",
        "percentage",
        "how did i score"
    ]

    if any(keyword in q for keyword in marks_keywords):

        return {
            "tool": "marks_tool",
            "subject": None,
            "exam": None,
            "day": None,
            "status": None,
            "metric": None,
            "confidence": 1.0
        }

    # ---------------------------------------------------------
    # PROFILE
    # ---------------------------------------------------------

    profile_keywords = [
        "my name",
        "student name",
        "child name",
        "roll number",
        "roll no",
        "admission number",
        "admission no",
        "date of birth",
        "dob",
        "profile"
    ]

    if any(keyword in q for keyword in profile_keywords):

        return {
            "tool": "profile_tool",
            "subject": None,
            "exam": None,
            "day": None,
            "status": None,
            "metric": None,
            "confidence": 1.0
        }

    # =========================================================
    # NO MATCH
    # =========================================================

    print("Router returned invalid JSON.")
    print("RAW ROUTER RESPONSE:")
    print(raw_response)

    return None