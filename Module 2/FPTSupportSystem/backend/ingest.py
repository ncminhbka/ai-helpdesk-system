"""
PDF ingestion script for RAG knowledge base.
Creates embeddings ONCE and persists to ChromaDB.
Uses checksum-based cache invalidation to avoid re-processing.
"""
import os
import json
import hashlib
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

from dotenv import load_dotenv
load_dotenv()


# Configuration
DOCS_DIR = Path(os.getenv("DOCS_DIR", "../docs"))
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"))
CACHE_FILE = CHROMA_PERSIST_DIR / ".cache_checksums.json"

# Text splitter configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def calculate_file_checksum(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def calculate_checksums(docs_dir: Path) -> dict:
    """Calculate checksums for all PDF files in directory."""
    checksums = {}
    for pdf_file in docs_dir.glob("*.pdf"):
        checksums[pdf_file.name] = calculate_file_checksum(pdf_file)
    return checksums


def load_cached_checksums() -> dict:
    """Load cached checksums from file."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_checksums(checksums: dict):
    """Save checksums to cache file."""
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(checksums, f, indent=2)


def load_pdf_documents(docs_dir: Path) -> List[Document]:
    """Load and split PDF documents."""
    all_documents = []
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    pdf_files = list(docs_dir.glob("*.pdf"))
    print(f"📄 Found {len(pdf_files)} PDF files")
    
    for pdf_file in pdf_files:
        try:
            print(f"  Loading: {pdf_file.name}")
            loader = PyPDFLoader(str(pdf_file))
            documents = loader.load()
            
            # Add source metadata
            for doc in documents:
                doc.metadata["source"] = pdf_file.name
                doc.metadata["page_label"] = doc.metadata.get("page", 0) + 1
            
            # Split documents
            split_docs = text_splitter.split_documents(documents)
            all_documents.extend(split_docs)
            print(f"    ✓ {len(split_docs)} chunks created")
            
        except Exception as e:
            print(f"    ✗ Error loading {pdf_file.name}: {e}")
    
    return all_documents


def create_vectorstore(documents: List[Document]) -> Chroma:
    """Create ChromaDB vectorstore from documents."""
    print("\n🔄 Creating embeddings...")
    
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create vectorstore with persistence
    vectorstore = Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=str(CHROMA_PERSIST_DIR),
        collection_name="fpt_policies"
    )
    
    print(f"✅ Created vectorstore with {len(documents)} documents")
    return vectorstore


def load_vectorstore() -> Chroma:
    """Load existing vectorstore from disk."""
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    vectorstore = Chroma(
        persist_directory=str(CHROMA_PERSIST_DIR),
        embedding_function=embeddings,
        collection_name="fpt_policies"
    )
    
    return vectorstore


def ingest_documents(force: bool = False) -> Chroma:
    """
    Main ingestion function.
    Creates embeddings ONCE and persists to disk.
    Only re-embeds if files change (checksum validation).
    
    Args:
        force: If True, force re-ingestion even if cache is valid
    
    Returns:
        ChromaDB vectorstore
    """
    print("=" * 50)
    print("FPT Knowledge Base Ingestion")
    print("=" * 50)
    
    # Ensure docs directory exists
    if not DOCS_DIR.exists():
        print(f"❌ Documents directory not found: {DOCS_DIR}")
        print("   Please create the directory and add PDF files.")
        return None
    
    # Calculate current checksums
    current_checksums = calculate_checksums(DOCS_DIR)
    
    if not current_checksums:
        print(f"❌ No PDF files found in {DOCS_DIR}")
        return None
    
    print(f"\n📁 Documents directory: {DOCS_DIR.absolute()}")
    print(f"💾 Vector store directory: {CHROMA_PERSIST_DIR.absolute()}")
    
    # Check if cache exists and is valid
    if not force:
        cached_checksums = load_cached_checksums()
        
        if cached_checksums == current_checksums and CHROMA_PERSIST_DIR.exists():
            print("\n✅ Using cached embeddings (no changes detected)")
            print("   To force re-ingestion, run with --force flag")
            return load_vectorstore()
        
        if cached_checksums:
            # Show which files changed
            print("\n📝 Changes detected:")
            for name, checksum in current_checksums.items():
                if name not in cached_checksums:
                    print(f"   + NEW: {name}")
                elif cached_checksums[name] != checksum:
                    print(f"   ~ MODIFIED: {name}")
            for name in cached_checksums:
                if name not in current_checksums:
                    print(f"   - REMOVED: {name}")
    else:
        print("\n⚠️ Force re-ingestion requested")
    
    # Load and process documents
    print("\n📖 Loading PDF documents...")
    documents = load_pdf_documents(DOCS_DIR)
    
    if not documents:
        print("❌ No documents loaded")
        return None
    
    print(f"\n📊 Total chunks: {len(documents)}")
    
    # Create vectorstore
    vectorstore = create_vectorstore(documents)
    
    # Save checksums
    save_checksums(current_checksums)
    print("\n💾 Checksums cached for future runs")
    
    print("\n" + "=" * 50)
    print("✅ Ingestion complete!")
    print("=" * 50)
    
    return vectorstore


if __name__ == "__main__":
    import sys
    
    force = "--force" in sys.argv
    ingest_documents(force=force)
