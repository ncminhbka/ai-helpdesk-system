import os
import sys
import streamlit as st
from dotenv import load_dotenv

# Add the current directory to sys.path to ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocessing import load_docs, split_docs_semantic
from hyde import HyDEQueryTransformer
from retriever import HybridRetriever
from reranker import FlashRankReranker
from tool import create_advanced_retrieval_tool
from workflow_viz import get_workflow_mermaid, get_workflow_description
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

# Page configuration
st.set_page_config(
    page_title="Advanced RAG Chatbot - Module 2",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling (same gradient theme as Module 1)
st.markdown("""
    <style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: rgba(255, 255, 255, 0.95);
        border-radius: 15px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
    
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Input box styling */
    .stTextInput > div > div > input {
        border-radius: 20px;
        border: 2px solid #667eea;
        padding: 10px 20px;
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 10px 30px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Title styling */
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: rgba(102, 126, 234, 0.1);
        border-radius: 10px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent_initialized" not in st.session_state:
    st.session_state.agent_initialized = False

if "graph" not in st.session_state:
    st.session_state.graph = None

def initialize_agent():
    """Initialize the Advanced RAG agent with all components."""
    try:
        # Load environment variables
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        load_dotenv(dotenv_path)

        if not os.getenv("OPENAI_API_KEY"):
            st.error("❌ Error: OPENAI_API_KEY not found in .env file.")
            return False

        with st.spinner("📚 Loading PDF documents..."):
            # 1. Load PDFs
            pdf_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pdf")
            documents = load_docs(pdf_directory)
            
            if not documents:
                st.error("❌ No documents loaded. Please add PDF files to the 'pdf' folder.")
                return False

        with st.spinner("✂️ Semantic chunking (this may take a moment)..."):
            # 2. Semantic Chunking
            chunks = split_docs_semantic(documents)

        with st.spinner("🔄 Initializing HyDE transformer..."):
            # 3. Initialize HyDE
            llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
            hyde_transformer = HyDEQueryTransformer(llm=llm)

        with st.spinner("🔍 Creating hybrid retriever (BM25 + Vector)..."):
            # 4. Create Hybrid Retriever
            hybrid_retriever = HybridRetriever(
                documents=chunks,
                k=5,           # Final number after fusion
                bm25_k=10,     # BM25 retrieval count
                vector_k=10    # Vector retrieval count
            )

        with st.spinner("⭐ Initializing FlashRank reranker..."):
            # 5. Initialize Reranker
            reranker = FlashRankReranker(top_n=3)

        with st.spinner("🛠️ Setting up advanced retrieval tool..."):
            # 6. Create Tool
            tool = create_advanced_retrieval_tool(
                hyde_transformer=hyde_transformer,
                hybrid_retriever=hybrid_retriever,
                reranker=reranker
            )
            tools = [tool]

            # 7. Initialize Agent
            agent_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

            system_message = (
                "You are a helpful assistant specialized in FPT company policies. "
                "When answering questions based on retrieved documents, you MUST provide clear citations. "
                "Use the 'Source' and 'Page' information provided in the tool output. "
                "Format citations as [Source: <filename>, Page: <page_number>]. "
                "If the information is not found in the documents, state that clearly."
            )
            
            st.session_state.graph = create_agent(
                agent_llm, 
                tools=tools, 
                system_prompt=SystemMessage(content=system_message)
            )

        st.session_state.agent_initialized = True
        st.success("✅ Advanced RAG Agent initialized successfully!")
        return True

    except Exception as e:
        st.error(f"❌ An error occurred during initialization: {e}")
        import traceback
        st.error(traceback.format_exc())
        return False

def process_query(query):
    """Process user query through the Advanced RAG agent."""
    try:
        inputs = {"messages": [("user", query)]}
        response = st.session_state.graph.invoke(inputs)
        last_message = response["messages"][-1]
        return last_message.content
    except Exception as e:
        return f"❌ An error occurred: {str(e)}"

# Sidebar
with st.sidebar:
    st.title("⚙️ Configuration")
    st.markdown("---")
    
    st.markdown("### 📚 About Module 2")
    st.markdown("""
    This **Advanced RAG** system features:
    - 🔄 **HyDE**: Query transformation
    - 🔍 **Hybrid Search**: BM25 + Vector + RRF
    - ⭐ **FlashRank**: Reranking
    - 🤖 **ReAct Agent**: GPT-4o-mini
    - 📊 **Debug Logging**: All stages logged
    """)
    
    st.markdown("---")
    
    # Initialize/Reinitialize button
    if st.button("🔄 Initialize Agent", use_container_width=True):
        st.session_state.agent_initialized = False
        st.session_state.graph = None
        st.session_state.messages = []
        with st.spinner("Initializing..."):
            initialize_agent()
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    
    # Status indicator
    if st.session_state.agent_initialized:
        st.success("✅ Agent Status: Ready")
    else:
        st.warning("⚠️ Agent Status: Not Initialized")
    
    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.markdown("""
    - Ask about FPT policies
    - Citations included automatically
    - Check `debug_logs/` folder for details
    - Compare with Module 1 results
    """)

# Main content
st.title("🚀 Advanced RAG Chatbot - Module 2")
st.markdown("### Powered by HyDE + Hybrid Search + Reranking")

# Workflow visualization section
with st.expander("📊 View RAG Workflow", expanded=False):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display the workflow diagram as an image
        workflow_img_path = os.path.join(os.path.dirname(__file__), "rag_workflow_diagram_1768906834555.png")
        if os.path.exists(workflow_img_path):
            st.image(workflow_img_path, caption="Advanced RAG System Pipeline", width="stretch")
        else:
            st.warning("Workflow diagram not found. Please check the Module 2 folder for PNG files.")
    
    with col2:
        st.markdown(get_workflow_description())

# Initialize agent if not already done
if not st.session_state.agent_initialized:
    st.info("👋 Welcome! Click 'Initialize Agent' in the sidebar to get started.")
    if st.button("🚀 Initialize Now", type="primary"):
        with st.spinner("Initializing Advanced RAG Agent..."):
            initialize_agent()
else:
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Type your question here..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate and display assistant response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Processing (HyDE → Retrieval → Reranking → Response)..."):
                response = process_query(prompt)
                st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 20px;'>"
    "Built with ❤️ using Streamlit & LangChain | Module 2: Advanced RAG"
    "</div>",
    unsafe_allow_html=True
)
