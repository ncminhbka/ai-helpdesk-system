import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

def load_docs(directory_path: str):
    """
    Loads all PDF documents from the specified directory.
    """
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
                    doc.metadata['source'] = filename  # Use filename instead of full path for cleaner citation
                    doc.metadata['page_label'] = doc.metadata.get('page', 0) + 1  # User friendly page number
                documents.extend(docs)
                print(f"Loaded {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {e}")
    return documents

def split_docs_semantic(documents):
    """
    Splits documents into chunks using SemanticChunker.
    This uses embeddings to find natural breakpoints in the text.
    """
    embeddings = OpenAIEmbeddings()
    
    # Create semantic chunker
    text_splitter = SemanticChunker(
        embeddings=embeddings,
        breakpoint_threshold_type="percentile",  # Can be "percentile", "standard_deviation", or "interquartile"
        breakpoint_threshold_amount=95  # Only split when similarity drops below 95th percentile
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} semantic chunks.")
    
    return chunks
