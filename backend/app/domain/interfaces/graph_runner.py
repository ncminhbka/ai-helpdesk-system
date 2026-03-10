"""Graph runner interface — domain contract, no framework dependencies."""
from abc import ABC, abstractmethod


class IGraphRunner(ABC):
    @abstractmethod
    async def is_interrupted(self, session_id: str) -> bool:
        """Trả True nếu graph đang bị interrupt (chờ HITL xác nhận)."""
        ...

    @abstractmethod
    async def invoke(self, session_id: str, user_id: int, user_email: str, message: str) -> dict:
        """Chạy graph với message mới. Trả về raw result dict."""
        ...

    @abstractmethod
    async def resume(self, session_id: str, payload: dict) -> dict:
        """Resume graph sau HITL interrupt. Trả về raw result dict."""
        ...

    @abstractmethod
    def extract_response(self, result: dict) -> str:
        """Lấy nội dung text cuối cùng từ AI trong result dict."""
        ...
