import uuid
from datetime import datetime, timezone
from typing import Optional, List, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat import ChatSession, Message
from app.utils.helpers import truncate_text, safe_json_dumps

class ChatRepository:
    @staticmethod
    async def create_session(
        db: AsyncSession, user_id: int, title: str = "New Chat"
    ) -> ChatSession:
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_session(
        db: AsyncSession, session_id: str, user_id: int
    ) -> Optional[ChatSession]:
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
    @staticmethod
    async def list_session_by_user_id(db: AsyncSession, user_id: int) -> List[ChatSession]:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
        )
        return result.scalars().all()
    @staticmethod
    async def list_sessions(db: AsyncSession, user_id: int) -> List[ChatSession]:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def save_message(
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str,
        message_type: str = "message",
        metadata: dict = None,
    ) -> Message:
        msg = Message(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            metadata_json=safe_json_dumps(metadata) if metadata else None,
        )
        db.add(msg)
        await db.commit()
        return msg

    @staticmethod
    async def update_session_title(
        db: AsyncSession, session_id: str, title: str
    ) -> Optional[ChatSession]:
        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.title = truncate_text(title, 50)
            session.updated_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(session)
        return session

    @staticmethod
    async def get_message_count(db: AsyncSession, session_id: str) -> int:
        result = await db.execute(
            select(Message).where(Message.session_id == session_id)
        )
        return len(result.scalars().all())

    @staticmethod
    async def get_messages(db: AsyncSession, session_id: str) -> List[Message]:
        """Fetch all messages in a session ordered by creation time."""
        result = await db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at)
        )
        return result.scalars().all()

    @staticmethod
    async def delete_session(db: AsyncSession, session: ChatSession):
        """Delete a chat session."""
        await db.delete(session)
        await db.commit()
