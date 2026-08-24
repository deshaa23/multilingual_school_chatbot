from ai.tools.sql_tools import run_sql_tool


print("\n========== MARKS ==========")

marks_result = run_sql_tool(
    tool_name="marks",
    student_id=1
)

print(marks_result)


print("\n========== ATTENDANCE ==========")

attendance_result = run_sql_tool(
    tool_name="attendance",
    student_id=1
)

print(attendance_result)