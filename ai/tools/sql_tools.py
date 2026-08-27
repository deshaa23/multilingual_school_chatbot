from ai.tools.marks_tool import get_marks
from ai.tools.attendance_tool import get_attendance
from ai.tools.assignment_tool import get_assignments
from ai.tools.timetable_tool import get_timetable
from ai.tools.performance_tool import get_performance_data


def run_sql_tool(
    tool_name: str,
    student_id: int,
    question=None,
    **kwargs
):
    """
    Central dispatcher for SQL/data retrieval tools.
    """

    print()
    print("========== SQL TOOL DISPATCHER ==========")
    print(f"Tool Name : {tool_name}")
    print(f"Student ID: {student_id}")
    print(f"Question  : {question}")
    print(f"Arguments : {kwargs}")
    print("=========================================")
    print()

    # =========================================================
    # NORMALIZE TOOL NAME
    # =========================================================

    if tool_name.endswith("_tool"):

        tool_name = tool_name[:-5]

    # =========================================================
    # MARKS
    # =========================================================

    if tool_name == "marks":

        return get_marks(
            student_id=student_id,
            subject=kwargs.get("subject"),
            exam=kwargs.get("exam")
        )

    # =========================================================
    # ATTENDANCE
    # =========================================================

    if tool_name == "attendance":

        return get_attendance(
            student_id=student_id,
            metric=kwargs.get(
                "metric"
            ),

            attendance_phrase=kwargs.get(
                "attendance_phrase"
            ),

            question=question
        )

    # =========================================================
    # ASSIGNMENTS
    # =========================================================

    if tool_name == "assignments":

        return get_assignments(
            student_id=student_id,
            status=kwargs.get("status")
        )

    # =========================================================
    # PERFORMANCE
    # =========================================================

    if tool_name == "performance":

        return get_performance_data(
            student_id=student_id,
            metric=kwargs.get("metric")
        )

    # =========================================================
    # TIMETABLE
    # =========================================================

    if tool_name == "timetable":

        return get_timetable(
            student_id=student_id,
            day=kwargs.get("day")
        )

    # =========================================================
    # UNKNOWN TOOL
    # =========================================================

    raise ValueError(
        f"Unknown SQL tool: {tool_name}"
    )