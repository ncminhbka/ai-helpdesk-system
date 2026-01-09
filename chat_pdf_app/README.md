# PDF RAG Chatbot - Production System

A production-grade Retrieval-Augmented Generation (RAG) chatbot for accurate PDF document question-answering with guaranteed source citations.

## Features

- **Multi-PDF Support**: Upload and query multiple PDF documents simultaneously
- **Zero Hallucination**: Strict grounding ensures answers only come from documents
- **Precise Citations**: Every answer includes source filename and page numbers
- **Table Support**: Handles structured data in PDFs with markdown table output
- **LangGraph Agent**: Stateful conversation flow with validation gates
- **FAISS Vector Store**: Fast, local semantic search with MMR re-ranking
- **Streamlit UI**: Professional chat interface with document management

## Architecture

- **LLM**: OpenAI GPT model
- **Embeddings**: OpenAI text-embedding-ada-002
- **Vector Store**: FAISS (CPU-optimized)
- **Orchestration**: LangGraph state machine
- **Framework**: LangChain 0.3+
- **UI**: Streamlit

## Prerequisites

1. **Python 3.10+**
2. **OpenAI API Key**: Obtain your API key from [OpenAI](https://platform.openai.com/).
3. Set the API key as an environment variable:
   ```bash
   export OPENAI_API_KEY=your-api-key
   ```

## Installation

1. Clone or create project directory:
```bash
   mkdir pdf_rag_chatbot
   cd pdf_rag_chatbot
```

2. Install dependencies:
```bash
   pip install -r requirements.txt
```

## Usage

1. Start the application:
```bash
   streamlit run app.py
```

2. Open browser at `http://localhost:8501`

3. Upload PDF documents via sidebar

4. Click "Index Documents" to process files

5. Ask questions in the chat interface

## Project Structure
````
pdf_rag_chatbot/
├── requirements.txt
├── config.py              # Configuration constants
├── app.py                 # Streamlit UI
├── src/
│   ├── __init__.py
│   ├── llm_manager.py     # Ollama LLM/embeddings
│   ├── document_processor.py  # PDF processing
│   ├── vector_store.py    # FAISS management
│   └── graph_agent.py     # LangGraph agent
└── vector_store/          # Auto-created FAISS index
````