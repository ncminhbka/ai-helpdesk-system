"""LLM and Embeddings management using OpenAI."""

from typing import Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.embeddings import Embeddings
import config
import os
class LLMManager:
    """Manages OpenAI LLM and embedding model instances."""
    
    _llm_instance: Optional[BaseChatModel] = None
    _embeddings_instance: Optional[Embeddings] = None
    
    @classmethod
    def get_llm(cls, temperature: float = config.TEMPERATURE) -> BaseChatModel:
        """Get or create OpenAI LLM instance (GPT-4o-mini).
        
        Returns:
            ChatOpenAI instance
        """
        if cls._llm_instance is None:
            # Sử dụng gpt-4o-mini là model rẻ và nhanh nhất của OpenAI hiện tại
            cls._llm_instance = ChatOpenAI(
                model="gpt-4o-mini", 
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                temperature=temperature,
                max_tokens=1024,
            )
        return cls._llm_instance
    
    @classmethod
    def get_embeddings(cls) -> Embeddings:
        """Get or create OpenAI embeddings instance.
        
        Returns:
            OpenAIEmbeddings instance
        """
        if cls._embeddings_instance is None:
            # text-embedding-3-small là model embedding rẻ nhất và hiệu suất cực tốt
            cls._embeddings_instance = OpenAIEmbeddings(
                model="text-embedding-3-small",
                openai_api_key=os.getenv("OPENAI_API_KEY"),
            )
        return cls._embeddings_instance
    
    @classmethod
    def reset(cls):
        """Reset singleton instances."""
        cls._llm_instance = None
        cls._embeddings_instance = None