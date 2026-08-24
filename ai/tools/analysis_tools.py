from ai.tools.performance_tool import analyze_performance


def run_analysis_tool(
    tool_name: str,
    student_id: int,
    **kwargs
):
    """
    Central dispatcher for analysis tools.

    Parameters
    ----------
    tool_name : str
        Name of the analysis operation.
    student_id : int
        Student whose data should be analyzed.
    """

    if tool_name == "performance":
        return analyze_performance(
            student_id=student_id
        )

    raise ValueError(
        f"Unknown analysis tool: {tool_name}"
    )