"""
FAQ Agent - Handles policy questions using RAG.
Implements ReAct pattern with CompleteOrEscalate for workflow control.
"""
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.infrastructure.ai.shared.base import Assistant, CompleteOrEscalate
from app.infrastructure.ai.faq.tools import search_fpt_policies
from app.infrastructure.ai.faq.prompt import FAQ_SYSTEM_PROMPT
from app.infrastructure.utils.helpers import get_vietnam_time
from dotenv import load_dotenv

load_dotenv()


# ==================== TOOL DEFINITIONS ====================

# FAQ tools (all are safe - read-only)
faq_tools = [search_fpt_policies]


# ==================== RUNNABLE CREATION ====================

def get_faq_runnable() -> Runnable:
    """Create the FAQ agent runnable."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", FAQ_SYSTEM_PROMPT),
        ("placeholder", "{messages}"),
    ]).partial(time=get_vietnam_time)

    return prompt | llm.bind_tools(faq_tools + [CompleteOrEscalate])


# ==================== AGENT INSTANCE ====================

faq_runnable = get_faq_runnable()
faq_assistant = Assistant(faq_runnable)


def get_faq_agent() -> Assistant:
    """Get the FAQ assistant instance."""
    return faq_assistant
