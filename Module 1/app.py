import os
import sys
import streamlit as st
from dotenv import load_dotenv

# Add the current directory to sys.path to ensure local imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from preprocessing import load_docs, split_docs
from vector_store import create_vector_store, get_retriever
from tool import create_retrieval_tool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

# Page configuration
st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
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
    
    /* Citation styling */
    .citation {
        background-color: #f0f2f6;
        border-left: 4px solid #667eea;
        padding: 8px 12px;
        margin: 8px 0;
        border-radius: 5px;
        font-size: 0.9em;
        color: #555;
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
    """Initialize the RAG agent with vector store and tools."""
    try:
        # Load environment variables
        dotenv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        load_dotenv(dotenv_path)

        if not os.getenv("OPENAI_API_KEY"):
            st.error("❌ Error: OPENAI_API_KEY not found in .env file.")
            return False

        with st.spinner("🔄 Loading PDF documents..."):
            # 1. Load PDFs
            pdf_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pdf")
            documents = load_docs(pdf_directory)
            
            if not documents:
                st.error("❌ No documents loaded. Please add PDF files to the 'pdf' folder.")
                return False

        with st.spinner("✂️ Splitting documents into chunks..."):
            # 2. Split Docs
            chunks = split_docs(documents)

        with st.spinner("🧠 Creating vector store..."):
            # 3. Create Vector Store
            vector_store = create_vector_store(chunks)

        with st.spinner("🔍 Setting up retriever..."):
            # 4. Get Retriever
            retriever = get_retriever(vector_store)

            # 5. Create Retrieval Tool
            tools = [create_retrieval_tool(retriever)]

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
            
            st.session_state.graph = create_agent(
                llm, 
                tools=tools, 
                system_prompt=SystemMessage(content=system_message)
            )

        st.session_state.agent_initialized = True
        st.success("✅ RAG Agent initialized successfully!")
        return True

    except Exception as e:
        st.error(f"❌ An error occurred during initialization: {e}")
        return False

def process_query(query):
    """Process user query through the RAG agent."""
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
    
    st.markdown("### 📚 About")
    st.markdown("""
    This RAG (Retrieval-Augmented Generation) chatbot uses:
    - **LangChain** for agent orchestration
    - **OpenAI GPT-4o-mini** for responses
    - **FAISS** for vector storage
    - **PDF documents** as knowledge base
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
    - Ask questions about your PDF documents
    - Citations will be provided with answers
    - Use clear and specific questions
    - Check the source and page numbers
    """)

# Main content
st.title("🤖 RAG Chatbot Assistant")
st.markdown("### Ask questions about your documents")

# Initialize agent if not already done
if not st.session_state.agent_initialized:
    st.info("👋 Welcome! Click 'Initialize Agent' in the sidebar to get started.")
    if st.button("🚀 Initialize Now", type="primary"):
        with st.spinner("Initializing RAG Agent..."):
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
            with st.spinner("🤔 Thinking..."):
                response = process_query(prompt)
                st.markdown(response)
        
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; padding: 20px;'>"
    "Built with ❤️ using Streamlit & LangChain | Powered by OpenAI"
    "</div>",
    unsafe_allow_html=True
)
