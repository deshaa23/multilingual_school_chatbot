from pathlib import Path
from langchain_community.document_loaders import PyPDFLoader

def load_documents(documents_path="documents"):
    """
    Load all PDF files from the documents folder.

    """
    documents = []

    pdf_files = Path(documents_path).glob("*.pdf")

    for pdf_files in pdf_files:
        print(f"Loading: {pdf_files.name}")
        loader =PyPDFLoader(pdf_files)
        documents.extend(loader.load())

    print(f"\nTotal pages loaded: {len(documents)}")
    return documents
