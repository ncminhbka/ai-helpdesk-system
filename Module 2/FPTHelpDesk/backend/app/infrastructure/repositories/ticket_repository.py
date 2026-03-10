from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.enums import TicketStatus
from app.domain.entities.ticket_entity import TicketEntity
from app.domain.interfaces.ticket_repository import ITicketRepository
from app.infrastructure.database.models.ticket_model import Ticket


class TicketRepository(ITicketRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _to_entity(self, model: Ticket) -> TicketEntity:
        return TicketEntity(
            ticket_id=model.ticket_id,
            user_id=model.user_id,
            content=model.content,
            description=model.description,
            status=TicketStatus(model.status),
            customer_name=model.customer_name,
            customer_phone=model.customer_phone,
            email=model.email,
            time=model.time,
        )

    async def create(self, ticket: TicketEntity) -> TicketEntity:
        db_ticket = Ticket(
            user_id=ticket.user_id,
            content=ticket.content,
            description=ticket.description,
            status=ticket.status.value,
            customer_name=ticket.customer_name,
            customer_phone=ticket.customer_phone,
            email=ticket.email,
        )
        self.db.add(db_ticket)
        await self.db.commit()
        await self.db.refresh(db_ticket)
        return self._to_entity(db_ticket)

    async def get_by_id(self, ticket_id: int) -> Optional[TicketEntity]:
        result = await self.db.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_recent_by_user_id(self, user_id: int, limit: int = 10) -> List[TicketEntity]:
        result = await self.db.execute(
            select(Ticket)
            .where(Ticket.user_id == user_id)
            .order_by(Ticket.time.desc())
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def update(self, ticket: TicketEntity) -> TicketEntity:
        result = await self.db.execute(
            select(Ticket).where(Ticket.ticket_id == ticket.ticket_id)
        )
        db_ticket = result.scalar_one()
        db_ticket.content = ticket.content
        db_ticket.description = ticket.description
        db_ticket.status = ticket.status.value
        db_ticket.customer_name = ticket.customer_name
        db_ticket.customer_phone = ticket.customer_phone
        db_ticket.email = ticket.email
        await self.db.commit()
        await self.db.refresh(db_ticket)
        return self._to_entity(db_ticket)
