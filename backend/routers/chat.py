from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import traceback
import re

from backend.dependencies import get_current_user
from backend.database import fetch_one, fetch_all

from ai.sql_generator import generate_sql
from ai.sql_validator import validate_sql
from ai.query_executor import execute_sql
from ai.answer_generator import generate_answer
from ai.analyzer import analyze_results

from rag.rag_pipeline import rag_answer

from ai.language_detector import get_language
from ai.query_translator import translate_query
from ai.constraint_engine import apply_constraints
from ai.query_rewriter import rewrite_query
from ai.planner_validator import validate_plan

from ai.formatters import (
    format_marks,
    format_attendance,
    format_timetable,
    format_assignments,
    format_class,
    format_teacher,
    format_profile,
    format_performance,
)

from ai.planner import plan_query


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/chat",
    tags=["Chatbot"]
)


# =========================================================
# MODELS
# =========================================================

class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


# =========================================================
# SUBJECT ALIASES
# =========================================================

SUBJECT_ALIASES = {
    "math": "mathematics",
    "maths": "mathematics",

    "sci": "science",

    "sst": "social science",
    "social studies": "social science",
    "social sciences": "social science",

    "cs": "computer science",
    "comp science": "computer science",
    "computer": "computer science",
    "computers": "computer science",

    "eng": "english",
    "hin": "hindi",

    "phy": "physics",
    "chem": "chemistry",
    "bio": "biology",
}


# =========================================================
# SUBJECT DETECTION
# =========================================================

def detect_subject(question: str, plan: dict):
    """
    Get subject from the plan first.
    Fall back to deterministic detection from the question.
    """

    # -----------------------------------------------------
    # 1. Check constraints
    # -----------------------------------------------------

    constraints = plan.get("constraints") or {}

    subject = constraints.get("subject")

    if subject:
        return normalize_subject(subject)

    # -----------------------------------------------------
    # 2. Check context
    # -----------------------------------------------------

    context = plan.get("context") or {}

    subject = context.get("subject")

    if subject:
        return normalize_subject(subject)

    # -----------------------------------------------------
    # 3. Detect from question
    # -----------------------------------------------------

    q = question.lower()

    # Longest aliases first
    aliases = sorted(
        SUBJECT_ALIASES.keys(),
        key=len,
        reverse=True
    )

    for alias in aliases:

        if re.search(
            rf"\b{re.escape(alias)}\b",
            q
        ):
            return SUBJECT_ALIASES[alias]

    # Canonical names
    canonical_subjects = [
        "mathematics",
        "science",
        "social science",
        "english",
        "hindi",
        "computer science",
        "physics",
        "chemistry",
        "biology",
    ]

    for subject in sorted(
        canonical_subjects,
        key=len,
        reverse=True
    ):

        if re.search(
            rf"\b{re.escape(subject)}\b",
            q
        ):
            return subject

    return None


# =========================================================
# SUBJECT NORMALIZATION
# =========================================================

def normalize_subject(subject):
    """
    Convert aliases to canonical subject names.
    """

    if not subject:
        return None

    subject = str(subject).strip().lower()

    return SUBJECT_ALIASES.get(
        subject,
        subject
    )


# =========================================================
# EXAM DETECTION
# =========================================================

def detect_exam(question: str, plan: dict):
    """
    Detect exam from plan or question.
    """

    constraints = plan.get("constraints") or {}

    exam = constraints.get("exam")

    if exam:
        return normalize_exam(exam)

    q = question.lower()

    if re.search(
        r"\b(mid\s*term|midterm|mid-term|half\s*yearly|half-yearly)\b",
        q
    ):
        return "midterm"

    if re.search(
        r"\b(final|finals|annual|yearly|year\s*end)\b",
        q
    ):
        return "final"

    return None


# =========================================================
# EXAM NORMALIZATION
# =========================================================

def normalize_exam(exam):

    if not exam:
        return None

    exam = str(exam).strip().lower()

    if exam in {
        "mid term",
        "midterm",
        "mid-term",
        "half yearly",
        "half-yearly",
        "mid examination",
        "mid exam",
    }:
        return "midterm"

    if exam in {
        "final",
        "finals",
        "final exam",
        "final examination",
        "annual",
        "annual exam",
        "annual examination",
        "yearly",
        "year end",
    }:
        return "final"

    return exam


# =========================================================
# SQL NORMALIZATION
# =========================================================

