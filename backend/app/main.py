"""
FPT HelpDesk Backend - FastAPI Application Entry Point.

Initializes database, compiles LangGraph, and serves the API.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import init_db
from app.agents.graph import create_graph
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

    # Build and compile the multi-agent graph
    graph = create_graph()
    app.state.graph = graph
    print(f"✅ LangGraph compiled (HITL: {'enabled' if settings.ENABLE_HITL else 'disabled'})")

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
