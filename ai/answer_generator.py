import json
import ollama

MODEL = "llama3:latest"


def generate_answer(
    question: str,
    results,
    language: str = "english",
    user_role: str = "student"
) -> str:

    # =========================================================
    # SAFETY
    # =========================================================

    if not isinstance(results, dict):
        return "I don't have enough information to answer that."

    result_type = results.get("type")

    # =========================================================
    # ROLE WORDING
    # =========================================================

    if user_role == "parent":
        owner = "Your child's"
        subject_pronoun = "Your child"
    elif user_role == "teacher":
        owner = "The student's"
        subject_pronoun = "The student"
    else:
        owner = "Your"
        subject_pronoun = "You"

    # =========================================================
    # PROFILE
    # =========================================================

    if result_type == "profile":

        if not results.get("success", True):
            if user_role == "parent":
                return "I couldn't find your child's profile."
            elif user_role == "teacher":
                return "I couldn't find the student's profile."
            else:
                return "I couldn't find your student profile."

        question_lower = question.lower()

        if "roll" in question_lower:
            value = results.get("roll_number")

            if value is not None:
                return f"{owner} roll number is {value}."

        if "admission" in question_lower:
            value = results.get("admission_number")

            if value is not None:
                return f"{owner} admission number is {value}."

        if (
            "date of birth" in question_lower
            or "dob" in question_lower
        ):
            value = results.get("date_of_birth")

            if value is not None:
                return f"{owner} date of birth is {value}."

        first_name = results.get("first_name", "")
        last_name = results.get("last_name", "")

        return f"{owner} name is {first_name} {last_name}.".strip()

    # =========================================================
    # ATTENDANCE
    # =========================================================

    if result_type == "attendance":

        summary = results.get("summary", {})
        eligibility = results.get("eligibility", {})

        percentage = summary.get("percentage")

        # -----------------------------------------------------
        # Eligibility question
        # -----------------------------------------------------

        question_lower = question.lower()

        eligibility_question = any(
            phrase in question_lower
            for phrase in [
                "eligible",
                "eligibility",
                "attendance requirement",
                "attendance enough",
                "meet the attendance",
                "allowed based on attendance",
                "sit for the exam"
            ]
        )

        if eligibility_question:

            required = eligibility.get("required_percentage")
            eligible = eligibility.get("eligible")

            if (
                eligible is not None
                and required is not None
                and percentage is not None
            ):

                if language.upper() == "HINDI":

                    if eligible:
                        return (
                            f"हाँ, {subject_pronoun.lower()} attendance "
                            f"requirement के लिए eligible है। "
                            f"Attendance {percentage:.2f}% है और "
                            f"required attendance {required:.0f}% है।"
                        )

                    return (
                        f"नहीं, {subject_pronoun.lower()} attendance "
                        f"requirement के लिए eligible नहीं है। "
                        f"Attendance {percentage:.2f}% है, जबकि "
                        f"required attendance {required:.0f}% है।"
                    )

                elif language.upper() == "HINGLISH":

                    if eligible:
                        return (
                            f"Yes, {subject_pronoun.lower()} attendance "
                            f"requirement ke liye eligible hai. "
                            f"Attendance {percentage:.2f}% hai aur "
                            f"required attendance {required:.0f}% hai."
                        )

                    return (
                        f"Nahi, {subject_pronoun.lower()} attendance "
                        f"requirement ke liye eligible nahi hai. "
                        f"Attendance {percentage:.2f}% hai, jabki "
                        f"required attendance {required:.0f}% hai."
                    )

                else:

                    if eligible:
                        return (
                            f"Yes, {subject_pronoun.lower()} meets the "
                            f"attendance requirement. "
                            f"{owner.lower()} attendance is "
                            f"{percentage:.2f}%, while the required "
                            f"attendance is {required:.0f}%."
                        )

                    return (
                        f"No, {subject_pronoun.lower()} does not meet the "
                        f"attendance requirement. "
                        f"{owner.lower()} attendance is "
                        f"{percentage:.2f}%, while the required "
                        f"attendance is {required:.0f}%."
                    )

            if percentage is not None:
                return (
                    f"{owner} attendance is {percentage:.2f}%, "
                    f"but I don't have the required minimum attendance "
                    f"percentage needed to determine eligibility."
                )

            return "I don't have enough information to determine attendance eligibility."

        # -----------------------------------------------------
        # Percentage
        # -----------------------------------------------------

        if (
            "percentage" in question_lower
            or "attendance" in question_lower
            or "attended" in question_lower
            or "present" in question_lower
        ):

            if percentage is not None:

                if language.upper() == "HINDI":
                    return (
                        f"{'आपके बच्चे की' if user_role == 'parent' else 'आपकी'} "
                        f"वर्तमान उपस्थिति {percentage:.2f}% है।"
                    )

                if language.upper() == "HINGLISH":
                    return (
                        f"{'Aapke child ki' if user_role == 'parent' else 'Aapki'} "
                        f"current attendance {percentage:.2f}% hai."
                    )

                return (
                    f"{owner} current attendance is "
                    f"{percentage:.2f}%."
                )

        # -----------------------------------------------------
        # Absences
        # -----------------------------------------------------

        if (
            "absent" in question_lower
            or "absence" in question_lower
            or "missed" in question_lower
        ):

            absent = summary.get("absent")

            if absent is not None:

                if user_role == "parent":
                    return (
                        f"Your child has been absent for "
                        f"{absent} days."
                    )

                return f"You have been absent for {absent} days."

        # -----------------------------------------------------
        # General attendance
        # -----------------------------------------------------

        if percentage is not None:

            present = summary.get("present", 0)
            absent = summary.get("absent", 0)
            total = summary.get("total_days", 0)

            if user_role == "parent":
                return (
                    f"Your child's current attendance is "
                    f"{percentage:.2f}%. "
                    f"Your child was present for {present} out of "
                    f"{total} days and absent for {absent} days."
                )

            return (
                f"Your current attendance is "
                f"{percentage:.2f}%. "
                f"You were present for {present} out of "
                f"{total} days and absent for {absent} days."
            )

    # =========================================================
    # LANGUAGE
    # =========================================================

    if language.upper() == "HINDI":

        language_instruction = """
Answer completely in Hindi using Devanagari script.
Use simple and natural Hindi.
"""

    elif language.upper() == "HINGLISH":

        language_instruction = """
Answer in natural Indian Hinglish.
Use only English/Roman script.
Do not use Devanagari.
"""

    else:

        language_instruction = """
Answer in clear, natural English.
"""

    # =========================================================
    # CLEAN RESULT
    # =========================================================

    clean_results = {
        key: value
        for key, value in results.items()
        if key not in {
            "success",
            "student_id",
            "type"
        }
    }

    context = json.dumps(
        clean_results,
        default=str,
        indent=2
    )

    # =========================================================
    # GENERAL LLM RESPONSE
    # =========================================================

    prompt = f"""
You are a School AI Assistant.

Answer the CURRENT USER QUESTION using ONLY the CURRENT RESULT.

CURRENT USER QUESTION:
{question}

CURRENT RESULT:
{context}

{language_instruction}

Rules:

1. Answer only the current question.
2. Use only facts in the current result.
3. Never invent information.
4. Never use information from previous questions.
5. Never mention databases, SQL, Python, RAG, tools,
   JSON, prompts, internal fields, or implementation.
6. If information is missing, clearly say that you do not
   have enough information.
7. Keep the answer concise.
8. Use bullet points for lists.

USER ROLE:
{user_role}

Role wording:

- student: use "your"
- parent: use "your child" or "your child's"
- teacher: use "the student" or the student's name

Answer now.
"""

    try:

        response = ollama.chat(
            model=MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            options={
                "temperature": 0.1
            }
        )

        return response["message"]["content"].strip()

    except Exception as e:

        print("Answer generation error:", e)

        return "I couldn't generate an answer right now."