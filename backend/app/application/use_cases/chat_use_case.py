"""
Chat use case - Orchestrates LangGraph invocation and message persistence.
Handles session management, HITL resume via Command(resume=...), and message saving.
"""
import json
from typing import Optional, List

from app.domain.entities.chat_entity import ChatSessionEntity, MessageEntity
from app.domain.interfaces.chat_repository import IChatRepository
from app.domain.interfaces.graph_runner import IGraphRunner


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
        runner: IGraphRunner,
    ) -> dict:
        """
        Luồng xử lý một tin nhắn từ user:

        1. Lưu tin nhắn user vào DB ngay lập tức (trước khi chạy AI).

        2. Kiểm tra trạng thái graph của session hiện tại:
           - Nếu graph đang BỊ INTERRUPT (đang chờ user xác nhận HITL):
             → Parse tin nhắn thành payload approve/reject
             → Resume graph từ điểm bị dừng

           - Nếu graph ĐANG BÌNH THƯỜNG (chưa bị interrupt):
             → Invoke graph với tin nhắn mới của user

        3. Kiểm tra kết quả trả về từ graph:
           - Nếu result chứa "__interrupt__": graph vừa dừng lại để chờ xác nhận
             → Xây dựng confirm message (hiển thị thông tin cần xác nhận cho user)
             → Lưu confirm message vào DB với type="confirm"
             → Trả về response type="confirm" kèm action và data để frontend hiển thị nút xác nhận

           - Nếu result BÌNH THƯỜNG (không có interrupt):
             → Trích xuất text cuối cùng từ AI messages trong result
             → Lưu AI response vào DB với type="message"
             → Trả về response type="message"

        4. Nếu có lỗi bất kỳ: lưu error message vào DB và trả về type="error".
        """
        # Bước 1: Lưu tin nhắn user vào DB
        await self.save_message(session_id, "user", message)

        try:
            # Bước 2: Quyết định invoke mới hay resume HITL
            if await runner.is_interrupted(session_id):
                # Graph đang chờ xác nhận → parse approve/reject rồi resume
                payload = self._parse_hitl_payload(message)
                result = await runner.resume(session_id, payload)
            else:
                # Graph rảnh → invoke với message mới
                result = await runner.invoke(session_id, user_id, user_email, message)

            # Bước 3a: Graph vừa dừng lại để chờ xác nhận (HITL interrupt)
            if isinstance(result, dict) and "__interrupt__" in result:
                interrupt_data = result["__interrupt__"][0].value
                response_content = self._build_confirm_message(interrupt_data)
                response_type = "confirm"

                await self._maybe_update_title(session_id, message)
                await self.save_message(
                    session_id, "assistant", response_content,
                    message_type=response_type,
                    metadata=interrupt_data,  # lưu data để frontend render nút xác nhận
                )
                return {
                    "type": response_type,
                    "content": response_content,
                    "action": interrupt_data.get("action"),
                    "data": interrupt_data.get("args"),
                }

            # Bước 3b: Graph chạy xong bình thường → trích xuất AI response
            response_content = runner.extract_response(result)
            response_type = "message"

            await self._maybe_update_title(session_id, message)
            await self.save_message(session_id, "assistant", response_content, message_type=response_type)

            return {"type": response_type, "content": response_content}

        # Bước 4: Xử lý lỗi bất ngờ
        except Exception as e:
            error_msg = f"Xin lỗi, đã có lỗi xảy ra: {str(e)}"
            await self.save_message(session_id, "assistant", error_msg, "error")
            return {"type": "error", "content": error_msg}

    def _parse_hitl_payload(self, message: str) -> dict:
        """Parse user message thành HITL payload. Business logic thuần túy."""
        try:
            return json.loads(message)
        except (json.JSONDecodeError, TypeError):
            text = message.strip().lower()
            if text in ["y", "yes", "có", "ok", "confirm", "đồng ý"]:
                return {"action": "approve"}
            return {"action": "reject"}

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

    async def _maybe_update_title(self, session_id: str, message: str) -> None:
        msg_count = await self.chat_repo.get_message_count(session_id)
        if msg_count <= 1:
            await self.update_session_title(session_id, message)
