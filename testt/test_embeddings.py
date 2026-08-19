from rag.embeddings import get_embedding_model

embedding_model = get_embedding_model()

vector = embedding_model.embed_query("What are the school rules?")

print(f"Embedding dimension: {len(vector)}")
print(vector[:10])