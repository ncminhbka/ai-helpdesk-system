import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

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
        
        self.log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug_logs")
        os.makedirs(self.log_dir, exist_ok=True)
    
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
        
        # Log HyDE transformation
        self._log_hyde(query, hypothetical_doc)
        
        return hypothetical_doc
    
    def _log_hyde(self, original_query: str, hypothetical_doc: str):
        """
        Log HyDE transformation to debug file.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self.log_dir, f"hyde_{timestamp}.txt")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write(f"HyDE QUERY TRANSFORMATION - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")
            
            f.write("ORIGINAL QUERY:\n")
            f.write("-" * 80 + "\n")
            f.write(original_query + "\n")
            f.write("-" * 80 + "\n\n")
            
            f.write("HYPOTHETICAL DOCUMENT:\n")
            f.write("-" * 80 + "\n")
            f.write(hypothetical_doc + "\n")
            f.write("-" * 80 + "\n")
        
        print(f"HyDE transformation logged to: {log_file}")
