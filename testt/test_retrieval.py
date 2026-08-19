from rag.rag_pipeline import retrieve_documents

query = "What is the attendance requirement?"

results = retrieve_documents(query)

print(f"\nRetrieved {len(results)} chunks\n")

for i, doc in enumerate(results, start=1):
    print("=" * 80)
    print(f"Result {i}")
    print("=" * 80)
    print(doc.page_content)
    print(doc.metadata)
    print()