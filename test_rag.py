from ai.query_processor import process_query


question = "What are the school uniform rules for grades VI-X?"

print("\n================================")
print("RAG FULL PIPELINE TEST")
print("================================")

answer = rag_answer(
    english_question=question,
    original_question=question,
    language="ENGLISH"
)

print("\n================================")
print("FINAL RAG ANSWER")
print("================================")
print(answer)