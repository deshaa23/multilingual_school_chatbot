import ollama

MODEL = "llama3:latest"


def generate_answer(prompt: str) -> str:
    """
    Always generate the answer in English.
    Translation is handled separately.
    """

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """
You are an AI School Assistant.

The prompt already contains:
- the user's question
- the retrieved school documents

Answer ONLY using the retrieved school documents.

IMPORTANT RULES:

- Answer ONLY in English.
- NEVER use outside knowledge.
- NEVER invent information.
- NEVER guess.
- NEVER summarize unless the user explicitly asks.
- Preserve ALL bullet points.
- Preserve headings.
- Include ALL relevant rules, policies and steps.
- Do NOT omit information.
- Do NOT merge multiple rules.
- Do NOT generate examples.
- Do NOT mention context, retrieval, documents, SQL or AI.

If the answer is not found, reply exactly:

I couldn't find this information in the available school documents.
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