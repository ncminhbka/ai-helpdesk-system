"""
FAQ Agent - Handles policy questions using RAG.
Implements ReAct pattern with CompleteOrEscalate for workflow control.
"""
import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from app.agents.base_agent import Assistant, CompleteOrEscalate
from app.tools.rag_tools import search_fpt_policies

from dotenv import load_dotenv
load_dotenv()


from app.agents.prompts import FAQ_SYSTEM_PROMPT


# ==================== TOOL DEFINITIONS ====================

# FAQ tools (all are safe - read-only)
faq_tools = [search_fpt_policies]


# ==================== RUNNABLE CREATION ====================

def get_faq_runnable() -> Runnable:
    """Create the FAQ agent runnable."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.2,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", FAQ_SYSTEM_PROMPT),
        ("placeholder", "{messages}"),
    ]).partial(time=datetime.now)
    
    # Bind tools including CompleteOrEscalate
    return prompt | llm.bind_tools(faq_tools + [CompleteOrEscalate])


# ==================== AGENT INSTANCE ====================

# Create the FAQ assistant using ReAct pattern
faq_runnable = get_faq_runnable()
faq_assistant = Assistant(faq_runnable)


def get_faq_agent() -> Assistant:
    """Get the FAQ assistant instance."""
    return faq_assistant
