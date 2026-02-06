
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


async def get_db():
    """Dependency for getting database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    """Initialize database tables."""
    from app.models.base import Base
    # Ensure all models are imported so they are registered with Base
    # import app.models explicitly if needed, but imported in main usually works if side-effect
    # safe to import here
    from app.models import user, chat, ticket, booking
    
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Optional: Reset DB
        await conn.run_sync(Base.metadata.create_all)
