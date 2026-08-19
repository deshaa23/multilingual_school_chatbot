from ai.sql_generator import generate_sql
from ai.sql_validator import validate_sql
from ai.query_executor import execute_sql

question = "Show all records from students table."

sql= generate_sql(question)

print("Generated SQL:")
print(sql)

validated_sql= validate_sql(sql)
results = execute_sql(validated_sql)
print("\nDatabase Results:")

for row in results:
    print(row)