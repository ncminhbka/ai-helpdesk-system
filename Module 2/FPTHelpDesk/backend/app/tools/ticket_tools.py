"""
Ticket tools for the Ticket Agent.
Handles support ticket creation, tracking, and updating.
Uses dynamic interrupt() for HITL confirmation on sensitive operations.
"""
from langchain_core.tools import tool
from sqlalchemy import select
from langgraph.types import interrupt

from app.core.database import async_session_maker
from app.core.config import settings
from app.models.ticket import Ticket, TicketStatus


# ==================== HITL HELPERS ====================

_HIDDEN_FIELDS = {"user_id", "session_id"}

_FIELD_LABELS = {
    "content": "Nội dung", "description": "Mô tả",
    "customer_name": "Tên KH", "customer_phone": "SĐT",
    "email": "Email", "ticket_id": "Mã ticket", "status": "Trạng thái",
}

_ACTION_LABELS = {
    "create_ticket": "Tạo ticket hỗ trợ",
    "update_ticket": "Cập nhật ticket",
}


def _hitl_gate(tool_name: str, args: dict) -> dict | None:
    """
    HITL gate using dynamic interrupt().
    Returns the (possibly edited) args if approved, or None if rejected.
    Only activates when ENABLE_HITL is True.
    """
    if not settings.ENABLE_HITL:
        return args

    visible_args = {
        k: v for k, v in args.items()
        if k not in _HIDDEN_FIELDS and v is not None
    }

    response = interrupt({
        "action": tool_name,
        "display_name": _ACTION_LABELS.get(tool_name, tool_name),
        "args": visible_args,
        "field_labels": {k: v for k, v in _FIELD_LABELS.items() if k in visible_args},
    })

    if isinstance(response, dict) and response.get("action") == "approve":
        edits = response.get("edits", {})
        merged = {**args}
        for key, value in edits.items():
            if key in merged and value is not None and str(value).strip():
                merged[key] = value
        return merged

    return None


# ==================== TOOLS ====================

@tool
async def create_ticket(
    content: str,
    description: str,
    customer_name: str = None,
    customer_phone: str = None,
    email: str = None,
    user_id: int = None,
) -> str:
    """
    Create a new support ticket.

    Args:
        content: Brief description / title of the issue
        description: Detailed description of the issue
        customer_name: Customer's name (optional)
        customer_phone: Customer's phone number (optional)
        email: Customer's email (optional)
        user_id: User ID from context (injected automatically)
    """
    # HITL gate
    args = _hitl_gate("create_ticket", {
        "content": content, "description": description,
        "customer_name": customer_name, "customer_phone": customer_phone,
        "email": email, "user_id": user_id,
    })
    if args is None:
        return "❌ Người dùng đã hủy thao tác tạo ticket."

    # Unpack (possibly edited) args
    content = args["content"]
    description = args["description"]
    customer_name = args.get("customer_name")
    customer_phone = args.get("customer_phone")
    email = args.get("email")
    user_id = args.get("user_id")

    async with async_session_maker() as session:
        ticket = Ticket(
            user_id=user_id or 0,
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
    user_id: int = None,
) -> str:
    """
    Track ticket status. Provide ticket_id for specific ticket,
    or leave empty to see all tickets for the current user.

    Args:
        ticket_id: Specific ticket ID to track (optional)
        user_id: User ID from context (injected automatically)
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
            result = await session.execute(
                select(Ticket)
                .where(Ticket.user_id == (user_id or 0))
                .order_by(Ticket.time.desc())
                .limit(10)
            )
            tickets = result.scalars().all()
            if not tickets:
                return "📋 No tickets found."
            return "\n\n---\n\n".join(_format_ticket(t) for t in tickets)


@tool
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
    # HITL gate
    args = _hitl_gate("update_ticket", {
        "ticket_id": ticket_id, "content": content, "description": description,
        "status": status, "customer_name": customer_name,
        "customer_phone": customer_phone, "email": email,
    })
    if args is None:
        return "❌ Người dùng đã hủy thao tác cập nhật ticket."

    # Unpack (possibly edited) args
    ticket_id = args["ticket_id"]
    content = args.get("content")
    description = args.get("description")
    status = args.get("status")
    customer_name = args.get("customer_name")
    customer_phone = args.get("customer_phone")
    email = args.get("email")

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
        f"  👤 Name: {ticket.customer_name or 'N/A'}\n"
        f"  📞 Phone: {ticket.customer_phone or 'N/A'}\n"
        f"  📧 Email: {ticket.email or 'N/A'}\n"
        f"  🕒 Created: {time_str}\n"
        f"  📌 Status: {ticket.status}"
    )
