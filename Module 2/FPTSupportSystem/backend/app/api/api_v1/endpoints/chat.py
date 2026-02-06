
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.services.chat_service import ChatService
from app.schemas.chat import (
    ChatRequest, ChatResponse, SessionCreate, SessionResponse, 
    SessionUpdate, MessageResponse, ConfirmRequest
)
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    req: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Send a message and get response."""
    try:
        if not hasattr(req.app.state, "graph"):
            raise ValueError("Graph not initialized in app.state")

        return await ChatService.process_message(
            db, 
            request.session_id, 
            current_user.id, 
            current_user.email, 
            request.message,
            req.app.state.graph
        )
    except Exception as e:
        print(f"Endpoint Error: {e}")
        import traceback
        import os
        from datetime import datetime
        
        traceback.print_exc()
        
        log_path = os.path.join(os.path.dirname(__file__), "../../../error.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n--- ENDPOINT ERROR at {datetime.utcnow()} ---\n")
            f.write(f"Error: {str(e)}\n")
            f.write(traceback.format_exc())
            f.write("\n------------------------------\n")
            
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")

@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreate = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a new chat session."""
    title = request.title if request else "New Chat"
    session = await ChatService.create_session(db, current_user.id, title)
    return session

@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """List all sessions for current user."""
    from sqlalchemy import select
    from app.models.chat import ChatSession
    
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return sessions

@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get session with messages."""
    session = await ChatService.get_session(db, session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    from sqlalchemy import select
    from app.models.chat import Message
    from app.utils.helpers import safe_json_loads
    
    messages_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = messages_result.scalars().all()
    
    return {
        "session_id": session.session_id,
        "title": session.title,
        "created_at": session.created_at.isoformat(), # + "Z" dealt by validation maybe, or explicit
        "updated_at": session.updated_at.isoformat(),
        "messages": [
            {
                "role": m.role,
                "content": m.content,
                "message_type": m.message_type,
                "metadata": safe_json_loads(m.metadata_json) if m.metadata_json else None,
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
    }


