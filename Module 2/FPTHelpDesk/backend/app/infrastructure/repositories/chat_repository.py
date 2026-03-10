import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.utils.helpers import truncate_text, safe_json_dumps
from app.domain.entities.chat_entity import ChatSessionEntity, MessageEntity
from app.domain.interfaces.chat_repository import IChatRepository
from app.infrastructure.database.models.chat_model import ChatSession, Message


class ChatRepository(IChatRepository):
    def __init__(self, db: AsyncSession):
        self.db = db

    def _session_to_entity(self, model: ChatSession) -> ChatSessionEntity:
        return ChatSessionEntity(
            session_id=model.session_id,
            user_id=model.user_id,
            title=model.title,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _message_to_entity(self, model: Message) -> MessageEntity:
        metadata = None
        if model.metadata_json:
            try:
                metadata = json.loads(model.metadata_json)
            except (json.JSONDecodeError, TypeError):
                metadata = None
        return MessageEntity(
            id=model.id,
            session_id=model.session_id,
            role=model.role,
            content=model.content,
            message_type=model.message_type,
            metadata=metadata,
            created_at=model.created_at,
        )

    async def create_session(self, user_id: int, title: str = "New Chat") -> ChatSessionEntity:
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
        )
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return self._session_to_entity(session)

    async def get_session(self, session_id: str, user_id: int) -> Optional[ChatSessionEntity]:
        result = await self.db.execute(
            select(ChatSession).where(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user_id,
            )
        )
        model = result.scalar_one_or_none()
        return self._session_to_entity(model) if model else None

    async def list_session_by_user_id(self, user_id: int) -> List[ChatSessionEntity]:
        result = await self.db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
        )
        return [self._session_to_entity(m) for m in result.scalars().all()]

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_type: str = "message",
        metadata: Optional[dict] = None,
    ) -> MessageEntity:
        msg = Message(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            metadata_json=safe_json_dumps(metadata) if metadata else None,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return self._message_to_entity(msg)

    async def update_session_title(self, session_id: str, title: str) -> None:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.title = truncate_text(title, 50)
            session.updated_at = datetime.now(timezone.utc)
            await self.db.commit()

    async def get_message_count(self, session_id: str) -> int:
        result = await self.db.execute(
            select(Message).where(Message.session_id == session_id)
        )
        return len(result.scalars().all())

    async def get_messages(self, session_id: str) -> List[MessageEntity]:
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
        )
        return [self._message_to_entity(m) for m in result.scalars().all()]

    async def delete_session(self, session_id: str) -> None:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            await self.db.delete(session)
            await self.db.commit()
