"""
Ticket tools for the Ticket Agent.
Handles support ticket creation, tracking, and updating.
"""
from typing import Annotated
from langchain_core.tools import tool
from langgraph.prebuilt import InjectedState
from sqlalchemy import select

from app.core.database import async_session_maker
from app.models.ticket import Ticket, TicketStatus
from app.utils.hitl import hitl_protected


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

    async with async_session_maker() as session:
        ticket = Ticket(
            user_id=user_id,
            content=content,
            description=description,
            customer_name=customer_name,
            customer_phone=customer_phone,
            email=email,
            status=TicketStatus.PENDING.value,
        )
        session.add(ticket)
        await session.commit()
        await session.refresh(ticket)

        return (
            f"✅ Ticket created successfully!\n"
            f"🎫 Ticket ID: {ticket.ticket_id}\n"
            f"📝 Content: {content}\n"
            f"📋 Description: {description}\n"
            f"👤 Name: {customer_name or 'N/A'}\n"
            f"📧 Email: {email or 'N/A'}\n"
            f"📌 Status: {ticket.status}"
        )


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
    async with async_session_maker() as session:
        if ticket_id:
            result = await session.execute(
                select(Ticket).where(Ticket.ticket_id == ticket_id)
            )
            ticket = result.scalar_one_or_none()
            if not ticket:
                return f"❌ Ticket #{ticket_id} not found."
            return _format_ticket(ticket)
        else:
            if not user_id:
                return "❌ Lỗi: Không thể xác định người dùng. Vui lòng đăng nhập lại."
            result = await session.execute(
                select(Ticket)
                .where(Ticket.user_id == user_id)
                .order_by(Ticket.time.desc())
                .limit(10)
            )
            tickets = result.scalars().all()
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
    async with async_session_maker() as session:
        result = await session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )
        ticket = result.scalar_one_or_none()

        if not ticket:
            return f"❌ Ticket #{ticket_id} not found."

        if ticket.status in [TicketStatus.FINISHED.value, TicketStatus.CANCELED.value]:
            return f"❌ Cannot update ticket #{ticket_id}: status is '{ticket.status}'."

        updates = []
        if content:
            ticket.content = content
            updates.append(f"Content → {content}")
        if description:
            ticket.description = description
            updates.append(f"Description → {description}")
        if status:
            valid_statuses = [s.value for s in TicketStatus]
            if status not in valid_statuses:
                return f"❌ Invalid status '{status}'. Valid: {', '.join(valid_statuses)}"
            ticket.status = status
            updates.append(f"Status → {status}")
        if customer_name:
            ticket.customer_name = customer_name
            updates.append(f"Name → {customer_name}")
        if customer_phone:
            ticket.customer_phone = customer_phone
            updates.append(f"Phone → {customer_phone}")
        if email:
            ticket.email = email
            updates.append(f"Email → {email}")

        if not updates:
            return "⚠️ No fields to update."

        await session.commit()
        return f"✅ Ticket #{ticket_id} updated:\n" + "\n".join(f"  • {u}" for u in updates)


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
