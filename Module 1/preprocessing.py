import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_docs(directory_path: str):
    """
    Loads all PDF documents from the specified directory.
    """
    # Add page_label to metadata for citation clarity if needed, 
    # but let's just use 'page' in the tool.
    documents = []
    if not os.path.exists(directory_path):
        print(f"Directory not found: {directory_path}")
        return documents

    for filename in os.listdir(directory_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(directory_path, filename)
            try:
                loader = PyPDFLoader(file_path)
                docs = loader.load()
                # Ensure metadata is clean
                for doc in docs:
                    doc.metadata['source'] = filename # Use filename instead of full path for cleaner citation
                    doc.metadata['page_label'] = doc.metadata.get('page', 0) + 1 # User friendly page number
                documents.extend(docs)
                print(f"Loaded {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return documents

def split_docs(documents, chunk_size=1000, chunk_overlap=200):
    """
    Splits documents into chunks using RecursiveCharacterTextSplitter.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        add_start_index=True
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks
