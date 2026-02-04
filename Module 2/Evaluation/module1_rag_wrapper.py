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


class Module1RAGWrapper:
    """Wrapper for Module 1 Naive RAG system for RAGAS evaluation."""
    
    def __init__(self):
        """Initialize Module 1 RAG system."""
        # Load environment variables
        dotenv_path = os.path.join(PROJECT_ROOT, '.env')
        load_dotenv(dotenv_path)

        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("Error: OPENAI_API_KEY not found in .env file.")

        # Set LangSmith project
        os.environ["LANGCHAIN_PROJECT"] = "Module1-RAGAS-Evaluation"

        # Import Module 1 components
        module1_path = os.path.join(PROJECT_ROOT, "Module 1")
        
        preprocessing = import_module_from_path("m1_preprocessing", os.path.join(module1_path, "preprocessing.py"))
        vector_store_mod = import_module_from_path("m1_vector_store", os.path.join(module1_path, "vector_store.py"))
        tool_mod = import_module_from_path("m1_tool", os.path.join(module1_path, "tool.py"))

        # 1. Load PDFs
        pdf_directory = os.path.join(PROJECT_ROOT, "pdf")
        documents = preprocessing.load_docs(pdf_directory)
        if not documents:
            raise ValueError("No documents loaded.")

        # 2. Split Docs
        chunks = preprocessing.split_docs(documents)

        # 3. Create Vector Store
        vector_store = vector_store_mod.create_vector_store(chunks)

        # 4. Get Retriever
        self.retriever = vector_store_mod.get_retriever(vector_store)

        # 5. Create Retrieval Tool
        self.tool = tool_mod.create_retrieval_tool(self.retriever)
        tools = [self.tool]

        # 6. Initialize LLM
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # 7. Create Agent
        system_message = (
            "You are a helpful assistant. "
            "When answering questions based on retrieved documents, you MUST provide clear citations. "
            "Use the 'Source' and 'Page' information provided in the tool output. "
            "Format citations as [Source: <filename>, Page: <page_number>]. "
            "If the information is not found in the documents, state that clearly."
        )
        
        self.graph = create_agent(llm, tools=tools, system_prompt=SystemMessage(content=system_message))

    def query(self, question: str) -> dict:
        """
        Query the RAG system and return answer with contexts.
        
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
                    for tool_call in msg.tool_calls:
                        # Get the actual tool output from the next message
                        pass
                elif hasattr(msg, "content") and isinstance(msg.content, str):
                    # Check if this is a tool response message
                    if hasattr(msg, "type") and msg.type == "tool":
                        # This is a tool output
                        contexts.append(msg.content)
            
            # If no contexts found from messages, retrieve directly
            if not contexts:
                retrieved_docs = self.retriever.invoke(question)
                contexts = [doc.page_content for doc in retrieved_docs]
            
            return {
                "answer": answer,
                "contexts": contexts
            }
            
        except Exception as e:
            print(f"Error in Module 1 query: {e}")
            return {
                "answer": f"Error: {str(e)}",
                "contexts": []
            }
