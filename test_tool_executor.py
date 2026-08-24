from ai.tools.tool_executor import execute_tool


student_id = 1


print("\n========== MARKS ==========")

result = execute_tool(
    tool_name="marks_tool",
    student_id=student_id
)

print(result)


print("\n========== ATTENDANCE ==========")

result = execute_tool(
    tool_name="attendance_tool",
    student_id=student_id
)

print(result)


print("\n========== PERFORMANCE ==========")

result = execute_tool(
    tool_name="performance_tool",
    student_id=student_id
)

print(result)