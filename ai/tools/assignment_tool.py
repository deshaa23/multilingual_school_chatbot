from backend.database import fetch_all


def get_assignments(
    student_id: int,
    status: str | None = None
):
    """
    Fetch assignments available to the student's class.

    Supports:
    - all assignments
    - pending assignments
    - completed/overdue filtering through status
    """

    query = """
        SELECT
            a.assignment_id,
            a.title,
            a.description,
            sub.subject_name AS subject,
            a.assigned_date,
            a.due_date
        FROM students s
        JOIN class_subjects cs
            ON s.class_id = cs.class_id
        JOIN subjects sub
            ON cs.subject_id = sub.subject_id
        JOIN assignments a
            ON cs.class_subject_id = a.class_subject_id
        WHERE s.student_id = %s
    """

    params = [student_id]

    if status == "pending":
        query += """
            AND a.due_date >= CURRENT_DATE
        """

    elif status == "overdue":
        query += """
            AND a.due_date < CURRENT_DATE
        """

    query += """
        ORDER BY a.due_date ASC, sub.subject_name ASC
    """

    results = fetch_all(query, tuple(params))

    return {
        "type": "assignments",
        "success": True,
        "student_id": student_id,
        "status": status,
        "results": results
    }