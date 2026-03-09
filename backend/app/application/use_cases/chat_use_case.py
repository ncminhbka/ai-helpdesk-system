"""
Chat use case - Orchestrates LangGraph invocation and message persistence.
Handles session management, HITL resume via Command(resume=...), and message saving.
"""
import json
from typing import Optional, Any, List

from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command

from app.infrastructure.database.models.chat_model import ChatSession
from app.infrastructure.repositories.chat_repository import ChatRepository


class ChatUseCase:

    @staticmethod
    async def create_session(
        db: AsyncSession, user_id: int, title: str = "New Chat"
    ) -> ChatSession:
        """Create a new chat session."""
        return await ChatRepository.create_session(db, user_id, title)

    @staticmethod
    async def get_session(
        db: AsyncSession, session_id: str, user_id: int
    ) -> Optional[ChatSession]:
        """Get a session owned by the specified user."""
        return await ChatRepository.get_session(db, session_id, user_id)

    @staticmethod
    async def list_session_by_user_id(
        db: AsyncSession, user_id: int
    ) -> List[ChatSession]:
        """List all sessions for a specific user."""
        return await ChatRepository.list_session_by_user_id(db, user_id)

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
        await ChatRepository.save_message(
            db, session_id, role, content, message_type, metadata
        )

    @staticmethod
    async def update_session_title(
        db: AsyncSession, session_id: str, title: str
    ):
        """Update session title (e.g., from first message)."""
        await ChatRepository.update_session_title(db, session_id, title)

    @staticmethod
    async def get_messages(
        db: AsyncSession, session_id: str
    ) -> List[Any]:
        """Fetch all messages in a session."""
        return await ChatRepository.get_messages(db, session_id)

    @staticmethod
    async def delete_session(
        db: AsyncSession, session: ChatSession
    ):
        """Delete a chat session."""
        await ChatRepository.delete_session(db, session)

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
        """
        # Save user message
        await ChatUseCase.save_message(db, session_id, "user", message)

        # Graph config with thread_id for checkpointer
        config = {"configurable": {"thread_id": session_id}}

        try:
            # Check if the graph is ALREADY in an interrupted state
            current_state = await graph.aget_state(config)
            is_interrupted = bool(current_state.next)

            if is_interrupted:
                result = await ChatUseCase._handle_hitl_resume(
                    graph, config, message
                )
            else:
                result = await ChatUseCase._invoke_graph(
                    graph, config, message, user_id, user_email, session_id
                )

            # Check if the result contains an __interrupt__ after invoke
            if isinstance(result, dict) and "__interrupt__" in result:
                interrupt_data = result["__interrupt__"][0].value
                response_content = ChatUseCase._build_confirm_message(interrupt_data)
                response_type = "confirm"

                # Update session title from first message
                await ChatUseCase._maybe_update_title(db, session_id, message)

                # Save assistant message
                await ChatUseCase.save_message(
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
            response_content = ChatUseCase._extract_response(result)
            response_type = "message"

            # Update session title from first message
            await ChatUseCase._maybe_update_title(db, session_id, message)

            # Save assistant message
            await ChatUseCase.save_message(
                db, session_id, "assistant", response_content,
                message_type=response_type,
            )

            return {"type": response_type, "content": response_content}

        except Exception as e:
            error_msg = f"Xin lỗi, đã có lỗi xảy ra: {str(e)}"
            await ChatUseCase.save_message(
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
        """
        try:
            resume_payload = json.loads(message)
        except (json.JSONDecodeError, TypeError):
            text = message.strip().lower()
            if text in ["y", "yes", "có", "ok", "confirm", "đồng ý"]:
                resume_payload = {"action": "approve"}
            else:
                resume_payload = {"action": "reject"}

        result = await graph.ainvoke(Command(resume=resume_payload), config)
        return result

    @staticmethod
    async def _maybe_update_title(db: AsyncSession, session_id: str, message: str):
        """Update session title from first message if needed."""
        msg_count = await ChatRepository.get_message_count(db, session_id)
        if msg_count <= 1:
            await ChatUseCase.update_session_title(db, session_id, message)

    @staticmethod
    def _extract_response(result: dict) -> str:
        """Extract the final assistant response text from graph result."""
        messages = result.get("messages", [])

        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content:
                content = msg.content
                if isinstance(content, list):
                    text_parts = [
                        p.get("text", "") for p in content
                        if isinstance(p, dict) and p.get("text")
                    ]
                    if text_parts:
                        return "\n".join(text_parts)
                elif isinstance(content, str) and content.strip():
                    return content

        return "Tôi không thể xử lý yêu cầu này. Vui lòng thử lại."
