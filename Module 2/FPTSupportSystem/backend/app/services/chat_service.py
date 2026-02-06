
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
import uuid
import json

from app.models.chat import ChatSession, Message
from app.models.action import PendingAction
from app.schemas.chat import ChatResponse


class ChatService:
    @staticmethod
    async def create_session(db: AsyncSession, user_id: int, title: str = "New Chat") -> ChatSession:
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_session(db: AsyncSession, session_id: str, user_id: int) -> Optional[ChatSession]:
        result = await db.execute(
            select(ChatSession)
            .where(ChatSession.session_id == session_id)
            .where(ChatSession.user_id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def process_message(
        db: AsyncSession, 
        session_id: str, 
        user_id: int, 
        user_email: str, 
        message: str,
        graph: Any
    ) -> ChatResponse:
        import random
        run_id = random.randint(1000, 9999)
        print(f"[{run_id}] DEBUG: ChatService.process_message called", flush=True)
        print(f"[{run_id}] DEBUG: Params: session_id={session_id}, user_id={user_id}, msg={message}", flush=True)
        print(f"[{run_id}] DEBUG: Graph object: {type(graph)}", flush=True)
        
        try:
            # Get session
            session = await ChatService.get_session(db, session_id, user_id)
            if not session:
                print(f"[{run_id}] DEBUG: Session not found", flush=True)
                raise ValueError("Session not found")
            
            # Save user message
            user_msg = Message(
                session_id=session_id,
                role="user",
                content=message,
                message_type="message"
            )
            db.add(user_msg)
            
            # Update title if first message
            messages_count = await db.execute(
                select(func.count()).select_from(Message).where(Message.session_id == session_id)
            )
            if messages_count.scalar() <= 1 or session.title == "New Chat":
                session.title = message[:50] + ("..." if len(message) > 50 else "")
                
            # Prepare LangChain messages
            from langchain_core.messages import HumanMessage, ToolMessage
            
            config = {"configurable": {"thread_id": session_id}}
            
            # Check current state for interrupts
            print(f"[{run_id}] DEBUG: Checking graph state...", flush=True)
            snapshot = await graph.aget_state(config)
            print(f"[{run_id}] DEBUG: Snapshot next: {snapshot.next}", flush=True)
            
            response_text = ""
            
            try:
                # If graph is paused (next steps exist), handle HITL
                if snapshot.next:
                    print(f"[{run_id}] DEBUG: Graph is paused. Handling input...", flush=True) 
                    # Simple logic: "yes" | "confirm" -> approve, else -> deny
                    clean_msg = message.strip().lower()
                    if clean_msg in ["yes", "confirm", "ok", "đồng ý", "xác nhận"]:
                        # Approve: Resume with None
                        print(f"Resuming graph for session {session_id} (Approved)")
                        result = await graph.ainvoke(None, config)
                    else:
                        # Deny: Resume with ToolMessage rejecting the call
                        # We need the tool_call_id from the last message
                        last_msg = snapshot.values["messages"][-1]
                        if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                            tool_call_id = last_msg.tool_calls[0]["id"]
                            tool_msg = ToolMessage(
                                tool_call_id=tool_call_id,
                                content=f"API call denied by user. Reasoning: '{message}'. Continue assisting, accounting for the user's input.",
                            )
                            print(f"Resuming graph for session {session_id} (Denied: {message})")
                            result = await graph.ainvoke({"messages": [tool_msg]}, config)
                        else:
                            # Should not happen if paused on tool, but fallback
                            result = await graph.ainvoke({"messages": [HumanMessage(content=message)]}, config)
                else:
                    # Normal interaction
                    result = await graph.ainvoke(
                        {
                            "messages": [HumanMessage(content=message)],
                            "user_id": user_id,
                            "user_email": user_email,
                            "session_id": session_id,
                            "language": "vi",
                            "dialog_state": []
                        },
                        config
                    )
                
                # Check if paused AGAIN after execution (e.g., hit a sensitive tool)
                final_snapshot = await graph.aget_state(config)
                if final_snapshot.next:
                    response_text = "Hành động này cần xác nhận. Bạn có đồng ý thực hiện không? (Trả lời 'yes/confirm' hoặc lý do từ chối)"
                else:
                    # Process normal response
                    last_agent_response = result.get("last_agent_response", {})
                    
                    if result.get("messages"):
                        for msg in reversed(result["messages"]):
                            if hasattr(msg, "content") and msg.content:
                                response_text = msg.content
                                break
                    
                    if not response_text:
                        response_text = last_agent_response.get("response", "Xin lỗi, tôi không hiểu yêu cầu của bạn.")
                    
                assistant_msg = Message(
                    session_id=session_id,
                    role="assistant",
                    content=response_text,
                    message_type="message"
                )
                db.add(assistant_msg)
                session.updated_at = datetime.utcnow()
                await db.commit()
                
                return ChatResponse(type="message", content=response_text)
            except Exception:
                raise
        except Exception as e:
            print(f"[{run_id}] DEBUG: Chat error CAUGHT: {e}", flush=True)
            print(f"Chat error: {e}")
            import traceback
            traceback.print_exc()
            
            # Log to file
            import os
            log_path = os.path.join(os.path.dirname(__file__), "../../error.log")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"\n--- Error at {datetime.utcnow()} ---\n")
                f.write(f"Error: {str(e)}\n")
                f.write(traceback.format_exc())
                f.write("\n------------------------------\n")
                
            error_response = "Xin lỗi, đã có lỗi xảy ra."
            error_msg = Message(
                session_id=session_id,
                role="assistant",
                content=error_response,
                message_type="error"
            )
            db.add(error_msg)
            await db.commit()
            return ChatResponse(type="error", content=error_response)
