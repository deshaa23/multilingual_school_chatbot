from langchain_chroma import Chroma
from rag.document_loader import load_documents
from rag.text_splitter import split_documents
from rag.embeddings import get_embedding_model

CHROMA_DB_DIR = "chroma_db"

def create_vector_store():
    """
    create and persist the chromadb vector store.
    """
    documents = load_documents()

    chunks = split_documents(documents)

    embedding_model = get_embedding_model()

    vector_store = Chroma.from_documents(
        documents = chunks,
        embedding = embedding_model,
        persist_directory = CHROMA_DB_DIR,   
    )
    print(f"\nSuccessfully stored {len(chunks)} chunks in ChromaDB.")

    return vector_store