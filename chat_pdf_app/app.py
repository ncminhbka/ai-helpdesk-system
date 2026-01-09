"""Streamlit UI for PDF RAG Chatbot."""

import streamlit as st
import os
import tempfile
from typing import List
from src.document_processor import PDFProcessor
from src.vector_store import VectorStoreManager
from src.graph_agent import RAGAgent
from src.llm_manager import LLMManager
import config



# Page configuration
st.set_page_config(
    page_title="PDF RAG Chatbot",
    page_icon="📚",
    layout="wide"
)

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "vector_store_manager" not in st.session_state:
        st.session_state.vector_store_manager = None
    
    if "agent" not in st.session_state:
        st.session_state.agent = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "processed_files" not in st.session_state:
        st.session_state.processed_files = set()
    
    if "indexed_count" not in st.session_state:
        st.session_state.indexed_count = 0

def process_uploaded_files(uploaded_files: List) -> int:
    """Process uploaded PDF files and add to vector store."""
    if not uploaded_files:
        return 0
    
    # Initialize components if needed
    if st.session_state.vector_store_manager is None:
        embeddings = LLMManager.get_embeddings()
        st.session_state.vector_store_manager = VectorStoreManager(embeddings)
        st.session_state.vector_store_manager.create_or_load_store(force_new=True)
    
    processor = PDFProcessor()
    total_chunks = 0
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, uploaded_file in enumerate(uploaded_files):
        if uploaded_file.name in st.session_state.processed_files:
            continue
        
        status_text.text(f"Processing {uploaded_file.name}...")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            tmp_path = tmp_file.name
        
        try:
            chunks = processor.process_pdf(tmp_path)
            st.session_state.vector_store_manager.add_documents(chunks)
            total_chunks += len(chunks)
            st.session_state.processed_files.add(uploaded_file.name)
        except Exception as e:
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        progress_bar.progress((idx + 1) / len(uploaded_files))
    
    if total_chunks > 0:
        st.session_state.vector_store_manager.save()
        if st.session_state.agent is None:
            st.session_state.agent = RAGAgent(st.session_state.vector_store_manager)
    
    status_text.text("Processing complete!")
    progress_bar.empty()
    return total_chunks

def display_chat_message(role: str, content: str):
    """Display a chat message."""
    with st.chat_message(role):
        st.markdown(content)

def display_retrieved_chunks(docs: List):
    """Display retrieved document chunks in expandable section."""
    if not docs:
        return
    
    with st.expander(f"📄 Retrieved Context ({len(docs)} chunks)", expanded=False):
        for i, doc in enumerate(docs):
            metadata = doc.metadata
            st.markdown(f"**Chunk {i+1}** - {metadata.get('source', 'unknown')}, "
                       f"Page {metadata.get('page', '?')}")
            st.text_area(
                f"Content {i+1}",
                doc.page_content,
                height=150,
                key=f"chunk_{i}_{len(st.session_state.chat_history)}",
                label_visibility="collapsed"
            )
            st.markdown("---")

def main():
    """Main Streamlit application."""
    initialize_session_state()
    
    # Header
    st.title("📚 PDF RAG Chatbot (LangGraph + Ollama)")
    st.markdown("Hệ thống trả lời câu hỏi chính xác, có trích dẫn và hỗ trợ bảng biểu.")
    
    # Sidebar for PDF upload
    with st.sidebar:
        st.header("📁 Document Upload")
        uploaded_files = st.file_uploader(
            "Upload PDF files",
            type=["pdf"],
            accept_multiple_files=True,
            key="pdf_uploader"
        )
        
        if uploaded_files:
            new_files = [f for f in uploaded_files if f.name not in st.session_state.processed_files]
            if new_files:
                if st.button("Index Documents", type="primary"):
                    chunks_added = process_uploaded_files(new_files)
                    st.session_state.indexed_count += chunks_added
                    st.success(f"✅ Indexed {chunks_added} chunks")
                    st.rerun()

        st.markdown("---")
        st.subheader("⚙️ Configuration")
        st.info(f"**Model:** {config.LLM_MODEL}\n\n**Rerank:** Enabled")

        if st.session_state.processed_files:
            if st.button("Clear All Data", type="secondary"):
                if st.session_state.vector_store_manager:
                    st.session_state.vector_store_manager.clear()
                st.session_state.processed_files.clear()
                st.session_state.indexed_count = 0
                st.session_state.chat_history = []
                st.session_state.agent = None
                st.rerun()

    # Main Area
    if not st.session_state.processed_files:
        st.info("👈 Hãy upload tài liệu PDF ở thanh bên trái để bắt đầu.")
        return # Thoát hàm main nếu chưa có file

    # Display Chat History
    for message in st.session_state.chat_history:
        display_chat_message(message["role"], message["content"])
        if message["role"] == "assistant" and "retrieved_docs" in message:
            display_retrieved_chunks(message["retrieved_docs"])

    # Chat Input
    if prompt := st.chat_input("Hỏi bất cứ điều gì về tài liệu..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        display_chat_message("user", prompt)
        
        with st.chat_message("assistant"):
            with st.spinner("Đang suy nghĩ và kiểm tra tài liệu..."):
                try:
                    # Gọi LangGraph Agent
                    result = st.session_state.agent.query(prompt)
                    
                    answer = result.get("generation", "Tôi không tìm thấy thông tin.")
                    retrieved_docs = result.get("documents", [])
                    
                    st.markdown(answer)
                    
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": answer,
                        "retrieved_docs": retrieved_docs
                    })
                    display_retrieved_chunks(retrieved_docs)
                    
                except Exception as e:
                    error_msg = f"❌ Đã có lỗi xảy ra: {str(e)}"
                    st.error(error_msg)

# Khởi chạy ứng dụng
if __name__ == "__main__":
    main()