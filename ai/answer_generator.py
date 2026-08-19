import json
import ollama

MODEL = "llama3:latest"


def generate_answer(question: str, results: list, language: str = "english") -> str:

    if language.upper() == "HINDI":
        language_instruction = """
Answer completely in Hindi.

Rules:
- Use only Devanagari script.
- Translate all database information into natural Hindi.
- Do not mix English except proper nouns (CBSE, Class 6, etc.).
- Preserve headings and bullet points.
"""
    elif language.upper() == "HINGLISH":
        language_instruction = """
You MUST answer ONLY in natural Indian Hinglish.

STRICT RULES:

- NEVER answer in full English.
- NEVER use Hindi (Devanagari) script.
- Use only English letters.
- Translate every sentence into natural Hinglish.
- Keep only proper nouns in English (Library, CBSE, Mathematics, Delhi Public School, etc.).

DO NOT start with:
- "According to the school documents..."
- "According to the context..."
- "Based on the documents..."
- "The documents state..."
- "Note:"

Start answering immediately.

If the context contains a list of rules, return the list in Hinglish.

Example:

Library Rules

• Library books mein likhna, marking ya underlining karna mana hai.
• Book due date se pehle return karni zaroori hai.
• Agar due date holiday ho, to next working day book return karni hogi.
• Personal books ya belongings library mein lana allowed nahi hai.
• Har student ko Almanac aur pencil saath laani chahiye.
Example:

Aapke Marks

Mid Term:
• Maths: 83/100
• English: 76/100

Final Term:
• Maths: 88/100
• English: 82/100
"""
    else:
        language_instruction = """
        Answer in English.
        """

    context = json.dumps(results, default=str, indent=2)

    prompt = f"""
Question:
{question}

Database Results:
{context}

Instructions:

You are answering a school-related question using ONLY the database results.

Rules:
- Never mention your reasoning.
- Never use phrases like "I assume", "it seems", or "probably".
- Never explain how you reached the answer.
- If records exist, present them in a clean and organized format.
- Use headings and bullet points where appropriate.
- Group related information together.
- Do not repeat the same information.
- Do not invent any information.
- If the database results are empty, reply:
  "I couldn't find this information in the database."

Special formatting rules:

If the question is about marks:
If the database contains marks:

Group the marks by exam first.

Format exactly like this:

Your Marks

Mid Term:
• Mathematics: 83/100
• English: 76/100
• Science: 79/100

Final Term:
• Mathematics: 88/100
• English: 82/100
• Science: 84/100

Rules:
- Create one section for each exam (Mid Term, Final Term, Unit Test, etc.).
- Under each section, list every subject and its marks.
- Do not write everything in one paragraph.
- Use bullet points.
- If an exam has no marks, do not include that section.


If the question is about attendance:
Attendance

• Total Classes: ...
• Attended: ...
• Attendance Percentage: ...

If the question is about assignments:
Assignments

• Science
  - Photosynthesis Project
  - Due: 10 Aug 2026

• English
  - Essay Writing
  - Due: 12 Aug 2026
"""
    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"""

You are a professional School AI Assistant.

The database results are factual.

Use ONLY the provided database results.

Rules:
- Never use outside knowledge.
- Never invent information.
- Never mention SQL.
- Never mention the database.
- Never mention reasoning.
- Keep the answer concise.
- Preserve headings and bullet points.
- Answer in the requested language.

If the database results are empty, reply exactly:

I couldn't find this information in the database.

{language_instruction}

Rules:
- Never say "I assume".
- Never explain your reasoning.
- Never mention the database.
- Never mention SQL.
- Always format the answer neatly.
- Use headings, bullets, and spacing.
- Keep the answer concise.                

Answer ONLY using the provided database results.

If the answer is not present in the results, say:
'I couldn't find this information in the database.'

Be concise and accurate.

{language_instruction}
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