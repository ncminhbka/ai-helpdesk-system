"""
LangGraph orchestration for FPT Customer Support Chatbot.
Implements specialized workflows with ReAct agents and HITL.
"""
import os
from typing import Literal
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.prebuilt import tools_condition, ToolNode
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage


from app.utils.state import AgentState
from app.utils.intent_classifier import (
    get_intent_classifier,
    IntentCategory,
    get_greeting_response,
    get_out_of_scope_response,
    get_harmful_response,
)
from app.agents import (
    get_primary_assistant,
    get_booking_agent,
    get_ticket_agent,
    get_faq_agent,
    get_it_support_agent,
    CompleteOrEscalate,
    ToBookingAgent,
    ToTicketAgent,
    ToFAQAgent,
    ToITSupportAgent,
    create_entry_node,
    pop_dialog_state,
    booking_safe_tools,
    booking_sensitive_tools,
    ticket_safe_tools,
    ticket_sensitive_tools,
    faq_tools,
    it_support_tools,
)

from dotenv import load_dotenv
load_dotenv()


# ==================== TOOL NODE FACTORY ====================

def create_tool_node_with_fallback(tools: list) -> ToolNode:
    """Create a ToolNode with error handling fallback."""
    return ToolNode(tools).with_fallbacks(
        [ToolNode(tools)],  # Simple retry on failure
        exception_key="error"
    )

# ==================== NODE FUNCTIONS ====================

async def fetch_user_info(state: AgentState) -> dict:
    """Fetch user information at the start of the conversation."""
    user_info = f"User ID: {state.get('user_id', 'Unknown')}, Email: {state.get('user_email', 'Unknown')}"
    return {"user_info": user_info}


async def classify_intent_node(state: AgentState) -> dict:
    """Classify user intent and detect language."""
    messages = state["messages"]
    last_message = messages[-1]
    
    if not isinstance(last_message, HumanMessage):
        return {"current_intent": None}
    
    # Pass previous messages for context
    chat_history = messages[:-1] if len(messages) > 1 else []
    
    classifier = get_intent_classifier()
    result = await classifier.classify(last_message.content, chat_history=chat_history)
    
    return {
        "current_intent": result.intent.value,
        "language": result.language
    }


async def handle_direct_response(state: AgentState) -> dict:
    """Handle greeting, out-of-scope, and harmful intents directly."""
    intent = state.get("current_intent")
    language = state.get("language", "vi")
    
    if intent == IntentCategory.GREETING.value:
        response = get_greeting_response(language)
    elif intent == IntentCategory.OUT_OF_SCOPE.value:
        response = get_out_of_scope_response(language)
    elif intent == IntentCategory.HARMFUL.value:
        response = get_harmful_response(language)
    else:
        response = "I'm not sure how to help with that."
    
    return {
        "messages": [AIMessage(content=response)],
        "last_agent_response": {"type": "message", "response": response},
    }


async def primary_assistant_node(state: AgentState) -> dict:
    """Primary assistant that handles general queries or delegates."""
    assistant = get_primary_assistant()
    
    # Add user_info to state for the prompt
    state_with_info = {**state, "user_info": state.get("user_info", "")}
    
    return await assistant(state_with_info)


async def booking_agent_node(state: AgentState) -> dict:
    """Booking agent for room reservation operations."""
    agent = get_booking_agent()
    state_with_info = {**state, "user_info": state.get("user_info", "")}
    return await agent(state_with_info)


async def ticket_agent_node(state: AgentState) -> dict:
    """Ticket agent for support ticket operations."""
    agent = get_ticket_agent()
    state_with_info = {**state, "user_info": state.get("user_info", "")}
    return await agent(state_with_info)


async def faq_agent_node(state: AgentState) -> dict:
    """FAQ agent for policy questions."""
    agent = get_faq_agent()
    return await agent(state)


async def it_support_agent_node(state: AgentState) -> dict:
    """IT support agent for technical issues."""
    agent = get_it_support_agent()
    return await agent(state)


