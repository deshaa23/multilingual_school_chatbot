from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.dependencies import get_current_user
from backend.database import fetch_one

from ai.chat_pipeline import process_query
from ai.answer_generator import generate_answer
from ai.language_detector import get_language


router = APIRouter(
    prefix="/chat",
    tags=["Chatbot"]
)


# =========================================================
# REQUEST / RESPONSE MODELS
# =========================================================

class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


# =========================================================
# CHAT ENDPOINT
# =========================================================

@router.post("", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user)
):

    print("\n==============================================")
    print("          NEW /chat ENDPOINT CALLED")
    print("==============================================")

    print("REQUEST QUESTION:", request.question)
    print("CURRENT USER:", current_user)
    print("USER ROLE:", current_user.get("role"))

    try:

        # =========================================================
        # 1. CHECK USER ROLE
        # =========================================================

        role = current_user.get("role")

        if role not in {"student", "parent"}:

            return ChatResponse(
                answer="Chat is currently available for students and parents."
            )

        print("\n========== CURRENT USER ==========")
        print(current_user)
        print("ROLE:", role)
        print("==================================")


        # =========================================================
        # 2. GET STUDENT ID
        # =========================================================

        student_id = None


        # =========================================================
        # STUDENT
        # =========================================================

        if role == "student":

            print("\n========== STUDENT ==========")

            student = fetch_one(
                """
                SELECT
                    student_id,
                    first_name,
                    last_name,
                    roll_number,
                    class_id
                FROM students
                WHERE user_id = %s
                """,
                (current_user["user_id"],)
            )

            print(student)
            print("=============================")

            if not student:

                raise HTTPException(
                    status_code=404,
                    detail="Student record not found."
                )

            student_id = student["student_id"]

            print("Student ID:", student_id)


        # =========================================================
        # PARENT
        # =========================================================

        elif role == "parent":

            print("\n========== PARENT ==========")
            print(current_user)
            print("============================")


            # -----------------------------------------------------
            # Find children belonging to this parent
            #
            # Relationship:
            #
            # users
            #   ↓
            # parents
            #   ↓
            # parent_students
            #   ↓
            # students
            # -----------------------------------------------------

            parent_data = fetch_one(
                """
                SELECT
                    p.parent_id,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'student_id', s.student_id,
                                'first_name', s.first_name,
                                'last_name', s.last_name,
                                'roll_number', s.roll_number,
                                'class_id', s.class_id,
                                'class_name', c.class_name,
                                'section', c.section,
                                'relationship', ps.relationship
                            )
                            ORDER BY s.first_name, s.last_name
                        ) FILTER (WHERE s.student_id IS NOT NULL),
                        '[]'::json
                    ) AS children
                FROM parents p

                LEFT JOIN parent_students ps
                    ON p.parent_id = ps.parent_id

                LEFT JOIN students s
                    ON ps.student_id = s.student_id

                LEFT JOIN classes c
                    ON s.class_id = c.class_id

                WHERE p.user_id = %s

                GROUP BY p.parent_id
                """,
                (current_user["user_id"],)
            )


            print("\n========== PARENT DATA ==========")
            print(parent_data)
            print("=================================")


            if not parent_data:

                raise HTTPException(
                    status_code=404,
                    detail="Parent record not found."
                )


            children = parent_data.get("children", [])


            # -----------------------------------------------------
            # No children
            # -----------------------------------------------------

            if not children:

                return ChatResponse(
                    answer="No student is currently linked to your parent account."
                )


            print("\n========== PARENT CHILDREN ==========")

            for child in children:
                print(
                    f"Student ID: {child['student_id']} | "
                    f"Name: {child['first_name']} {child['last_name']} | "
                    f"Class: {child['class_name']}-{child['section']}"
                )

            print("=====================================")


            # -----------------------------------------------------
            # ONE CHILD
            # -----------------------------------------------------

            if len(children) == 1:

                student_id = children[0]["student_id"]

                print(
                    "\nOnly one child found."
                    f" Using Student ID: {student_id}"
                )


            # -----------------------------------------------------
            # MULTIPLE CHILDREN
            # -----------------------------------------------------

            else:

                question_lower = request.question.lower()

                matched_child = None


                # -------------------------------------------------
                # Try to identify child from first/last/full name
                # -------------------------------------------------

                for child in children:

                    first_name = child["first_name"].lower()
                    last_name = child["last_name"].lower()
                    full_name = f"{first_name} {last_name}"


                    if full_name in question_lower:

                        matched_child = child
                        break


                    if first_name in question_lower:

                        matched_child = child
                        break


                    if last_name in question_lower:

                        matched_child = child
                        break


                # -------------------------------------------------
                # Child found in question
                # -------------------------------------------------

                if matched_child:

                    student_id = matched_child["student_id"]

                    print(
                        "\n========== SELECTED CHILD =========="
                    )

                    print(
                        f"Name: "
                        f"{matched_child['first_name']} "
                        f"{matched_child['last_name']}"
                    )

                    print(
                        "Student ID:",
                        student_id
                    )

                    print("====================================")


                # -------------------------------------------------
                # Multiple children but no child identified
                # -------------------------------------------------

                else:

                    child_names = []

                    for child in children:

                        name = (
                            f"{child['first_name']} "
                            f"{child['last_name']}"
                        )

                        child_names.append(name)


                    children_text = ", ".join(child_names)


                    return ChatResponse(
                        answer=(
                            "You have multiple children linked to your account. "
                            "Please specify which child you are asking about. "
                            f"Your children are: {children_text}."
                        )
                    )


        # =========================================================
        # SAFETY CHECK
        # =========================================================

        if student_id is None:

            raise HTTPException(
                status_code=404,
                detail="Unable to determine the student."
            )


        print("\n========== FINAL STUDENT CONTEXT ==========")
        print("User Role :", role)
        print("Student ID:", student_id)
        print("===========================================")


        # =========================================================
        # 3. DETECT LANGUAGE
        # =========================================================

        language = get_language(
            request.question
        )

        print("\n========== LANGUAGE ==========")
        print("Question :", request.question)
        print("Language :", language)
        print("==============================")


        # =========================================================
        # 4. PROCESS CHAT QUERY
        # =========================================================

        print("\n========== NEW CHAT PIPELINE ==========")

        result = process_query(
            question=request.question,
            student_id=student_id,
            language=language
        )


        print("\n========== NEW PIPELINE RESULT ==========")
        print(result)
        print("==========================================")


        # =========================================================
        # 5. GENERATE FINAL ANSWER
        # =========================================================

        if result.get("type") == "rag":

            # RAG already generates its final answer
            answer = result["answer"]

        else:

            answer = generate_answer(
                question=request.question,
                results=result,
                language=language,
                user_role=current_user["role"]
            )


        # =========================================================
        # 6. FINAL ANSWER
        # =========================================================

        print("\n========== FINAL ANSWER ==========")
        print(answer)
        print("==================================")


        # =========================================================
        # 7. RETURN RESPONSE
        # =========================================================

        return ChatResponse(
            answer=answer
        )


    # =============================================================
    # HTTP EXCEPTIONS
    # =============================================================

    except HTTPException:
        raise


    # =============================================================
    # OTHER ERRORS
    # =============================================================

    except Exception as e:

        print("\n==============================================")
        print("              CHAT ERROR")
        print("==============================================")

        print("ERROR TYPE:", type(e).__name__)
        print("ERROR:", str(e))

        print("==============================================")


        raise HTTPException(
            status_code=500,
            detail="Unable to process your request."
        )