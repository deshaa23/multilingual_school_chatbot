from backend.database import fetch_all


def get_marks(
    student_id: int,
    subject: str | None = None,
    exam: str | None = None,
    metric: str | None = None
):
    """
    Fetch marks for a student.
    
    Supports:
    - subject filtering
    - exam filtering
    - highest score
    - lowest score

    This tool returns raw mark information.
    It does not generate a natural-language answer.
    """

    query = """
        SELECT
            sub.subject_name AS subject,
            e.exam_name AS exam,
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
    """

    params = [student_id]

    if subject:
        query += """
            AND LOWER(sub.subject_name) = LOWER(%s)
        """
        params.append(subject)

    if exam:
        query += """
            AND LOWER(e.exam_name) = LOWER(%s)
        """
        params.append(exam)

    # Handle highest / lowest score
    if metric == "highest":
        query += """
            ORDER BY m.marks_obtained DESC
            LIMIT 1
        """

    elif metric == "lowest":
        query += """
            ORDER BY m.marks_obtained ASC
            LIMIT 1
        """

    else:
        query += """
            ORDER BY e.start_date, sub.subject_name
        """

    results = fetch_all(query, tuple(params))

    return {
        "type": "marks",
        "success": True,
        "student_id": student_id,
        "metric": metric,
        "results": results
    }