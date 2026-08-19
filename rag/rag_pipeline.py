from langchain_chroma import Chroma

from rag.embeddings import get_embedding_model
from rag.rag_prompt import build_rag_prompt

from ai.rag_answer_generator import generate_answer
from ai.language_translator import translate

CHROMA_DB_DIR = "chroma_db"


def get_vector_store():
    embedding_model = get_embedding_model()

    vector_store = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embedding_model,
    )

    return vector_store


def retrieve_documents(query, k=5):

    vector_store = get_vector_store()

    results = vector_store.similarity_search(
        query=query,
        k=k
    )

    return results


def rag_answer(
    english_question,
    original_question,
    language="ENGLISH"
):

    print("\nSearching Chroma using:")
    print(english_question)

    documents = retrieve_documents(english_question, k=5)
    print("\n========== Retrieved Chunks ==========\n")
    for i, doc in enumerate(documents, start=1):
        print(f"\n----- Chunk {i} -----")
        print(doc.page_content)

    context = "\n\n".join(
        doc.page_content
        for doc in documents
    )
    print("\nRetrieved Context:")
    print(context)

    prompt = build_rag_prompt(
        original_question,
        context
    )
    print("\nLanguage sent to generator:", language)
    print("\nOriginal Question:", original_question)
    print("\nEnglish Query:", english_question)
    print("\nRetrieved Context:\n", context)

    english_answer = generate_answer(prompt)
    print("\nEnglish Answer:")
    print(english_answer)
    final_answer = translate(
    english_answer,
    language
)
    print("\nTranslated Answer:")
    print(final_answer)
    return final_answer