"""
IT Support Agent - Handles technical troubleshooting using Tavily search.
Implements ReAct pattern with CompleteOrEscalate for workflow control.
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.infrastructure.ai.shared.base import Assistant, CompleteOrEscalate
from app.infrastructure.ai.it_support.tools import search_it_solutions
from app.infrastructure.ai.it_support.prompt import IT_SUPPORT_SYSTEM_PROMPT
from app.application.utils.helpers import get_vietnam_time
from dotenv import load_dotenv

load_dotenv()


# ==================== TOOL DEFINITIONS ====================

# IT Support tools (all are safe - read-only search)
it_support_tools = [search_it_solutions]


# ==================== RUNNABLE CREATION ====================

def get_it_support_runnable() -> Runnable:
    """Create the IT support agent runnable."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", IT_SUPPORT_SYSTEM_PROMPT),
        ("placeholder", "{messages}"),
    ]).partial(time=get_vietnam_time)

    return prompt | llm.bind_tools(it_support_tools + [CompleteOrEscalate])


# ==================== AGENT INSTANCE ====================

it_support_runnable = get_it_support_runnable()
it_support_assistant = Assistant(it_support_runnable)


def get_it_support_agent() -> Assistant:
    """Get the IT support assistant instance."""
    return it_support_assistant
