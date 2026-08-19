def get_query_type(question: str):
    q = question.lower()

    if any(word in q for word in [
        "mark",
        "result",
        "score",
        "grade"
    ]):
        return "marks"

    elif any(word in q for word in [
        "attendance",
        "present",
        "absent"
    ]):
        return "attendance"

    elif any(word in q for word in [
        "timetable",
        "schedule",
        "class timing"
    ]):
        return "timetable"

    elif any(word in q for word in [
        "assignment",
        "homework"
    ]):
        return "assignment"

    elif any(word in q for word in [
        "fee",
        "fees",
        "payment"
    ]):
        return "fees"

    return "dynamic"