def normalize_sql(sql: str):

    if not sql:
        return ""

    sql = sql.strip()

    # Remove markdown
    sql = re.sub(
        r"```sql",
        "",
        sql,
        flags=re.IGNORECASE
    )

    sql = sql.replace(
        "```",
        ""
    )

    # -----------------------------------------------------
    # IMPORTANT:
    # Fix accidental "10AND" / "10WHERE"
    # -----------------------------------------------------

    sql = re.sub(
        r"(\d)(AND|OR|WHERE)\b",
        r"\1 \2",
        sql,
        flags=re.IGNORECASE
    )

    # -----------------------------------------------------
    # Remove accidental duplicate semicolons
    # -----------------------------------------------------

    sql = re.sub(
        r";+\s*$",
        ";",
        sql
    )

    return sql.strip()


# =========================================================
# ENSURE WHERE CLAUSE
# =========================================================

def ensure_where(sql: str):

    if re.search(
        r"\bWHERE\b",
        sql,
        re.IGNORECASE
    ):
        return sql

    # Insert before GROUP BY / ORDER BY / LIMIT
    match = re.search(
        r"\b(GROUP\s+BY|ORDER\s+BY|LIMIT)\b",
        sql,
        re.IGNORECASE
    )

    if match:

        position = match.start()

        return (
            sql[:position]
            + "WHERE 1 = 1\n"
            + sql[position:]
        )

    return (
        sql.rstrip().rstrip(";")
        + "\nWHERE 1 = 1;"
    )


# =========================================================
# MARKS CONSTRAINT ENGINE
# =========================================================

def apply_marks_constraints(
    sql: str,
    question: str,
    plan: dict,
    student_id: int
):
    """
    Dedicated constraint engine for marks queries.

    IMPORTANT:
    We do NOT use the generic constraint_engine here.

    This prevents:
        s.subject_name
        10AND
        duplicate constraints
        incorrect exam conditions
    """

    if not sql:
        raise ValueError(
            "Generated SQL is empty."
        )

    sql = normalize_sql(sql)

    # -----------------------------------------------------
    # SECURITY:
    # Force logged-in student's ID.
    # -----------------------------------------------------

    student_pattern = re.compile(
        r"m\.student_id\s*=\s*\d+",
        re.IGNORECASE
    )

    if student_pattern.search(sql):

        sql = student_pattern.sub(
            f"m.student_id = {int(student_id)}",
            sql
        )

    else:

        sql = ensure_where(sql)

        sql = re.sub(
            r"\bWHERE\b",
            f"WHERE m.student_id = {int(student_id)} AND ",
            sql,
            count=1,
            flags=re.IGNORECASE
        )

    # -----------------------------------------------------
    # SUBJECT
    # -----------------------------------------------------

    subject = detect_subject(
        question,
        plan
    )

    if subject:

        # Remove existing subject conditions generated
        # by the LLM so we don't create duplicates.
        #
        # We intentionally keep this conservative.
        # The SQL generator normally already generates
        # the correct condition.

        subject_condition = (
            "LOWER(sub.subject_name) = "
            f"LOWER('{subject}')"
        )

        # Check whether subject is already constrained.
        existing_subject = re.search(
            r"LOWER\s*\(\s*sub\.subject_name\s*\)"
            r"\s*(?:=|LIKE|ILIKE)",
            sql,
            re.IGNORECASE
        )

        if not existing_subject:

            # Insert after WHERE
            sql = re.sub(
                r"\bWHERE\b",
                (
                    "WHERE "
                    + subject_condition
                    + " AND "
                ),
                sql,
                count=1,
                flags=re.IGNORECASE
            )

    # -----------------------------------------------------
    # EXAM
    # -----------------------------------------------------

    exam = detect_exam(
        question,
        plan
    )

    if exam:

        # Only apply an exam condition if the query
        # actually joins exams.
        has_exam_join = re.search(
            r"\b(?:JOIN|LEFT\s+JOIN|INNER\s+JOIN)"
            r"\s+exams\s+e\b",
            sql,
            re.IGNORECASE
        )

        if has_exam_join:

            existing_exam = re.search(
                r"LOWER\s*\(\s*e\.exam_name\s*\)"
                r"|e\.exam_name\s+(?:LIKE|ILIKE|=)",
                sql,
                re.IGNORECASE
            )

            if not existing_exam:

                if exam == "midterm":

                    exam_condition = """
(
    LOWER(e.exam_name) LIKE '%mid%'
    OR LOWER(e.exam_name) LIKE '%half%'
    OR LOWER(e.exam_name) LIKE '%term 1%'
    OR LOWER(e.exam_name) LIKE '%first term%'
    OR LOWER(e.exam_name) LIKE '%first semester%'
)
""".strip()

                elif exam == "final":

                    exam_condition = """
(
    LOWER(e.exam_name) LIKE '%final%'
    OR LOWER(e.exam_name) LIKE '%annual%'
    OR LOWER(e.exam_name) LIKE '%year end%'
    OR LOWER(e.exam_name) LIKE '%term 2%'
    OR LOWER(e.exam_name) LIKE '%second term%'
    OR LOWER(e.exam_name) LIKE '%second semester%'
)
""".strip()

                else:
                    exam_condition = None

                if exam_condition:

                    # Always add safely after WHERE.
                    sql = re.sub(
                        r"\bWHERE\b",
                        (
                            "WHERE "
                            + exam_condition
                            + "\nAND "
                        ),
                        sql,
                        count=1,
                        flags=re.IGNORECASE
                    )

    # -----------------------------------------------------
    # FINAL SAFETY NORMALIZATION
    # -----------------------------------------------------

    sql = normalize_sql(sql)

    # -----------------------------------------------------
    # NEVER allow alias `s` unless it exists.
    # -----------------------------------------------------

    if re.search(
        r"\bs\.subject_name\b",
        sql,
        re.IGNORECASE
    ):

        # If subjects is joined as `sub`, repair it.
        if re.search(
            r"\bsubjects\s+sub\b",
            sql,
            re.IGNORECASE
        ):
            sql = re.sub(
                r"\bs\.subject_name\b",
                "sub.subject_name",
                sql,
                flags=re.IGNORECASE
            )

    # -----------------------------------------------------
    # Force student ownership one final time.
    # -----------------------------------------------------

    student_matches = re.findall(
        r"m\.student_id\s*=\s*(\d+)",
        sql,
        re.IGNORECASE
    )

    if not student_matches:

        raise ValueError(
            "Student ownership condition is missing."
        )

    if any(
        int(value) != int(student_id)
        for value in student_matches
    ):

        raise ValueError(
            "Unauthorized student_id detected in SQL."
        )

    return sql.strip().rstrip(";") + ";"


