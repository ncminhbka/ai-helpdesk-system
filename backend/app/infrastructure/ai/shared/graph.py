"""
LangGraph orchestration for the FPT HelpDesk multi-agent system.

This module defines the full StateGraph with:
- Primary assistant for intent routing
- 4 specialized agent workflows (Booking, Ticket, FAQ, IT Support)
- Entry/exit node utilities for agent handoffs
- Unified tool nodes per agent (HITL is handled inside tools via interrupt())
"""
from langchain_core.messages import ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition, ToolNode


from app.infrastructure.ai.shared.state import AgentState

from app.infrastructure.ai.primary.agent import get_primary_agent
from app.infrastructure.ai.booking.agent import get_booking_agent, booking_tools
from app.infrastructure.ai.ticket.agent import get_ticket_agent, ticket_tools
from app.infrastructure.ai.faq.agent import get_faq_agent, faq_tools
from app.infrastructure.ai.it_support.agent import get_it_support_agent, it_support_tools


# ==================== UTILITY FUNCTIONS ====================

def create_entry_node(display_name: str, node_name: str):
    """
    Create an entry node that pushes the agent NODE NAME onto the dialog stack
    and inserts a system message to orient the new agent.

    Args:
        display_name: Human-readable name for the orientation message (e.g. "Booking Agent")
        node_name: Actual graph node name for routing (e.g. "booking_agent")
    """
    def entry_node(state: AgentState) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {display_name}. "
                            f"Reflect on the above conversation between the user and the primary assistant. "
                            f"The user's intent is to use the {display_name}'s capabilities. "
                            f"Use the provided tools to assist the user. Remember, you are {display_name}. "
                            f"If the user needs help outside your scope, call CompleteOrEscalate to return to the primary assistant. "
                            f"Do not mention who you are — just act as the relevant assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": node_name,
        }

    return entry_node


