"""
Ticket tools for the Ticket Agent.
Handles support ticket creation, tracking, and updating.
"""
from typing import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState

from app.infrastructure.database.models.ticket_model import Ticket
from app.application.use_cases.ticket_use_case import TicketUseCase
from app.infrastructure.hitl.decorator import hitl_protected


# ==================== TOOLS ====================

@tool
@hitl_protected(display_name="Tạo ticket hỗ trợ", cancel_message="❌ Người dùng đã hủy thao tác tạo ticket.")
async def create_ticket(
    content: str,
    description: str,
    customer_name: str = None,
    customer_phone: str = None,
    email: str = None,
    user_id: Annotated[int, InjectedState("user_id")] = None,
) -> str:
    """
    Create a new support ticket.

    Args:
        content: Brief description / title of the issue
        description: Detailed description of the issue
        customer_name: Customer's name (optional)
        customer_phone: Customer's phone number (optional)
        email: Customer's email (optional)
    """
    if not user_id:
        return "❌ Lỗi: Không thể xác định người dùng. Vui lòng đăng nhập lại."

    try:
        ticket = await TicketUseCase.create_ticket(
            user_id=user_id,
            content=content,
            description=description,
            customer_name=customer_name,
            customer_phone=customer_phone,
            email=email,
        )

        return (
            f"✅ Ticket created successfully!\n"
            f"🎫 Ticket ID: {ticket.ticket_id}\n"
            f"📝 Content: {content}\n"
            f"📋 Description: {description}\n"
            f"👤 Name: {customer_name or 'N/A'}\n"
            f"📧 Email: {email or 'N/A'}\n"
            f"📌 Status: {ticket.status}"
        )
    except Exception as e:
        return f"❌ Error: {str(e)}"


@tool
async def track_ticket(
    ticket_id: int = None,
    user_id: Annotated[int, InjectedState("user_id")] = None,
) -> str:
    """
    Track ticket status. Provide ticket_id for a specific ticket,
    or leave empty to see all tickets for the current user.

    Args:
        ticket_id: Specific ticket ID to track (optional)
    """
    if ticket_id:
        ticket = await TicketUseCase.get_ticket_by_id(ticket_id)
        if not ticket:
            return f"❌ Ticket #{ticket_id} not found."
        return _format_ticket(ticket)
    else:
        if not user_id:
            return "❌ Lỗi: Không thể xác định người dùng. Vui lòng đăng nhập lại."
        tickets = await TicketUseCase.get_recent_tickets_by_user(user_id)
        if not tickets:
            return "📋 No tickets found."
        return "\n\n---\n\n".join(_format_ticket(t) for t in tickets)


@tool
@hitl_protected(display_name="Cập nhật ticket", cancel_message="❌ Người dùng đã hủy thao tác cập nhật ticket.")
async def update_ticket(
    ticket_id: int,
    content: str = None,
    description: str = None,
    status: str = None,
    customer_name: str = None,
    customer_phone: str = None,
    email: str = None,
) -> str:
    """
    Update an existing support ticket. Only non-Finished and non-Canceled tickets can be updated.

    Args:
        ticket_id: ID of the ticket to update
        content: Updated content/title (optional)
        description: Updated description (optional)
        status: Updated status - Pending, Resolving, Canceled, Finished (optional)
        customer_name: Updated customer name (optional)
        customer_phone: Updated phone (optional)
        email: Updated email (optional)
    """
    success, message, updates = await TicketUseCase.update_ticket(
        ticket_id=ticket_id,
        content=content,
        description=description,
        status=status,
        customer_name=customer_name,
        customer_phone=customer_phone,
        email=email,
    )

    if not success:
        return message

    return f"{message}\n" + "\n".join(f"  • {u}" for u in updates)


def _format_ticket(ticket: Ticket) -> str:
    """Format a ticket for display."""
    time_str = ticket.time.strftime("%Y-%m-%d %H:%M") if ticket.time else "N/A"
    return (
        f"🎫 Ticket #{ticket.ticket_id}\n"
        f"  📝 Content: {ticket.content}\n"
        f"  📋 Description: {ticket.description or 'N/A'}\n"
        f"  🕒 Created: {time_str}\n"
        f"  👤 Name: {ticket.customer_name or 'N/A'}\n"
        f"  📞 Phone: {ticket.customer_phone or 'N/A'}\n"
        f"  📧 Email: {ticket.email or 'N/A'}\n"
        f"  📌 Status: {ticket.status}"
    )
