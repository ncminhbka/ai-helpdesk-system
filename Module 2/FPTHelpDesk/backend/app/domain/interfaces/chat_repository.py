"""Abstract interface for chat session and message data access."""
from abc import ABC, abstractmethod
from typing import Optional, List

from app.domain.entities.chat_entity import ChatSessionEntity, MessageEntity


class IChatRepository(ABC):
    @abstractmethod
    async def create_session(self, user_id: int, title: str) -> ChatSessionEntity: ...

    @abstractmethod
    async def get_session(self, session_id: str, user_id: int) -> Optional[ChatSessionEntity]: ...

    @abstractmethod
    async def list_session_by_user_id(self, user_id: int) -> List[ChatSessionEntity]: ...

    @abstractmethod
    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_type: str = "message",
        metadata: Optional[dict] = None,
    ) -> MessageEntity: ...

    @abstractmethod
    async def update_session_title(self, session_id: str, title: str) -> None: ...

    @abstractmethod
    async def get_message_count(self, session_id: str) -> int: ...

    @abstractmethod
    async def get_messages(self, session_id: str) -> List[MessageEntity]: ...

    @abstractmethod
    async def delete_session(self, session_id: str) -> None: ...
