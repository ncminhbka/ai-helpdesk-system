"""
Chat service - Orchestrates LangGraph invocation and message persistence.
Handles session management, HITL resume via Command(resume=...), and message saving.
"""
import json
import uuid
from datetime import datetime
from typing import Optional, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.types import Command

from app.models.chat import ChatSession, Message
from app.utils.helpers import truncate_text, safe_json_dumps


class ChatService:

    @staticmethod
    async def create_session(
        db: AsyncSession, user_id: int, title: str = "New Chat"
    ) -> ChatSession:
        """Create a new chat session."""
        session = ChatSession(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    @staticmethod
    async def get_session(
        db: AsyncSession, session_id: str, user_id: int
    ) -> Optional[ChatSession]:
        """Get a session owned by the specified user."""
        result = await db.execute(
            select(ChatSession).where(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def save_message(
        db: AsyncSession,
        session_id: str,
        role: str,
        content: str,
        message_type: str = "message",
        metadata: dict = None,
    ):
        """Persist a message to the database."""
        msg = Message(
            session_id=session_id,
            role=role,
            content=content,
            message_type=message_type,
            metadata_json=safe_json_dumps(metadata) if metadata else None,
        )
        db.add(msg)
        await db.commit()

    @staticmethod
    async def update_session_title(
        db: AsyncSession, session_id: str, title: str
    ):
        """Update session title (e.g., from first message)."""
        result = await db.execute(
            select(ChatSession).where(ChatSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()
        if session:
            session.title = truncate_text(title, 50)
            session.updated_at = datetime.utcnow()
            await db.commit()

    @staticmethod
    async def process_message(
        db: AsyncSession,
        session_id: str,
        user_id: int,
        user_email: str,
        message: str,
        graph: Any,
    ) -> dict:
        """
        Process a user message through the LangGraph.

        Flow:
        1. Save user message to DB
        2. Check if graph is paused (HITL interrupt) and handle resume
        3. Otherwise, invoke graph with new message
        4. After invoke, check for __interrupt__ in result
        5. Return confirm-type response if interrupted, else message-type
        """
        # Save user message
        await ChatService.save_message(db, session_id, "user", message)

        # Graph config with thread_id for checkpointer
        config = {"configurable": {"thread_id": session_id}}

        try:
            # Check if the graph is ALREADY in an interrupted state 
            current_state = await graph.aget_state(config)
            is_interrupted = bool(current_state.next)

            if is_interrupted: # (confirmation form already shown, waiting for user response)
                # HITL flow: user is responding to confirmation
                result = await ChatService._handle_hitl_resume(
                    graph, config, message
                )
            else:
                # Normal flow: invoke graph with new message
                result = await ChatService._invoke_graph(
                    graph, config, message, user_id, user_email, session_id
                )

            # Check if the result contains an __interrupt__ after invoke
            if isinstance(result, dict) and "__interrupt__" in result:
                interrupt_data = result["__interrupt__"][0].value
                response_content = ChatService._build_confirm_message(interrupt_data)
                response_type = "confirm"

                # Update session title from first message
                await ChatService._maybe_update_title(db, session_id, message)

                # Save assistant message
                await ChatService.save_message(
                    db, session_id, "assistant", response_content,
                    message_type=response_type,
                    metadata=interrupt_data,
                )

                return {
                    "type": response_type,
                    "content": response_content,
                    "action": interrupt_data.get("action"),
                    "data": interrupt_data.get("args"),
                }

            # Normal (non-interrupted) response
            response_content = ChatService._extract_response(result)
            response_type = "message"

            # Update session title from first message
            await ChatService._maybe_update_title(db, session_id, message)

            # Save assistant message
            await ChatService.save_message(
                db, session_id, "assistant", response_content,
                message_type=response_type,
            )

            return {"type": response_type, "content": response_content}

        except Exception as e:
            error_msg = f"Xin lỗi, đã có lỗi xảy ra: {str(e)}"
            await ChatService.save_message(
                db, session_id, "assistant", error_msg, "error"
            )
            return {"type": "error", "content": error_msg}

    @staticmethod
    def _build_confirm_message(interrupt_data: dict) -> str:
        """Build a confirmation message from the interrupt payload."""
        display_name = interrupt_data.get("display_name", "Thao tác")
        args = interrupt_data.get("args", {})
        field_labels = interrupt_data.get("field_labels", {})

        lines = [f"⚠️ **Xác nhận: {display_name}**\n"]

        for key, value in args.items():
            if value is not None and str(value).strip():
                label = field_labels.get(key, key)
                lines.append(f"- **{label}**: {value}")

        lines.append("\n---")
        lines.append("Nhấn **Xác nhận** để thực hiện, **Sửa** để chỉnh sửa, hoặc **Hủy** để hủy thao tác.")
        return "\n".join(lines)

    @staticmethod
    async def _invoke_graph(
        graph, config, message, user_id, user_email, session_id
    ) -> dict:
        """Invoke the LangGraph with a new user message."""
        input_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "user_email": user_email,
            "session_id": session_id,
        }

        return await graph.ainvoke(input_state, config)

    @staticmethod
    async def _handle_hitl_resume(graph, config, message) -> dict:
        """
        Handle HITL confirmation resume using Command(resume=...).
        The frontend sends a JSON payload: {"action":"approve|reject", "edits":{...}}
        """
        # Try to parse structured JSON from frontend
        try:
            resume_payload = json.loads(message)
        except (json.JSONDecodeError, TypeError):
            # Fallback: treat plain text as simple approve/reject
            text = message.strip().lower()
            if text in ["y", "yes", "có", "ok", "confirm", "đồng ý"]:
                resume_payload = {"action": "approve"}
            else:
                resume_payload = {"action": "reject"}

        # Resume the graph with the structured payload
        result = await graph.ainvoke(Command(resume=resume_payload), config)
        return result

    @staticmethod
    async def _maybe_update_title(db: AsyncSession, session_id: str, message: str):
        """Update session title from first message if needed."""
        count_result = await db.execute(
            select(Message).where(Message.session_id == session_id)
        )
        msg_count = len(count_result.scalars().all())
        if msg_count <= 1: # only update title if there is only one message
            await ChatService.update_session_title(db, session_id, message)

    @staticmethod
    def _extract_response(result: dict) -> str:
        """Extract the final assistant response text from graph result."""
        messages = result.get("messages", [])

        # Walk backwards to find the last AI message with content
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                content = msg.content
                if isinstance(content, list):
                    # Multi-part content
                    text_parts = [
                        p.get("text", "") for p in content
                        if isinstance(p, dict) and p.get("text")
                    ]
                    if text_parts:
                        return "\n".join(text_parts)
                elif isinstance(content, str) and content.strip():
                    return content

        return "Tôi không thể xử lý yêu cầu này. Vui lòng thử lại."
