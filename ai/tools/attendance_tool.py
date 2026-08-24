from backend.database import fetch_all


# Set this to the attendance percentage required by your school.
ATTENDANCE_REQUIREMENT = 75.0


def get_attendance(
    student_id: int,
    metric=None
):
    """
    Fetch attendance records for a student and calculate
    attendance-related metrics.
    """

    query = """
        SELECT
            attendance_date,
            status
        FROM attendance
        WHERE student_id = %s
        ORDER BY attendance_date;
    """

    results = fetch_all(
        query,
        (student_id,)
    )

    total = len(results)

    present = sum(
        1
        for row in results
        if str(row["status"]).lower() == "present"
    )

    absent = sum(
        1
        for row in results
        if str(row["status"]).lower() == "absent"
    )

    late = sum(
        1
        for row in results
        if str(row["status"]).lower() == "late"
    )

    percentage = (
        (present / total) * 100
        if total > 0
        else 0
    )

    percentage = round(percentage, 2)

    # =========================================================
    # ELIGIBILITY
    # =========================================================

    eligible = percentage >= ATTENDANCE_REQUIREMENT

    return {
        "type": "attendance",
        "success": True,
        "student_id": student_id,
        "metric": metric,

        "summary": {
            "total_days": total,
            "present": present,
            "absent": absent,
            "late": late,
            "percentage": percentage
        },

        "eligibility": {
            "required_percentage": ATTENDANCE_REQUIREMENT,
            "current_percentage": percentage,
            "eligible": eligible
        },

        "records": results
    }