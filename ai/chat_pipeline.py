from ai.router import route_query
from ai.tools.tool_executor import execute_tool


def process_query(
    question: str,
    student_id: int
):
    """
    Main chatbot pipeline.

    Flow:

        User Question
              ↓
           Router
              ↓
        Tool Executor
              ↓
          Tool Result
    """

    # ==========================================
    # 1. ROUTE THE QUESTION
    # ==========================================

    route = route_query(question)

    tool_name = route["tool"]
    metric = route.get("metric")

    print("\n========== ROUTING ==========")
    print(f"Question : {question}")
    print(f"Tool     : {tool_name}")
    print(f"Metric   : {metric}")
    print(f"Confidence: {route['confidence']}")
    print("=============================")

    # ==========================================
    # 2. GENERAL CHAT
    # ==========================================

    if tool_name == "general_chat":

        return {
            "type": "general_chat",
            "success": True,
            "message": "General chat handling will be connected next."
        }

    # ==========================================
    # 3. RAG
    # ==========================================

    if tool_name == "rag_tool":

        return {
            "type": "rag",
            "success": True,
            "message": "RAG handling will be connected next."
        }

    # ==========================================
    # 4. EXECUTE TOOL
    # ==========================================

    result = execute_tool(
        tool_name=tool_name,
        student_id=student_id,
        status=route.get("status"),
        day=route.get("day"),
        subject=route.get("subject"),
        exam=route.get("exam")
    )


    return result