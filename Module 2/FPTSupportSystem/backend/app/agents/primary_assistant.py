"""
Primary Assistant - Main router agent with intent classification and transfer tools.
Routes queries to specialized agents or handles directly (greetings, blocks).
"""
import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.agents.base_agent import (
    Assistant,
    ToBookingAgent,
    ToTicketAgent,
    ToFAQAgent,
    ToITSupportAgent,
)


from dotenv import load_dotenv
load_dotenv()


from app.agents.prompts import PRIMARY_SYSTEM_PROMPT


# ==================== TOOL DEFINITIONS ====================




# Transfer tools to delegate to specialized assistants
transfer_tools = [
    ToBookingAgent,
    ToTicketAgent,
    ToFAQAgent,
    ToITSupportAgent,
]


# ==================== RUNNABLE CREATION ====================

def get_primary_assistant_runnable() -> Runnable:
    """Create the primary assistant runnable."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", PRIMARY_SYSTEM_PROMPT),
        ("placeholder", "{messages}"),
    ]).partial(time=datetime.now)
    
    # Bind transfer tools
    return prompt | llm.bind_tools(transfer_tools)


# ==================== AGENT INSTANCE ====================

# Create the primary assistant using ReAct pattern
primary_runnable = get_primary_assistant_runnable()
primary_assistant = Assistant(primary_runnable)


def get_primary_assistant() -> Assistant:
    """Get the primary assistant instance."""
    return primary_assistant