# =========================================================
# STUDENT SQL AUTHORIZATION
# =========================================================

def verify_student_sql(
    sql: str,
    student_id: int
):
    """
    Final security check.

    Academic SQL must always contain:
        m.student_id = logged_in_student_id
    """

    matches = re.findall(
        r"\bm\.student_id\s*=\s*(\d+)",
        sql,
        re.IGNORECASE
    )

    if not matches:

        raise ValueError(
            "SQL does not contain a student ownership condition."
        )

    for value in matches:

        if int(value) != int(student_id):

            raise ValueError(
                "You can only access your own academic information."
            )

    return True


# =========================================================
# REPAIR SQL
# =========================================================

def repair_sql(
    failed_sql: str,
    error: Exception,
    question: str,
    plan: dict,
    student_id: int,
    user_context: dict
):
    """
    Repair SQL using the LLM.

    The repaired SQL is then passed through the same
    deterministic constraint process.
    """

    repair_prompt = f"""
The following PostgreSQL SELECT query failed.

USER QUESTION:
{question}

EXECUTION PLAN:
{plan}

FAILED SQL:
{failed_sql}

DATABASE ERROR:
{str(error)}

STUDENT ID:
{student_id}

Fix the SQL.

RULES:

1. Return ONLY PostgreSQL SELECT SQL.
2. Use only existing tables and columns.
3. Never invent columns.
4. Preserve the user's intent.
5. Preserve student_id = {student_id}.
6. Do not access another student's data.
7. If subjects is joined as `sub`, use `sub.subject_name`.
8. Do NOT use `s.subject_name` unless the query explicitly contains:
   subjects s
9. marks.subject_id does not exist.
10. Subject relationship:
    marks
    -> class_subjects
    -> subjects
11. Exam relationship:
    marks
    -> exams
12. Do not use UPDATE.
13. Do not use DELETE.
14. Do not use INSERT.
15. Do not use DROP.
16. Do not use ALTER.
17. Return ONLY SELECT SQL.
"""

    repair_plan = dict(plan)

    # Do not let the SQL generator accidentally
    # reapply constraints.
    repair_plan["constraints"] = {}

    repaired_sql = generate_sql(
        repair_prompt,
        repair_plan,
        user_context
    )

    repaired_sql = normalize_sql(
        repaired_sql
    )

    # -----------------------------------------------------
    # Reapply deterministic constraints.
    # -----------------------------------------------------

    if plan.get("intent") == "marks":

        repaired_sql = apply_marks_constraints(
            repaired_sql,
            question,
            plan,
            student_id
        )

    else:

        repaired_sql = apply_constraints(
            repaired_sql,
            plan,
            user_context
        )

    repaired_sql = normalize_sql(
        repaired_sql
    )

    return repaired_sql


