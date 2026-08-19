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

from rag.intent_classifier import detect_intent
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

router = APIRouter(
    prefix="/chat",
    tags=["Chatbot"]
)


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str



@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user)
):
    print("========== /chat endpoint called ==========")
    try:

        # -----------------------------
        # Build User Context
        # -----------------------------
        user_context = {
            "user_id": current_user["user_id"],
            "email": current_user["email"],
            "role": current_user["role"],
            "student_id": None,
            "teacher_id": None,
            "parent_id": None,
            "children": []
        }

        # Student
        if current_user["role"] == "student":

           student = fetch_one("""
            SELECT student_id,
                               first_name,
                               last_name
            FROM students
            WHERE user_id=%s;
            """, (current_user["user_id"],))
           print("Current User:", current_user)
           print("Student Query Result:", student)
           
           if student:
               user_context["student_id"] = student["student_id"]
               user_context["first_name"] = student["first_name"].lower()
               user_context["last_name"] = student["last_name"].lower()
        # Teacher
        elif current_user["role"] == "teacher":

            teacher = fetch_one(
                """
                SELECT teacher_id
                FROM teachers
                WHERE user_id=%s;
                """,
                (current_user["user_id"],)
            )

            if teacher:
                user_context["teacher_id"] = teacher["teacher_id"]

        # Parent
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
                    user_context["parent_id"] = parent["parent_id"]
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

        # -----------------------------
        # Detect Language
        # -----------------------------
        language = get_language(request.question)

        print("\nDetected Language:")
        print(language)

        # -----------------------------
        # Translate Query
        # -----------------------------
        english_query = translate_query(
        request.question,
        language
        )
        print("Original Query:", request.question)
        print("Translated Query:", english_query)
        print("After translate:")
        print(repr(english_query))
        
        
        english_query = english_query.lower()
        
        NORMALIZATION = {
        "results": "marks",
        "result": "marks",
        "score": "marks",
        "scores": "marks",
        "grade": "marks",
        "grades": "marks",
        }

        for old, new in NORMALIZATION.items():
            english_query = re.sub(rf"\b{old}\b", new, english_query)
        """
        english_query = english_query.replace("maths", "mathematics")
        english_query = english_query.replace("math", "mathematics")
        english_query = english_query.replace("chem", "chemistry")
        english_query = english_query.replace("sci", "science")
        # Exam name normalization
        english_query = english_query.replace("midterm", "mid term")
        english_query = english_query.replace("mid-term", "mid term")
        english_query = english_query.replace("mid term exam", "mid term examination")
        english_query = english_query.replace("mid term examination", "mid term")

        english_query = english_query.replace("final exam", "final examination")
        english_query = english_query.replace("final term", "final examination")
        english_query = english_query.replace("annual exam", "final examination")
        """
        english_query = rewrite_query(english_query)
        
        print("\nEnglish Query:")
        print(english_query)
        

        # -----------------------------
        # Detect Intent
        # -----------------------------
        #intent = detect_intent(english_query)
        
        
        print("Before planner:")
        print(repr(english_query))
        
        plan = plan_query(english_query)
        # Apply deterministic fallback validation
        plan = validate_plan(plan, english_query)
        
        print("\n========== PLAN DEBUG ==========")
        print(plan)
        print("Intent:", plan.get("intent"))
        print("Confidence:", plan.get("confidence"))
        print("================================")

        if plan["intent"] == "unknown":
            return ChatResponse(
                answer="I'm not sure I understood your question. Could you please rephrase it?"
    )
        
        
        if plan["intent"] == "unknown":
            return ChatResponse(
        answer="I'm not sure I understood your question. Could you please rephrase it?"
    )
        print("\n===== EXECUTION PLAN =====")
        print(plan)
        print("==========================")

        """patterns = {
            "marks": r"\bmarks?\b",
            "attendance": r"\battendance\b",
            "assignment": r"\bassignments?\b|\bhomework\b",
            "timetable": r"\btimetable\b|\bschedule\b",
            "teacher": r"\bclass teacher\b|\bteacher\b",
            "profile": r"\broll number\b|\badmission number\b|\bdate of birth\b",
            "class": r"\bwhich class\b"
        }

        detected_intents = []

        for intent_name, pattern in patterns.items():
            if re.search(pattern, english_query):
                detected_intents.append(intent_name)
                """
        intent = plan["intent"]
        print("\nDetected Intent:")
        print(intent)

        """print("Detected SQL Intents:", intent)

        if len(intent) > 1:
            if language.upper() == "HINDI":
                return ChatResponse(
                    answer="कृपया एक समय में केवल एक शैक्षणिक प्रश्न पूछें।"
                )

            elif language.upper() == "HINGLISH":
                return ChatResponse(
                    answer="Please ek time par sirf ek academic question puchiye."
                )

            else:
                return ChatResponse(
                    answer="Please ask one academic question at a time."
                )
        print("\nDetected Intent:")
        print(intent) 
        """
    
        # -----------------------------
        # RAG
        # -----------------------------
        #if intent == "rag":
        if plan["source"] == "rag":

            answer = rag_answer(
                english_query,
                request.question,
                language
            )

            return ChatResponse(answer=answer)

        if current_user["role"] == "parent":
            children = user_context["children"]
            all_students = fetch_all("""
                    SELECT
                        student_id,
                        LOWER(first_name) AS first_name,
                        LOWER(last_name) AS last_name
                    FROM students;
                """)

            query = english_query.lower()

            # Handle "riya's", "rahul's", etc.
            query = query.replace("'s", "")
            query = query.replace("’s", "")

            requested_student = None

            # Find which student's name is mentioned
            for student in all_students:

                full = f"{student['first_name']} {student['last_name']}"

                if (
                re.search(rf"\b{re.escape(student['first_name'])}\b", query)
                or re.search(rf"\b{re.escape(student['last_name'])}\b", query)
                or re.search(rf"\b{re.escape(full)}\b", query)
                ):
                    requested_student = student
                    break

            print("Requested Student:", requested_student)
            print("Parent Children:", children)
            print("Matched:", matched if 'matched' in locals() else None)

            if requested_student:

                matched = None

                for child in children:

                    print(
                        "Comparing:",
                        child["student_id"],
                        requested_student["student_id"]
                    )

                    if int(child["student_id"]) == int(requested_student["student_id"]):
                        matched = child
                        break

                if matched:

                    user_context["student_id"] = matched["student_id"]

                    english_query = (
                        english_query
                        .replace(
                            f"{matched['first_name'].lower()} {matched['last_name'].lower()}",
                            ""
                        )
                        .replace(f"{matched['first_name'].lower()}'s", "")
                        .replace(f"{matched['first_name'].lower()}’s", "")
                        .replace(matched["first_name"].lower(), "")
                        .replace(matched["last_name"].lower(), "")
                        .replace("of", "")
                        .strip()
                    )

                    print("Updated Query:", english_query)
                    request.question = english_query

                else:

                    return ChatResponse(
                        answer="You can only access your own children's information."
                    )

            else:

                if len(children) == 1:

                    user_context["student_id"] = children[0]["student_id"]

                else:

                    names = "\n".join(
                        f"- {c['first_name']} {c['last_name']}"
                        for c in children
                    )

                    if language.upper() == "HINDI":

                        answer = f"""आपके खाते से एक से अधिक बच्चे जुड़े हुए हैं।

                    कृपया बताइए कि आपको किस बच्चे की जानकारी चाहिए।

                    आपके बच्चे:
                    {names}
                    """

                    elif language.upper() == "HINGLISH":

                        answer = f"""Aapke account se multiple children linked hain.

                    Please bataye kis child ki information chahiye.

                    Aapke children:
                    {names}
                    """

                    else:

                        answer = f"""You have multiple children linked to your account.

                    Please specify whose information you want.

                    Your children are:
                    {names}
                    """

                    return ChatResponse(answer=answer)    
        requested_name = None
        if current_user["role"] == "student":
            my_first = user_context["first_name"].lower()
            my_last = user_context["last_name"].lower()
            students = fetch_all("""
            SELECT LOWER(first_name) AS first_name,
            LOWER(last_name) AS last_name
            FROM students;
            """)
            for student in students:
                first = student["first_name"]
                last = student["last_name"]
                full = f"{first} {last}"
                if (
                re.search(rf"\b{re.escape(first)}\b", english_query) or
                re.search(rf"\b{re.escape(last)}\b", english_query) or
                re.search(rf"\b{re.escape(full)}\b", english_query)
                ):

        
                    if first != my_first or last != my_last:
                        return ChatResponse(
                            answer="BLOCKED BY NAME CHECK"
            )
        
        if plan["confidence"] < 0.4:
            return ChatResponse(
                answer="I'm not sure I understood your question. Could you please rephrase it?"
    )

        
        # -----------------------------
        # Generate SQL
        # -----------------------------
        
        llm_plan = plan.copy()
        llm_plan["constraints"] = dict(plan.get("constraints") or {})
        llm_plan["context"] = dict(plan.get("context") or {})
        sql = generate_sql(
            english_query,
            llm_plan,
            user_context
        )

        print("User Context Before SQL:", user_context)
        print("\nRaw SQL from LLM:")
        print(sql)

        # -----------------------------
        # Validate SQL
        # -----------------------------
        print("\n===== RAW SQL =====")
        print(sql)
        validated_sql = validate_sql(sql)
        
        print("\n===== AFTER VALIDATOR =====")
        print(validated_sql)
        
        # Deterministic marks/performance SQL already contains the
        # complete subject/exam/student constraints.  Do NOT pass it
        # through the old constraint engine, which can add stale or
        # incorrect subject aliases (e.g. science for computer science).
        if plan.get("intent") not in {"marks", "performance"}:
            validated_sql = apply_constraints(
                validated_sql,
                plan,
                user_context
            )
        else:
            print("\n===== CONSTRAINT ENGINE SKIPPED =====")
            print("Deterministic SQL already contains planner constraints.")

        print("\n===== AFTER CONSTRAINTS =====")
        print(validated_sql)
        

        if current_user["role"] == "student":
            my_id = user_context["student_id"]

            """ 
            Force the logged-in student's ID
            validated_sql = re.sub(
                r"student_id\s*=\s*\d+",
                f"student_id = {my_id}",
                validated_sql,
                flags=re.IGNORECASE,
            )"""

            print("\n========== SQL AUTH DEBUG ==========")
            print("Student ID:", my_id)
            print("Validated SQL:")
            print(validated_sql)
            print("===================================\n")

            student_match = re.search(
            r"student_id\s*=\s*(\d+)",
            validated_sql,
            re.IGNORECASE,
        )

        sql_student_id = None
        if student_match:
            sql_student_id = int(student_match.group(1))

        if sql_student_id != my_id:
            return ChatResponse(
            answer="You can only access your own academic information."
        )

        if any(table in validated_sql.lower()
               for table in ["fines", "books", "library"]):
            answer = rag_answer(
                english_query,
                request.question,
                language
            )

            return ChatResponse(answer=answer)

        print("\nValidated SQL:")
        print(validated_sql)
        # -----------------------------
        # Execute SQL
        # -----------------------------
        try:
            results = execute_sql(validated_sql)
        except Exception as e:
            print("SQL Error:", e)
            repair_prompt = f"""
            The following SQL failed.
            SQL:
            {validated_sql}
            Database Error:
            {str(e)}
            Fix the SQL.
            Rules:
            - Return ONLY SQL.
            - Use only existing tables and columns.
            - Do not invent columns.
            """
            try:
                repaired_sql = generate_sql(repair_prompt,llm_plan, user_context)
                validated_sql = validate_sql(repaired_sql)
                results = execute_sql(validated_sql)
                
                
                    
                if "timetable" in validated_sql.lower():
                    day_order = {
                        "Monday": 1,
                        "Tuesday": 2,
                        "Wednesday": 3,
                        "Thursday": 4,
                        "Friday": 5,
                        "Saturday": 6,
                    }

                    results = sorted(
                        results,
                        key=lambda r: (
                            day_order.get(r["day_of_week"], 99),
                            r["start_time"],
                        ),
                    )
            except Exception as e:
                print("SQL Error:", e)
                return ChatResponse(
                    answer="I couldn't process your request. Please try again."
    )
                """
        # -----------------------------
        # Format Response
        # -----------------------------
        
       
        sql_lower = validated_sql.lower()
        print("SQL LOWER:")
        print(repr(sql_lower))

        if plan["intent"] == "marks":
            print(">>> USING format_marks()")
            
            answer = format_marks(results,language)
            print("\nFormatted Answer:")
            print(answer)
            print("\n================ FORMATTED ANSWER ================\n")
            print(answer)
            print("\n==================================================\n")

        elif plan["intent"] == "attendance":

            answer = format_attendance(results,language)

        elif plan["intent"] == "timetable":

            answer = format_timetable(results,language)

        elif plan["intent"] == "assignments":

            answer = format_assignments(results,language)
            
        elif plan["intent"] == "teacher":
            answer = format_teacher(results, language)
            
           
            
        elif plan["intent"] == "profile":
            print(results)
            answer = format_profile(results, language)

        
        elif plan["intent"] == "class":
            answer = format_class(results, language)
            
        

        else:

            answer = generate_answer(
                request.question,
                results,
                language
            )

        return ChatResponse(answer=answer)
        """
        # -----------------------------
        # Analyze performance queries
        # -----------------------------
        if plan.get("intent") == "performance" or plan.get("analysis"):
            answer = analyze_results(
                english_query,
                plan,
                results
            )
        else:
            sql_lower = validated_sql.lower()
            print("SQL LOWER:")
            print(repr(sql_lower))

            if plan["intent"] == "marks":
                answer = format_marks(results, language)
            elif plan["intent"] == "attendance":
                answer = format_attendance(results, language)
            elif plan["intent"] == "timetable":
                answer = format_timetable(results, language)
            elif plan["intent"] == "assignments":
                answer = format_assignments(results, language)
            elif plan["intent"] == "teacher":
                answer = format_teacher(results, language)
            elif plan["intent"] == "profile":
                answer = format_profile(results, language)
            elif plan["intent"] == "class":
                answer = format_class(results, language)
            else:
                answer = generate_answer(
                    request.question,
                    results,
                    language
                )

        return ChatResponse(answer=answer)

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        traceback.print_exc()
        raise