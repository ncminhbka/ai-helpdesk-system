import os
from datetime import datetime
from typing import List
from langchain_core.documents import Document
from flashrank import Ranker, RerankRequest

class FlashRankReranker:
    """
    Reranker using FlashRank - a lightweight, fast reranking model.
    No API key required.
    """
    
    def __init__(self, model_name: str = "ms-marco-MiniLM-L-12-v2", top_n: int = 3):
        """
        Initialize FlashRank reranker.
        
        Args:
            model_name: FlashRank model to use
            top_n: Number of top documents to return after reranking
        """
        print(f"Initializing FlashRank with model: {model_name}")
        self.ranker = Ranker(model_name=model_name, cache_dir="./flashrank_cache")
        self.top_n = top_n
        
        self.log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        print(f"FlashRank reranker initialized (top_n={top_n})")
    
    def rerank(self, query: str, documents: List[Document]) -> List[Document]:
        """
        Rerank documents based on relevance to query.
        
        Args:
            query: Search query
            documents: List of documents to rerank
            
        Returns:
            Reranked list of top_n documents
        """
        if not documents:
            print("No documents to rerank")
            return []
        
        print(f"Reranking {len(documents)} documents...")
        
        # Prepare passages for FlashRank
        passages = []
        for i, doc in enumerate(documents):
            passages.append({
                "id": i,
                "text": doc.page_content,
                "meta": {
                    "source": doc.metadata.get("source", "Unknown"),
                    "page": doc.metadata.get("page_label", "Unknown")
                }
            })
        
        # Create rerank request
        rerank_request = RerankRequest(query=query, passages=passages)
        
        # Perform reranking
        results = self.ranker.rerank(rerank_request)
        
        # Map results back to documents
        reranked_docs = []
        for result in results[:self.top_n]:
            original_idx = result["id"]
            doc = documents[original_idx]
            # Add rerank score to metadata
            doc.metadata["rerank_score"] = result["score"]
            doc.metadata["rerank_rank"] = len(reranked_docs) + 1
            reranked_docs.append(doc)
        
        # Log reranking results
        self._log_reranking(query, documents, reranked_docs, results)
        
        print(f"Reranking complete. Returned top {len(reranked_docs)} documents.")
        return reranked_docs
    
    def _log_reranking(self, query: str, original_docs: List[Document], 
                      reranked_docs: List[Document], results: List[dict]):
        """
        Log reranking results to debug file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"rerank_{timestamp}.txt")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"FLASHRANK RERANKING DEBUG LOG - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write(f"QUERY: {query}\n\n")
            
            # Original documents (before reranking)
            f.write("=" * 80 + "\n")
            f.write(f"DOCUMENTS BEFORE RERANKING (Total: {len(original_docs)})\n")
            f.write("=" * 80 + "\n")
            for i, doc in enumerate(original_docs, 1):
                f.write(f"\n--- Original Document {i} ---\n")
                f.write(f"Source: {doc.metadata.get('source', 'Unknown')}\n")
                f.write(f"Page: {doc.metadata.get('page_label', 'Unknown')}\n")
                if 'rrf_score' in doc.metadata:
                    f.write(f"RRF Score: {doc.metadata.get('rrf_score', 'N/A'):.6f}\n")
                f.write(f"\nContent:\n{doc.page_content[:200]}...\n")
            
            # Reranked documents
            f.write("\n" + "=" * 80 + "\n")
            f.write(f"DOCUMENTS AFTER RERANKING (Top {self.top_n})\n")
            f.write("=" * 80 + "\n")
            for i, doc in enumerate(reranked_docs, 1):
                f.write(f"\n--- Reranked Document {i} ---\n")
                f.write(f"Source: {doc.metadata.get('source', 'Unknown')}\n")
                f.write(f"Page: {doc.metadata.get('page_label', 'Unknown')}\n")
                f.write(f"Rerank Score: {doc.metadata.get('rerank_score', 'N/A'):.6f}\n")
                if 'rrf_score' in doc.metadata:
                    f.write(f"RRF Score: {doc.metadata.get('rrf_score', 'N/A'):.6f}\n")
                f.write(f"\nContent:\n{doc.page_content[:200]}...\n")
            
            # Score comparison
            f.write("\n" + "=" * 80 + "\n")
            f.write("RERANKING SCORE SUMMARY\n")
            f.write("=" * 80 + "\n")
            for result in results[:self.top_n]:
                f.write(f"Rank {results.index(result) + 1}: "
                       f"Score={result['score']:.6f}, "
                       f"ID={result['id']}\n")
        
        print(f"Reranking logged to: {log_file}")
