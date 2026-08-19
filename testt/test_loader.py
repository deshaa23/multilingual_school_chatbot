from rag.document_loader import load_documents

documents = load_documents()

print("\nFirst Page:\n")
print(documents[0].page_content[:1000])