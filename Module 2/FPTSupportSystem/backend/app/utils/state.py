"""
State management for LangGraph multi-agent system.
Implements dialog state stack for tracking active workflows.
"""
from typing import Annotated, Optional, Literal, TypedDict
from langgraph.graph.message import add_messages, AnyMessage


def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """
    Update dialog state stack (push/pop agents).
    
    Args:
        left: Current stack
        right: Action - None (no change), "pop" (remove last), or agent name (push)
    
    Returns:
        Updated stack
    """
    if right is None:
        return left
    if right == "pop":
        return left[:-1] if left else []
    return left + [right]


# Valid dialog states for type safety
DialogState = Literal[
    "primary_assistant",
    "booking_agent",
    "ticket_agent",
    "faq_agent",
    "it_support_agent",
]


class AgentState(TypedDict):
    """
    Global state for the multi-agent system.
    
    Attributes:
        messages: Conversation history with automatic message merging
        user_id: Authenticated user's ID
        user_email: User's email address
        session_id: Current chat session ID
        language: Detected language ('vi' or 'en')
        current_intent: Classified intent from primary assistant
        dialog_state: Stack tracking which agent is in control
        pending_confirmation: Data for HITL confirmation
        last_agent_response: Last response from any agent
    """
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: Optional[int]
    user_email: Optional[str]
    session_id: Optional[str]
    language: str
    current_intent: Optional[str]
    dialog_state: Annotated[list[DialogState], update_dialog_stack]
    pending_confirmation: Optional[dict]
    last_agent_response: Optional[dict]
    user_info: Optional[str]
