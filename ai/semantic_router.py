# ai/semantic_router.py

from sentence_transformers import SentenceTransformer, util


# =========================================================
# EMBEDDING MODEL
# =========================================================

MODEL_NAME = "all-MiniLM-L6-v2"

_model = None


def get_model():
    global _model

    if _model is None:
        print("Loading semantic router embedding model...")
        _model = SentenceTransformer(MODEL_NAME)

    return _model


# =========================================================
# INTENT EXAMPLES
# =========================================================
#
# IMPORTANT:
# These are NOT meant to cover every possible question.
#
# They simply give the embedding model examples of the
# meaning of each category.
#
# Millions of different phrasings can map to these concepts.
# =========================================================

INTENT_EXAMPLES = {

    "marks": [

        "show my marks",
        "show my scores",
        "what did I score",
        "what are my scores",
        "tell me my marks",
        "how much did I get",
        "what grade did I get",
        "show my result",
        "show my results",
        "my academic results",
        "my examination marks",
        "my exam scores",
        "marks obtained by me",
        "how many marks did I get",
        "what were my marks",
        "tell me my exam performance",
        "show my report card",
        "show my subject marks",
        "what did I get in mathematics",
        "what did I score in science",
    ],

    "performance": [

        "which is my strongest subject",
        "what is my best subject",
        "which subject am I best at",
        "which subject do I perform best in",
        "what is my weakest subject",
        "which subject am I weakest in",
        "where am I performing poorly",
        "am I improving",
        "is my performance improving",
        "how is my performance changing",
        "show my performance trend",
        "am I getting better",
        "am I getting worse",
        "compare my exams",
        "compare my performance",
        "compare my mid term and final",
        "which subject has my highest percentage",
        "which subject has my lowest percentage",
        "where do I perform best",
        "where do I need improvement",
    ],

    "attendance": [

        "show my attendance",
        "what is my attendance",
        "how much attendance do I have",
        "what percentage attendance do I have",
        "how many classes did I attend",
        "how many classes did I miss",
        "show attendance percentage",
        "attendance record",
        "attendance status",
        "my attendance details",
        "am I present enough",
        "how many days was I absent",
        "how many days was I present",
        "attendance for this month",
        "attendance for this year",
        "my attendance percentage",
    ],

    "assignments": [

        "show my assignments",
        "what assignments do I have",
        "give me my homework",
        "show my homework",
        "which assignments are pending",
        "which assignments are due",
        "what homework is pending",
        "assignment deadlines",
        "assignment due dates",
        "my pending work",
        "my submitted assignments",
        "which assignment should I complete",
        "what work is due",
        "show upcoming assignments",
        "show assignment status",
    ],

    "timetable": [

        "show my timetable",
        "what is my timetable",
        "what classes do I have",
        "what subjects do I have today",
        "what class do I have today",
        "what is my schedule",
        "show my class schedule",
        "what period do I have",
        "which class is next",
        "what do I have on monday",
        "classes on tuesday",
        "my school schedule",
        "today's classes",
        "tomorrow's classes",
        "show my periods",
        "what subject is next",
    ],

    "teacher": [

        "who is my teacher",
        "who teaches mathematics",
        "who is my class teacher",
        "tell me about my teacher",
        "teacher details",
        "show teacher information",
        "which teacher teaches science",
        "who teaches my class",
    ],

    "profile": [

        "show my profile",
        "what is my roll number",
        "what is my date of birth",
        "show my student details",
        "my student information",
        "what is my admission number",
        "tell me my personal details",
        "my profile information",
    ],

    "class": [

        "which class am I in",
        "what class am I studying in",
        "show my class",
        "what is my section",
        "which section am I in",
        "tell me my class details",
    ],

    "rag": [

        "what are the school rules",
        "what is the attendance policy",
        "what are the exam rules",
        "when are exams conducted",
        "what is the examination schedule",
        "how do I submit an assignment",
        "what is the assignment submission policy",
        "what are the school holidays",
        "what is the grading policy",
        "what is the minimum attendance requirement",
        "how does the school grading system work",
        "tell me about school policies",
        "school information",
        "school guidelines",
        "examination guidelines",
        "assignment guidelines",
        "attendance rules",
    ]
}


# =========================================================
# SMALL CONCEPT ALIASES
# =========================================================
#
# These are only additional semantic hints.
# Do NOT attempt to put every possible word here.
# =========================================================

CONCEPT_ALIASES = {

    "marks": {
        "marks",
        "mark",
        "score",
        "scores",
        "result",
        "results",
        "grade",
        "grades",
        "percentage",
        "percent",
        "report card",
        "exam score",
    },

    "attendance": {
        "attendance",
        "present",
        "absent",
        "absence",
        "presence",
        "attended",
        "missed",
    },

    "assignments": {
        "assignment",
        "assignments",
        "homework",
        "task",
        "tasks",
        "submission",
        "submitted",
        "pending",
        "due",
        "deadline",
        "work",
    },

    "timetable": {
        "timetable",
        "schedule",
        "class",
        "classes",
        "period",
        "periods",
        "lecture",
        "today",
        "tomorrow",
    },

    "performance": {
        "strongest",
        "weakest",
        "best",
        "worst",
        "improve",
        "improving",
        "decline",
        "declining",
        "trend",
        "compare",
        "comparison",
        "performance",
        "highest",
        "lowest",
    },

    "rag": {
        "policy",
        "rule",
        "rules",
        "guideline",
        "guidelines",
        "procedure",
        "requirement",
        "requirements",
        "how do I",
        "what is the policy",
    }
}


# =========================================================
# BUILD EMBEDDINGS
# =========================================================

_embeddings_cache = None


def _build_embeddings():

    global _embeddings_cache

    if _embeddings_cache is not None:
        return _embeddings_cache

    model = get_model()

    embeddings = {}

    for intent, examples in INTENT_EXAMPLES.items():

        embeddings[intent] = model.encode(
            examples,
            convert_to_tensor=True,
            normalize_embeddings=True
        )

    _embeddings_cache = embeddings

    return embeddings


# =========================================================
# SEMANTIC ROUTING
# =========================================================

def semantic_route(question: str):

    question = question.strip()

    if not question:
        return {
            "intent": "rag",
            "confidence": 0.0,
            "scores": {}
        }

    model = get_model()

    embeddings = _build_embeddings()

    query_embedding = model.encode(
        question,
        convert_to_tensor=True,
        normalize_embeddings=True
    )

    scores = {}

    for intent, intent_embeddings in embeddings.items():

        similarities = util.cos_sim(
            query_embedding,
            intent_embeddings
        )[0]

        scores[intent] = float(
            similarities.max().item()
        )

    # -----------------------------------------------------
    # Alias boost
    # -----------------------------------------------------

    question_lower = question.lower()

    for intent, aliases in CONCEPT_ALIASES.items():

        matches = 0

        for alias in aliases:

            if alias in question_lower:
                matches += 1

        if matches:
            scores[intent] += min(
                matches * 0.025,
                0.10
            )

    # -----------------------------------------------------
    # Best intent
    # -----------------------------------------------------

    sorted_scores = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    best_intent, best_score = sorted_scores[0]

    return {
        "intent": best_intent,
        "confidence": round(
            min(best_score, 1.0),
            4
        ),
        "scores": {
            k: round(v, 4)
            for k, v in sorted_scores
        }
    }