from decimal import Decimal

from ai.tools.tool_executor import execute_tool
from rag.rag_pipeline import rag_answer
from ai.router import route_question


# =============================================================
# HELPER FUNCTIONS
# =============================================================

def to_float(value):
    """
    Safely convert Decimal / numeric values to float.
    """

    if value is None:
        return None

    try:
        return float(value)

    except (TypeError, ValueError):

        return None


# =============================================================
# MARKS ANALYSIS
# =============================================================

def analyze_marks(results):
    """
    Analyze marks returned by marks_tool.
    """

    if not results:

        return {
            "success": False,
            "message": "No marks data available."
        }

    # ---------------------------------------------------------
    # Group by exam
    # ---------------------------------------------------------

    exams = {}

    for row in results:

        exam = row.get("exam")

        if not exam:
            continue

        if exam not in exams:
            exams[exam] = []

        exams[exam].append(row)

    if not exams:

        return {
            "success": False,
            "message": "No examination data available."
        }

    # ---------------------------------------------------------
    # Determine exam order
    # ---------------------------------------------------------

    def exam_priority(exam_name):

        name = str(exam_name).lower()

        if "unit" in name:
            return 1

        if "periodic" in name:
            return 2

        if "mid" in name:
            return 3

        if "half" in name:
            return 4

        if "final" in name:
            return 5

        if "annual" in name:
            return 6

        return 100

    ordered_exams = sorted(
        exams.keys(),
        key=exam_priority
    )

    latest_exam = ordered_exams[-1]

    previous_exam = (
        ordered_exams[-2]
        if len(ordered_exams) >= 2
        else None
    )

    latest_rows = exams[latest_exam]

    previous_rows = (
        exams[previous_exam]
        if previous_exam
        else []
    )

    # ---------------------------------------------------------
    # Latest marks by subject
    # ---------------------------------------------------------

    latest_by_subject = {}

    for row in latest_rows:

        subject = row.get("subject")

        if subject:
            latest_by_subject[subject] = row

    # ---------------------------------------------------------
    # Previous marks by subject
    # ---------------------------------------------------------

    previous_by_subject = {}

    for row in previous_rows:

        subject = row.get("subject")

        if subject:
            previous_by_subject[subject] = row

    # ---------------------------------------------------------
    # Calculate subject-wise improvement
    # ---------------------------------------------------------

    improvements = []

    if previous_exam:

        common_subjects = (
            set(latest_by_subject.keys())
            & set(previous_by_subject.keys())
        )

        for subject in sorted(common_subjects):

            latest_marks = to_float(
                latest_by_subject[subject].get(
                    "marks_obtained"
                )
            )

            previous_marks = to_float(
                previous_by_subject[subject].get(
                    "marks_obtained"
                )
            )

            if (
                latest_marks is None
                or previous_marks is None
            ):
                continue

            difference = latest_marks - previous_marks

            improvements.append({
                "subject": subject,
                "previous_exam": previous_exam,
                "previous_marks": previous_marks,
                "latest_exam": latest_exam,
                "latest_marks": latest_marks,
                "difference": difference
            })

    # ---------------------------------------------------------
    # Weakest / strongest latest subject
    # ---------------------------------------------------------

    latest_subject_scores = []

    for subject, row in latest_by_subject.items():

        marks = to_float(
            row.get("marks_obtained")
        )

        maximum = to_float(
            row.get("maximum_marks")
        )

        if marks is not None:

            percentage = None

            if maximum:
                percentage = (
                    marks / maximum
                ) * 100

            latest_subject_scores.append({
                "subject": subject,
                "marks": marks,
                "maximum_marks": maximum,
                "percentage": percentage
            })

    weakest_subject = None
    strongest_subject = None

    if latest_subject_scores:

        weakest_subject = min(
            latest_subject_scores,
            key=lambda x:
            x["percentage"]
            if x["percentage"] is not None
            else x["marks"]
        )

        strongest_subject = max(
            latest_subject_scores,
            key=lambda x:
            x["percentage"]
            if x["percentage"] is not None
            else x["marks"]
        )

    # ---------------------------------------------------------
    # Overall improvement
    # ---------------------------------------------------------

    improved_subjects = [
        item
        for item in improvements
        if item["difference"] > 0
    ]

    declined_subjects = [
        item
        for item in improvements
        if item["difference"] < 0
    ]

    unchanged_subjects = [
        item
        for item in improvements
        if item["difference"] == 0
    ]

    if improvements:

        if len(improved_subjects) == len(improvements):

            overall_status = "improved_in_all_subjects"

        elif len(declined_subjects) == len(improvements):

            overall_status = "declined_in_all_subjects"

        elif improved_subjects:

            overall_status = "improved_in_some_subjects"

        else:

            overall_status = "no_improvement"

    else:

        overall_status = "comparison_not_available"

    return {
        "success": True,

        "latest_exam": latest_exam,

        "previous_exam": previous_exam,

        "latest_subject_scores": latest_subject_scores,

        "weakest_subject": weakest_subject,

        "strongest_subject": strongest_subject,

        "improvements": improvements,

        "improved_subjects": improved_subjects,

        "declined_subjects": declined_subjects,

        "unchanged_subjects": unchanged_subjects,

        "overall_status": overall_status
    }


