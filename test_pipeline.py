from ai.pipeline import process_query


question = "Hello"

result = process_query(
    question=question,
    student_id=1
)

print("\n================================")
print("FINAL RESULT")
print("================================")
print(result)