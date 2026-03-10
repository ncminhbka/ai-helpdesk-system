"""Password hashing interface — domain contract, no framework dependencies."""
from abc import ABC, abstractmethod


class IPasswordHasher(ABC):
    @abstractmethod
    def hash(self, plain_password: str) -> str: ... # ko cần biết dùng thuật toán gì, chỉ cần hash và verify là đủ, thuật toán có thể thay đổi sau này mà ko ảnh hưởng đến các phần khác của ứng dụng.

    @abstractmethod
    def verify(self, plain_password: str, hashed_password: str) -> bool: ...
