"""
LangGraph orchestration for FPT Customer Support Chatbot.
Implements hierarchical multi-agent architecture with state management.
"""
import os
from typing import Annotated, Optional, Literal, TypedDict
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages, AnyMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import AIMessage, HumanMessage

from agents import (
    get_primary_assistant,
    get_faq_agent,
    get_ticket_agent,
    get_booking_agent,
    get_it_support_agent
)
from utils.intent_classifier import get_intent_classifier, IntentCategory

from dotenv import load_dotenv
load_dotenv()


# ==================== STATE DEFINITION ====================

def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Update dialog state stack (push/pop agents)."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1] if left else []
    return left + [right]


class AgentState(TypedDict):
    """Global state for the multi-agent system."""
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: Optional[int]
    user_email: Optional[str]
    session_id: Optional[str]
    language: str
    current_intent: Optional[str]
    dialog_state: Annotated[list[str], update_dialog_stack]
    pending_confirmation: Optional[dict]
    last_agent_response: Optional[dict]


# ==================== NODE FUNCTIONS ====================

async def classify_intent_node(state: AgentState) -> dict:
    """Classify user intent and check safety with conversation context."""
    messages = state["messages"]
    last_message = messages[-1]
    
    if not isinstance(last_message, HumanMessage):
        return {"current_intent": None}
    
    # Pass previous messages (excluding current) for context
    chat_history = messages[:-1] if len(messages) > 1 else []
    
    classifier = get_intent_classifier()
    result = await classifier.classify(last_message.content, chat_history=chat_history)
    
    return {
        "current_intent": result.intent.value,
        "language": result.language
    }


async def primary_assistant_node(state: AgentState) -> dict:
    """Primary assistant handles routing and direct responses."""
    from utils.intent_classifier import (
        get_greeting_response,
        get_out_of_scope_response,
        get_harmful_response
    )
    
    intent = state.get("current_intent")
    language = state.get("language", "vi")
    
    # Handle direct response cases
    if intent == IntentCategory.GREETING.value:
        response = get_greeting_response(language)
        return {
            "messages": [AIMessage(content=response)],
            "last_agent_response": {"type": "message", "response": response},
            "dialog_state": None  # Stay in primary
        }
    
    if intent == IntentCategory.OUT_OF_SCOPE.value:
        response = get_out_of_scope_response(language)
        return {
            "messages": [AIMessage(content=response)],
            "last_agent_response": {"type": "message", "response": response},
            "dialog_state": None
        }
    
    if intent == IntentCategory.HARMFUL.value:
        response = get_harmful_response(language)
        return {
            "messages": [AIMessage(content=response)],
            "last_agent_response": {"type": "message", "response": response},
            "dialog_state": None
        }
    
    # For valid intents, add handoff message
    assistant = get_primary_assistant()
    handoff_msg = await assistant.generate_handoff_message(
        f"{intent.split('_')[0]}_agent" if intent else "primary",
        state["messages"][-1].content,
        language
    )
    
    return {
        "messages": [AIMessage(content=handoff_msg)] if handoff_msg else [],
        "dialog_state": intent  # Track which agent is active
    }


async def faq_agent_node(state: AgentState) -> dict:
    """FAQ Agent processes policy questions."""
    agent = get_faq_agent()
    last_message = state["messages"][-1]
    
    # Get the original user message
    user_message = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break
    
    if not user_message:
        return {}
    
    result = await agent.process(
        user_message=user_message,
        chat_history=state["messages"][:-1],
        language=state.get("language", "vi")
    )
    
    return {
        "messages": [AIMessage(content=result["response"])],
        "last_agent_response": result,
        "dialog_state": "pop"  # Return to primary
    }


async def ticket_agent_node(state: AgentState) -> dict:
    """Ticket Agent processes ticket operations."""
    agent = get_ticket_agent()
    
    # Get the original user message
    user_message = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break
    
    if not user_message:
        return {}
    
    user_info = {
        "user_id": state.get("user_id"),
        "email": state.get("user_email")
    }
    
    result = await agent.process(
        user_message=user_message,
        chat_history=state["messages"][:-1],
        user_info=user_info,
        language=state.get("language", "vi")
    )
    
    # Handle confirmation request
    if result.get("type") == "confirm":
        return {
            "messages": [AIMessage(content=result.get("message", "Please confirm."))],
            "pending_confirmation": result,
            "last_agent_response": result,
            "dialog_state": "pop"
        }
    
    return {
        "messages": [AIMessage(content=result.get("response", ""))],
        "last_agent_response": result,
        "dialog_state": "pop"
    }


