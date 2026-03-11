"""
JWT token creation/decoding and password hashing utilities.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from app.infrastructure.config.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # Tạo instance của class CryptContext để hash password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password) # So sánh password plain với hashed password


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password) # Hash password using bcrypt


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token with user id and email in payload.
        Kết quả của này là một chuỗi JWT token đã được mã hóa (Header.Payload.Signature), 
        chứa thông tin người dùng và thời gian hết hạn. Token này sẽ được trả về cho client 
        sau khi đăng nhập thành công, và client sẽ sử dụng token này để xác thực các yêu cầu 
        tiếp theo đến server.
    """
    to_encode = data.copy() # Tạo bản sao của data
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM) # Tạo JWT token


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token. Returns payload or None."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except Exception:
        return None
