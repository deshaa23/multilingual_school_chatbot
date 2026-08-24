"""
Performance Analysis Tool

Responsibilities:
1. Retrieve a student's exam performance from PostgreSQL.
2. Compare exam performance.
3. Calculate overall improvement.
4. Calculate subject-wise improvement.
5. Identify strongest, weakest, and most-improved subjects.

PostgreSQL:
    Used for retrieving the raw academic data.

Python:
    Used for analysis and evaluation.
"""

from backend.database import fetch_all


# ============================================================
# 1. GET PERFORMANCE DATA
# ============================================================

def get_performance_data(student_id: int):
    """
    Fetch exam-wise marks for a student.

    Returns raw performance data from PostgreSQL.

    Database relationship:

        marks
          ↓ class_subject_id
        class_subjects
          ↓ subject_id
        subjects

        marks
          ↓ exam_id
        exams
    """

    query = """
        SELECT
            sub.subject_name,
            e.exam_id,
            e.exam_name,
            e.start_date,
            e.end_date,
            m.marks_obtained,
            m.maximum_marks

        FROM marks m

        JOIN class_subjects cs
            ON m.class_subject_id = cs.class_subject_id

        JOIN subjects sub
            ON cs.subject_id = sub.subject_id

        JOIN exams e
            ON m.exam_id = e.exam_id

        WHERE m.student_id = %s

        ORDER BY
            e.start_date,
            sub.subject_name;
    """

    results = fetch_all(query, (student_id,))

    return results


# ============================================================
# 2. CALCULATE PERCENTAGE
# ============================================================

def calculate_percentage(marks_obtained, maximum_marks):
    """
    Convert marks into percentage.

    Example:
        42 / 50 -> 84%
    """

    if maximum_marks is None or maximum_marks == 0:
        return 0.0

    return round(
        (float(marks_obtained) / float(maximum_marks)) * 100,
        2
    )


# ============================================================
# 3. IDENTIFY EXAM TYPE
# ============================================================

def get_exam_type(exam_name):
    """
    Identify whether an exam is Mid Term or Final.

    This is intentionally based on the exam name because
    the current database schema does not have a separate
    exam_type column.
    """

    name = str(exam_name).lower()

    if "mid" in name:
        return "mid_term"

    if "final" in name:
        return "final"

    if "annual" in name:
        return "final"

    return "other"


# ============================================================
# 4. PREPARE SUBJECT-WISE DATA
# ============================================================

def build_subject_comparison(results):
    """
    Convert raw database rows into:

        Subject
            ↓
        Mid Term
            ↓
        Final
            ↓
        Improvement
    """

    subjects = {}

    for row in results:

        subject = row["subject_name"]
        exam_type = get_exam_type(row["exam_name"])

        percentage = calculate_percentage(
            row["marks_obtained"],
            row["maximum_marks"]
        )

        if subject not in subjects:
            subjects[subject] = {
                "subject": subject,
                "mid_term": None,
                "final": None,
            }

        if exam_type == "mid_term":

            subjects[subject]["mid_term"] = percentage

        elif exam_type == "final":

            subjects[subject]["final"] = percentage

    comparisons = []

    for subject, data in subjects.items():

        mid_term = data["mid_term"]
        final = data["final"]

        # Only compare subjects where both exams exist.
        if mid_term is None or final is None:
            continue

        improvement = round(final - mid_term, 2)

        comparisons.append({
            "subject": subject,
            "mid_term": mid_term,
            "final": final,
            "change": improvement,
            "improved": improvement > 0
        })

    return comparisons


# ============================================================
# 5. CALCULATE OVERALL PERFORMANCE
# ============================================================

def calculate_overall_performance(comparisons):
    """
    Calculate average Mid Term and Final percentages.

    Example:

        Mid Term:
        82 + 79 + 85 + 79 + 88
        ------------------------
                  5

        Final:
        87 + 84 + 88 + 85 + 91
        ------------------------
                  5
    """

    if not comparisons:
        return {
            "mid_term": None,
            "final": None,
            "change": None,
            "improved": False
        }

    mid_scores = [
        item["mid_term"]
        for item in comparisons
    ]

    final_scores = [
        item["final"]
        for item in comparisons
    ]

    mid_average = round(
        sum(mid_scores) / len(mid_scores),
        2
    )

    final_average = round(
        sum(final_scores) / len(final_scores),
        2
    )

    change = round(
        final_average - mid_average,
        2
    )

    return {
        "mid_term": mid_average,
        "final": final_average,
        "change": change,
        "improved": change > 0
    }


# ============================================================
# 6. FIND STRONGEST SUBJECT
# ============================================================

def find_strongest_subject(comparisons):
    """
    Find the subject with the highest Final score.
    """

    if not comparisons:
        return None

    strongest = max(
        comparisons,
        key=lambda x: x["final"]
    )

    return {
        "subject": strongest["subject"],
        "score": strongest["final"]
    }


