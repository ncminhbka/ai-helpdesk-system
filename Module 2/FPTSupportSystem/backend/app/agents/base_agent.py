"""
Base agent classes and shared schemas for ReAct pattern implementation.
Provides Assistant class and CompleteOrEscalate tool for workflow control.
"""
from typing import Callable
from pydantic import BaseModel, Field
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import ToolMessage

from app.utils.state import AgentState


class CompleteOrEscalate(BaseModel):
    """
    Tool to mark the current task as completed and/or escalate control 
    back to the primary assistant for re-routing.
    
    Use this when:
    - Task is fully completed
    - User changed their mind
    - User needs help outside current agent's scope
    """
    cancel: bool = Field(
        default=True,
        description="True if canceling current task, False if task completed successfully"
    )
    reason: str = Field(
        description="Reason for completing or escalating"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "cancel": True,
                    "reason": "User changed their mind about the current task."
                },
                {
                    "cancel": False,
                    "reason": "Successfully completed the booking."
                },
                {
                    "cancel": True,
                    "reason": "User needs help with tickets instead of booking."
                }
            ]
        }


# ==================== TRANSFER SCHEMAS ====================

class ToBookingAgent(BaseModel):
    """Transfer work to the specialized booking assistant."""
    request: str = Field(
        description="Summary of user's booking request and any clarifying questions needed"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "request": "User wants to book a meeting room for tomorrow at 2pm"
            }
        }


class ToTicketAgent(BaseModel):
    """Transfer work to the specialized ticket support assistant."""
    request: str = Field(
        description="Summary of user's ticket request"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "request": "User wants to create a support ticket for laptop issue"
            }
        }


class ToFAQAgent(BaseModel):
    """Transfer work to the FAQ/policy assistant."""
    request: str = Field(
        description="The policy question to research"
    )


class ToITSupportAgent(BaseModel):
    """Transfer work to the IT support assistant."""
    request: str = Field(
        description="Description of the technical issue"
    )


# ==================== ASSISTANT CLASS ====================

class Assistant:
    """
    ReAct-style assistant with retry loop.
    
    Implements the core agent pattern from LangGraph tutorial:
    - Invokes the LLM runnable
    - Retries if no valid output
    - Returns messages for state update
    """
    
    def __init__(self, runnable: Runnable):
        """
        Initialize assistant with a runnable (prompt | llm.bind_tools).
        
        Args:
            runnable: LangChain runnable that processes state and returns AI response
        """
        self.runnable = runnable
    
    async def __call__(self, state: AgentState, config: RunnableConfig = None) -> dict:
        """
        Process state and return updated messages.
        
        Implements retry loop to ensure valid output.
        """
        while True:
            result = await self.runnable.ainvoke(state, config)
            
            # Check if we got a valid response
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                # No valid output, ask for retry
                from langchain_core.messages import HumanMessage
                messages = state["messages"] + [
                    HumanMessage(content="Respond with a real output.")
                ]
                state = {**state, "messages": messages}
            else:
                break
        
        return {"messages": result}


# ==================== UTILITY FUNCTIONS ====================

def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    """
    Create an entry node function for a specialized workflow.
    
    This marks the handoff from primary assistant to a specialized agent
    by adding a ToolMessage and updating the dialog state.
    
    Args:
        assistant_name: Human-readable name for the assistant
        new_dialog_state: State to push onto dialog stack
    
    Returns:
        Node function that handles the handoff
    """
    def entry_node(state: AgentState) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. "
                    f"Reflect on the above conversation between the host assistant and the user. "
                    f"The user's intent is unsatisfied. Use the provided tools to assist the user. "
                    f"Remember, you are {assistant_name}, and the action is not complete until "
                    f"after you have successfully invoked the appropriate tool. "
                    f"If the user changes their mind or needs help with other tasks, "
                    f"call the CompleteOrEscalate function to let the primary assistant take control. "
                    f"Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,
        }
    
    return entry_node


def pop_dialog_state(state: AgentState) -> dict:
    """
    Pop the dialog stack and return to the primary assistant.
    
    This handles the CompleteOrEscalate tool call by:
    - Adding a ToolMessage confirming the handoff
    - Setting dialog_state to "pop"
    """
    messages = []
    if state["messages"][-1].tool_calls:
        messages.append(
            ToolMessage(
                content="Resuming dialog with the host assistant. "
                "Please reflect on the past conversation and assist the user as needed.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {
        "dialog_state": "pop",
        "messages": messages,
    }
