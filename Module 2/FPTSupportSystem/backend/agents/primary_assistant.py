"""
Primary Assistant - Main router agent with intent classification.
Routes queries to specialized agents or handles directly (greetings, blocks).
"""
import os
from typing import Literal, Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage

from dotenv import load_dotenv
load_dotenv()


# Agent routing targets
AGENT_ROUTES = Literal[
    "faq_agent",
    "ticket_agent", 
    "booking_agent",
    "it_support_agent",
    "respond_directly",
    "end"
]


PRIMARY_SYSTEM_PROMPT = """You are the Primary Assistant for FPT Customer Support System.

Your responsibilities:
1. Route user requests to the appropriate specialized agent
2. Respond directly for simple interactions (greetings, clarifications)
3. Maintain context throughout the conversation
4. Ensure smooth handoff between agents

Available agents:
- FAQ Agent: Questions about FPT policies, regulations, code of conduct, data protection, human rights
- Ticket Agent: Create, track, or update support tickets
- Booking Agent: Book, track, update, or cancel meeting rooms
- IT Support Agent: Technical issues with computers, software, hardware, troubleshooting

Always be helpful, professional, and maintain a friendly tone.
Support both Vietnamese and English languages.
"""


class PrimaryAssistant:
    """Primary assistant that routes queries and handles direct responses."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
    
    async def route_query(
        self,
        intent: str,
        message: str,
        language: str = "vi"
    ) -> tuple[AGENT_ROUTES, Optional[str]]:
        """
        Determine routing based on classified intent.
        
        Returns:
            Tuple of (route_target, direct_response)
            If direct_response is not None, respond directly without routing.
        """
        from utils.intent_classifier import (
            IntentCategory,
            get_greeting_response,
            get_out_of_scope_response,
            get_harmful_response
        )
        
        # Direct response cases
        if intent == IntentCategory.GREETING.value:
            return ("respond_directly", get_greeting_response(language))
        
        if intent == IntentCategory.OUT_OF_SCOPE.value:
            return ("respond_directly", get_out_of_scope_response(language))
        
        if intent == IntentCategory.HARMFUL.value:
            return ("respond_directly", get_harmful_response(language))
        
        # Routing cases
        if intent == IntentCategory.FAQ_POLICY.value:
            return ("faq_agent", None)
        
        if intent in [
            IntentCategory.TICKET_CREATE.value,
            IntentCategory.TICKET_TRACK.value,
            IntentCategory.TICKET_UPDATE.value
        ]:
            return ("ticket_agent", None)
        
        if intent in [
            IntentCategory.BOOKING_CREATE.value,
            IntentCategory.BOOKING_TRACK.value,
            IntentCategory.BOOKING_UPDATE.value,
            IntentCategory.BOOKING_CANCEL.value
        ]:
            return ("booking_agent", None)
        
        if intent == IntentCategory.IT_SUPPORT.value:
            return ("it_support_agent", None)
        
        # Default: respond directly with clarification
        clarification = {
            "vi": "Xin lỗi, tôi không hiểu rõ yêu cầu của bạn. Bạn có thể nói rõ hơn không?",
            "en": "I'm sorry, I didn't understand your request. Could you please clarify?"
        }
        return ("respond_directly", clarification.get(language, clarification["en"]))
    
    async def generate_handoff_message(
        self,
        target_agent: str,
        user_message: str,
        language: str = "vi"
    ) -> str:
        """Generate a handoff message when routing to another agent."""
        handoff_messages = {
            "faq_agent": {
                "vi": "Tôi sẽ tìm kiếm thông tin về chính sách FPT cho bạn...",
                "en": "Let me search for FPT policy information for you..."
            },
            "ticket_agent": {
                "vi": "Tôi sẽ giúp bạn với ticket hỗ trợ...",
                "en": "I'll help you with your support ticket..."
            },
            "booking_agent": {
                "vi": "Tôi sẽ giúp bạn với việc đặt phòng họp...",
                "en": "I'll help you with meeting room booking..."
            },
            "it_support_agent": {
                "vi": "Tôi sẽ tìm giải pháp cho vấn đề kỹ thuật của bạn...",
                "en": "I'll find a solution for your technical issue..."
            }
        }
        
        return handoff_messages.get(target_agent, {}).get(language, "Processing your request...")
    
    async def generate_response(
        self,
        messages: list,
        user_info: dict
    ) -> str:
        """Generate a direct response from Primary Assistant."""
        formatted_messages = [{"role": "system", "content": PRIMARY_SYSTEM_PROMPT}]
        
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                formatted_messages.append({"role": "assistant", "content": msg.content})
        
        response = await self.llm.ainvoke(formatted_messages)
        return response.content


# Singleton instance
_primary_assistant: Optional[PrimaryAssistant] = None


def get_primary_assistant() -> PrimaryAssistant:
    """Get or create primary assistant singleton."""
    global _primary_assistant
    if _primary_assistant is None:
        _primary_assistant = PrimaryAssistant()
    return _primary_assistant