async def booking_agent_node(state: AgentState) -> dict:
    """Booking Agent processes booking operations."""
    agent = get_booking_agent()
    
    # Get the original user message
    user_message = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break
    
    if not user_message:
        return {}
    
    user_info = {
        "user_id": state.get("user_id"),
        "email": state.get("user_email")
    }
    
    result = await agent.process(
        user_message=user_message,
        chat_history=state["messages"][:-1],
        user_info=user_info,
        language=state.get("language", "vi")
    )
    
    # Handle confirmation request
    if result.get("type") == "confirm":
        return {
            "messages": [AIMessage(content=result.get("message", "Please confirm."))],
            "pending_confirmation": result,
            "last_agent_response": result,
            "dialog_state": "pop"
        }
    
    return {
        "messages": [AIMessage(content=result.get("response", ""))],
        "last_agent_response": result,
        "dialog_state": "pop"
    }


async def it_support_agent_node(state: AgentState) -> dict:
    """IT Support Agent handles technical issues."""
    agent = get_it_support_agent()
    
    # Get the original user message
    user_message = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            user_message = msg.content
            break
    
    if not user_message:
        return {}
    
    result = await agent.process(
        user_message=user_message,
        chat_history=state["messages"][:-1],
        language=state.get("language", "vi")
    )
    
    return {
        "messages": [AIMessage(content=result.get("response", ""))],
        "last_agent_response": result,
        "dialog_state": "pop"
    }


# ==================== ROUTING FUNCTION ====================

def route_by_intent(state: AgentState) -> Literal[
    "faq_agent",
    "ticket_agent",
    "booking_agent",
    "it_support_agent",
    "end"
]:
    """Route to appropriate agent based on classified intent."""
    intent = state.get("current_intent")
    
    if not intent:
        return "end"
    
    # Direct response cases - already handled in primary_assistant
    if intent in [
        IntentCategory.GREETING.value,
        IntentCategory.OUT_OF_SCOPE.value,
        IntentCategory.HARMFUL.value
    ]:
        return "end"
    
    # FAQ routing
    if intent == IntentCategory.FAQ_POLICY.value:
        return "faq_agent"
    
    # Ticket routing
    if intent in [
        IntentCategory.TICKET_CREATE.value,
        IntentCategory.TICKET_TRACK.value,
        IntentCategory.TICKET_UPDATE.value
    ]:
        return "ticket_agent"
    
    # Booking routing
    if intent in [
        IntentCategory.BOOKING_CREATE.value,
        IntentCategory.BOOKING_TRACK.value,
        IntentCategory.BOOKING_UPDATE.value,
        IntentCategory.BOOKING_CANCEL.value
    ]:
        return "booking_agent"
    
    # IT Support routing
    if intent == IntentCategory.IT_SUPPORT.value:
        return "it_support_agent"
    
    return "end"


# ==================== GRAPH CONSTRUCTION ====================

def create_graph() -> StateGraph:
    """Create the LangGraph workflow."""
    
    # Create graph builder
    builder = StateGraph(AgentState)
    
    # Add nodes
    builder.add_node("classify_intent", classify_intent_node)
    builder.add_node("primary_assistant", primary_assistant_node)
    builder.add_node("faq_agent", faq_agent_node)
    builder.add_node("ticket_agent", ticket_agent_node)
    builder.add_node("booking_agent", booking_agent_node)
    builder.add_node("it_support_agent", it_support_agent_node)
    
    # Add edges
    builder.add_edge(START, "classify_intent")
    builder.add_edge("classify_intent", "primary_assistant")
    
    # Conditional routing from primary assistant
    builder.add_conditional_edges(
        "primary_assistant",
        route_by_intent,
        {
            "faq_agent": "faq_agent",
            "ticket_agent": "ticket_agent",
            "booking_agent": "booking_agent",
            "it_support_agent": "it_support_agent",
            "end": END
        }
    )
    
    # All agents return to END
    builder.add_edge("faq_agent", END)
    builder.add_edge("ticket_agent", END)
    builder.add_edge("booking_agent", END)
    builder.add_edge("it_support_agent", END)
    
    return builder


# ==================== GRAPH INSTANCE ====================

async def get_compiled_graph():
    """Get compiled graph with checkpointer."""
    builder = create_graph()
    
    # Create SQLite checkpointer for persistence
    checkpoint_path = os.getenv("LANGGRAPH_CHECKPOINT_DB", "./langgraph_checkpoint.db")
    checkpointer = AsyncSqliteSaver.from_conn_string(checkpoint_path)
    
    # Compile with checkpointer
    graph = builder.compile(checkpointer=checkpointer)
    
    return graph


# Simple graph without checkpointer for testing
def get_simple_graph():
    """Get compiled graph without checkpointer (for testing)."""
    builder = create_graph()
    return builder.compile()
