"""
Primary Assistant - Routes requests to specialized agents.
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.agents.base_agent import (
    Assistant, ToBookingAgent, ToTicketAgent, ToFAQAgent, ToITSupportAgent
)
from app.agents.prompts import PRIMARY_SYSTEM_PROMPT
from app.utils.helpers import get_vietnam_time
from dotenv import load_dotenv

load_dotenv()

# get primary assistant runnable (prompt + llm + tools)
def get_primary_assistant_runnable() -> Runnable:
    """Create the primary assistant runnable with transfer tools."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", PRIMARY_SYSTEM_PROMPT),
        ("placeholder", "{messages}"),
    ]).partial(time=get_vietnam_time)

    # Bind transfer tools — primary assistant can ONLY delegate
    return prompt | llm.bind_tools(
        [ToBookingAgent, ToTicketAgent, ToFAQAgent, ToITSupportAgent]
    )


# Create singleton instances
primary_runnable = get_primary_assistant_runnable()
primary_assistant = Assistant(primary_runnable)


def get_primary_agent() -> Assistant:
    """Get the primary assistant instance."""
    return primary_assistant
