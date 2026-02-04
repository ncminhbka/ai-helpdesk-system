import os
import sys
from dotenv import load_dotenv

# Add the current directory to sys.path to ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocessing import load_docs, split_docs_semantic
from hyde import HyDEQueryTransformer
from retriever import HybridRetriever
from reranker import FlashRankReranker
from tool import create_advanced_retrieval_tool
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

    print("\n" + "="*80)
    print("INITIALIZING ADVANCED RAG SYSTEM (MODULE 2)")
    print("="*80 + "\n")

    # 1. Load PDFs
    print("STEP 1: Loading PDF documents...")
    pdf_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pdf")
    documents = load_docs(pdf_directory)
    if not documents:
        print("No documents loaded. Exiting.")
        return
    print(f"✓ Loaded {len(documents)} documents\n")

    # 2. Semantic Chunking
    print("STEP 2: Semantic chunking...")
    chunks = split_docs_semantic(documents)
    print(f"✓ Created {len(chunks)} semantic chunks\n")

    # 3. Initialize HyDE Transformer
    print("STEP 3: Initializing HyDE transformer...")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    hyde_transformer = HyDEQueryTransformer(llm=llm)
    print("✓ HyDE transformer ready\n")

    # 4. Create Hybrid Retriever
    print("STEP 4: Creating hybrid retriever (BM25 + Vector)...")
    hybrid_retriever = HybridRetriever(
        documents=chunks,
        k=5,           # Final number after fusion
        bm25_k=10,     # BM25 retrieval count
        vector_k=10    # Vector retrieval count
    )
    print("✓ Hybrid retriever ready\n")

    # 5. Initialize Reranker
    print("STEP 5: Initializing FlashRank reranker...")
    reranker = FlashRankReranker(top_n=3)
    print("✓ Reranker ready\n")

    # 6. Create Advanced Retrieval Tool
    print("STEP 6: Creating advanced retrieval tool...")
    tool = create_advanced_retrieval_tool(
        hyde_transformer=hyde_transformer,
        hybrid_retriever=hybrid_retriever,
        reranker=reranker
    )
    tools = [tool]
    print("✓ Tool created\n")

    # 7. Initialize Agent LLM
    print("STEP 7: Initializing agent...")
    agent_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # 8. Create Agent with ReAct pattern
    system_message = (
        "You are a helpful assistant specialized in FPT company policies. "
        "When answering questions based on retrieved documents, you MUST provide clear citations. "
        "Use the 'Source' and 'Page' information provided in the tool output. "
        "Format citations as [Source: <filename>, Page: <page_number>]. "
        "If the information is not found in the documents, state that clearly."
    )
    
    graph = create_agent(
        agent_llm, 
        tools=tools, 
        system_prompt=SystemMessage(content=system_message)
    )
    print("✓ Agent initialized\n")

    # 9. Interactive Loop
    print("="*80)
    print("Advanced RAG Agent Ready! (Type 'exit' to quit)")
    print("="*80 + "\n")
    
    while True:
        query = input("User: ")
        if query.lower() in ["exit", "quit"]:
            break
        
        try:
            inputs = {"messages": [("user", query)]}
            response = graph.invoke(inputs)
            last_message = response["messages"][-1]
            print(f"\nAgent: {last_message.content}\n")
            
        except Exception as e:
            print(f"An error occurred: {e}\n")

if __name__ == "__main__":
    main()
