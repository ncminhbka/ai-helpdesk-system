import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langsmith import traceable

class HyDEQueryTransformer:
    """
    HyDE (Hypothetical Document Embeddings) query transformer.
    Generates a hypothetical document that would answer the query,
    then uses that for retrieval instead of the raw query.
    """
    
    def __init__(self, llm=None):
        """
        Initialize HyDE transformer.
        
        Args:
            llm: Language model to use for generating hypothetical documents.
                 Defaults to GPT-4o-mini if not provided.
        """
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        
        # Prompt template for generating hypothetical document
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", 
             "You are an expert on FPT company policies including business conduct, "
             "human rights, and personal data protection. "
             "Generate a detailed paragraph that would appear in an official FPT policy document "
             "answering the following question. Write as if you are the document itself, "
             "not as a response to a question."),
            ("user", "{query}")
        ])
    
    @traceable(run_type="tool", name="HyDE Transformation")
    def transform(self, query: str) -> str:
        """
        Transform a query into a hypothetical document.
        
        Args:
            query: Original user query
            
        Returns:
            Hypothetical document text
        """
        chain = self.prompt | self.llm
        response = chain.invoke({"query": query})
        hypothetical_doc = response.content
        
        return hypothetical_doc
