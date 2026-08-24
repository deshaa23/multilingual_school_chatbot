from ai.tools.sql_tools import run_sql_tool
from ai.tools.analysis_tools import run_analysis_tool
from ai.tools.assignment_tool import get_assignments
from ai.tools.timetable_tool import get_timetable


def execute_tool(
    tool_name: str,
    student_id: int,
    **kwargs
):
    """
    Execute the tool selected by the router.
    """

    # ==========================================
    # MARKS
    # ==========================================

    if tool_name == "marks_tool":

        return run_sql_tool(
            tool_name="marks",
            student_id=student_id,
            **kwargs
        )

    # ==========================================
    # ATTENDANCE
    # ==========================================

    if tool_name == "attendance_tool":

        return run_sql_tool(
            tool_name="attendance",
            student_id=student_id,
            **kwargs
        )

    # ==========================================
    # ASSIGNMENTS
    # ==========================================

    if tool_name == "assignment_tool":

        return run_sql_tool(
            tool_name="assignments",
            student_id=student_id,
            status=kwargs.get("status")
        )

    # ==========================================
    # TIMETABLE
    # ==========================================

    if tool_name == "timetable_tool":

        return run_sql_tool(
            tool_name="timetable",
            student_id=student_id,
            day=kwargs.get("day")
        )

    # ==========================================
    # PERFORMANCE
    # ==========================================

    if tool_name == "performance_tool":

        return run_analysis_tool(
            tool_name="performance",
            student_id=student_id,
            **kwargs
        )

    # ==========================================
    # UNKNOWN TOOL
    # ==========================================

    return {
        "success": False,
        "error": f"Unknown tool: {tool_name}"
    }