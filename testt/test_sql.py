from ai.sql_generator import generate_sql

question = "Show all students"

sql = generate_sql(question)
print(sql)