from rag.rag_pipeline import rag_answer

question = input("Ask a question: ")

answer = rag_answer(question)

print("\nAnswer:\n")
print(answer)