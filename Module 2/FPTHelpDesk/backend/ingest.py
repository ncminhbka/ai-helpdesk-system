"""
PDF ingestion script for RAG knowledge base.
Creates embeddings ONCE and persists to PostgreSQL via pgvector.
Uses checksum-based cache invalidation to avoid re-processing.

Usage:
    python ingest.py          # Normal run (uses cache)
    python ingest.py --force  # Force re-ingestion
"""
import os
import json
import hashlib
from pathlib import Path
from typing import List

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from langchain_core.documents import Document

from dotenv import load_dotenv
load_dotenv()


# Configuration
DOCS_DIR = Path(os.getenv("DOCS_DIR", "../docs"))
CACHE_FILE = Path(os.getenv("INGEST_CACHE_FILE", "./.ingest_cache.json"))
COLLECTION_NAME = "fpt_policies"

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Build PostgreSQL connection string from individual env vars
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fpt_helpdesk")
PG_CONNECTION = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def calculate_file_checksum(file_path: Path) -> str:
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def calculate_checksums(docs_dir: Path) -> dict:
    """Calculate checksums for all PDF files."""
    return {
        pdf_file.name: calculate_file_checksum(pdf_file)
        for pdf_file in docs_dir.glob("*.pdf")
    }


def load_cached_checksums() -> dict:
    """Load cached checksums."""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_checksums(checksums: dict):
    """Save checksums to cache file."""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        json.dump(checksums, f, indent=2)


def load_pdf_documents(docs_dir: Path) -> List[Document]:
    """Load and split PDF documents."""
    all_documents = []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    pdf_files = list(docs_dir.glob("*.pdf"))
    print(f"📄 Found {len(pdf_files)} PDF files")

    for pdf_file in pdf_files:
        try:
            print(f"  Loading: {pdf_file.name}")
            loader = PyPDFLoader(str(pdf_file))
            documents = loader.load()

            for doc in documents:
                doc.metadata["source"] = pdf_file.name
                doc.metadata["page_label"] = doc.metadata.get("page", 0) + 1

            split_docs = text_splitter.split_documents(documents)
            all_documents.extend(split_docs)
            print(f"    ✓ {len(split_docs)} chunks created")

        except Exception as e:
            print(f"    ✗ Error loading {pdf_file.name}: {e}")

    return all_documents


def get_embeddings() -> OpenAIEmbeddings:
    """Get OpenAI embeddings model."""
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        api_key=os.getenv("OPENAI_API_KEY"),
    )


def create_vectorstore(documents: List[Document]) -> PGVector:
    """Create pgvector vectorstore from documents."""
    print("\n🔄 Creating embeddings and storing in PostgreSQL...")

    embeddings = get_embeddings()

    vectorstore = PGVector.from_documents(
        documents=documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        connection=PG_CONNECTION,
        pre_delete_collection=True,  # Clear old data on re-ingest
    )

    print(f"✅ Stored {len(documents)} chunks in PostgreSQL (pgvector)")
    return vectorstore


def ingest_documents(force: bool = False) -> PGVector:
    """
    Main ingestion function.
    Creates embeddings ONCE and persists to PostgreSQL.
    Only re-embeds if files change (checksum validation).
    """
    print("=" * 50)
    print("FPT Knowledge Base Ingestion (pgvector)")
    print("=" * 50)

    if not DOCS_DIR.exists():
        print(f"❌ Documents directory not found: {DOCS_DIR}")
        print("   Please create the directory and add PDF files.")
        return None

    current_checksums = calculate_checksums(DOCS_DIR)

    if not current_checksums:
        print(f"❌ No PDF files found in {DOCS_DIR}")
        return None

    print(f"\n📁 Documents directory: {DOCS_DIR.absolute()}")
    print(f"🐘 PostgreSQL connection: {DB_HOST}:{DB_PORT}/{DB_NAME}")

    if not force:
        cached_checksums = load_cached_checksums()

        if cached_checksums == current_checksums:
            print("\n✅ Using cached embeddings (no changes detected)")
            print("   (Embeddings already stored in PostgreSQL)")
            return None  # Embeddings already in DB, no need to return store

        if cached_checksums:
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

    print("\n📖 Loading PDF documents...")
    documents = load_pdf_documents(DOCS_DIR)

    if not documents:
        print("❌ No documents loaded")
        return None

    print(f"\n📊 Total chunks: {len(documents)}")

    vectorstore = create_vectorstore(documents)
    save_checksums(current_checksums)
    print("\n💾 Checksums cached for future runs")

    print(f"\n{'=' * 50}")
    print("✅ Ingestion complete!")
    print("=" * 50)

    return vectorstore


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    ingest_documents(force=force)
