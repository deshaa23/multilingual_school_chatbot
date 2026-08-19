from ai.embeddings import get_embedding, cosine_similarity

INTENT_EXAMPLES = {

    "marks": [
        "What are my marks?",
        "Show me my exam marks",
        "What scores did I get?",
        "How many marks did I obtain?",
        "Tell me my exam scores",
        "What were my grades?",
        "Show my results",
        "What did I score in my exams?"
    ],

    "performance": [
        "How did I perform?",
        "How did I do in my exams?",
        "How is my academic performance?",
        "How am I performing?",
        "How am I doing academically?",
        "What is my overall performance?",
        "How well am I doing?",
        "Am I performing well?",
        "Am I improving?",
        "Which subjects need improvement?"
    ],

    "attendance": [
        "What is my attendance?",
        "How much attendance do I have?",
        "Show my attendance",
        "How many classes did I attend?",
        "What percentage of classes did I attend?"
    ],

    "assignments": [
        "Show my assignments",
        "What assignments do I have?",
        "Do I have any pending homework?",
        "Which assignments are pending?",
        "What homework was given?"
    ],

    "timetable": [
        "What is my timetable?",
        "Show my class schedule",
        "What classes do I have today?",
        "When is my next class?",
        "What is today's schedule?"
    ],

    "teacher": [
        "Who is my teacher?",
        "Tell me about my teachers",
        "Who teaches mathematics?",
        "Who is my class teacher?",
        "Show my teacher information"
    ],

    "profile": [
        "Show my profile",
        "What is my roll number?",
        "What is my admission number?",
        "Tell me my student information",
        "Show my personal details"
    ],

    "fees": [
        "What are my school fees?",
        "How much fee do I have to pay?",
        "Show my fee details",
        "Is my fee paid?",
        "Do I have any pending fees?"
    ],

    "announcement": [
        "What are the latest announcements?",
        "Show school announcements",
        "Are there any new notices?",
        "What notices has the school posted?"
    ],

    "school_policy": [
        "What is the school policy?",
        "What are the school rules?",
        "Tell me about school regulations",
        "What are the school guidelines?"
    ]
}

INTENT_EMBEDDINGS = {}

for intent, examples in INTENT_EXAMPLES.items():

    INTENT_EMBEDDINGS[intent] = [
        get_embedding(example)
        for example in examples
    ]


def detect_intent(query: str):

    query_embedding = get_embedding(query)

    scores = {}

    for intent, embeddings in INTENT_EMBEDDINGS.items():

        similarities = [
            cosine_similarity(query_embedding, embedding)
            for embedding in embeddings
        ]

        scores[intent] = max(similarities)

    best_intent = max(scores, key=scores.get)

    best_score = scores[best_intent]

    return best_intent, best_score, scores