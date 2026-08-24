from ai.router import route_query


questions = [
    "What are my marks?",
    "How much did I improve from mid term to final?",
    "What is my attendance percentage?",
    "Show my timetable",
    "What assignments are pending?",
    "Who is my class teacher?",
    "What is my roll number?",
    "What is photosynthesis?",
    "Hello"
]


for question in questions:

    print("\n-----------------------------------")
    print("QUESTION:", question)

    result = route_query(question)

    print("ROUTER:", result)