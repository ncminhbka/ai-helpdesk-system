"""
Booking Agent - Handles meeting room booking operations.
Implements ReAct pattern with safe/sensitive tool separation.
"""
import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable


from app.agents.base_agent import Assistant, CompleteOrEscalate
from app.tools.booking_tools import book_room, track_booking, update_booking, cancel_booking

from dotenv import load_dotenv
load_dotenv()


from app.agents.prompts import BOOKING_SYSTEM_PROMPT


# ==================== TOOL DEFINITIONS ====================

# Safe tools: read-only operations, no user confirmation needed
booking_safe_tools = [track_booking]

# Sensitive tools: write operations, require user confirmation (HITL)
booking_sensitive_tools = [book_room, update_booking, cancel_booking]

# All booking tools
booking_tools = booking_safe_tools + booking_sensitive_tools


# ==================== RUNNABLE CREATION ====================

def get_booking_runnable() -> Runnable:
    """Create the booking agent runnable."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", BOOKING_SYSTEM_PROMPT),
        ("placeholder", "{messages}"),
    ]).partial(time=datetime.now)
    
    # Bind all tools including CompleteOrEscalate
    return prompt | llm.bind_tools(booking_tools + [CompleteOrEscalate])


# ==================== AGENT INSTANCE ====================

# Create the booking assistant using ReAct pattern
booking_runnable = get_booking_runnable()
booking_assistant = Assistant(booking_runnable)


def get_booking_agent() -> Assistant:
    """Get the booking assistant instance."""
    return booking_assistant
