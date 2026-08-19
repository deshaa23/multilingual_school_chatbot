def detect_intent(question: str) -> str:

    question = question.lower()
    
     # -------------------------
    # Assignment-specific phrases
    # -------------------------
    assignment_phrases = [
        "due date",
        "deadline",
        "last date",
        "complete",
        "submit",
        "finish",
        "assignment",
        "project",
        "homework",
        "due",
        "deadline",
        "submission",
        "assignments",
]
    
    rag_phrases = [
    "how do i",
    "how to",
    "procedure",
    "process",
    "policy",
    "rules",
    "guidelines"
]
    

    sql_keywords = [

    "my",
    "me",
    "mine",

    "marks",
    "attendance",
    "result",
    "results",

    "assignment",
    "assignments",

    "due",
    "deadline",
    "submit",
    "submission",
    "complete",
    "finish",

    "homework",
    "project",

    "timetable",

    "profile",

    "class",
    "section",

    "roll",
    "roll number",

    "admission number",

    "class teacher",

    "student"
]
    
    

    sql_hinglish = [

    "mere",
    "meri",
    "mera",

    "dikhao",
    "batao",

    "kab",

    "last date",

    "submit",

    "complete",

    "assignment",

    "project",

    "homework",

    "deadline",

    "attendance",

    "marks",

    "class",

    "teacher"
]

    rag_keywords = [

        "policy",
        "uniform",
        "dress",
        "library",
        "holiday",
        "transport",
        "bus",
        "canteen",
        "rules",
        "principal",
        "guideline",
        "document",
        "fee structure",
        "fees",
        "fine",
        "fines",
        "rule",
        "principal",
        "admission",
        "discipline",
        "school timings",
        "timings",
        "pay",
        "payment",

    ]
    
    if any(word in question for word in rag_keywords):
        return "rag"
    
    if any(phrase in question for phrase in rag_phrases):
        return "rag"
        
    if any(word in question for word in sql_keywords):
        return "sql"

    if any(word in question for word in sql_hinglish):
        return "sql"
    
    if any(word in question for word in assignment_phrases):
        return "sql"
    
    return "rag"