from backend.database import fetch_all


def get_timetable(
    student_id: int,
    day: str | None = None
):
    """
    Fetch the student's timetable.

    Supports:
    - complete weekly timetable
    - specific day
    """

    query = """
        SELECT
            t.day_of_week,
            t.start_time,
            t.end_time,
            t.room_number,
            sub.subject_name AS subject,
            CONCAT(
                COALESCE(teacher.first_name, ''),
                ' ',
                COALESCE(teacher.last_name, '')
            ) AS teacher
        FROM students s
        JOIN class_subjects cs
            ON s.class_id = cs.class_id
        JOIN subjects sub
            ON cs.subject_id = sub.subject_id
        JOIN timetable t
            ON cs.class_subject_id = t.class_subject_id
        LEFT JOIN teachers teacher
            ON cs.teacher_id = teacher.teacher_id
        WHERE s.student_id = %s
    """

    params = [student_id]

    if day:
        query += """
            AND LOWER(t.day_of_week) = LOWER(%s)
        """
        params.append(day)

    query += """
        ORDER BY
            CASE t.day_of_week
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
            END,
            t.start_time
    """

    results = fetch_all(query, tuple(params))

    return {
        "type": "timetable",
        "success": True,
        "student_id": student_id,
        "day": day,
        "results": results
    }