"""
FastAPI dependencies — full DI chain for all repos and use cases.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.auth_use_case import AuthUseCase
from app.application.use_cases.booking_use_case import BookingUseCase
from app.application.use_cases.chat_use_case import ChatUseCase
from app.application.use_cases.ticket_use_case import TicketUseCase
from app.application.use_cases.user_use_case import UserUseCase
from app.domain.entities.user_entity import UserEntity
from app.domain.interfaces.booking_repository import IBookingRepository
from app.domain.interfaces.chat_repository import IChatRepository
from app.domain.interfaces.ticket_repository import ITicketRepository
from app.domain.interfaces.user_repository import IUserRepository
from app.infrastructure.database.engine import get_db
from app.infrastructure.repositories.booking_repository import BookingRepository
from app.infrastructure.repositories.chat_repository import ChatRepository
from app.infrastructure.repositories.ticket_repository import TicketRepository
from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.security.jwt_bcrypt import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------------------------------
# Repository factories
# ---------------------------------------------------------------------------

def get_user_repository(db: AsyncSession = Depends(get_db)) -> IUserRepository:
    return UserRepository(db)


def get_ticket_repository(db: AsyncSession = Depends(get_db)) -> ITicketRepository:
    return TicketRepository(db)


def get_booking_repository(db: AsyncSession = Depends(get_db)) -> IBookingRepository:
    return BookingRepository(db)


def get_chat_repository(db: AsyncSession = Depends(get_db)) -> IChatRepository:
    return ChatRepository(db)


# ---------------------------------------------------------------------------
# Use case factories
# ---------------------------------------------------------------------------

def get_auth_use_case(
    repo: IUserRepository = Depends(get_user_repository),
) -> AuthUseCase:
    return AuthUseCase(repo)


def get_user_use_case(
    repo: IUserRepository = Depends(get_user_repository),
) -> UserUseCase:
    return UserUseCase(repo)


def get_ticket_use_case(
    repo: ITicketRepository = Depends(get_ticket_repository),
) -> TicketUseCase:
    return TicketUseCase(repo)


def get_booking_use_case(
    repo: IBookingRepository = Depends(get_booking_repository),
) -> BookingUseCase:
    return BookingUseCase(repo)


def get_chat_use_case(
    repo: IChatRepository = Depends(get_chat_repository),
) -> ChatUseCase:
    return ChatUseCase(repo)


# ---------------------------------------------------------------------------
# Authentication dependency
# ---------------------------------------------------------------------------

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: IUserRepository = Depends(get_user_repository),
) -> UserEntity:
    """Decode JWT and return the authenticated UserEntity."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    if payload is None:
        raise credentials_exception

    user_id_str: str = payload.get("sub")
    if user_id_str is None:
        raise credentials_exception

    try:
        user_id_int = int(user_id_str)
    except (ValueError, TypeError):
        raise credentials_exception

    user = await user_repo.get_by_id(user_id_int)
    if user is None:
        raise credentials_exception

    return user
