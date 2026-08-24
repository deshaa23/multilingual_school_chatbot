from backend.database import fetch_one


def get_profile(student_id: int):
    """
    Fetch the student's profile information.
    """

    query = """
        SELECT
            s.student_id,
            s.first_name,
            s.last_name,
            s.admission_number,
            s.roll_number,
            s.date_of_birth,
            s.gender,
            s.admission_date,
            c.class_name,
            c.section,
            c.academic_year,
            u.email
        FROM students s
        JOIN classes c
            ON s.class_id = c.class_id
        JOIN users u
            ON s.user_id = u.user_id
        WHERE s.student_id = %s
    """

    result = fetch_one(query, (student_id,))

    if not result:
        return {
            "type": "profile",
            "success": False,
            "student_id": student_id,
            "results": None,
            "message": "Student profile not found."
        }

    return {
        "type": "profile",
        "success": True,
        "student_id": student_id,
        "results": result
    }