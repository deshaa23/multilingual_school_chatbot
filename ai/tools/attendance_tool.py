from backend.database import fetch_all


def get_attendance(
    student_id: int
):
    """
    Fetch attendance records for a student.
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
        1 for row in results
        if row["status"].lower() == "present"
    )

    absent = sum(
        1 for row in results
        if row["status"].lower() == "absent"
    )

    late = sum(
        1 for row in results
        if row["status"].lower() == "late"
    )

    percentage = (
        (present / total) * 100
        if total > 0
        else 0
    )

    return {
        "type": "attendance",
        "success": True,
        "student_id": student_id,
        "summary": {
            "total_days": total,
            "present": present,
            "absent": absent,
            "late": late,
            "percentage": round(percentage, 2)
        },
        "records": results
    }