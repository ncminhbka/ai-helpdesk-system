import os
import sys
import importlib.util
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

# Get project root directory (go up 2 levels from Module 2/Evaluation/)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def import_module_from_path(module_name, file_path):
    """Import a module from a specific file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


class Module2RAGWrapper:
    """Wrapper for Module 2 Advanced RAG system for RAGAS evaluation."""
    
    def __init__(self):
        """Initialize Module 2 Advanced RAG system."""
        # Load environment variables
        dotenv_path = os.path.join(PROJECT_ROOT, '.env')
        load_dotenv(dotenv_path)

        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("Error: OPENAI_API_KEY not found in .env file.")

        # Set LangSmith project
        os.environ["LANGCHAIN_PROJECT"] = "Module2-RAGAS-Evaluation"

        # Import Module 2 components (now in Optimization folder)
        module2_path = os.path.join(PROJECT_ROOT, "Module 2", "Optimization")
        
        preprocessing = import_module_from_path("m2_preprocessing", os.path.join(module2_path, "preprocessing.py"))
        hyde_mod = import_module_from_path("m2_hyde", os.path.join(module2_path, "hyde.py"))
        retriever_mod = import_module_from_path("m2_retriever", os.path.join(module2_path, "retriever.py"))
        reranker_mod = import_module_from_path("m2_reranker", os.path.join(module2_path, "reranker.py"))
        tool_mod = import_module_from_path("m2_tool", os.path.join(module2_path, "tool.py"))

        # 1. Load PDFs
        pdf_directory = os.path.join(PROJECT_ROOT, "pdf")
        documents = preprocessing.load_docs(pdf_directory)
        if not documents:
            raise ValueError("No documents loaded.")

        # 2. Semantic Chunking
        chunks = preprocessing.split_docs_semantic(documents)

        # 3. Initialize HyDE Transformer
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
        self.hyde_transformer = hyde_mod.HyDEQueryTransformer(llm=llm)

        # 4. Create Hybrid Retriever
        self.hybrid_retriever = retriever_mod.HybridRetriever(
            documents=chunks,
            k=5,           # Final number after fusion
            bm25_k=10,     # BM25 retrieval count
            vector_k=10    # Vector retrieval count
        )

        # 5. Initialize Reranker
        self.reranker = reranker_mod.FlashRankReranker(top_n=3)

        # 6. Create Advanced Retrieval Tool
        self.tool = tool_mod.create_advanced_retrieval_tool(
            hyde_transformer=self.hyde_transformer,
            hybrid_retriever=self.hybrid_retriever,
            reranker=self.reranker
        )
        tools = [self.tool]

        # 7. Initialize Agent LLM
        agent_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # 8. Create Agent with ReAct pattern
        system_message = (
            "You are a helpful assistant specialized in FPT company policies. "
            "When answering questions based on retrieved documents, you MUST provide clear citations. "
            "Use the 'Source' and 'Page' information provided in the tool output. "
            "Format citations as [Source: <filename>, Page: <page_number>]. "
            "If the information is not found in the documents, state that clearly."
        )
        
        self.graph = create_agent(
            agent_llm, 
            tools=tools, 
            system_prompt=SystemMessage(content=system_message)
        )

    def query(self, question: str) -> dict:
        """
        Query the Advanced RAG system and return answer with contexts.
        
        Args:
            question: The question to answer
            
        Returns:
            dict with 'answer' and 'contexts' keys
        """
        try:
            # Get response from agent
            inputs = {"messages": [("user", question)]}
            response = self.graph.invoke(inputs)
            
            # Extract answer
            last_message = response["messages"][-1]
            answer = last_message.content
            
            # Extract contexts from tool calls
            contexts = []
            for msg in response["messages"]:
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    # This is a tool call message
                    pass
                elif hasattr(msg, "content") and isinstance(msg.content, str):
                    # Check if this is a tool response message
                    if hasattr(msg, "type") and msg.type == "tool":
                        # This is a tool output
                        contexts.append(msg.content)
            
            # If no contexts found from messages, retrieve directly
            if not contexts:
                # Use HyDE to transform the query
                transformed_query = self.hyde_transformer.transform(question)
                # Get hybrid retrieval results
                retrieved_docs = self.hybrid_retriever.retrieve(transformed_query)
                # Rerank
                reranked_docs = self.reranker.rerank(question, retrieved_docs)
                contexts = [doc.page_content for doc in reranked_docs]
            
            return {
                "answer": answer,
                "contexts": contexts
            }
            
        except Exception as e:
            print(f"Error in Module 2 query: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "contexts": []
            }
