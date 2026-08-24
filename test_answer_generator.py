from ai.answer_generator import generate_answer


tool_result = {
    "type": "performance_analysis",
    "success": True,
    "overall": {
        "mid_term": 85.2,
        "final": 89.8,
        "change": 4.6,
        "improved": True
    },
    "subjects": [
        {
            "subject": "Computer Science",
            "mid_term": 93.0,
            "final": 96.0,
            "change": 3.0,
            "improved": True
        },
        {
            "subject": "English",
            "mid_term": 84.0,
            "final": 89.0,
            "change": 5.0,
            "improved": True
        },
        {
            "subject": "Mathematics",
            "mid_term": 88.0,
            "final": 92.0,
            "change": 4.0,
            "improved": True
        },
        {
            "subject": "Science",
            "mid_term": 81.0,
            "final": 86.0,
            "change": 5.0,
            "improved": True
        },
        {
            "subject": "Social Science",
            "mid_term": 80.0,
            "final": 86.0,
            "change": 6.0,
            "improved": True
        }
    ],
    "strongest_subject": {
        "subject": "Computer Science",
        "score": 96.0
    },
    "weakest_subject": {
        "subject": "Science",
        "score": 86.0
    },
    "most_improved_subject": {
        "subject": "Social Science",
        "change": 6.0
    }
}


question = "How much did I improve from mid term to final?"


answer = generate_answer(
    question,
    tool_result
)


print("\n========== GENERATED ANSWER ==========")
print(answer)
print("======================================")