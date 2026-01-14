import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path to ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocessing import load_docs, split_docs
from vector_store import create_vector_store, get_retriever
from tool import create_retrieval_tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

def main():
    # Load environment variables
    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
    load_dotenv(dotenv_path)

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in .env file.")
        return

    # 1. Load PDFs
    pdf_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf")
    documents = load_docs(pdf_directory)
    if not documents:
        print("No documents loaded. Exiting.")
        return

    # 2. Split Docs
    chunks = split_docs(documents)

    # 3. Create Vector Store
    vector_store = create_vector_store(chunks)

    # 4. Get Retriever
    retriever = get_retriever(vector_store)

    # 5. Create Retrieval Tool
    tools = [create_retrieval_tool(retriever)]

    # 6. Initialize LLM
    # Using gpt-4o-mini as requested/implied by user edit
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 7. Create Agent (using LangGraph)
    # Define system instruction for citation
    system_message = (
        "You are a helpful assistant. "
        "When answering questions based on retrieved documents, you MUST provide clear citations. "
        "Use the 'Source' and 'Page' information provided in the tool output. "
        "Format citations as [Source: <filename>, Page: <page_number>]. "
        "If the information is not found in the documents, state that clearly."
    )
    
    # create_react_agent in langgraph returns a compiled graph
    graph = create_agent(llm, tools=tools, system_prompt=SystemMessage(content=system_message))

    # 8. Interactive Loop
    print("\nAgent initialized (LangGraph + Citations). Type 'exit' to quit.\n")
    while True:
        query = input("User: ")
        if query.lower() in ["exit", "quit"]:
            break
        
        try:
            inputs = {"messages": [("user", query)]}
            response = graph.invoke(inputs)
            last_message = response["messages"][-1]
            print(f"Agent: {last_message.content}\n")
            
        except Exception as e:
            print(f"An error occurred: {e}\n")

if __name__ == "__main__":
    main()
