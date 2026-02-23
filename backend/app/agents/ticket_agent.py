"""
Ticket Agent - Handles support ticket operations.
Implements ReAct pattern with safe/sensitive tool separation.
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.agents.base_agent import Assistant, CompleteOrEscalate
from app.tools.ticket_tools import create_ticket, track_ticket, update_ticket
from app.agents.prompts import TICKET_SYSTEM_PROMPT
from app.utils.helpers import get_vietnam_time
from dotenv import load_dotenv

load_dotenv()


# ==================== TOOL DEFINITIONS ====================

# Safe tools: read-only
ticket_safe_tools = [track_ticket]

# Sensitive tools: write operations
ticket_sensitive_tools = [create_ticket, update_ticket]

# All ticket tools
ticket_tools = ticket_safe_tools + ticket_sensitive_tools


# ==================== RUNNABLE CREATION ====================

def get_ticket_runnable() -> Runnable:
    """Create the ticket agent runnable."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", TICKET_SYSTEM_PROMPT),
        ("placeholder", "{messages}"),
    ]).partial(time=get_vietnam_time)

    return prompt | llm.bind_tools(ticket_tools + [CompleteOrEscalate])


# ==================== AGENT INSTANCE ====================

ticket_runnable = get_ticket_runnable()
ticket_assistant = Assistant(ticket_runnable)


def get_ticket_agent() -> Assistant:
    """Get the ticket assistant instance."""
    return ticket_assistant
