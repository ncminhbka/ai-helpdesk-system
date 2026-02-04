"""
Ticket management tools for the Ticket Support Agent.
Supports HITL (Human-in-the-Loop) confirmation before database writes.
"""
from datetime import datetime
from typing import Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field


class TicketData(BaseModel):
    """Schema for ticket data."""
    content: str = Field(description="Brief description of the issue")
    description: str = Field(description="Detailed description of the issue")
    customer_name: Optional[str] = Field(default=None, description="Customer's name")
    customer_phone: Optional[str] = Field(default=None, description="Customer's phone number")
    email: Optional[str] = Field(default=None, description="Customer's email address")


class TicketUpdateData(BaseModel):
    """Schema for ticket update data."""
    ticket_id: int = Field(description="ID of the ticket to update")
    content: Optional[str] = Field(default=None, description="Updated content")
    description: Optional[str] = Field(default=None, description="Updated description")
    customer_name: Optional[str] = Field(default=None, description="Updated customer name")
    customer_phone: Optional[str] = Field(default=None, description="Updated phone number")
    email: Optional[str] = Field(default=None, description="Updated email")


@tool
def create_ticket(
    content: str,
    description: str,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    email: Optional[str] = None
) -> dict:
    """
    Prepare a new support ticket for creation.
    This returns data for user confirmation before actual database write.
    
    Args:
        content: Brief description of the issue (required)
        description: Detailed description of the issue (required)
        customer_name: Customer's name (optional)
        customer_phone: Customer's phone number (optional)
        email: Customer's email address (optional, may be auto-filled from context)
    
    Returns:
        Dictionary with confirmation data
    """
    return {
        "requires_confirmation": True,
        "action": "create_ticket",
        "data": {
            "content": content,
            "description": description,
            "customer_name": customer_name or "",
            "customer_phone": customer_phone or "",
            "email": email or "",
        },
        "message_vi": "Vui lòng xác nhận thông tin ticket hỗ trợ:",
        "message_en": "Please confirm support ticket information:",
        "fields": [
            {"name": "content", "label": "Nội dung / Content", "type": "text", "required": True},
            {"name": "description", "label": "Mô tả chi tiết / Description", "type": "textarea", "required": True},
            {"name": "customer_name", "label": "Họ tên / Name", "type": "text", "required": False},
            {"name": "customer_phone", "label": "Số điện thoại / Phone", "type": "tel", "required": False},
            {"name": "email", "label": "Email", "type": "email", "required": False},
        ]
    }


@tool
def track_ticket(ticket_id: int) -> dict:
    """
    Track the status and information of an existing ticket.
    This is a read-only operation, no confirmation needed.
    
    Args:
        ticket_id: The ID of the ticket to track
    
    Returns:
        Dictionary indicating this is a query action
    """
    return {
        "requires_confirmation": False,
        "action": "track_ticket",
        "data": {
            "ticket_id": ticket_id
        }
    }


@tool
def update_ticket(
    ticket_id: int,
    content: Optional[str] = None,
    description: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    email: Optional[str] = None
) -> dict:
    """
    Prepare ticket update for confirmation.
    Only provided fields will be updated.
    
    Args:
        ticket_id: ID of the ticket to update (required)
        content: Updated content (optional)
        description: Updated description (optional)
        customer_name: Updated customer name (optional)
        customer_phone: Updated phone number (optional)
        email: Updated email (optional)
    
    Returns:
        Dictionary with confirmation data
    """
    # Build update data with only provided fields
    update_data = {"ticket_id": ticket_id}
    fields = []
    
    if content is not None:
        update_data["content"] = content
        fields.append({"name": "content", "label": "Nội dung / Content", "type": "text"})
    
    if description is not None:
        update_data["description"] = description
        fields.append({"name": "description", "label": "Mô tả / Description", "type": "textarea"})
    
    if customer_name is not None:
        update_data["customer_name"] = customer_name
        fields.append({"name": "customer_name", "label": "Họ tên / Name", "type": "text"})
    
    if customer_phone is not None:
        update_data["customer_phone"] = customer_phone
        fields.append({"name": "customer_phone", "label": "Số điện thoại / Phone", "type": "tel"})
    
    if email is not None:
        update_data["email"] = email
        fields.append({"name": "email", "label": "Email", "type": "email"})
    
    return {
        "requires_confirmation": True,
        "action": "update_ticket",
        "data": update_data,
        "message_vi": f"Vui lòng xác nhận cập nhật ticket #{ticket_id}:",
        "message_en": f"Please confirm update for ticket #{ticket_id}:",
        "fields": fields
    }


