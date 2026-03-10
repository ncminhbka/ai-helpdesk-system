"""
Chat use case - Orchestrates LangGraph invocation and message persistence.
Handles session management, HITL resume via Command(resume=...), and message saving.
"""
import json
from typing import Optional, Any, List

from langchain_core.messages import HumanMessage, AIMessage
from langgraph.types import Command

from app.domain.entities.chat_entity import ChatSessionEntity, MessageEntity
from app.domain.interfaces.chat_repository import IChatRepository


class ChatUseCase:
    def __init__(self, chat_repo: IChatRepository):
        self.chat_repo = chat_repo

    async def create_session(self, user_id: int, title: str = "New Chat") -> ChatSessionEntity:
        return await self.chat_repo.create_session(user_id, title)

    async def get_session(self, session_id: str, user_id: int) -> Optional[ChatSessionEntity]:
        return await self.chat_repo.get_session(session_id, user_id)

    async def list_session_by_user_id(self, user_id: int) -> List[ChatSessionEntity]:
        return await self.chat_repo.list_session_by_user_id(user_id)

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str,
        message_type: str = "message",
        metadata: dict = None,
    ) -> MessageEntity:
        return await self.chat_repo.save_message(session_id, role, content, message_type, metadata)

    async def update_session_title(self, session_id: str, title: str) -> None:
        await self.chat_repo.update_session_title(session_id, title)

    async def get_messages(self, session_id: str) -> List[MessageEntity]:
        return await self.chat_repo.get_messages(session_id)

    async def delete_session(self, session_id: str) -> None:
        await self.chat_repo.delete_session(session_id)

    async def process_message(
        self,
        session_id: str,
        user_id: int,
        user_email: str,
        message: str,
        graph: Any,
    ) -> dict:
        """Process a user message through the LangGraph."""
        await self.save_message(session_id, "user", message)

        config = {"configurable": {"thread_id": session_id}}

        try:
            current_state = await graph.aget_state(config)
            is_interrupted = bool(current_state.next)

            if is_interrupted:
                result = await self._handle_hitl_resume(graph, config, message)
            else:
                result = await self._invoke_graph(graph, config, message, user_id, user_email, session_id)

            if isinstance(result, dict) and "__interrupt__" in result:
                interrupt_data = result["__interrupt__"][0].value
                response_content = self._build_confirm_message(interrupt_data)
                response_type = "confirm"

                await self._maybe_update_title(session_id, message)
                await self.save_message(
                    session_id, "assistant", response_content,
                    message_type=response_type,
                    metadata=interrupt_data,
                )
                return {
                    "type": response_type,
                    "content": response_content,
                    "action": interrupt_data.get("action"),
                    "data": interrupt_data.get("args"),
                }

            response_content = self._extract_response(result)
            response_type = "message"

            await self._maybe_update_title(session_id, message)
            await self.save_message(session_id, "assistant", response_content, message_type=response_type)

            return {"type": response_type, "content": response_content}

        except Exception as e:
            error_msg = f"Xin lỗi, đã có lỗi xảy ra: {str(e)}"
            await self.save_message(session_id, "assistant", error_msg, "error")
            return {"type": "error", "content": error_msg}

    def _build_confirm_message(self, interrupt_data: dict) -> str:
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

    async def _invoke_graph(self, graph, config, message, user_id, user_email, session_id) -> dict:
        input_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "user_email": user_email,
            "session_id": session_id,
        }
        return await graph.ainvoke(input_state, config)

    async def _handle_hitl_resume(self, graph, config, message) -> dict:
        try:
            resume_payload = json.loads(message)
        except (json.JSONDecodeError, TypeError):
            text = message.strip().lower()
            if text in ["y", "yes", "có", "ok", "confirm", "đồng ý"]:
                resume_payload = {"action": "approve"}
            else:
                resume_payload = {"action": "reject"}
        return await graph.ainvoke(Command(resume=resume_payload), config)

    async def _maybe_update_title(self, session_id: str, message: str) -> None:
        msg_count = await self.chat_repo.get_message_count(session_id)
        if msg_count <= 1:
            await self.update_session_title(session_id, message)

    @staticmethod
    def _extract_response(result: dict) -> str:
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
