def timetable_sql(student_id):

    return f"""
    SELECT
        t.day_of_week,
        t.start_time,
        t.end_time,
        t.room_number,
        s.subject_name
    FROM timetable t
    JOIN class_subjects cs
        ON t.class_subject_id = cs.class_subject_id
    JOIN subjects s
        ON cs.subject_id = s.subject_id
    WHERE cs.class_id = (
        SELECT class_id
        FROM students
        WHERE student_id = {student_id}
    )
    ORDER BY
        CASE t.day_of_week
            WHEN 'Monday' THEN 1
            WHEN 'Tuesday' THEN 2
            WHEN 'Wednesday' THEN 3
            WHEN 'Thursday' THEN 4
            WHEN 'Friday' THEN 5
            WHEN 'Saturday' THEN 6
        END,
        t.start_time;
    """