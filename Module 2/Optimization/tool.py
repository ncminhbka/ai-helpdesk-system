from typing import List
from langchain_core.tools import BaseTool
from langchain_core.documents import Document
from pydantic import BaseModel, Field

class AdvancedRetrievalTool(BaseTool):
    """
    Advanced retrieval tool that integrates:
    1. HyDE (Hypothetical Document Embeddings) for query transformation
    2. Hybrid retrieval (BM25 + Vector with RRF fusion)
    3. Reranking with FlashRank
    """
    
    name: str = "pdf_search"
    description: str = (
        "Search for information in FPT policy documents (business conduct, "
        "human rights policy, personal data protection). "
        "This tool uses advanced retrieval techniques including semantic search, "
        "keyword matching, and relevance reranking to find the most relevant information."
    )
    
    # Custom fields
    hyde_transformer: object = Field(default=None, exclude=True)
    hybrid_retriever: object = Field(default=None, exclude=True)
    reranker: object = Field(default=None, exclude=True)
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, query: str) -> str:
        """
        Execute the advanced retrieval pipeline.
        
        Args:
            query: User's search query
            
        Returns:
            Formatted string with retrieved documents and citations
        """
        # Step 1: Transform query using HyDE
        print(f"\n{'='*60}")
        print("STEP 1: HyDE Query Transformation")
        print(f"{'='*60}")
        transformed_query = self.hyde_transformer.transform(query)
        print(f"Transformed query generated.\n")
        
        # Step 2: Hybrid retrieval
        print(f"{'='*60}")
        print("STEP 2: Hybrid Retrieval (BM25 + Vector + RRF)")
        print(f"{'='*60}")
        retrieved_docs = self.hybrid_retriever.invoke(transformed_query)
        print(f"Retrieved {len(retrieved_docs)} documents.\n")
        
        # Step 3: Reranking
        print(f"{'='*60}")
        print("STEP 3: Reranking with FlashRank")
        print(f"{'='*60}")
        reranked_docs = self.reranker.rerank(query, retrieved_docs)
        print(f"Reranked to top {len(reranked_docs)} documents.\n")
        
        # Format results for agent
        return self._format_documents(reranked_docs)
    
    def _format_documents(self, documents: List[Document]) -> str:
        """
        Format documents with citations for the agent.
        """
        if not documents:
            return "No relevant information found in the documents."
        
        formatted_parts = []
        for i, doc in enumerate(documents, 1):
            source = doc.metadata.get('source', 'Unknown')
            page = doc.metadata.get('page_label', 'Unknown')
            content = doc.page_content
            
            formatted_parts.append(
                f"Document {i}:\n"
                f"Content: {content}\n"
                f"Source: {source}\n"
                f"Page: {page}\n"
            )
        
        return "\n---\n".join(formatted_parts)


def create_advanced_retrieval_tool(hyde_transformer, hybrid_retriever, reranker):
    """
    Factory function to create the advanced retrieval tool.
    
    Args:
        hyde_transformer: HyDE query transformer instance
        hybrid_retriever: Hybrid retriever instance
        reranker: Reranker instance
        
    Returns:
        AdvancedRetrievalTool instance
    """
    return AdvancedRetrievalTool(
        hyde_transformer=hyde_transformer,
        hybrid_retriever=hybrid_retriever,
        reranker=reranker
    )
