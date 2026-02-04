"""
JWT Authentication module for FPT Customer Support Chatbot.
"""
import os
import bcrypt
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, get_user_by_id, get_user_by_email, User

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ==================== SCHEMAS ====================

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== PASSWORD FUNCTIONS ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Hash a password."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


# ==================== TOKEN FUNCTIONS ====================

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"DEBUG decode_token: payload = {payload}")
        user_id = payload.get("sub")
        email: str = payload.get("email")
        
        if user_id is None:
            print("DEBUG decode_token: user_id is None")
            return None
        
        # Ensure user_id is int
        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            print(f"DEBUG decode_token: user_id conversion failed for {user_id}")
            return None
            
        return TokenData(user_id=user_id, email=email)
    except JWTError as e:
        print(f"DEBUG decode_token: JWTError = {e}")
        return None
    except Exception as e:
        print(f"DEBUG decode_token: Unexpected error = {e}")
        return None


# ==================== DEPENDENCIES ====================

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user.
    Raises HTTPException if authentication fails.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    print(f"DEBUG: Token received: {token[:50]}..." if token else "DEBUG: No token")
    
    token_data = decode_token(token)
    print(f"DEBUG: Token data: {token_data}")
    
    if token_data is None:
        print("DEBUG: Token decode failed")
        raise credentials_exception
    
    user = await get_user_by_id(db, token_data.user_id)
    print(f"DEBUG: User found: {user}")
    
    if user is None:
        print("DEBUG: User not found in DB")
        raise credentials_exception
    
    return user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Optional authentication dependency.
    Returns None if no token or invalid token.
    """
    if token is None:
        return None
    
    try:
        return await get_current_user(token, db)
    except HTTPException:
        return None


# ==================== AUTH FUNCTIONS ====================

async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = await get_user_by_email(db, email)
    
    if user is None:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user


def create_user_token(user: User) -> Token:
    """Create access token for a user."""
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email},  # sub must be string per JWT spec
        expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")