def pop_dialog_state(state: AgentState) -> dict:
    """Pop current agent from dialog stack — returns control to the parent."""
    messages = []
    if state["messages"][-1].tool_calls:
        messages.append(
            ToolMessage(
                content="Returning to the primary assistant. Please reflect on the conversation and assist the user.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {
        "dialog_state": "pop",
        "messages": messages,
    }


# ==================== ROUTING FUNCTIONS ====================

def route_primary_assistant(state: AgentState):
    """Route primary assistant's output to the correct specialized agent."""
    route = tools_condition(state)
    if route == END:
        return END

    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        tool_name = tool_calls[0]["name"]

        if tool_name == "ToBookingAgent":
            return "enter_booking"
        elif tool_name == "ToTicketAgent":
            return "enter_ticket"
        elif tool_name == "ToFAQAgent":
            return "enter_faq"
        elif tool_name == "ToITSupportAgent":
            return "enter_it_support"

    return END


def route_booking_agent(state: AgentState):
    """Route booking agent output to tools or back to primary."""
    route = tools_condition(state)
    if route == END:
        return END

    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        tool_name = tool_calls[0]["name"]
        if tool_name == "CompleteOrEscalate":
            return "leave_skill"
        return "booking_tools"

    return END


def route_ticket_agent(state: AgentState):
    """Route ticket agent output to tools or back to primary."""
    route = tools_condition(state)
    if route == END:
        return END

    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        tool_name = tool_calls[0]["name"]
        if tool_name == "CompleteOrEscalate":
            return "leave_skill"
        return "ticket_tools"

    return END


def route_faq_agent(state: AgentState):
    """Route FAQ agent output to tools or back to primary."""
    route = tools_condition(state)
    if route == END:
        return END

    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        tool_name = tool_calls[0]["name"]
        if tool_name == "CompleteOrEscalate":
            return "leave_skill"
        return "faq_tools"

    return END


def route_it_support_agent(state: AgentState):
    """Route IT support agent output to tools or back to primary."""
    route = tools_condition(state)
    if route == END:
        return END

    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        tool_name = tool_calls[0]["name"]
        if tool_name == "CompleteOrEscalate":
            return "leave_skill"
        return "it_support_tools"

    return END


def route_to_workflow(state: AgentState):
    """
    Entry routing: if a specialized agent is active (dialog_state has entries),
    resume that agent. Otherwise, start with the primary assistant.
    """
    dialog_state = state.get("dialog_state")
    if not dialog_state:
        return "primary_assistant"
    return dialog_state[-1]


# ==================== GRAPH CONSTRUCTION ====================

def create_graph(checkpointer=None):
    """
    Build and return the compiled LangGraph StateGraph.

    The graph structure:
    START → fetch_user_info → route_to_workflow →
        ├── primary_assistant → route to enter_* nodes
        ├── booking workflow (enter → agent → tools → back to agent)
        ├── ticket workflow (enter → agent → tools → back to agent)
        ├── faq workflow (enter → agent → tools → back to agent)
        └── it_support workflow (enter → agent → tools → back to agent)

    HITL: When ENABLE_HITL=true, sensitive tools use dynamic interrupt()
    inside the tool functions themselves — no interrupt_before needed.
    """
    builder = StateGraph(AgentState)

    # ----- Fetch user info node -----
    def fetch_user_info(state: AgentState):
        """Pass-through node that ensures user context is available."""
        return {
            "user_info": {
                "user_id": state.get("user_id"),
                "user_email": state.get("user_email"),
            }
        }

    builder.add_node("fetch_user_info", fetch_user_info)
    builder.add_edge(START, "fetch_user_info")
    builder.add_conditional_edges("fetch_user_info", route_to_workflow)

    # ----- Primary Assistant -----
    builder.add_node("primary_assistant", get_primary_agent())
    builder.add_conditional_edges(
        "primary_assistant",
        route_primary_assistant,
        {
            "enter_booking": "enter_booking",
            "enter_ticket": "enter_ticket",
            "enter_faq": "enter_faq",
            "enter_it_support": "enter_it_support",
            END: END,
        },
    )

    # ----- Leave Skill (shared) -----
    builder.add_node("leave_skill", pop_dialog_state)
    builder.add_edge("leave_skill", "primary_assistant")

    # ==================== BOOKING WORKFLOW ====================
    builder.add_node("enter_booking", create_entry_node("Booking Agent", "booking_agent"))
    builder.add_node("booking_agent", get_booking_agent())
    builder.add_node("booking_tools", ToolNode(booking_tools))

    builder.add_edge("enter_booking", "booking_agent")
    builder.add_conditional_edges(
        "booking_agent",
        route_booking_agent,
        {
            "booking_tools": "booking_tools",
            "leave_skill": "leave_skill",
            END: END,
        },
    )
    builder.add_edge("booking_tools", "booking_agent")

    # ==================== TICKET WORKFLOW ====================
    builder.add_node("enter_ticket", create_entry_node("Ticket Agent", "ticket_agent"))
    builder.add_node("ticket_agent", get_ticket_agent())
    builder.add_node("ticket_tools", ToolNode(ticket_tools))

    builder.add_edge("enter_ticket", "ticket_agent")
    builder.add_conditional_edges(
        "ticket_agent",
        route_ticket_agent,
        {
            "ticket_tools": "ticket_tools",
            "leave_skill": "leave_skill",
            END: END,
        },
    )
    builder.add_edge("ticket_tools", "ticket_agent")

    # ==================== FAQ WORKFLOW ====================
    builder.add_node("enter_faq", create_entry_node("FAQ Agent", "faq_agent"))
    builder.add_node("faq_agent", get_faq_agent())
    builder.add_node("faq_tools", ToolNode(faq_tools))

    builder.add_edge("enter_faq", "faq_agent")
    builder.add_conditional_edges(
        "faq_agent",
        route_faq_agent,
        {
            "faq_tools": "faq_tools",
            "leave_skill": "leave_skill",
            END: END,
        },
    )
    builder.add_edge("faq_tools", "faq_agent")

    # ==================== IT SUPPORT WORKFLOW ====================
    builder.add_node("enter_it_support", create_entry_node("IT Support Agent", "it_support_agent"))
    builder.add_node("it_support_agent", get_it_support_agent())
    builder.add_node("it_support_tools", ToolNode(it_support_tools))

    builder.add_edge("enter_it_support", "it_support_agent")
    builder.add_conditional_edges(
        "it_support_agent",
        route_it_support_agent,
        {
            "it_support_tools": "it_support_tools",
            "leave_skill": "leave_skill",
            END: END,
        },
    )
    builder.add_edge("it_support_tools", "it_support_agent")

    # ----- Compile with checkpointer (no interrupt_before needed) -----
    graph = builder.compile(checkpointer=checkpointer)

    return graph
