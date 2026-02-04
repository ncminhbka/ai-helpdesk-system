"""
Booking Agent - Handles meeting room booking operations.
Returns HITL confirmation requests for create/update/cancel operations.
"""
import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from tools.booking_tools import book_room, track_booking, update_booking, cancel_booking

from dotenv import load_dotenv
load_dotenv()


BOOKING_SYSTEM_PROMPT = """You are the Booking Agent for FPT Customer Support.

Your role is to help users with meeting room bookings:
1. Book new meeting rooms
2. Track existing booking status
3. Update booking information
4. Cancel bookings

Available tools:
- book_room: Create a new room booking
- track_booking: Check status of an existing booking
- update_booking: Update booking information
- cancel_booking: Cancel a booking

Instructions:
1. Gather necessary information from the user
2. For BOOK: Ask for reason (purpose) and time (datetime)
3. For TRACK: Ask for booking ID
4. For UPDATE: Ask for booking ID and what to update
5. For CANCEL: Ask for booking ID and confirm
6. Optional info: customer_name, customer_phone, email, note
7. Time format: YYYY-MM-DD HH:MM

User context will be injected automatically (email from session if available).
Support both Vietnamese and English.
"""


class BookingAgent:
    """Booking Agent for managing meeting room bookings."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.tools = [book_room, track_booking, update_booking, cancel_booking]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
    
    async def process(
        self,
        user_message: str,
        chat_history: list = None,
        user_info: dict = None,
        language: str = "vi"
    ) -> dict:
        """
        Process a booking-related request.
        
        Returns:
            Dictionary with response or confirmation request
        """
        messages = [SystemMessage(content=BOOKING_SYSTEM_PROMPT)]
        
        # Add user context
        if user_info:
            context = f"\nUser context: email={user_info.get('email', 'not provided')}"
            messages[0] = SystemMessage(content=BOOKING_SYSTEM_PROMPT + context)
        
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
            if tool_name == "book_room":
                result = book_room.invoke(tool_args)
            elif tool_name == "track_booking":
                result = track_booking.invoke(tool_args)
            elif tool_name == "update_booking":
                result = update_booking.invoke(tool_args)
            elif tool_name == "cancel_booking":
                result = cancel_booking.invoke(tool_args)
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
            
            # Query action (track_booking) - return as confirm type for main.py to execute
            if result.get("action") in ["track_booking"]:
                return {
                    "type": "confirm",  # Use confirm type so main.py can intercept and execute
                    "action": result["action"],
                    "data": result["data"],
                    "message": "Đang tra cứu thông tin đặt phòng... / Looking up booking information..."
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
_booking_agent: Optional[BookingAgent] = None


def get_booking_agent() -> BookingAgent:
    global _booking_agent
    if _booking_agent is None:
        _booking_agent = BookingAgent()
    return _booking_agent
