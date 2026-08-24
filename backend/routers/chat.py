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


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user=Depends(get_current_user)
):

    print("\n==============================================")
    print("          NEW /chat ENDPOINT CALLED")
    print("==============================================")

    try:

        # =========================================================
        # 1. CHECK USER ROLE
        # =========================================================

        if current_user["role"] != "student":
            return ChatResponse(
                answer="Chat is currently available for students."
            )

        print("\n========== CURRENT USER ==========")
        print(current_user)
        print("==================================")

        # =========================================================
        # 2. GET STUDENT ID
        # =========================================================

        student = fetch_one(
            """
            SELECT
                student_id,
                first_name,
                last_name
            FROM students
            WHERE user_id = %s
            """,
            (current_user["user_id"],)
        )

        print("\n========== STUDENT ==========")
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
        # 3. DETECT LANGUAGE
        # =========================================================

        language = get_language(request.question)

        print("\n========== LANGUAGE ==========")
        print("Question :", request.question)
        print("Language :", language)
        print("==============================")

        # =========================================================
        # 4. NEW CHAT PIPELINE
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
            answer = result["answer"]
        else:
            answer = generate_answer(
                question=request.question,
                results=result,
                language=language
    )

        print("\n========== FINAL ANSWER ==========")
        print(answer)
        print("==================================")

        # =========================================================
        # 6. RETURN RESPONSE
        # =========================================================

        return ChatResponse(
            answer=answer
        )

    except HTTPException:
        raise

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