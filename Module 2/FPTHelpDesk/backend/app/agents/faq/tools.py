"""
RAG tools for the FAQ Agent.
Uses pgvector (PostgreSQL extension) for semantic search over FPT policy documents.
"""
import os
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector
from dotenv import load_dotenv

load_dotenv()

# Singleton vectorstore
_vectorstore = None

# Build connection string from individual env vars
def _get_pg_connection() -> str:
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "fpt_helpdesk")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


def get_vectorstore() -> PGVector:
    """Load the pgvector vectorstore (singleton)."""
    global _vectorstore
    if _vectorstore is None:
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        _vectorstore = PGVector(
            embeddings=embeddings,
            collection_name="fpt_policies",
            connection=_get_pg_connection(),
            use_jsonb=True,
        )

    return _vectorstore


@tool
def search_fpt_policies(query: str) -> str:
    """
    Search FPT corporate policies and documents.
    Use this tool to answer questions about:
    - FPT Code of Business Conduct
    - Human Rights Policy
    - Personal Data Protection Regulation
    - Any other FPT corporate policies

    Args:
        query: The policy question to search for (in Vietnamese or English)
    """
    try:
        vectorstore = get_vectorstore()
        docs = vectorstore.similarity_search(query, k=4)

        if not docs:
            return "Không tìm thấy thông tin phù hợp trong tài liệu chính sách."

        results = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page_label", "?")
            content = doc.page_content.strip()

            results.append(
                f"**[{i}] {source} - Trang {page}**\n{content}"
            )

        return "\n\n---\n\n".join(results)

    except Exception as e:
        return f"Lỗi khi tìm kiếm: {str(e)}"
