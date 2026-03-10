"""
Base agent components for the multi-agent system.

Contains:
- Assistant class: ReAct loop execution with retries
- CompleteOrEscalate: Tool for agent handoff/completion
- Transfer schemas: ToBookingAgent, ToTicketAgent, ToFAQAgent, ToITSupportAgent
"""
from langchain_core.messages import ToolMessage, trim_messages
from langchain_core.runnables import Runnable, RunnableConfig
from pydantic import BaseModel, Field
from typing import Literal, Optional

from app.infrastructure.ai.shared.state import AgentState


# ==================== ASSISTANT CLASS ====================

class Assistant:
    """
    ReAct pattern agent wrapper.
    Invokes the runnable (prompt+LLM+tools) in a loop until it produces
    a valid response (not empty, not just tool calls with no content).
    Includes history trimming to prevent context window overflow.
    """

    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    # invoke the runnable with the state and config until it produces a valid response
    async def __call__(self, state: AgentState, config: RunnableConfig):
        max_retries = 3

        # Trim messages to keep context window manageable
        trimmed_messages = trim_messages(
            state["messages"],
            max_tokens=4000,
            strategy="last",
            token_counter="approximate",
            include_system=True,
            start_on="human",
            allow_partial=False,
        )

        # Create a temporary state for the invocation with trimmed messages
        invoke_state = {**state, "messages": trimmed_messages}

        for attempt in range(max_retries):
            # Invoke with the trimmed state, but original config
            result = await self.runnable.ainvoke(invoke_state, config)

            # If no tool calls and no content, retry with nudge
            if not result.tool_calls and (
                not result.content
                or (isinstance(result.content, list) and not result.content[0].get("text"))
            ):
                messages = state["messages"] + [
                    ("user", "Respond with a real output. Do not leave your response empty.")
                ]
                state = {**state, "messages": messages}
                continue

            break

        return {"messages": result}


# ==================== COMPLETE OR ESCALATE ====================

class CompleteOrEscalate(BaseModel):
    """
    Tool for a specialized agent to signal completion or escalation.

    Use this when:
    1. The task is completed successfully (cancel=False)
    2. The user needs a different type of help (cancel=True)
    3. The user changes their mind (cancel=True)
    """

    cancel: bool = Field(
        default=True,
        description="True if the user wants to cancel the current task or needs different help."
    )
    reason: str = Field(
        description="Brief explanation of why completing or escalating."
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "cancel": True,
                    "reason": "User wants to ask about policies instead of booking.",
                },
                {
                    "cancel": False,
                    "reason": "Successfully created the ticket.",
                },
            ]
        }


# ==================== TRANSFER SCHEMAS ====================

# Fake tooks for primary assistant to transfer to specialized agents
class ToBookingAgent(BaseModel):
    """Transfer to the Booking Agent for meeting room operations."""
    request: str = Field(
        description="The user's booking-related request to hand off."
    )


class ToTicketAgent(BaseModel):
    """Transfer to the Ticket Agent for support ticket operations."""
    request: str = Field(
        description="The user's ticket-related request to hand off."
    )


class ToFAQAgent(BaseModel):
    """Transfer to the FAQ Agent for FPT policy questions."""
    request: str = Field(
        description="The user's policy question to hand off."
    )


class ToITSupportAgent(BaseModel):
    """Transfer to the IT Support Agent for technical troubleshooting."""
    request: str = Field(
        description="The user's IT issue to hand off."
    )
