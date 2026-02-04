"""
Ticket Agent - Handles support ticket operations.
Returns HITL confirmation requests for create/update operations.
"""
import os
from typing import Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from tools.ticket_tools import create_ticket, track_ticket, update_ticket

from dotenv import load_dotenv
load_dotenv()


TICKET_SYSTEM_PROMPT = """You are the Ticket Support Agent for FPT Customer Support.

Your role is to help users with support tickets:
1. Create new support tickets for IT or customer support issues
2. Track existing ticket status
3. Update ticket information

Available tools:
- create_ticket: Create a new support ticket
- track_ticket: Check status of an existing ticket
- update_ticket: Update ticket information

Instructions:
1. Gather necessary information from the user
2. For CREATE: Ask for content (issue title) and description (details)
3. For TRACK: Ask for ticket ID
4. For UPDATE: Ask for ticket ID and what to update
5. Optional info: customer_name, customer_phone, email
6. Always confirm the information before proceeding

User context will be injected automatically (email from session if available).
Support both Vietnamese and English.
"""


class TicketAgent:
    """Ticket Agent for managing support tickets."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.tools = [create_ticket, track_ticket, update_ticket]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
    
    async def process(
        self,
        user_message: str,
        chat_history: list = None,
        user_info: dict = None,
        language: str = "vi"
    ) -> dict:
        """
        Process a ticket-related request.
        
        Returns:
            Dictionary with response or confirmation request
        """
        messages = [SystemMessage(content=TICKET_SYSTEM_PROMPT)]
        
        # Add user context
        if user_info:
            context = f"\nUser context: email={user_info.get('email', 'not provided')}"
            messages[0] = SystemMessage(content=TICKET_SYSTEM_PROMPT + context)
        
        if chat_history:
            messages.extend(chat_history[-6:])
        
        messages.append(HumanMessage(content=user_message))
        
        # Invoke LLM with tools
        response = await self.llm_with_tools.ainvoke(messages)
        
        # Check if tool call is requested
        if response.tool_calls:
            tool_call = response.tool_calls[0]
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            
            # Inject email from context if not provided
            if user_info and "email" not in tool_args and user_info.get("email"):
                tool_args["email"] = user_info["email"]
            
            # Execute the tool
            if tool_name == "create_ticket":
                result = create_ticket.invoke(tool_args)
            elif tool_name == "track_ticket":
                result = track_ticket.invoke(tool_args)
            elif tool_name == "update_ticket":
                result = update_ticket.invoke(tool_args)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            # Check if confirmation is required
            if result.get("requires_confirmation"):
                return {
                    "type": "confirm",
                    "action": result["action"],
                    "data": result["data"],
                    "fields": result.get("fields", []),
                    "message": result.get(f"message_{language}", result.get("message_vi", ""))
                }
            
            # Query action (track_ticket) - return as confirm type for main.py to execute
            # Since track_ticket doesn't have message, we pass the action data for execution
            if result.get("action") in ["track_ticket"]:
                return {
                    "type": "confirm",  # Use confirm type so main.py can intercept and execute
                    "action": result["action"],
                    "data": result["data"],
                    "message": "Đang tra cứu thông tin ticket... / Looking up ticket information..."
                }
            
            # Direct response (shouldn't normally reach here)
            return {
                "type": "message",
                "response": str(result)
            }
        
        # No tool call - conversational response
        return {
            "type": "message",
            "response": response.content
        }


# Singleton
_ticket_agent: Optional[TicketAgent] = None


def get_ticket_agent() -> TicketAgent:
    global _ticket_agent
    if _ticket_agent is None:
        _ticket_agent = TicketAgent()
    return _ticket_agent
