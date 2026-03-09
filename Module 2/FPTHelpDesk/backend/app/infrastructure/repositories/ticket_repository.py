from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models.ticket_model import Ticket
from app.domain.entities.enums import TicketStatus
from app.domain.interfaces.ticket_repository import ITicketRepository


class TicketRepository(ITicketRepository):

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        content: str,
        description: str,
        customer_name: Optional[str],
        customer_phone: Optional[str],
        email: Optional[str],
    ) -> Ticket:
        ticket = Ticket(
            user_id=user_id,
            content=content,
            description=description,
            customer_name=customer_name,
            customer_phone=customer_phone,
            email=email,
            status=TicketStatus.PENDING.value,
        )
        db.add(ticket)
        await db.commit()
        await db.refresh(ticket)
        return ticket

    @staticmethod
    async def get_by_id(db: AsyncSession, ticket_id: int) -> Optional[Ticket]:
        result = await db.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_recent_by_user_id(db: AsyncSession, user_id: int, limit: int = 10) -> List[Ticket]:
        result = await db.execute(
            select(Ticket)
            .where(Ticket.user_id == user_id)
            .order_by(Ticket.time.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def update(db: AsyncSession, ticket: Ticket) -> Ticket:
        await db.commit()
        await db.refresh(ticket)
        return ticket
