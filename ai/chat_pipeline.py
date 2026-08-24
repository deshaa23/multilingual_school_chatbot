from ai.router import route_query
from ai.tools.tool_executor import execute_tool
from rag.rag_pipeline import rag_answer


def process_query(
    question: str,
    student_id: int,
    language: str = "ENGLISH",
    original_question: str = None
):
    """
    Main chatbot pipeline.

    Flow:

        User Question
              ↓
           Router
              ↓
       ┌──────┴──────┐
       ↓             ↓
    SQL Tools      RAG Tool
       ↓             ↓
    Database      Chroma
       ↓             ↓
       └──────┬──────┘
              ↓
          Tool Result
    """

    if original_question is None:
        original_question = question

    # ==========================================
    # 1. ROUTE THE QUESTION
    # ==========================================

    route = route_query(question)

    tool_name = route["tool"]

    print("\n========== ROUTING ==========")
    print(f"Question  : {question}")
    print(f"Tool      : {tool_name}")
    print(f"Metric    : {route.get('metric')}")
    print(f"Subject   : {route.get('subject')}")
    print(f"Exam      : {route.get('exam')}")
    print(f"Day       : {route.get('day')}")
    print(f"Status    : {route.get('status')}")
    print(f"Confidence: {route.get('confidence')}")
    print("=============================")

    # ==========================================
    # 2. GENERAL CHAT
    # ==========================================

    if tool_name == "general_chat":

        return {
            "type": "general_chat",
            "success": True,
            "message": "General chat"
        }

    # ==========================================
    # 3. RAG
    # ==========================================

    if tool_name == "rag_tool":

        print("\n========== RAG TOOL ==========")
        print("English Question :", question)
        print("Original Question:", original_question)
        print("Language         :", language)
        print("==============================")

        answer = rag_answer(
            english_question=question,
            original_question=question,
            language="ENGLISH"
        )

        return {
            "type": "rag",
            "success": True,
            "answer": answer
        }

    # ==========================================
    # 4. SQL / DATABASE TOOLS
    # ==========================================

    print("\n========== SQL TOOL ==========")
    print("Tool:", tool_name)
    print("==============================")

    result = execute_tool(
        tool_name=tool_name,
        student_id=student_id,
        subject=route.get("subject"),
        exam=route.get("exam"),
        day=route.get("day"),
        status=route.get("status"),
        metric=route.get("metric")
    )

    return result