# ==================== ROUTING FUNCTIONS ====================

def route_after_intent(state: AgentState) -> Literal[
    "handle_direct",
    "primary_assistant",
]:
    """Route based on classified intent."""
    intent = state.get("current_intent")
    
    # Direct response cases
    if intent in [
        IntentCategory.GREETING.value,
        IntentCategory.OUT_OF_SCOPE.value,
        IntentCategory.HARMFUL.value,
    ]:
        return "handle_direct"
    
    return "primary_assistant"


def route_primary_assistant(state: AgentState) -> Literal[
    "enter_booking",
    "enter_ticket", 
    "enter_faq",
    "enter_it_support",
    "primary_assistant_tools",
    "__end__",
]:
    """Route from primary assistant based on tool calls."""
    route = tools_condition(state)
    if route == END:
        return END
    
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        tool_name = tool_calls[0]["name"]
        if tool_name == ToBookingAgent.__name__:
            return "enter_booking"
        elif tool_name == ToTicketAgent.__name__:
            return "enter_ticket"
        elif tool_name == ToFAQAgent.__name__:
            return "enter_faq"
        elif tool_name == ToITSupportAgent.__name__:
            return "enter_it_support"
        return "primary_assistant_tools"
    
    return END


def route_booking_agent(state: AgentState) -> Literal[
    "booking_safe_tools",
    "booking_sensitive_tools",
    "leave_skill",
    "__end__",
]:
    """Route from booking agent based on tool calls."""
    route = tools_condition(state)
    if route == END:
        return END
    
    tool_calls = state["messages"][-1].tool_calls
    if not tool_calls:
        return END
    
    # Check for escalation
    if any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls):
        return "leave_skill"
    
    # Route to safe or sensitive tools
    safe_names = [t.name for t in booking_safe_tools]
    if all(tc["name"] in safe_names for tc in tool_calls):
        return "booking_safe_tools"
    
    return "booking_sensitive_tools"


def route_ticket_agent(state: AgentState) -> Literal[
    "ticket_safe_tools",
    "ticket_sensitive_tools",
    "leave_skill",
    "__end__",
]:
    """Route from ticket agent based on tool calls."""
    route = tools_condition(state)
    if route == END:
        return END
    
    tool_calls = state["messages"][-1].tool_calls
    if not tool_calls:
        return END
    
    # Check for escalation
    if any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls):
        return "leave_skill"
    
    # Route to safe or sensitive tools
    safe_names = [t.name for t in ticket_safe_tools]
    if all(tc["name"] in safe_names for tc in tool_calls):
        return "ticket_safe_tools"
    
    return "ticket_sensitive_tools"


def route_faq_agent(state: AgentState) -> Literal[
    "faq_tools",
    "leave_skill",
    "__end__",
]:
    """Route from FAQ agent."""
    route = tools_condition(state)
    if route == END:
        return END
    
    tool_calls = state["messages"][-1].tool_calls
    if not tool_calls:
        return END
    
    if any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls):
        return "leave_skill"
    
    return "faq_tools"


def route_it_support_agent(state: AgentState) -> Literal[
    "it_support_tools",
    "leave_skill",
    "__end__",
]:
    """Route from IT support agent."""
    route = tools_condition(state)
    if route == END:
        return END
    
    tool_calls = state["messages"][-1].tool_calls
    if not tool_calls:
        return END
    
    if any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls):
        return "leave_skill"
    
    return "it_support_tools"


def route_to_workflow(state: AgentState) -> Literal[
    "classify_intent",
    "primary_assistant",
    "booking_agent",
    "ticket_agent",
    "faq_agent",
    "it_support_agent",
]:
    """Route to the currently active workflow after fetching user info."""
    dialog_state = state.get("dialog_state")
    if not dialog_state:
        return "classify_intent"
    
    # Resume the last active agent
    current = dialog_state[-1]
    if current == "booking_agent":
        return "booking_agent"
    elif current == "ticket_agent":
        return "ticket_agent"
    elif current == "faq_agent":
        return "faq_agent"
    elif current == "it_support_agent":
        return "it_support_agent"
    
    return "classify_intent"

