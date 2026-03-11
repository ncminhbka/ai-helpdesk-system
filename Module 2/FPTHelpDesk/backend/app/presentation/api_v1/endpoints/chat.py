"""Chat and session management endpoints."""
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException

from app.application.dtos.chat_dto import (
    ChatRequest, ChatResponse, SessionCreate, SessionResponse, MessageResponse,
)
from app.application.use_cases.chat_use_case import ChatUseCase
from app.domain.entities.user_entity import UserEntity
from app.domain.interfaces.graph_runner import IGraphRunner
from app.presentation.dependencies import get_chat_use_case, get_current_user, get_graph_runner

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ChatUseCase = Depends(get_chat_use_case),
    runner: IGraphRunner = Depends(get_graph_runner),
) -> Any:
    """Send a message and get response from the multi-agent system."""
    try:
        return await use_case.process_message(
            session_id=request.session_id,
            user_id=current_user.id,
            user_email=current_user.email,
            message=request.message,
            runner=runner,
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@router.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreate = None,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ChatUseCase = Depends(get_chat_use_case),
) -> Any:
    """Create a new chat session."""
    title = request.title if request else "New Chat"
    entity = await use_case.create_session(current_user.id, title)
    return SessionResponse(
        session_id=entity.session_id,
        title=entity.title,
        created_at=entity.created_at,
        updated_at=entity.updated_at,
    )


@router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    current_user: UserEntity = Depends(get_current_user),
    use_case: ChatUseCase = Depends(get_chat_use_case),
) -> Any:
    """List all sessions for current user."""
    entities = await use_case.list_session_by_user_id(current_user.id)
    return [
        SessionResponse(
            session_id=e.session_id,
            title=e.title,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        for e in entities
    ]


@router.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ChatUseCase = Depends(get_chat_use_case),
) -> Any:
    """Get session with all messages."""
    session = await use_case.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = await use_case.get_messages(session_id)

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
                "metadata": m.metadata,
                "created_at": m.created_at.isoformat() + "Z",
            }
            for m in messages
        ],
    }


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: UserEntity = Depends(get_current_user),
    use_case: ChatUseCase = Depends(get_chat_use_case),
) -> Any:
    """Delete a chat session and all its messages."""
    session = await use_case.get_session(session_id, current_user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await use_case.delete_session(session_id)
    return {"detail": "Session deleted"}
