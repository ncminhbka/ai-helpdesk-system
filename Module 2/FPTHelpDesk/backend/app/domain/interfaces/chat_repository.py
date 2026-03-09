"""Abstract interface for chat session and message data access."""
from abc import ABC, abstractmethod
from typing import Optional, List, Any


class IChatRepository(ABC):
    @abstractmethod
    async def create_session(self, db, user_id: int, title: str) -> object: ...

    @abstractmethod
    async def get_session(self, db, session_id: str, user_id: int) -> Optional[object]: ...

    @abstractmethod
    async def list_session_by_user_id(self, db, user_id: int) -> List[object]: ...

    @abstractmethod
    async def save_message(
        self, db, session_id: str, role: str, content: str,
        message_type: str, metadata: dict
    ) -> object: ...

    @abstractmethod
    async def update_session_title(self, db, session_id: str, title: str) -> Optional[object]: ...

    @abstractmethod
    async def get_message_count(self, db, session_id: str) -> int: ...

    @abstractmethod
    async def get_messages(self, db, session_id: str) -> List[Any]: ...

    @abstractmethod
    async def delete_session(self, db, session: object) -> None: ...
