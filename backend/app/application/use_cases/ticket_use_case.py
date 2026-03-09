from typing import List, Optional

from app.infrastructure.database.engine import async_session_maker
from app.infrastructure.database.models.ticket_model import Ticket
from app.domain.entities.enums import TicketStatus
from app.infrastructure.repositories.ticket_repository import TicketRepository


class TicketUseCase:

    @staticmethod
    async def create_ticket(
        user_id: int,
        content: str,
        description: str,
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> Ticket:
        async with async_session_maker() as session:
            ticket = await TicketRepository.create(
                db=session,
                user_id=user_id,
                content=content,
                description=description,
                customer_name=customer_name,
                customer_phone=customer_phone,
                email=email,
            )
            return ticket

    @staticmethod
    async def get_ticket_by_id(ticket_id: int) -> Optional[Ticket]:
        async with async_session_maker() as session:
            return await TicketRepository.get_by_id(session, ticket_id)

    @staticmethod
    async def get_recent_tickets_by_user(user_id: int, limit: int = 10) -> List[Ticket]:
        async with async_session_maker() as session:
            return await TicketRepository.get_recent_by_user_id(session, user_id, limit)

    @staticmethod
    async def update_ticket(
        ticket_id: int,
        content: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        customer_name: Optional[str] = None,
        customer_phone: Optional[str] = None,
        email: Optional[str] = None,
    ) -> tuple[bool, str, List[str]]:
        """Returns (success, message, list_of_updates)."""
        async with async_session_maker() as session:
            ticket = await TicketRepository.get_by_id(session, ticket_id)

            if not ticket:
                return False, f"❌ Ticket #{ticket_id} not found.", []

            if ticket.status in [TicketStatus.FINISHED.value, TicketStatus.CANCELED.value]:
                return False, f"❌ Cannot update ticket #{ticket_id}: status is '{ticket.status}'.", []

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
                    return False, f"❌ Invalid status '{status}'. Valid: {', '.join(valid_statuses)}", []
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
                return False, "⚠️ No fields to update.", []

            await TicketRepository.update(session, ticket)
            return True, f"✅ Ticket #{ticket_id} updated.", updates
