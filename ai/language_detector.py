import re


def get_language(question: str) -> str:
    question = question.strip()

    # Hindi (Devanagari Unicode range)
    if re.search(r'[\u0900-\u097F]', question):
        return "HINDI"
    
    # Pure English sentence
    if re.fullmatch(r"[A-Za-z0-9\s?.',-]+", question):
        return "ENGLISH"

    # Common Hinglish words
    hinglish_words = [
    "mera", "meri", "mere",
    "dikhao", "dikha",
    "batao", "bata",
    "kitna", "kitni",
    "kab", "kaun",
    "kya", "kaise", "kaisi", "kyu",
    "hai", "hain", "ho",
    "ki", "ka", "ke",
    "apna", "apni", "apne",
    "mujhe", "tum", "aap",
    "dekhao", "dikhaiye"

    ]

    text = question.lower()

    if any(word in text.split() for word in hinglish_words):
        return "HINGLISH"

    return "ENGLISH"