# ==================== ACTUAL DATABASE OPERATIONS ====================
# These are called AFTER user confirmation

async def execute_create_ticket(db_session, user_id: int, data: dict) -> dict:
    """Execute ticket creation after user confirmation."""
    from database import Ticket, TicketStatus
    
    ticket = Ticket(
        user_id=user_id,
        content=data["content"],
        description=data.get("description", ""),
        customer_name=data.get("customer_name"),
        customer_phone=data.get("customer_phone"),
        email=data.get("email"),
        status=TicketStatus.PENDING.value,
        time=datetime.utcnow()
    )
    
    db_session.add(ticket)
    await db_session.commit()
    await db_session.refresh(ticket)
    
    return {
        "success": True,
        "ticket_id": ticket.ticket_id,
        "message_vi": f"✅ Đã tạo ticket hỗ trợ thành công với mã #{ticket.ticket_id}",
        "message_en": f"✅ Support ticket created successfully with ID #{ticket.ticket_id}"
    }


async def execute_track_ticket(db_session, user_id: int, data: dict) -> dict:
    """Execute ticket tracking query."""
    from sqlalchemy import select
    from database import Ticket
    
    ticket_id = data["ticket_id"]
    
    result = await db_session.execute(
        select(Ticket).where(
            Ticket.ticket_id == ticket_id,
            Ticket.user_id == user_id
        )
    )
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        return {
            "success": False,
            "message_vi": f"❌ Không tìm thấy ticket #{ticket_id}",
            "message_en": f"❌ Ticket #{ticket_id} not found"
        }
    
    return {
        "success": True,
        "ticket": ticket.to_dict(),
        "message_vi": f"📋 Thông tin ticket #{ticket_id}:\n"
                      f"• Nội dung: {ticket.content}\n"
                      f"• Mô tả: {ticket.description}\n"
                      f"• Trạng thái: {ticket.status}\n"
                      f"• Thời gian tạo: {ticket.time.strftime('%d/%m/%Y %H:%M')}",
        "message_en": f"📋 Ticket #{ticket_id} information:\n"
                      f"• Content: {ticket.content}\n"
                      f"• Description: {ticket.description}\n"
                      f"• Status: {ticket.status}\n"
                      f"• Created: {ticket.time.strftime('%Y-%m-%d %H:%M')}"
    }


async def execute_update_ticket(db_session, user_id: int, data: dict) -> dict:
    """Execute ticket update after user confirmation."""
    from sqlalchemy import select
    from database import Ticket, TicketStatus
    
    ticket_id = data.pop("ticket_id")
    
    result = await db_session.execute(
        select(Ticket).where(
            Ticket.ticket_id == ticket_id,
            Ticket.user_id == user_id
        )
    )
    ticket = result.scalar_one_or_none()
    
    if not ticket:
        return {
            "success": False,
            "message_vi": f"❌ Không tìm thấy ticket #{ticket_id}",
            "message_en": f"❌ Ticket #{ticket_id} not found"
        }
    
    # Check if ticket can be updated
    if ticket.status in [TicketStatus.FINISHED.value, TicketStatus.CANCELED.value]:
        return {
            "success": False,
            "message_vi": f"❌ Không thể cập nhật ticket đã {ticket.status.lower()}",
            "message_en": f"❌ Cannot update ticket with status {ticket.status}"
        }
    
    # Update fields
    for key, value in data.items():
        if hasattr(ticket, key) and value is not None:
            setattr(ticket, key, value)
    
    await db_session.commit()
    
    return {
        "success": True,
        "ticket_id": ticket_id,
        "message_vi": f"✅ Đã cập nhật ticket #{ticket_id} thành công",
        "message_en": f"✅ Ticket #{ticket_id} updated successfully"
    }
