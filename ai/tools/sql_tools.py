from ai.tools.marks_tool import get_marks
from ai.tools.attendance_tool import get_attendance
from ai.tools.assignment_tool import get_assignments
from ai.tools.timetable_tool import get_timetable


def run_sql_tool(
    tool_name: str,
    student_id: int,
    **kwargs
):
    """
    Central dispatcher for SQL/data retrieval tools.
    """

    # -----------------------------
    # Marks
    # -----------------------------
    if tool_name == "marks":
        return get_marks(
            student_id=student_id,
            subject=kwargs.get("subject"),
            exam=kwargs.get("exam")
        )

    # -----------------------------
    # Attendance
    # -----------------------------
    if tool_name == "attendance":
        return get_attendance(
            student_id=student_id
        )

    # -----------------------------
    # Assignments
    # -----------------------------
    if tool_name == "assignments":
        return get_assignments(
            student_id=student_id,
            status=kwargs.get("status")
        )

    # -----------------------------
    # Timetable
    # -----------------------------
    if tool_name == "timetable":
        return get_timetable(
            student_id=student_id,
            day=kwargs.get("day")
        )

    raise ValueError(
        f"Unknown SQL tool: {tool_name}"
    )