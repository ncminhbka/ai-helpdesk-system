"""Token service interface — domain contract, no framework dependencies."""
from abc import ABC, abstractmethod


class ITokenService(ABC):
    @abstractmethod
    def create_token(self, user_id: int, email: str) -> str: ...
