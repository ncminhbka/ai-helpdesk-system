"""
RAG tools for FAQ Agent.
Loads from persistent ChromaDB vector store (no re-embedding).
"""
import os
from typing import Optional
from pathlib import Path
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from dotenv import load_dotenv
load_dotenv()

# Configuration
CHROMA_PERSIST_DIR = Path(os.getenv("CHROMA_PERSIST_DIR", "./chroma_db"))

# Global singleton - loaded once at startup
_vectorstore: Optional[Chroma] = None


def get_vectorstore() -> Chroma:
    """
    Get or create vectorstore singleton.
    Loads from persistent storage (no embedding calls for documents).
    Only query embedding is created when searching.
    """
    global _vectorstore
    
    if _vectorstore is None:
        if not CHROMA_PERSIST_DIR.exists():
            raise ValueError(
                f"Vector store not found at {CHROMA_PERSIST_DIR}. "
                "Please run 'python ingest.py' first to create the knowledge base."
            )
        
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        _vectorstore = Chroma(
            persist_directory=str(CHROMA_PERSIST_DIR),
            embedding_function=embeddings,
            collection_name="fpt_policies"
        )
        print(f"✅ Loaded vector store from {CHROMA_PERSIST_DIR}")
    
    return _vectorstore


def format_search_results(docs: list, query: str) -> str:
    """Format search results with sources."""
    if not docs:
        return "Không tìm thấy thông tin liên quan trong cơ sở dữ liệu chính sách FPT."
    
    results = []
    seen_content = set()
    
    for i, doc in enumerate(docs, 1):
        # Deduplicate similar content
        content_hash = hash(doc.page_content[:100])
        if content_hash in seen_content:
            continue
        seen_content.add(content_hash)
        
        source = doc.metadata.get("source", "Unknown")
        page = doc.metadata.get("page_label", "N/A")
        
        results.append(
            f"**[{i}] Nguồn: {source} (Trang {page})**\n"
            f"{doc.page_content}\n"
        )
    
    return "\n---\n".join(results)


@tool
def search_fpt_policies(query: str) -> str:
    """
    Search FPT policies and regulations knowledge base.
    Use this tool to answer questions about:
    - FPT Code of Business Conduct
    - FPT Human Rights Policy
    - Personal Data Protection Regulations
    - Other FPT policies and guidelines
    
    Args:
        query: The question or search query about FPT policies
    
    Returns:
        Relevant policy information with sources
    """
    try:
        vectorstore = get_vectorstore()
        
        # Perform similarity search
        # Only the query is embedded (not re-embedding documents)
        docs = vectorstore.similarity_search(query, k=4)
        
        return format_search_results(docs, query)
        
    except Exception as e:
        return f"Lỗi khi tìm kiếm: {str(e)}"



# Pre-load vectorstore on module import (optional)
def preload_vectorstore():
    """Pre-load vectorstore at startup."""
    try:
        get_vectorstore()
    except Exception as e:
        print(f"⚠️ Could not preload vectorstore: {e}")
