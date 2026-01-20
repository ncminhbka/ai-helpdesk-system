"""
Workflow visualization for the Advanced RAG system.
Generates Mermaid diagram showing the complete pipeline.
"""

def get_workflow_mermaid() -> str:
    """
    Returns Mermaid diagram code for the RAG workflow.
    """
    mermaid_code = """
graph TD
    A[User Query] --> B[HyDE Transformation]
    B -->|Hypothetical Document| C[Hybrid Retrieval]
    
    C --> D[BM25 Search<br/>Keyword-based]
    C --> E[Vector Search<br/>Semantic]
    
    D -->|Top 10| F[RRF Fusion]
    E -->|Top 10| F
    
    F -->|Top 5| G[FlashRank Reranking]
    
    G -->|Top 3| H[ReAct Agent]
    
    H --> I{Need More Info?}
    
    I -->|Yes| J[Call Tool Again]
    J --> B
    
    I -->|No| K[Generate Response<br/>with Citations]
    
    K --> L[Final Answer]
    
    style A fill:#e1f5ff,stroke:#01579b,stroke-width:2px
    style B fill:#fff3e0,stroke:#e65100,stroke-width:2px
    style C fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    style D fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    style E fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px
    style F fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style G fill:#fce4ec,stroke:#880e4f,stroke-width:2px
    style H fill:#e0f2f1,stroke:#004d40,stroke-width:2px
    style L fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
"""
    return mermaid_code

def get_workflow_description() -> str:
    """
    Returns a text description of the workflow.
    """
    description = """
### Advanced RAG Pipeline Steps:

1. **HyDE Transformation** 🔄
   - Converts user query into a hypothetical document
   - Bridges vocabulary gap between query and documents

2. **Hybrid Retrieval** 🔍
   - **BM25 Search**: Keyword-based sparse retrieval (top 10)
   - **Vector Search**: Semantic dense retrieval (top 10)
   - **RRF Fusion**: Combines results using Reciprocal Rank Fusion

3. **Reranking** ⭐
   - FlashRank reranks fused results
   - Returns top 3 most relevant documents

4. **ReAct Agent** 🤖
   - Uses retrieved documents to answer questions
   - Provides citations (source file, page number)
   - Can iteratively call tools if needed

5. **Response** ✅
   - Final answer with proper citations
   - Grounded in retrieved documents
"""
    return description
