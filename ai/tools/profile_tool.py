from backend.database import fetch_one


def get_profile(
    student_id: int,
    metric=None,
    **kwargs
):
    """
    Retrieve profile information for the logged-in student.
    """

    student = fetch_one(
        """
        SELECT
            s.student_id,
            s.first_name,
            s.last_name,
            s.roll_number,
            s.admission_number,
            s.date_of_birth
        FROM students s
        WHERE s.student_id = %s
        """,
        (student_id,)
    )

    if not student:
        return {
            "success": False,
            "error": "Student profile not found."
        }

    return {
        "success": True,
        "type": "profile",
        "data": student
    }