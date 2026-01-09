"""Configuration constants for the RAG chatbot system."""

import os

# OpenAI Configuration

LLM_MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "gpt-4o-embedding-3-small"

# Chunking Configuration
CHUNK_SIZE = 800  # Characters per chunk
CHUNK_OVERLAP = 200  # Overlap between chunks
MIN_CHUNK_SIZE = 100  # Minimum viable chunk size

# Retrieval Configuration
TOP_K_RETRIEVAL = 6  # Number of chunks to retrieve
MMR_DIVERSITY = 0.3  # 0 = max relevance, 1 = max diversity

# Vector Store Configuration
VECTOR_STORE_PATH = "./vector_store"

# Generation Configuration
MAX_CONTEXT_LENGTH = 4000  # Max characters for LLM context
TEMPERATURE = 0.1  # Low temperature for factual accuracy

# System Prompts
QUERY_ANALYSIS_PROMPT = """You are a query analyzer. Analyze the user's question and extract:
1. The core information need
2. Whether it requires comparison or structured data
3. Key entities or concepts to search for

Question: {question}

Provide a brief analysis in 2-3 sentences."""

GENERATION_PROMPT = """You are a precise document assistant. Answer the question using ONLY the provided context.

STRICT RULES:
1. ONLY use information explicitly stated in the context
2. If the context doesn't contain sufficient information, say: "The document does not contain enough information to answer this question."
3. When citing, use the exact source metadata provided
4. If the answer involves comparison or structured data, format it as a markdown table
5. Be concise but complete

Context:
{context}

Question: {question}

Provide your answer following this format:
Answer:
<your answer here>

Evidence:
- [filename, page X]
- [filename, page Y]
"""

VALIDATION_PROMPT = """Evaluate if the provided context contains sufficient information to answer the question.

Context:
{context}

Question: {question}

Respond with ONLY 'SUFFICIENT' or 'INSUFFICIENT' followed by a brief reason (one sentence)."""