# ==================== GRAPH CONSTRUCTION ====================

def create_graph() -> StateGraph:
    """Create the LangGraph workflow with specialized agents."""
    builder = StateGraph(AgentState)
    
    # ==================== ADD NODES ====================
    
    # Entry point
    builder.add_node("fetch_user_info", fetch_user_info)
    builder.add_edge(START, "fetch_user_info")
    
    builder.add_node("enter_booking", create_entry_node("Booking Assistant", "booking_agent"))
    builder.add_node("booking_agent", booking_agent_node)
    builder.add_node("booking_safe_tools", create_tool_node_with_fallback(booking_safe_tools))
    builder.add_node("booking_sensitive_tools", create_tool_node_with_fallback(booking_sensitive_tools))
    
    builder.add_node("enter_ticket", create_entry_node("Ticket Support Assistant", "ticket_agent"))
    builder.add_node("ticket_agent", ticket_agent_node)
    builder.add_node("ticket_safe_tools", create_tool_node_with_fallback(ticket_safe_tools))
    builder.add_node("ticket_sensitive_tools", create_tool_node_with_fallback(ticket_sensitive_tools))
    
    builder.add_node("enter_faq", create_entry_node("FAQ Assistant", "faq_agent"))
    builder.add_node("faq_agent", faq_agent_node)
    builder.add_node("faq_tools", create_tool_node_with_fallback(faq_tools))
    
    builder.add_node("enter_it_support", create_entry_node("IT Support Assistant", "it_support_agent"))
    builder.add_node("it_support_agent", it_support_agent_node)
    builder.add_node("it_support_tools", create_tool_node_with_fallback(it_support_tools))
    
    builder.add_node("leave_skill", pop_dialog_state)
    
    # ==================== ADD EDGES ====================
    
    # Entry flow
    builder.add_edge(START, "fetch_user_info")
    builder.add_conditional_edges("fetch_user_info", route_to_workflow)
    
    # Intent classification flow
    builder.add_conditional_edges("classify_intent", route_after_intent)
    builder.add_edge("handle_direct", END)
    
    # Primary assistant flow
    builder.add_conditional_edges("primary_assistant", route_primary_assistant)
    builder.add_edge("primary_assistant_tools", "primary_assistant")
    
    # Booking workflow
    builder.add_edge("enter_booking", "booking_agent")
    builder.add_conditional_edges("booking_agent", route_booking_agent)
    builder.add_edge("booking_safe_tools", "booking_agent")
    builder.add_edge("booking_sensitive_tools", "booking_agent")
    
    # Ticket workflow
    builder.add_edge("enter_ticket", "ticket_agent")
    builder.add_conditional_edges("ticket_agent", route_ticket_agent)
    builder.add_edge("ticket_safe_tools", "ticket_agent")
    builder.add_edge("ticket_sensitive_tools", "ticket_agent")
    
    # FAQ workflow
    builder.add_edge("enter_faq", "faq_agent")
    builder.add_conditional_edges("faq_agent", route_faq_agent)
    builder.add_edge("faq_tools", "faq_agent")
    
    # IT Support workflow
    builder.add_edge("enter_it_support", "it_support_agent")
    builder.add_conditional_edges("it_support_agent", route_it_support_agent)
    builder.add_edge("it_support_tools", "it_support_agent")
    
    # Leave skill returns to primary
    builder.add_edge("leave_skill", "primary_assistant")
    
    return builder


# ==================== GRAPH INSTANCES ====================

async def get_compiled_graph():
    """Get compiled graph with checkpointer."""
    builder = create_graph()
    
    # Create Memory checkpointer for testing/local run
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()
    
    # Compile with checkpointer
    graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["booking_sensitive_tools", "ticket_sensitive_tools"],
    )
    
    return graph


