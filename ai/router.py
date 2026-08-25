import json
import re
import ollama


ROUTER_MODEL = "llama3:latest"


def make_route(tool, confidence=1.0):
    return {
        "tool": tool,
        "subject": None,
        "exam": None,
        "day": None,
        "status": None,
        "metric": None,
        "confidence": confidence
    }


def route_question(question: str) -> dict:
    """
    Route the user's question to the correct school-data tool.

    Deterministic routing is used for obvious questions.
    LLM routing is used only when necessary.
    """

    q = question.lower().strip()

    print("\n========== ROUTER QUESTION ==========")
    print(question)
    print("=====================================")

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
    ]

    if any(keyword in q for keyword in attendance_keywords):
        print("Deterministic route: attendance_tool")
        return make_route("attendance_tool")

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
    ]

    if any(keyword in q for keyword in assignment_keywords):
        print("Deterministic route: assignment_tool")
        return make_route("assignment_tool")

    # =========================================================
    # TIMETABLE
    # =========================================================

    timetable_keywords = [
        "timetable",
        "time table",
        "schedule",
        "class schedule",
        "class today",
        "classes today",
        "class tomorrow",
        "classes tomorrow",
        "period",
        "periods",
    ]

    if any(keyword in q for keyword in timetable_keywords):
        print("Deterministic route: timetable_tool")
        return make_route("timetable_tool")

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
        return make_route("teacher_tool")

    # =========================================================
    # PROFILE
    # =========================================================

    profile_keywords = [
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
        "my name",
    ]

    if any(keyword in q for keyword in profile_keywords):
        print("Deterministic route: profile_tool")
        return make_route("profile_tool")

    # =========================================================
    # MARKS / EXAMS
    # =========================================================

    marks_keywords = [
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
        "highest marks",
        "lowest marks",
        "strongest subject",
        "weakest subject",
        "how did i score",
    ]

    if any(keyword in q for keyword in marks_keywords):
        print("Deterministic route: marks_tool")
        return make_route("marks_tool")

    # =========================================================
    # LLM FALLBACK
    # =========================================================

    router_prompt = f"""
You are a strict JSON router for a school assistant.

Choose exactly ONE tool from this list:

attendance_tool
assignment_tool
timetable_tool
teacher_tool
profile_tool
marks_tool
general_chat

Return ONLY valid JSON.

Do not write explanations.
Do not use markdown.
Do not use code fences.

Required format:

{{
    "tool": "tool_name",
    "subject": null,
    "exam": null,
    "day": null,
    "status": null,
    "metric": null,
    "confidence": 1.0
}}

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

        # =====================================================
        # EXTRACT JSON
        # =====================================================

        parsed = extract_router_json(raw)

        if parsed is None:

            print("Router returned invalid JSON.")

            # Final deterministic fallback
            fallback = deterministic_fallback(question)

            if fallback:
                return fallback

            return make_route("general_chat", 0.0)

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
            "general_chat"
        }

        if parsed.get("tool") not in valid_tools:

            print("Router selected invalid tool.")

            parsed["tool"] = "general_chat"

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

        return make_route("general_chat", 0.0)


# =============================================================
# JSON EXTRACTION
# =============================================================

def extract_router_json(raw_response: str):

    if not raw_response:
        return None

    raw_response = raw_response.strip()

    # ---------------------------------------------------------
    # 1. Direct JSON
    # ---------------------------------------------------------

    try:

        data = json.loads(raw_response)

        if isinstance(data, dict) and "tool" in data:
            return data

    except (json.JSONDecodeError, TypeError):
        pass

    # ---------------------------------------------------------
    # 2. Remove markdown fences
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
    # 3. Find JSON object inside text
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

    # ---------------------------------------------------------
    # ASSIGNMENTS
    # ---------------------------------------------------------

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
    ]

    if any(keyword in q for keyword in assignment_keywords):

        print("Fallback route: assignment_tool")

        return make_route("assignment_tool")

    # ---------------------------------------------------------
    # ATTENDANCE
    # ---------------------------------------------------------

    attendance_keywords = [
        "attendance",
        "attendence",
        "absent",
        "absence",
        "present",
        "attendance percentage",
    ]

    if any(keyword in q for keyword in attendance_keywords):

        print("Fallback route: attendance_tool")

        return make_route("attendance_tool")

    # ---------------------------------------------------------
    # TIMETABLE
    # ---------------------------------------------------------

    timetable_keywords = [
        "timetable",
        "time table",
        "schedule",
        "class schedule",
        "classes today",
        "classes tomorrow",
    ]

    if any(keyword in q for keyword in timetable_keywords):

        print("Fallback route: timetable_tool")

        return make_route("timetable_tool")

    # ---------------------------------------------------------
    # TEACHER
    # ---------------------------------------------------------

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

        print("Fallback route: teacher_tool")

        return make_route("teacher_tool")

    # ---------------------------------------------------------
    # PROFILE
    # ---------------------------------------------------------

    profile_keywords = [
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
        "my name",
    ]

    if any(keyword in q for keyword in profile_keywords):

        print("Fallback route: profile_tool")

        return make_route("profile_tool")

    # ---------------------------------------------------------
    # MARKS
    # ---------------------------------------------------------

    marks_keywords = [
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
        "highest marks",
        "lowest marks",
        "strongest subject",
        "weakest subject",
    ]

    if any(keyword in q for keyword in marks_keywords):

        print("Fallback route: marks_tool")

        return make_route("marks_tool")

    return None