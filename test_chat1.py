from ai.chat_pipeline import process_query
from ai.answer_generator import generate_answer


student_id = 1

questions = [
    "How am I performing?",
    "What is my overall performance?",
    "Which subject am I strongest in?",
    "Which subject am I weakest in?",
    "Which subject should I improve?",
    "What is my average performance?"
]

for question in questions:

    print("\n\n########################################")
    print("QUESTION:", question)
    print("########################################")

    result = process_query(
        question=question,
        student_id=student_id
    )

    print("\n========== TOOL RESULT ==========")
    print(result)

    answer = generate_answer(
        question=question,
        results=result,
        language="english"
    )

    print("\n========== FINAL ANSWER ==========")
    print(answer)
    print("==================================")