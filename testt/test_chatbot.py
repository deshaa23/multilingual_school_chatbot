from ai.sql_generator import generate_sql
from ai.sql_validator import validate_sql
from ai.query_executor import execute_sql
from ai.answer_generator import generate_answer

question = "Show all students"

sql = generate_sql(question)
print("Generated SQL:")
print(sql)

validated_sql = validate_sql(sql)
results = execute_sql(validated_sql)
answer = generate_answer(question, results)
print("\nFinal Answer:")
print(answer)