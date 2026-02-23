"""
RAG tools for the FAQ Agent.
Uses ChromaDB vector store for semantic search over FPT policy documents.
"""
import os
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv

load_dotenv()

# Singleton vectorstore
_vectorstore = None


def get_vectorstore() -> Chroma:
    """Load the ChromaDB vectorstore (singleton)."""
    global _vectorstore
    if _vectorstore is None:
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")

        if not os.path.exists(persist_dir):
            raise FileNotFoundError(
                f"ChromaDB directory not found: {persist_dir}\n"
                "Run 'python ingest.py' first to create embeddings."
            )

        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=os.getenv("OPENAI_API_KEY"),
        )

        _vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings,
            collection_name="fpt_policies",
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

    except FileNotFoundError as e:
        return str(e)
    except Exception as e:
        return f"Lỗi khi tìm kiếm: {str(e)}"
