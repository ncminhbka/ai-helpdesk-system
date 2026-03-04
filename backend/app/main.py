"""
FPT HelpDesk Backend - FastAPI Application Entry Point.

Initializes database, compiles LangGraph, and serves the API.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.agents.shared.graph import create_graph
from app.api.api_v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle:
    - Startup: Initialize database tables + compile LangGraph
    - Shutdown: Cleanup
    """
    print(f"🚀 Starting {settings.PROJECT_NAME}...")

    # Initialize database
    await init_db()
    print("✅ Database initialized")

    # Build and compile the multi-agent graph with persistent PostgreSQL checkpointer
    from psycopg_pool import AsyncConnectionPool
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    # Connect to PostgreSQL pool for checkpointing
    async with AsyncConnectionPool(
        conninfo=settings.CHECKPOINT_POSTGRES_URL,
        max_size=10,
        kwargs={"autocommit": True, "prepare_threshold": 0},
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)
        
        # Initialize checkpointer tables (run once)
        await checkpointer.setup()
        
        graph = create_graph(checkpointer=checkpointer)
        app.state.graph = graph
        print(f"✅ LangGraph compiled with persistent PostgreSQL checkpointer (HITL: {'enabled' if settings.ENABLE_HITL else 'disabled'})")
        
        yield

    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {"status": "ok", "project": settings.PROJECT_NAME}
