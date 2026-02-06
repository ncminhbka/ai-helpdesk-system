"""
Ticket management tools for the Ticket Support Agent.
Supports HITL (Human-in-the-Loop) confirmation before database writes.
"""
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from schemas.ticket import TicketData, TicketUpdateData






@tool(args_schema=TicketData)
async def create_ticket(
    content: str,
    description: str,
    user_id: int, 
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    email: Optional[str] = None
) -> dict:
    """
    Create a new support ticket in the database.
    
    Args:
        content: Brief description of the issue (required)
        description: Detailed description of the issue (required)
        user_id: The ID of the user creating the ticket (required)
        customer_name: Customer's name (optional)
        customer_phone: Customer's phone number (optional)
        email: Customer's email address (optional, may be auto-filled from context)
    
    Returns:
        Dictionary with result message.
    """
    from app.models.ticket import Ticket, TicketStatus
    from app.core.database import async_session_maker
    
    async with async_session_maker() as db:
        ticket = Ticket(
            user_id=user_id,
            content=content,
            description=description,
            customer_name=customer_name,
            customer_phone=customer_phone,
            email=email,
            status=TicketStatus.PENDING.value,
            time=datetime.utcnow()
        )
        
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
        
        return {
            "success": True,
            "message": f"✅ Support ticket created successfully with ID #{ticket.ticket_id}"
        }


@tool
async def track_ticket(ticket_id: int, user_id: int) -> dict:
    """
    Track the status and information of an existing ticket.
    
    Args:
        ticket_id: The ID of the ticket to track
        user_id: The ID of the user owning the ticket
    
    Returns:
        Dictionary with ticket info.
    """
    from sqlalchemy import select
    from app.models.ticket import Ticket
    from app.core.database import async_session_maker
    
    async with async_session_maker() as db:
        result = await db.execute(
            select(Ticket).where(
                Ticket.ticket_id == ticket_id,
                Ticket.user_id == user_id
            )
        )
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            return {"success": False, "message": f"❌ Ticket #{ticket_id} not found"}
        
        return {
            "success": True,
            "message": f"📋 Ticket #{ticket_id} information:\n"
                          f"• Content: {ticket.content}\n"
                          f"• Description: {ticket.description}\n"
                          f"• Status: {ticket.status}\n"
                          f"• Created: {ticket.time.strftime('%Y-%m-%d %H:%M')}"
        }


@tool(args_schema=TicketUpdateData)
async def update_ticket(
    ticket_id: int,
    user_id: int,
    content: Optional[str] = None,
    description: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    email: Optional[str] = None
) -> dict:
    """
    Update an existing ticket.
    
    Args:
        ticket_id: ID of the ticket to update (required)
        user_id: ID of the user (required)
        content: Updated content (optional)
        description: Updated description (optional)
        customer_name: Updated customer name (optional)
        customer_phone: Updated phone number (optional)
        email: Updated email (optional)
    
    Returns:
        Dictionary with result message.
    """
    from sqlalchemy import select
    from app.models.ticket import Ticket, TicketStatus
    from app.core.database import async_session_maker
    
    async with async_session_maker() as db:
        result = await db.execute(
            select(Ticket).where(
                Ticket.ticket_id == ticket_id,
                Ticket.user_id == user_id
            )
        )
        ticket = result.scalar_one_or_none()
        
        if not ticket:
            return {"success": False, "message": f"❌ Ticket #{ticket_id} not found"}
        
        if ticket.status in [TicketStatus.FINISHED.value, TicketStatus.CANCELED.value]:
            return {"success": False, "message": f"❌ Cannot update ticket with status {ticket.status}"}
        
        if content: ticket.content = content
        if description: ticket.description = description
        if customer_name: ticket.customer_name = customer_name
        if customer_phone: ticket.customer_phone = customer_phone
        if email: ticket.email = email
        
        await db.commit()
        
        return {
            "success": True,
            "message": f"✅ Ticket #{ticket_id} updated successfully"
        }
