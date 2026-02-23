"""
Chat service - Orchestrates LangGraph invocation and message persistence.
Handles session management, HITL resume, and message saving.
"""
import uuid
from datetime import datetime
from typing import Optional, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

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
        2. Check if graph is paused (HITL) and handle resume
        3. Otherwise, invoke graph with new message
        4. After invoke, check if graph is NOW interrupted (pending HITL)
        5. Return confirm-type response if HITL, else message-type
        """
        # Save user message
        await ChatService.save_message(db, session_id, "user", message)

        # Graph config with thread_id for checkpointer
        config = {"configurable": {"thread_id": session_id}}

        try:
            # Check if the graph is ALREADY in an interrupted (HITL) state
            current_state = graph.get_state(config)
            is_interrupted = bool(current_state.next)

            if is_interrupted:
                # HITL flow: user is responding to confirmation
                response_content = await ChatService._handle_hitl_resume(
                    graph, config, message, user_id, user_email
                )
                response_type = "message"
            else:
                # Normal flow: invoke graph with new message
                response_content = await ChatService._invoke_graph(
                    graph, config, message, user_id, user_email, session_id
                )
                response_type = "message"

            # After invoke, check if graph is NOW interrupted (new HITL pending)
            post_state = graph.get_state(config)
            is_now_interrupted = bool(post_state.next)

            pending_action = None
            pending_data = None

            if is_now_interrupted:
                response_type = "confirm"
                # Extract the pending tool call details
                pending_action, pending_data = ChatService._extract_pending_action(post_state)

                # Build a CLEAN confirmation message from tool call data
                # (don't use response_content — it repeats the agent's prior text)
                response_content = ChatService._build_confirm_message(
                    pending_action, pending_data
                )

            # Update session title from first message
            count_result = await db.execute(
                select(Message).where(Message.session_id == session_id)
            )
            msg_count = len(count_result.scalars().all())
            if msg_count <= 1:
                await ChatService.update_session_title(db, session_id, message)

            # Save assistant message
            await ChatService.save_message(
                db, session_id, "assistant", response_content,
                message_type=response_type,
            )

            result = {"type": response_type, "content": response_content}
            if pending_action:
                result["action"] = pending_action
            if pending_data:
                result["data"] = pending_data
            return result

        except Exception as e:
            error_msg = f"Xin lỗi, đã có lỗi xảy ra: {str(e)}"
            await ChatService.save_message(
                db, session_id, "assistant", error_msg, "error"
            )
            return {"type": "error", "content": error_msg}

    @staticmethod
    def _extract_pending_action(state) -> tuple:
        """Extract the pending tool call name and arguments from interrupted state."""
        try:
            messages = state.values.get("messages", [])
            for msg in reversed(messages):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_call = msg.tool_calls[0]
                    action_name = tool_call.get("name", "unknown")
                    action_args = tool_call.get("args", {})

                    # Map tool names to human-readable Vietnamese labels
                    action_labels = {
                        "book_room": "Đặt phòng họp",
                        "update_booking": "Cập nhật đặt phòng",
                        "cancel_booking": "Hủy đặt phòng",
                        "create_ticket": "Tạo ticket hỗ trợ",
                        "update_ticket": "Cập nhật ticket",
                    }
                    display_name = action_labels.get(action_name, action_name)
                    return display_name, action_args
        except Exception:
            pass
        return "thao tác", None

    @staticmethod
    def _build_confirm_message(action: str, data: dict) -> str:
        """Build a clean, non-duplicated confirmation message from tool call data."""
        lines = [f"⚠️ **Xác nhận: {action}**\n"]

        # Internal fields that should NOT be shown to the user
        hidden_fields = {"user_id", "session_id"}

        if data:
            # Map common field names to Vietnamese labels
            field_labels = {
                "room_name": "Phòng", "room": "Phòng", "reason": "Lý do", "time": "Thời gian",
                "customer_name": "Tên KH", "customer_phone": "SĐT",
                "email": "Email", "note": "Ghi chú",
                "content": "Nội dung", "description": "Mô tả",
                "booking_id": "Mã đặt phòng", "ticket_id": "Mã ticket",
                "status": "Trạng thái",
            }
            for key, value in data.items():
                if key in hidden_fields:
                    continue
                if value is not None and str(value).strip():
                    label = field_labels.get(key, key)
                    lines.append(f"- **{label}**: {value}")

        lines.append("\n---")
        lines.append("Gõ **y** hoặc **có** để xác nhận, hoặc bất kỳ nội dung khác để hủy.")
        return "\n".join(lines)

    @staticmethod
    async def _invoke_graph(
        graph, config, message, user_id, user_email, session_id
    ) -> str:
        """Invoke the LangGraph with a new user message."""
        input_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "user_email": user_email,
            "session_id": session_id,
        }

        result = await graph.ainvoke(input_state, config)
        return ChatService._extract_response(result)

    @staticmethod
    async def _handle_hitl_resume(
        graph, config, message, user_id, user_email
    ) -> str:
        """
        Handle HITL confirmation resume.
        The graph is paused before a sensitive tool node.
        User says 'y/yes' to proceed or anything else to cancel.
        """
        user_confirms = message.strip().lower() in ["y", "yes", "có", "ok", "confirm", "đồng ý"]

        if user_confirms:
            # Resume: just continue execution (tool will run)
            result = await graph.ainvoke(None, config)
            return ChatService._extract_response(result)
        else:
            # Cancel: get current state and create a ToolMessage to skip the tool
            current_state = graph.get_state(config)
            last_message = current_state.values.get("messages", [])[-1]

            # Determine which node was about to execute (the interrupted node)
            interrupted_node = current_state.next[0] if current_state.next else None

            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                tool_call_id = last_message.tool_calls[0]["id"]
                tool_name = last_message.tool_calls[0]["name"]

                # Inject cancellation ToolMessage AS IF it came from the interrupted node.
                # This tells LangGraph "this node already ran" so it proceeds to the NEXT
                # node (the agent) instead of re-entering the tool node.
                cancel_msg = ToolMessage(
                    content=f"Người dùng đã hủy thao tác '{tool_name}'. "
                            f"Hãy thông báo cho người dùng rằng thao tác đã bị hủy và hỏi họ muốn làm gì tiếp.",
                    tool_call_id=tool_call_id,
                )
                graph.update_state(
                    config,
                    {"messages": [cancel_msg]},
                    as_node=interrupted_node,
                )

            # Continue graph execution — agent sees the cancel and responds
            result = await graph.ainvoke(None, config)
            return ChatService._extract_response(result)

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
