"""LangGraph agent for PDF question answering."""

from typing import TypedDict, List, Annotated, Literal, Dict, Any
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import operator
import config
from src.llm_manager import LLMManager
from src.vector_store import VectorStoreManager
from dotenv import load_dotenv
import os  # Thêm import os

load_dotenv()

# --- CẤU HÌNH DEBUG ---
# Đảm bảo biến môi trường được set nếu chưa có trong .env
if "LANGCHAIN_TRACING_V2" not in os.environ:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
if "LANGCHAIN_PROJECT" not in os.environ:
    os.environ["LANGCHAIN_PROJECT"] = "PDF_RAG_Chatbot_Debug"
# ----------------------

# Define the state structure
class AgentState(TypedDict):
    """State object passed between graph nodes."""
    question: str
    query_analysis: str
    retrieved_docs: List[Document]
    context: str
    validation_result: str
    answer: str
    citations: List[str]
    messages: Annotated[List[BaseMessage], operator.add]
    error: str


class RAGAgent:
    """LangGraph-based RAG agent for PDF Q&A."""
    
    def __init__(self, vector_store_manager: VectorStoreManager):
        """Initialize the RAG agent.
        
        Args:
            vector_store_manager: Vector store manager instance
        """
        self.vector_store_manager = vector_store_manager
        self.llm = LLMManager.get_llm()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine.
        
        Returns:
            Compiled state graph
        """
        # Create graph
        workflow = StateGraph(AgentState)
        
        # Add nodes - Đổi tên node để tránh trùng với key 'query_analysis' trong State
        workflow.add_node("analyze_query", self._query_analysis_node)
        workflow.add_node("retrieval", self._retrieval_node)
        workflow.add_node("validation", self._validation_node)
        workflow.add_node("generation", self._generation_node)
        workflow.add_node("citation_formatting", self._citation_node)
        workflow.add_node("rejection", self._rejection_node)
        
        # Set entry point
        workflow.set_entry_point("analyze_query")
        
        # Add edges
        workflow.add_edge("analyze_query", "retrieval")
        workflow.add_edge("retrieval", "validation")
        
        # Conditional routing after validation
        workflow.add_conditional_edges(
            "validation",
            self._route_after_validation,
            {
                "generate": "generation",
                "reject": "rejection"
            }
        )
        
        workflow.add_edge("generation", "citation_formatting")
        workflow.add_edge("citation_formatting", END)
        workflow.add_edge("rejection", END)
        
        return workflow.compile()
    
    def _query_analysis_node(self, state: AgentState) -> AgentState:
        """Analyze the user query.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with query analysis
        """
        prompt = ChatPromptTemplate.from_template(config.QUERY_ANALYSIS_PROMPT)
        chain = prompt | self.llm | StrOutputParser()
        
        analysis = chain.invoke({"question": state["question"]})
        
        state["query_analysis"] = analysis
        state["messages"].append(AIMessage(content=f"Analysis: {analysis}"))
        
        return state
    
    def _retrieval_node(self, state: AgentState) -> AgentState:
        """Retrieve relevant documents.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with retrieved documents
        """
        try:
            # --- DEBUG LOGGING START ---
            print(f"\n{'-'*20} RETRIEVAL DEBUG {'-'*20}")
            print(f"User Question: {state['question']}")
            
            retriever = self.vector_store_manager.get_retriever()
            docs = retriever.invoke(state["question"])
            
            print(f"Found {len(docs)} documents:")
            for i, doc in enumerate(docs):
                source = doc.metadata.get('source_file', 'unknown')
                page = doc.metadata.get('page_number', '?')
                content_preview = doc.page_content[:150].replace('\n', ' ')
                print(f"[{i+1}] {source} (Page {page}): {content_preview}...")
            print(f"{'-'*20} END DEBUG {'-'*20}\n")
            # --- DEBUG LOGGING END ---
            
            state["retrieved_docs"] = docs
            state["messages"].append(
                AIMessage(content=f"Retrieved {len(docs)} relevant chunks")
            )
            
            # Build context string with metadata
            context_parts = []
            for i, doc in enumerate(docs):
                metadata = doc.metadata
                context_parts.append(
                    f"[Source: {metadata.get('source_file', 'unknown')}, "
                    f"Page: {metadata.get('page_number', '?')}]\n{doc.page_content}"
                )
            
            state["context"] = "\n\n---\n\n".join(context_parts)
            
            # Truncate context if too long
            if len(state["context"]) > config.MAX_CONTEXT_LENGTH:
                state["context"] = state["context"][:config.MAX_CONTEXT_LENGTH] + "\n...[truncated]"
            
        except Exception as e:
            print(f"!!! RETRIEVAL ERROR: {str(e)}") # Print error to console
            state["error"] = f"Retrieval error: {str(e)}"
            state["retrieved_docs"] = []
            state["context"] = ""
        
        return state
    
    def _validation_node(self, state: AgentState) -> AgentState:
        """Validate if retrieved context is sufficient.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with validation result
        """
        if not state["context"] or state.get("error"):
            state["validation_result"] = "INSUFFICIENT - No context retrieved"
            return state
        
        prompt = ChatPromptTemplate.from_template(config.VALIDATION_PROMPT)
        chain = prompt | self.llm | StrOutputParser()
        
        result = chain.invoke({
            "context": state["context"],
            "question": state["question"]
        })
        
        # --- DEBUG LOGGING ---
        print(f"Validation Result: {result}")
        # ---------------------

        state["validation_result"] = result
        state["messages"].append(AIMessage(content=f"Validation: {result}"))
        
        return state
    
    def _route_after_validation(self, state: AgentState) -> Literal["generate", "reject"]:
        """Route based on validation result.
        
        Args:
            state: Current agent state
            
        Returns:
            Next node to execute
        """
        validation = state["validation_result"].upper()
        
        if "SUFFICIENT" in validation:
            return "generate"
        else:
            return "reject"
    
    def _generation_node(self, state: AgentState) -> AgentState:
        """Generate answer from context.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with generated answer
        """
        prompt = ChatPromptTemplate.from_template(config.GENERATION_PROMPT)
        chain = prompt | self.llm | StrOutputParser()
        
        answer = chain.invoke({
            "context": state["context"],
            "question": state["question"]
        })
        
        state["answer"] = answer
        
        return state
    
    def _citation_node(self, state: AgentState) -> AgentState:
        """Format and validate citations.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with formatted citations
        """
        # Extract unique citations from retrieved docs
        citations = set()
        for doc in state["retrieved_docs"]:
            metadata = doc.metadata
            source = metadata.get("source_file", "unknown")
            page = metadata.get("page_number", "?")
            citations.add(f"[{source}, page {page}]")
        
        state["citations"] = sorted(list(citations))
        
        # Ensure answer includes Evidence section
        if "Evidence:" not in state["answer"]:
            evidence_section = "\n\nEvidence:\n" + "\n".join(f"- {cite}" for cite in state["citations"])
            state["answer"] += evidence_section
        
        return state
    
    def _rejection_node(self, state: AgentState) -> AgentState:
        """Handle insufficient context scenario.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with rejection message
        """
        state["answer"] = (
            "The document does not contain enough information to answer this question.\n\n"
            f"Reason: {state['validation_result']}"
        )
        state["citations"] = []
        
        return state
    
    def query(self, question: str) -> Dict[str, Any]:
        """Process a question through the agent.
        
        Args:
            question: User question
            
        Returns:
            Dictionary with answer, citations, and metadata
        """
        initial_state = {
            "question": question,
            "query_analysis": "",
            "retrieved_docs": [],
            "context": "",
            "validation_result": "",
            "answer": "",
            "citations": [],
            "messages": [HumanMessage(content=question)],
            "error": ""
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        return {
            "answer": final_state["answer"],
            "citations": final_state["citations"],
            "retrieved_docs": final_state["retrieved_docs"],
            "validation_result": final_state["validation_result"],
            "error": final_state.get("error", "")
        }