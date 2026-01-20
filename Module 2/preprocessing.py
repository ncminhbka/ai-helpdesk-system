import os
from datetime import datetime
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
    
    # Log chunks for debugging
    log_chunks(chunks)
    
    return chunks

def log_chunks(chunks):
    """
    Log chunk information to debug file.
    """
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_logs")
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"chunks_{timestamp}.txt")
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"SEMANTIC CHUNKING DEBUG LOG - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total chunks: {len(chunks)}\n\n")
        
        for i, chunk in enumerate(chunks, 1):
            f.write(f"\n{'=' * 80}\n")
            f.write(f"CHUNK {i}\n")
            f.write(f"{'=' * 80}\n")
            f.write(f"Source: {chunk.metadata.get('source', 'Unknown')}\n")
            f.write(f"Page: {chunk.metadata.get('page_label', 'Unknown')}\n")
            f.write(f"Length: {len(chunk.page_content)} characters\n")
            f.write(f"\nContent:\n{'-' * 80}\n")
            f.write(chunk.page_content[:500])  # First 500 chars
            if len(chunk.page_content) > 500:
                f.write(f"\n... ({len(chunk.page_content) - 500} more characters)")
            f.write(f"\n{'-' * 80}\n")
    
    print(f"Chunks logged to: {log_file}")
