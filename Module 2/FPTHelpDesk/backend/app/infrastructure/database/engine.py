"""
Async SQLAlchemy database engine, session factory, and initialization.
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.infrastructure.config.settings import settings # Import settings từ config.py

# Async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Session factory, every file need to use database must import this to create session
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db(): # hàm này sẽ được truyền vào Depends()
    """FastAPI dependency for database sessions."""
    async with async_session_maker() as session: # mượn 1 session từ pool
        try:
            yield session # tạm dừng thực thi, đưa session cho router
        finally:
            await session.close() # khi api chạy xong, quay lại đóng session


async def init_db():
    """Create all database tables."""
    from app.infrastructure.database.base import Base
    # Import all models to register them with Base.metadata
    from app.infrastructure.database.models import user_model, chat_model, ticket_model, booking_model  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