# ============================================================
# 7. FIND WEAKEST SUBJECT
# ============================================================

def find_weakest_subject(comparisons):
    """
    Find the subject with the lowest Final score.
    """

    if not comparisons:
        return None

    weakest = min(
        comparisons,
        key=lambda x: x["final"]
    )

    return {
        "subject": weakest["subject"],
        "score": weakest["final"]
    }

# ============================================================
# 8. FIND SUBJECT TO FOCUS ON
# ============================================================

def find_focus_subject(comparisons):
    """
    Identify the subject that needs the most attention.

    Priority:
    1. Lowest Final score
    2. If scores are similar, consider improvement

    The subject with the lowest Final score is considered
    the main focus area.
    """

    if not comparisons:
        return None

    focus = min(
        comparisons,
        key=lambda x: x["final"]
    )

    return {
        "subject": focus["subject"],
        "score": focus["final"],
        "mid_term": focus["mid_term"],
        "change": focus["change"]
    }

# ============================================================
# 7B. FIND LEAST IMPROVED SUBJECT
# ============================================================

def find_least_improved_subject(comparisons):
    """
    Find the subject with the smallest improvement
    from Mid Term to Final.
    """

    if not comparisons:
        return None

    least_improved = min(
        comparisons,
        key=lambda x: x["change"]
    )

    return {
        "subject": least_improved["subject"],
        "change": least_improved["change"]
    }

# ============================================================
# 8. FIND MOST IMPROVED SUBJECT
# ============================================================

def find_most_improved_subject(comparisons):
    """
    Find the subject with the largest improvement.
    """

    if not comparisons:
        return None

    most_improved = max(
        comparisons,
        key=lambda x: x["change"]
    )

    return {
        "subject": most_improved["subject"],
        "change": most_improved["change"]
    }
    
# ============================================================
# 9. FIND LEAST IMPROVED SUBJECT
# ============================================================

def find_least_improved_subject(comparisons):
    """
    Find the subject with the smallest improvement
    from Mid Term to Final.
    """

    if not comparisons:
        return None

    least_improved = min(
        comparisons,
        key=lambda x: x["change"]
    )

    return {
        "subject": least_improved["subject"],
        "mid_term": least_improved["mid_term"],
        "final": least_improved["final"],
        "change": least_improved["change"]
    }


# ============================================================
# 9. MAIN PERFORMANCE ANALYSIS
# ============================================================

def analyze_performance(student_id: int):
    """
    Main Python analysis function.

    Flow:

        PostgreSQL
             ↓
        raw results
             ↓
        subject comparison
             ↓
        overall analysis
             ↓
        insights
    """

    results = get_performance_data(student_id)

    if not results:
        return {
            "type": "performance_analysis",
            "success": False,
            "message": "No performance data found.",
            "overall": None,
            "subjects": []
        }

    comparisons = build_subject_comparison(results)

    if not comparisons:
        return {
            "type": "performance_analysis",
            "success": False,
            "message": (
                "There is not enough exam data to compare "
                "Mid Term and Final performance."
            ),
            "overall": None,
            "subjects": []
        }

    overall = calculate_overall_performance(
        comparisons
    )

    strongest = find_strongest_subject(
        comparisons
    )

    weakest = find_weakest_subject(
        comparisons
    )

    most_improved = find_most_improved_subject(
        comparisons
    )
    
    least_improved = find_least_improved_subject(
    comparisons
    )
    
    focus_subject = find_focus_subject(
    comparisons
    )

    return {
        "type": "performance_analysis",
        "success": True,

        "overall": overall,

        "subjects": comparisons,

        "strongest_subject": strongest,

        "weakest_subject": weakest,

        "most_improved_subject": most_improved,
        
        "least_improved_subject": least_improved,

        "focus_subject": focus_subject
    }


# ============================================================
# 10. TOOL ENTRY POINT
# ============================================================

def performance_tool(
    student_id: int,
    operation: str = "analyze"
):
    """
    Main entry point used by the chatbot.

    Supported operations:

        analyze
        compare_exams
        strongest_subject
        weakest_subject
        most_improved
        focus_subject
    """

    analysis = analyze_performance(student_id)

    if not analysis["success"]:
        return analysis

    if operation in (
        "analyze",
        "compare_exams"
    ):
        return analysis

    if operation == "strongest_subject":

        return {
            "type": "strongest_subject",
            "result": analysis["strongest_subject"]
        }

    if operation == "weakest_subject":

        return {
            "type": "weakest_subject",
            "result": analysis["weakest_subject"]
        }

    if operation == "most_improved":

        return {
            "type": "most_improved",
            "result": analysis["most_improved_subject"]
        }
        
    

    if operation == "focus_subject":

        return {
            "type": "focus_subject",
            "result": analysis["focus_subject"]
        }


    # Unknown operation
    return {
        "type": "performance_analysis",
        "success": False,
        "message": f"Unsupported performance operation: {operation}"
    }