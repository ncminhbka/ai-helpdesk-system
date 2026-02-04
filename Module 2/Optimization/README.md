# Module 2: Advanced RAG System

An advanced Retrieval-Augmented Generation (RAG) chatbot with semantic chunking, hybrid search, query enhancement, and reranking capabilities.

## Features

- 🔄 **HyDE** (Hypothetical Document Embeddings): Query transformation for better retrieval
- 🔍 **Hybrid Search**: Combines BM25 (keyword) + Vector (semantic) search with RRF fusion
- ⭐ **FlashRank Reranking**: Relevance-based document reranking
- ✂️ **Semantic Chunking**: Intelligent document splitting based on embeddings
- 📊 **Workflow Visualization**: Interactive Mermaid diagram of the RAG pipeline
- 🐛 **Debug Logging**: Comprehensive logs of all retrieval stages
- 🤖 **ReAct Agent**: Powered by GPT-4o-mini with citation support
- 🎨 **Beautiful UI**: Streamlit interface with gradient design

## Quick Start

### Installation

```bash
# Activate conda environment
conda activate agent_env

# Install dependencies
pip install -r requirements.txt
```

### Run Streamlit Interface (Recommended)

```bash
cd "Module 2"
streamlit run app.py
```

Then:
1. Click "Initialize Agent" in the sidebar
2. Wait for initialization to complete
3. Ask questions about FPT policies
4. View responses with citations

### Run CLI Agent

```bash
cd "Module 2"
python agent.py
```

## File Structure

```
Module 2/
├── preprocessing.py      # Semantic chunking
├── hyde.py              # Query transformation
├── retriever.py         # Hybrid search (BM25 + Vector + RRF)
├── reranker.py          # FlashRank reranking
├── tool.py              # Integrated retrieval tool
├── agent.py             # ReAct agent
├── workflow_viz.py      # Workflow visualization
├── app.py               # Streamlit UI
└── debug_logs/          # Auto-generated debug logs
```

## Debug Logging

Every query generates timestamped log files in `debug_logs/`:

- **`hyde_*.txt`**: Original query → Hypothetical document
- **`hybrid_retrieval_*.txt`**: BM25, Vector, and RRF fusion results
- **`rerank_*.txt`**: Before/after reranking comparison
- **`chunks_*.txt`**: Semantic chunking output (created during initialization)

## Architecture

```
User Query 
    ↓
HyDE Transformation
    ↓
Hybrid Retrieval
    ├── BM25 Search (top 10)
    └── Vector Search (top 10)
    ↓
RRF Fusion (top 5)
    ↓
FlashRank Reranking (top 3)
    ↓
ReAct Agent
    ↓
Response with Citations
```

## Key Improvements Over Module 1

| Feature | Module 1 | Module 2 |
|---------|----------|----------|
| Chunking | Fixed-size recursive | Semantic-based |
| Query Enhancement | None | HyDE |
| Search Method | Vector only | BM25 + Vector + RRF |
| Reranking | None | FlashRank |
| Retrieved Docs | 3 | 10+10→5→3 (multi-stage) |
| Debug Logs | None | All stages logged |
| Workflow Viz | None | Mermaid diagram |

## Technologies

- **LangChain v1.0+**: Agent framework
- **LangGraph**: Agent orchestration
- **OpenAI GPT-4o-mini**: LLM for generation
- **OpenAI Embeddings**: Vector embeddings
- **FAISS**: Vector similarity search
- **BM25**: Keyword search
- **FlashRank**: Lightweight reranking
- **Streamlit**: Web interface

## Environment Variables

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

## Data

Place PDF documents in `../pdf/` folder. Default FPT policy documents:
- FSoft_Code of Business Conduct.pdf
- FSoft_Human Rights Policy.pdf
- Regulation_Personal-Data-Protection.pdf

## Example Usage

**Question**: "What is FPT's policy on data protection?"

**System Process**:
1. HyDE generates hypothetical policy document
2. BM25 finds keyword matches (top 10)
3. Vector search finds semantic matches (top 10)
4. RRF merges results (top 5)
5. FlashRank reranks (top 3)
6. Agent generates response with citations

**Response**: 
> "According to FPT's Personal Data Protection Regulation, [specific details]... [Source: Regulation_Personal-Data-Protection.pdf, Page: 3]"

## Troubleshooting

**Import errors**: Ensure all dependencies are installed:
```bash
conda activate agent_env
pip install -r requirements.txt
```

**OPENAI_API_KEY not found**: Check `.env` file in project root

**Slow initialization**: First-time setup downloads embedding models. Subsequent runs are faster.

**Debug logs growing**: Delete old logs from `debug_logs/` folder as needed

## Development

To modify the RAG pipeline:
- **Chunking**: Edit `preprocessing.py` → `split_docs_semantic()`
- **Retrieval**: Edit `retriever.py` → adjust `bm25_k`, `vector_k`, `k` parameters
- **Reranking**: Edit `reranker.py` → change `top_n` parameter
- **Workflow**: Edit `workflow_viz.py` → update Mermaid diagram

## License

Part of FPT Intern AI Roadmap project.
