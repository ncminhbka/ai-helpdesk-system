
import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from app.core.config import settings
from app.core.database import init_db
from app.api.api_v1.api import api_router
from app.agents.graph import create_graph

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    
    # Initialize Graph with Checkpointer
    # Use MemorySaver for stability testing
    from langgraph.checkpoint.memory import MemorySaver
    checkpointer = MemorySaver()
    
    builder = create_graph()
    app.state.graph = builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["booking_sensitive_tools", "ticket_sensitive_tools"]
    )
    yield
    # Shutdown
    # Checkpointer context exiting will handle cleanup
    pass

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"message": "Welcome to FPT Support System API"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
