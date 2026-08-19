import ollama

MODEL = "llama3:latest"


def translate(text: str, language: str) -> str:
    """
    Translate an English answer into the requested language.
    Preserves all formatting and bullet points.
    """

    language = language.upper()

    if language == "ENGLISH":
        return text

    if language == "HINDI":

        instruction = """
Translate the following English text into natural Hindi.

Rules:
- Use only Devanagari script.
- Preserve every heading.
- Preserve every bullet point.
- Preserve every sentence.
- Do NOT summarize.
- Do NOT omit information.
- Do NOT add information.
"""

    else:

        instruction = """
Translate the following English text into natural Indian Hinglish.

Rules:
- Use English letters only.
- Do NOT use Hindi script.
- Preserve every heading.
- Preserve every bullet point.
- Preserve every sentence.
- Do NOT summarize.
- Do NOT omit information.
- Do NOT add information.

Example:

Library Rules

• Books ko due date se pehle return karna zaroori hai.
• Library mein silence maintain karni chahiye.
"""

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": instruction
            },
            {
                "role": "user",
                "content": text
            }
        ],
        options={
            "temperature": 0
        }
    )

    return response["message"]["content"].strip()