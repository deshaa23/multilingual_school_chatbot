from ai.tools.sql_tools import run_sql_tool
from ai.tools.analysis_tools import run_analysis_tool
from ai.tools.assignment_tool import get_assignments
from ai.tools.timetable_tool import get_timetable
from ai.tools.profile_tool import get_profile


def execute_tool(
    tool_name: str,
    student_id: int,
    subject=None,
    exam=None,
    day=None,
    status=None,
    metric=None,
    attendance_phrase=None,
    question=None,
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
            metric=metric,
            attendance_phrase=kwargs.get("attendance_phrase"),
            question = question 
        )

    # ==========================================
    # ASSIGNMENTS
    # ==========================================

    if tool_name == "assignment_tool":

        return run_sql_tool(
            tool_name="assignments",
            student_id=student_id,
            status=status
        )

    # ==========================================
    # TIMETABLE
    # ==========================================

    if tool_name == "timetable_tool":

        return run_sql_tool(
            tool_name="timetable",
            student_id=student_id,
            day=day
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
    # PROFILE
    # ==========================================

    if tool_name == "profile_tool":

        return get_profile(
            student_id=student_id,
            metric=metric
        )

    # ==========================================
    # UNKNOWN TOOL
    # ==========================================

    return {
        "success": False,
        "error": f"Unknown tool: {tool_name}"
    }