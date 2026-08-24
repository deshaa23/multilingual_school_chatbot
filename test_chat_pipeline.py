from ai.chat_pipeline import process_query
from ai.answer_generator import generate_answer


student_id = 1


questions = [ 
"Show me my assignments.",
"Do I have any pending assignments?",
"When is my Mathematics assignment due?",
"What is my attendance percentage?",
"How many days was I absent?",
"Show my attendance record.",
"What is my timetable?",
"What classes do I have today?",
"What classes do I have on Monday?",
"When is my Mathematics class?",
"What is my next assignment deadline?",
"Do I have low attendance?",
"Am I eligible based on my attendance? "


]


for question in questions:

    print("\n\n########################################")
    print(f"QUESTION: {question}")
    print("########################################")

    result = process_query(
        question=question,
        student_id=student_id
    )

    print("\n========== FINAL TOOL RESULT ==========")
    print(result)

    answer = generate_answer(
        question=question,
        results=result,
        language="english"
    )

    print("\n========== FINAL ANSWER ==========")
    print(answer)
    print("===================================")
    