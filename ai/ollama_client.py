import ollama

MODEL = "llama3:latest"


def generate_sql(prompt: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are an expert PostgreSQL SQL generator.

Return ONLY ONE valid PostgreSQL SQL statement.

Rules:
- Return ONLY SQL.
- Do NOT explain.
- Do NOT use markdown.
- Do NOT use ```sql.
- Do NOT write English sentences.
- Do NOT add comments.
- Never return multiple SQL statements.
- Always end with a semicolon.
"""
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0
        }
    )

    return response["message"]["content"].strip()
def generate_answer(prompt: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
                You are a helpful AI assistant for a school chatbot.
                Answer ONLY using the provided context.
                If the answer is not present in the context, say:
                'I couldn't find this information in the available school documents.'
                Be concise and accurate.
                """
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={"temperature": 0.2}
    )

    return response["message"]["content"].strip()

def classify_intent(question: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """

You are an intent classifier for a school chatbot.

Return ONLY one word:

SQL

or

RAG

---------------------------------------------------
Use SQL when the question requires data from the
school DATABASE.
---------------------------------------------------

Examples:

Show my profile
Give my profile
Show my details
Who am I?
What is my admission number?
What is my roll number?
Show my class
What is my section?
Who is my class teacher?
Show my timetable
Show my attendance
Show my marks
Show my exam results
Show my assignments
Show my fees
Show my subjects

---------------------------------------------------
Use RAG when the question asks about school
DOCUMENTS, RULES or POLICIES.
---------------------------------------------------

Examples:

What is the attendance policy?
How do I pay fees?
What are the school timings?
What is the dress code?
Explain library rules.
What holidays are there?
How can I apply for admission?

Return ONLY

SQL

or

RAG


Do not explain your answer.
"""
            },
            {
                "role": "user",
                "content": question
            }
        ],
        options={
            "temperature": 0
        }
    )

    return response["message"]["content"].strip()

def detect_language(question: str) -> str:
    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are a language detector.

Classify the user's question into exactly one language.

Rules:
- Return ENGLISH if the sentence is completely in English.
- Return HINDI if the sentence is written in Hindi (Devanagari script).
- Return HINDI if the sentence is Hinglish (Hindi written using English letters).

Examples:
Input: Show my marks
Output: ENGLISH

Input: What is my timetable?
Output: ENGLISH

Input: मेरे अंक दिखाओ
Output: HINDI

Input: मेरा टाइमटेबल दिखाओ
Output: HINDI

Input: Mere marks dikhao
Output: HINDI

Return ONLY one word:
ENGLISH
or
HINDI
"""
            },
            {
                "role": "user",
                "content": question
            }
        ],
        options={"temperature": 0}
    )

    return response["message"]["content"].strip().upper()