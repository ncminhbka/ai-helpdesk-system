"""
FastAPI main application for FPT Customer Support Chatbot.
Provides REST API endpoints for chat, authentication, sessions, and dashboard.
"""
import os
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import (
    init_db, get_db, async_session_maker,
    User, ChatSession, Message, Ticket, Booking, PendingAction,
    create_user, get_user_by_email
)
from auth import (
    get_current_user, get_password_hash, verify_password,
    create_user_token, Token, UserCreate, UserLogin, UserResponse
)
from graph import get_simple_graph
from tools import ACTION_EXECUTORS
from utils.helpers import safe_json_loads, safe_json_dumps

from dotenv import load_dotenv
load_dotenv()

# ==================== APP INITIALIZATION ====================

app = FastAPI(
    title="FPT Customer Support Chatbot API",
    description="Multi-agent chatbot for FPT customer support",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize graph
graph = None


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    global graph
    await init_db()
    graph = get_simple_graph()
    print("✅ Application started successfully")


# ==================== REQUEST/RESPONSE SCHEMAS ====================

class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    type: str  # 'message', 'confirm', 'error'
    content: Optional[str] = None
    action_id: Optional[str] = None
    action: Optional[str] = None
    data: Optional[dict] = None
    fields: Optional[list] = None


class ConfirmRequest(BaseModel):
    edits: Optional[dict] = None


class SessionCreate(BaseModel):
    title: Optional[str] = "New Chat"


class SessionUpdate(BaseModel):
    title: str


class SessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    role: str
    content: str
    message_type: str
    created_at: str


class TicketResponse(BaseModel):
    ticket_id: int
    content: str
    description: Optional[str]
    customer_name: Optional[str]
    customer_phone: Optional[str]
    email: Optional[str]
    time: str
    status: str


class BookingResponse(BaseModel):
    booking_id: int
    customer_name: Optional[str]
    customer_phone: Optional[str]
    email: Optional[str]
    reason: str
    time: str
    note: Optional[str]
    status: str


# ==================== AUTH ENDPOINTS ====================

@app.post("/auth/register", response_model=Token)
async def register(request: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if email exists
    existing = await get_user_by_email(db, request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user = await create_user(
        db,
        email=request.email,
        password_hash=get_password_hash(request.password),
        name=request.name
    )
    
    # Generate token
    return create_user_token(user)


@app.post("/auth/login", response_model=Token)
async def login(request: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and get access token."""
    user = await get_user_by_email(db, request.email)
    
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    return create_user_token(user)


@app.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        created_at=current_user.created_at
    )


# ==================== SESSION ENDPOINTS ====================

@app.post("/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreate = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session."""
    session = ChatSession(
        session_id=str(uuid.uuid4()),
        user_id=current_user.id,
        title=request.title if request else "New Chat"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return SessionResponse(
        session_id=session.session_id,
        title=session.title,
        created_at=session.created_at.isoformat() + "Z",
        updated_at=session.updated_at.isoformat() + "Z"
    )


@app.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all sessions for current user."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    
    return [
        SessionResponse(
            session_id=s.session_id,
            title=s.title,
            created_at=s.created_at.isoformat() + "Z",
            updated_at=s.updated_at.isoformat() + "Z"
        )
        for s in sessions
    ]


@app.get("/sessions/{session_id}")
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get session with messages."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.session_id == session_id)
        .where(ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get messages
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
                "created_at": m.created_at.isoformat() + "Z"
            }
            for m in messages
        ]
    }


@app.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.session_id == session_id)
        .where(ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    await db.delete(session)
    await db.commit()
    
    return {"message": "Session deleted"}


@app.patch("/sessions/{session_id}")
async def update_session(
    session_id: str,
    request: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update session title."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.session_id == session_id)
        .where(ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session.title = request.title
    await db.commit()
    
    return {"message": "Session updated"}


# ==================== CHAT ENDPOINTS ====================

@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Send a message and get response."""
    global graph
    
    # Verify session belongs to user
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.session_id == request.session_id)
        .where(ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Save user message
    user_msg = Message(
        session_id=request.session_id,
        role="user",
        content=request.message,
        message_type="message"
    )
    db.add(user_msg)
    
    # Check if this is the first message - update title
    messages_count = await db.execute(
        select(func.count()).select_from(Message).where(Message.session_id == request.session_id)
    )
    count = messages_count.scalar()
    
    if count <= 1 or session.title == "New Chat":
        # Generate title from first message
        title = request.message[:50] + ("..." if len(request.message) > 50 else "")
        session.title = title
    
    # Invoke graph
    try:
        from langchain_core.messages import HumanMessage, AIMessage
        
        # Load chat history from database for context
        history_result = await db.execute(
            select(Message)
            .where(Message.session_id == request.session_id)
            .order_by(Message.created_at)
            .limit(20)  # Keep last 20 messages for context
        )
        history_messages = history_result.scalars().all()
        
        # Convert DB messages to LangChain message format
        langchain_messages = []
        for msg in history_messages:
            if msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant" and msg.message_type != "confirm":
                langchain_messages.append(AIMessage(content=msg.content))
        
        # Add current user message
        langchain_messages.append(HumanMessage(content=request.message))
        
        result = await graph.ainvoke(
            {
                "messages": langchain_messages,
                "user_id": current_user.id,
                "user_email": current_user.email,
                "session_id": request.session_id,
                "language": "vi",
                "dialog_state": []
            },
            config={"configurable": {"thread_id": request.session_id}}
        )
        
        # Get the response
        last_agent_response = result.get("last_agent_response", {})
        pending = result.get("pending_confirmation")
        
        # Handle confirmation request
        if pending and pending.get("type") == "confirm":
            # Check if this is a query action (no confirmation needed, execute immediately)
            query_actions = {"track_ticket", "track_booking"}
            action_type = pending.get("action")
            
            if action_type in query_actions:
                # Execute query immediately without confirmation
                executor = ACTION_EXECUTORS.get(action_type)
                if executor:
                    try:
                        query_result = await executor(db, current_user.id, pending.get("data", {}))
                        response_text = query_result.get("message_vi", query_result.get("message_en", "Query completed."))
                        
                        # Save assistant message
                        assistant_msg = Message(
                            session_id=request.session_id,
                            role="assistant",
                            content=response_text,
                            message_type="message"
                        )
                        db.add(assistant_msg)
                        
                        session.updated_at = datetime.utcnow()
                        await db.commit()
                        
                        return ChatResponse(
                            type="message",
                            content=response_text
                        )
                    except Exception as e:
                        print(f"Query action error: {e}")
                        pass  # Fall through to normal response handling
            
            # This is a write action, needs confirmation
            # Save pending action
            action_id = str(uuid.uuid4())
            pending_action = PendingAction(
                action_id=action_id,
                user_id=current_user.id,
                session_id=request.session_id,
                action_type=pending["action"],
                data_json=safe_json_dumps(pending["data"]),
                expires_at=datetime.utcnow() + timedelta(minutes=5)
            )
            db.add(pending_action)
            
            # Save assistant message
            assistant_msg = Message(
                session_id=request.session_id,
                role="assistant",
                content=pending.get("message", "Please confirm."),
                message_type="confirm",
                metadata_json=safe_json_dumps({
                    "action_id": action_id,
                    "action": pending["action"],
                    "data": pending["data"],
                    "fields": pending.get("fields", [])
                })
            )
            db.add(assistant_msg)
            
            session.updated_at = datetime.utcnow()
            await db.commit()
            
            return ChatResponse(
                type="confirm",
                content=pending.get("message"),
                action_id=action_id,
                action=pending["action"],
                data=pending["data"],
                fields=pending.get("fields", [])
            )
        
        # Normal message response
        response_text = ""
        if result.get("messages"):
            # Get the last AI message
            for msg in reversed(result["messages"]):
                if hasattr(msg, 'content') and msg.content:
                    response_text = msg.content
                    break
        
        if not response_text:
            response_text = last_agent_response.get("response", "Xin lỗi, tôi không hiểu yêu cầu của bạn.")
        
        # Save assistant message
        assistant_msg = Message(
            session_id=request.session_id,
            role="assistant",
            content=response_text,
            message_type="message"
        )
        db.add(assistant_msg)
        
        session.updated_at = datetime.utcnow()
        await db.commit()
        
        return ChatResponse(
            type="message",
            content=response_text
        )
        
    except Exception as e:
        print(f"Chat error: {e}")
        import traceback
        traceback.print_exc()
        
        error_response = "Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại."
        
        # Save error message
        error_msg = Message(
            session_id=request.session_id,
            role="assistant",
            content=error_response,
            message_type="error"
        )
        db.add(error_msg)
        await db.commit()
        
        return ChatResponse(
            type="error",
            content=error_response
        )


@app.post("/confirm/{action_id}")
async def confirm_action(
    action_id: str,
    request: ConfirmRequest = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Confirm and execute a pending action."""
    # Get pending action
    result = await db.execute(
        select(PendingAction)
        .where(PendingAction.action_id == action_id)
        .where(PendingAction.user_id == current_user.id)
    )
    pending = result.scalar_one_or_none()
    
    if not pending:
        raise HTTPException(status_code=404, detail="Action not found or expired")
    
    # Check expiration
    if pending.expires_at < datetime.utcnow():
        await db.delete(pending)
        await db.commit()
        raise HTTPException(status_code=410, detail="Action expired")
    
    # Merge user edits with original data
    action_data = safe_json_loads(pending.data_json, {})
    if request and request.edits:
        action_data.update(request.edits)
    
    # Execute the action
    executor = ACTION_EXECUTORS.get(pending.action_type)
    if not executor:
        raise HTTPException(status_code=400, detail=f"Unknown action: {pending.action_type}")
    
    try:
        result = await executor(db, current_user.id, action_data)
        
        # Delete pending action
        await db.delete(pending)
        
        # Save confirmation result as message
        response_text = result.get("message_vi", result.get("message_en", "Action completed."))
        confirm_msg = Message(
            session_id=pending.session_id,
            role="assistant",
            content=response_text,
            message_type="message"
        )
        db.add(confirm_msg)
        
        await db.commit()
        
        return ChatResponse(
            type="message",
            content=response_text
        )
        
    except Exception as e:
        print(f"Action execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/cancel/{action_id}")
async def cancel_action(
    action_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel a pending action."""
    result = await db.execute(
        select(PendingAction)
        .where(PendingAction.action_id == action_id)
        .where(PendingAction.user_id == current_user.id)
    )
    pending = result.scalar_one_or_none()
    
    if pending:
        # Save cancellation message
        cancel_msg = Message(
            session_id=pending.session_id,
            role="assistant",
            content="Đã hủy thao tác. / Action cancelled.",
            message_type="message"
        )
        db.add(cancel_msg)
        
        await db.delete(pending)
        await db.commit()
    
    return {"message": "Action cancelled"}


# ==================== DASHBOARD ENDPOINTS ====================

@app.get("/tickets", response_model=List[TicketResponse])
async def list_tickets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all tickets for current user."""
    result = await db.execute(
        select(Ticket)
        .where(Ticket.user_id == current_user.id)
        .order_by(Ticket.time.desc())
    )
    tickets = result.scalars().all()
    
    return [
        TicketResponse(
            ticket_id=t.ticket_id,
            content=t.content,
            description=t.description,
            customer_name=t.customer_name,
            customer_phone=t.customer_phone,
            email=t.email,
            time=t.time.isoformat() + "Z" if t.time else None,
            status=t.status
        )
        for t in tickets
    ]


@app.get("/bookings", response_model=List[BookingResponse])
async def list_bookings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all bookings for current user."""
    result = await db.execute(
        select(Booking)
        .where(Booking.user_id == current_user.id)
        .order_by(Booking.time.desc())
    )
    bookings = result.scalars().all()
    
    return [
        BookingResponse(
            booking_id=b.booking_id,
            customer_name=b.customer_name,
            customer_phone=b.customer_phone,
            email=b.email,
            reason=b.reason,
            time=b.time.isoformat() + "Z" if b.time else None,
            note=b.note,
            status=b.status
        )
        for b in bookings
    ]


# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


# ==================== RUN SERVER ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
