"""
Booking Agent - Handles meeting room booking operations.
Implements ReAct pattern with safe/sensitive tool separation.
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.agents.base_agent import Assistant, CompleteOrEscalate
from app.tools.booking_tools import book_room, track_booking, update_booking, cancel_booking
from app.agents.prompts import BOOKING_SYSTEM_PROMPT
from app.utils.helpers import get_vietnam_time
from dotenv import load_dotenv

load_dotenv()


# ==================== TOOL DEFINITIONS ====================

# Safe tools: read-only, no HITL needed
booking_safe_tools = [track_booking]

# Sensitive tools: write operations, HITL confirmation
booking_sensitive_tools = [book_room, update_booking, cancel_booking]

# All booking tools
booking_tools = booking_safe_tools + booking_sensitive_tools


# ==================== RUNNABLE CREATION ====================

def get_booking_runnable() -> Runnable:
    """Create the booking agent runnable."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", BOOKING_SYSTEM_PROMPT),
        ("placeholder", "{messages}"),
    ]).partial(time=get_vietnam_time)

    return prompt | llm.bind_tools(booking_tools + [CompleteOrEscalate])


# ==================== AGENT INSTANCE ====================

booking_runnable = get_booking_runnable()
booking_assistant = Assistant(booking_runnable)


def get_booking_agent() -> Assistant:
    """Get the booking assistant instance."""
    return booking_assistant