# =========================================================
# CHAT ENDPOINT
# =========================================================

@router.post(
    "/",
    response_model=ChatResponse
)
def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user)
):

    print(
        "========== /chat endpoint called =========="
    )

    try:

        # =================================================
        # USER CONTEXT
        # =================================================

        user_context = {
            "user_id": current_user["user_id"],
            "email": current_user["email"],
            "role": current_user["role"],
            "student_id": None,
            "teacher_id": None,
            "parent_id": None,
            "children": []
        }

        # -------------------------------------------------
        # STUDENT
        # -------------------------------------------------

        if current_user["role"] == "student":

            student = fetch_one(
                """
                SELECT
                    student_id,
                    first_name,
                    last_name
                FROM students
                WHERE user_id = %s;
                """,
                (current_user["user_id"],)
            )

            print(
                "Current User:",
                current_user
            )

            print(
                "Student Query Result:",
                student
            )

            if not student:

                raise ValueError(
                    "Student profile could not be identified."
                )

            user_context["student_id"] = (
                student["student_id"]
            )

            user_context["first_name"] = (
                student["first_name"].lower()
            )

            user_context["last_name"] = (
                student["last_name"].lower()
            )

        # -------------------------------------------------
        # TEACHER
        # -------------------------------------------------

        elif current_user["role"] == "teacher":

            teacher = fetch_one(
                """
                SELECT teacher_id
                FROM teachers
                WHERE user_id = %s;
                """,
                (current_user["user_id"],)
            )

            if teacher:

                user_context["teacher_id"] = (
                    teacher["teacher_id"]
                )

        # -------------------------------------------------
        # PARENT
        # -------------------------------------------------

        elif current_user["role"] == "parent":

            parent = fetch_one(
                """
                SELECT parent_id
                FROM parents
                WHERE user_id = %s;
                """,
                (current_user["user_id"],)
            )

            if parent:

                user_context["parent_id"] = (
                    parent["parent_id"]
                )

                children = fetch_all(
                    """
                    SELECT
                        s.student_id,
                        s.first_name,
                        s.last_name
                    FROM parent_students ps
                    JOIN students s
                        ON ps.student_id = s.student_id
                    WHERE ps.parent_id = %s;
                    """,
                    (parent["parent_id"],)
                )

                user_context["children"] = children

        # =================================================
        # LANGUAGE
        # =================================================

        language = get_language(
            request.question
        )

        print(
            "\nDetected Language:",
            language
        )

        # =================================================
        # TRANSLATE
        # =================================================

        english_query = translate_query(
            request.question,
            language
        )

        print(
            "Original Query:",
            request.question
        )

        print(
            "Translated Query:",
            english_query
        )

        english_query = (
            english_query
            .lower()
            .strip()
        )

        # =================================================
        # BASIC NORMALIZATION
        # =================================================

        NORMALIZATION = {
            "results": "marks",
            "result": "marks",
            "score": "marks",
            "scores": "marks",
            "grade": "marks",
            "grades": "marks",
        }

        for old, new in NORMALIZATION.items():

            english_query = re.sub(
                rf"\b{re.escape(old)}\b",
                new,
                english_query
            )

        english_query = rewrite_query(
            english_query
        )

        english_query = (
            english_query
            .lower()
            .strip()
        )

        print(
            "\nEnglish Query:"
        )

        print(
            english_query
        )

        # =================================================
        # PLAN
        # =================================================

        print(
            "\n========== QUERY ROUTING =========="
        )

        plan = plan_query(
            english_query
        )

        plan = validate_plan(
            plan,
            english_query
        )

        print(
            "\n========== FINAL PLAN =========="
        )

        print(plan)

        print(
            "Intent:",
            plan.get("intent")
        )

        print(
            "Metric:",
            plan.get("metric")
        )

        print(
            "Source:",
            plan.get("source")
        )

        print(
            "Confidence:",
            plan.get("confidence")
        )

        print(
            "Constraints:",
            plan.get("constraints")
        )

        print(
            "================================"
        )

        # =================================================
        # UNKNOWN
        # =================================================

        if plan.get("intent") == "unknown":

            return ChatResponse(
                answer=(
                    "I'm not sure I understood your question. "
                    "Could you please rephrase it?"
                )
            )

        # =================================================
        # LOW CONFIDENCE
        # =================================================

        if plan.get("confidence", 0) < 0.4:

            return ChatResponse(
                answer=(
                    "I'm not sure I understood your question. "
                    "Could you please rephrase it?"
                )
            )

        # =================================================
        # RAG
        # =================================================

        if plan.get("source") == "rag":

            answer = rag_answer(
                english_query,
                request.question,
                language
            )

            return ChatResponse(
                answer=answer
            )

        # =================================================
        # PARENT ACCESS
        # =================================================

        if current_user["role"] == "parent":

            children = user_context[
                "children"
            ]

            # -------------------------------------------------
            # If only one child
            # -------------------------------------------------

            if len(children) == 1:

                user_context["student_id"] = (
                    children[0]["student_id"]
                )

            # -------------------------------------------------
            # Multiple children
            # -------------------------------------------------

            elif len(children) > 1:

                names = "\n".join(
                    f"- {c['first_name']} {c['last_name']}"
                    for c in children
                )

                if language.upper() == "HINDI":

                    return ChatResponse(
                        answer=(
                            "आपके खाते से एक से अधिक बच्चे जुड़े हुए हैं।\n\n"
                            "कृपया बताइए कि आपको किस बच्चे की जानकारी चाहिए।\n\n"
                            f"आपके बच्चे:\n{names}"
                        )
                    )

                if language.upper() == "HINGLISH":

                    return ChatResponse(
                        answer=(
                            "Aapke account se multiple children linked hain.\n\n"
                            "Please bataye kis child ki information chahiye.\n\n"
                            f"Aapke children:\n{names}"
                        )
                    )

                return ChatResponse(
                    answer=(
                        "You have multiple children linked to your account.\n\n"
                        "Please specify whose information you want.\n\n"
                        f"Your children are:\n{names}"
                    )
                )

        # =================================================
        # STUDENT SECURITY
        # =================================================

        student_id = user_context.get(
            "student_id"
        )

        if (
            current_user["role"] == "student"
            and not student_id
        ):

            raise ValueError(
                "Student profile could not be identified."
            )

        # =================================================
        # GENERATE SQL
        # =================================================

        print(
            "\n===== SQL GENERATOR ====="
        )

        print(
            "Question:",
            english_query
        )

        print(
            "Student ID:",
            student_id
        )

        print(
            "Intent:",
            plan.get("intent")
        )

        print(
            "Metric:",
            plan.get("metric")
        )

        print(
            "Constraints:",
            plan.get("constraints")
        )

        # -------------------------------------------------
        # SQL generator should not receive constraints
        # that will later be deterministically applied.
        # -------------------------------------------------

        llm_plan = dict(plan)

        llm_plan["constraints"] = {}

        sql = generate_sql(
            english_query,
            llm_plan,
            user_context
        )

        sql = normalize_sql(
            sql
        )

        print(
            "\n========== RAW SQL =========="
        )

        print(sql)

        print(
            "============================="
        )

        # =================================================
        # VALIDATE SQL
        # =================================================

        validated_sql = validate_sql(
            sql
        )

        validated_sql = normalize_sql(
            validated_sql
        )

        print(
            "\n========== VALIDATED SQL =========="
        )

        print(validated_sql)

        print(
            "==================================="
        )

        # =================================================
        # CONSTRAINT ENGINE
        # =================================================

        if plan.get("intent") == "marks":

            # IMPORTANT:
            # Do NOT call generic apply_constraints().
            #
            # It was producing:
            #     LOWER(s.subject_name)
            #
            # even though the query uses:
            #     subjects sub
            #
            # It was also producing:
            #     10AND
            #
            validated_sql = apply_marks_constraints(
                validated_sql,
                english_query,
                plan,
                student_id
            )

        else:

            validated_sql = apply_constraints(
                validated_sql,
                plan,
                user_context
            )

        validated_sql = normalize_sql(
            validated_sql
        )

        print(
            "\n===== FINAL SQL FROM CONSTRAINT ENGINE ====="
        )

        print(validated_sql)

        print(
            "============================================"
        )

        # =================================================
        # FINAL SECURITY CHECK
        # =================================================

        if (
            current_user["role"] == "student"
            and plan.get("intent") in {
                "marks",
                "attendance",
                "assignments",
                "timetable",
                "exams",
                "performance",
            }
        ):

            verify_student_sql(
                validated_sql,
                student_id
            )

        print(
            "\n========== SQL AUTH DEBUG =========="
        )

        print(
            "Student ID:",
            student_id
        )

        print(
            "Validated SQL:",
            validated_sql
        )

        print(
            "===================================="
        )

        # =================================================
        # RAG TABLE CHECK
        # =================================================

        sql_lower = validated_sql.lower()

        if any(
            table in sql_lower
            for table in [
                "fines",
                "books",
                "library"
            ]
        ):

            answer = rag_answer(
                english_query,
                request.question,
                language
            )

            return ChatResponse(
                answer=answer
            )

        # =================================================
        # EXECUTE SQL
        # =================================================

        print(
            "\n========== EXECUTING SQL =========="
        )

        print(
            validated_sql
        )

        try:

            results = execute_sql(
                validated_sql
            )

        except Exception as sql_error:

            print(
                "\nSQL ERROR:"
            )

            traceback.print_exc()

            # -------------------------------------------------
            # Attempt one repair
            # -------------------------------------------------

            try:

                repaired_sql = repair_sql(
                    validated_sql,
                    sql_error,
                    english_query,
                    plan,
                    student_id,
                    user_context
                )

                print(
                    "\n========== REPAIRED SQL =========="
                )

                print(
                    repaired_sql
                )

                # Final security check
                if (
                    current_user["role"] == "student"
                    and plan.get("intent") in {
                        "marks",
                        "attendance",
                        "assignments",
                        "timetable",
                        "exams",
                        "performance",
                    }
                ):

                    verify_student_sql(
                        repaired_sql,
                        student_id
                    )

                results = execute_sql(
                    repaired_sql
                )

                validated_sql = repaired_sql

            except Exception as repair_error:

                print(
                    "\nSQL REPAIR FAILED:"
                )

                traceback.print_exc()

                return ChatResponse(
                    answer=(
                        "I couldn't process your request. "
                        "Please try again."
                    )
                )

        # =================================================
        # DEBUG RESULTS
        # =================================================

        print(
            "\n========== SQL RESULTS =========="
        )

        print(results)

        print(
            "================================="
        )

        # =================================================
        # FORMAT RESPONSE
        # =================================================

        intent = plan.get(
            "intent"
        )

        metric = plan.get(
            "metric"
        )

        # -------------------------------------------------
        # MARKS
        # -------------------------------------------------

        if intent == "marks":

            answer = format_marks(
                results,
                language
            )

        # -------------------------------------------------
        # ATTENDANCE
        # -------------------------------------------------

        elif intent == "attendance":

            answer = format_attendance(
                results,
                language
            )

        # -------------------------------------------------
        # TIMETABLE
        # -------------------------------------------------

        elif intent == "timetable":

            answer = format_timetable(
                results,
                language
            )

        # -------------------------------------------------
        # ASSIGNMENTS
        # -------------------------------------------------

        elif intent == "assignments":

            answer = format_assignments(
                results,
                language
            )

        # -------------------------------------------------
        # TEACHER
        # -------------------------------------------------

        elif intent == "teacher":

            answer = format_teacher(
                results,
                language
            )

        # -------------------------------------------------
        # PROFILE
        # -------------------------------------------------

        elif intent == "profile":

            answer = format_profile(
                results,
                language
            )

        # -------------------------------------------------
        # CLASS
        # -------------------------------------------------

        elif intent == "class":

            answer = format_class(
                results,
                language
            )

        # -------------------------------------------------
        # PERFORMANCE
        # -------------------------------------------------

        elif intent == "performance":

            answer = format_performance(
                results,
                language
            )

        # -------------------------------------------------
        # FALLBACK
        # -------------------------------------------------

        else:

            answer = generate_answer(
                request.question,
                results,
                language
            )

        # =================================================
        # FINAL RESPONSE
        # =================================================

        print(
            "\n========== FINAL ANSWER =========="
        )

        print(answer)

        print(
            "=================================="
        )

        return ChatResponse(
            answer=answer
        )

    # =====================================================
    # VALUE ERROR
    # =====================================================

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    # =====================================================
    # UNEXPECTED ERROR
    # =====================================================

    except Exception as e:

        traceback.print_exc()

        raise