"""Chat and session management endpoints."""
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.chat import ChatSession, Message
from app.services.chat_service import ChatService
from app.schemas.chat import (
    ChatRequest, ChatResponse, SessionCreate,
    SessionResponse, MessageResponse,
)
from app.api.deps import get_current_user
from app.utils.helpers import safe_json_loads

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Send a message and get response from the multi-agent system."""
    try:
        if not hasattr(req.app.state, "graph"):
            raise ValueError("Graph not initialized")

        return await ChatService.process_message(
            db,
            request.session_id,
            current_user.id,
            current_user.email,
            request.message,
            req.app.state.graph,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreate = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Create a new chat session."""
    title = request.title if request else "New Chat"
    return await ChatService.create_session(db, current_user.id, title)


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all sessions for current user."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get session with all messages."""
    session = await ChatService.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = messages_result.scalars().all()

    return {
        "session_id": session.session_id,
        "title": session.title,
        "created_at": session.created_at.isoformat() + "Z",
        "updated_at": session.updated_at.isoformat() + "Z",
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "message_type": m.message_type,
                "metadata": safe_json_loads(m.metadata_json) if m.metadata_json else None,
                "created_at": m.created_at.isoformat() + "Z",
            }
            for m in messages
        ],
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Delete a chat session and all its messages."""
    session = await ChatService.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()
    return {"detail": "Session deleted"}
