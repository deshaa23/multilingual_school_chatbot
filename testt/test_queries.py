from backend.database import fetch_all

query = """
SELECT
    first_name,
    last_name
FROM students
ORDER BY student_id;
"""

students = fetch_all(query)

for student in students:
    print(student)