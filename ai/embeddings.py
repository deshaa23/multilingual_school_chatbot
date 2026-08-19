from sentence_transformers import SentenceTransformer
import numpy as np

MODEL_NAME = "BAAI/bge-small-en-v1.5"

model = SentenceTransformer(MODEL_NAME)


def get_embedding(text: str):
    embedding = model.encode(
        text,
        normalize_embeddings=True
    )
    return embedding


def cosine_similarity(a, b):
    return float(np.dot(a, b))