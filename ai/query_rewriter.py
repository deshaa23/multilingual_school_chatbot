import re


def rewrite_query(query: str) -> str:

    query = query.lower()

    replacements = {
        "math": "mathematics",
        "maths": "mathematics",
        "sci": "science",
        "chem": "chemistry",
        "eng": "english",

        "score": "marks",
        "scores": "marks",

        "homework": "assignments",

        "recent": "latest",
        "newest": "latest",

        "best subject": "highest marks subject",
        "worst subject": "lowest marks subject",

        "performance": "marks performance"
    }

    for old, new in replacements.items():
        query = re.sub(rf"\b{re.escape(old)}\b", new, query)

    return query