from ai.tools.analysis_tools import run_analysis_tool


result = run_analysis_tool(
    tool_name="performance",
    student_id=1
)

print("\n========== ANALYSIS TOOL RESULT ==========")
print(result)
print("==========================================")