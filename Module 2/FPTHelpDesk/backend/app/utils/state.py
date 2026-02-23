"""
AgentState definition and dialog stack management for LangGraph.
This is the central state schema shared by all agents.
"""
from typing import Annotated, Optional
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages


def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """
    Reducer for the dialog_state field.
    Manages a stack of active agent workflows.

    - If right is None, return left unchanged.
    - If right == "pop", remove the top of the stack.
    - Otherwise, push the new agent name onto the stack.
    """
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]


class AgentState(TypedDict):
    """
    Shared state for the multi-agent graph.

    Fields:
    - messages: Conversation messages (auto-merged by add_messages).
    - user_id: Authenticated user's database ID.
    - user_email: User's email for context injection into tools.
    - session_id: Current chat session ID.
    - user_info: Optional dict with extra user info (name, etc.).
    - language: Detected language ('vi' or 'en').
    - current_intent: Current topic/intent for routing.
    - dialog_state: Stack of active agent workflows.
    """
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: Optional[int]
    user_email: Optional[str]
    session_id: Optional[str]
    user_info: Optional[dict]
    language: Optional[str]
    current_intent: Optional[str]
    dialog_state: Annotated[list[str], update_dialog_stack]