# =============================================================
# MAIN CHAT PIPELINE
# =============================================================

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
    Database       Chroma
       ↓             ↓
       └──────┬──────┘
              ↓
        Structured Result
              ↓
         Marks Analysis
              ↓
        Final Answer Layer
    """

    # =========================================================
    # PRESERVE ORIGINAL QUESTION
    # =========================================================

    if original_question is None:
        original_question = question

    # =========================================================
    # 1. ROUTE QUESTION
    # =========================================================

    route = route_question(question)
    
    print("\n========== DEBUG ROUTE ==========")
    print(route)
    print("=================================")

    # Safety fallback
    if not route:

        route = {
            "tool": "general_chat",
            "subject": None,
            "exam": None,
            "day": None,
            "status": None,
            "metric": None,
            "confidence": 0.0
        }

    tool_name = route.get("tool")

    print("\n========== ROUTING ==========")
    print(f"Question  : {question}")
    print(f"Original  : {original_question}")
    print(f"Tool      : {tool_name}")
    print(f"Metric    : {route.get('metric')}")
    print(f"Subject   : {route.get('subject')}")
    print(f"Exam      : {route.get('exam')}")
    print(f"Day       : {route.get('day')}")
    print(f"Status    : {route.get('status')}")
    print(f"Confidence: {route.get('confidence')}")
    print("=============================")

    # =========================================================
    # 2. GENERAL CHAT
    # =========================================================

    if tool_name == "general_chat":

        return {
            "type": "general_chat",
            "success": True,
            "message": "General chat"
        }

    # =========================================================
    # 3. RAG
    # =========================================================
    #
    # IMPORTANT:
    # RAG returns immediately.
    #
    # It NEVER reaches execute_tool().
    # =========================================================

    if tool_name == "rag_tool":

        print("\n========== RAG TOOL ==========")
        print("English Question :", question)
        print("Original Question:", original_question)
        print("Language         :", language)
        print("==============================")

        try:

            answer = rag_answer(
                english_question=question,
                original_question=original_question,
                language=language
            )

            return {
                "type": "rag",
                "success": True,
                "answer": answer
            }

        except Exception as e:

            print("RAG ERROR:", e)

            return {
                "type": "rag",
                "success": False,
                "answer": "Sorry, I could not retrieve the requested school information."
            }

    # =========================================================
    # 4. SQL / DATABASE TOOL
    # =========================================================

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
        metric=route.get("metric"),
        question=question
    )

    # =========================================================
    # 5. MARKS ANALYSIS
    # =========================================================

    if (
        tool_name == "marks_tool"
        and result
        and result.get("success")
    ):

        raw_results = result.get(
            "results",
            []
        )

        analysis = analyze_marks(
            raw_results
        )

        result["analysis"] = analysis

        # Preserve route information

        result["metric"] = route.get(
            "metric"
        )

        result["requested_subject"] = route.get(
            "subject"
        )

    # =========================================================
    # 6. RETURN RESULT
    # =========================================================

    return result