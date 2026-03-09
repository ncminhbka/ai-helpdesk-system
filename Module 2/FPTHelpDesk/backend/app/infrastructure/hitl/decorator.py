"""
HITL (Human-in-the-Loop) decorator for LangGraph tools.

Provides @hitl_protected — a reusable decorator that adds interrupt()-based
confirmation to any sensitive tool function. The tool body only runs if the
user approves; otherwise a cancellation message is returned.

Usage:
    @hitl_protected(display_name="Đặt phòng họp", cancel_message="❌ Đã hủy.")
    @tool
    async def book_room(reason: str, time: str, ...):
        # pure business logic — no HITL code needed
"""
import functools
import inspect
from langgraph.types import interrupt
from app.infrastructure.config.settings import settings


# ==================== SHARED CONSTANTS ====================

# Fields hidden from user in confirmation card
HIDDEN_FIELDS = {"user_id", "session_id"}

# Vietnamese labels for common field names (used by all tools)
FIELD_LABELS = {
    "room_name": "Phòng", "reason": "Lý do", "time": "Thời gian",
    "customer_name": "Tên KH", "customer_phone": "SĐT",
    "email": "Email", "note": "Ghi chú",
    "booking_id": "Mã đặt phòng", "status": "Trạng thái",
    "content": "Nội dung", "description": "Mô tả",
    "ticket_id": "Mã ticket",
}


# ==================== DECORATOR ====================

def hitl_protected(
    display_name: str,
    cancel_message: str = "❌ Người dùng đã hủy thao tác.",
    hidden_fields: set[str] | None = None,
):
    """
    Decorator that adds HITL confirmation via LangGraph interrupt().

    When ENABLE_HITL is True, the decorator:
    1. Captures all kwargs passed to the tool
    2. Calls interrupt() with a structured payload (action, args, labels)
    3. If user approves → merges edits into kwargs → calls original function
    4. If user rejects → returns cancel_message without calling the function

    Args:
        display_name: Vietnamese display name for the confirmation card
        cancel_message: Message returned when user rejects the action
        hidden_fields: Extra fields to hide from user (merged with defaults)
    """
    _hidden = HIDDEN_FIELDS | (hidden_fields or set())

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not settings.ENABLE_HITL:
                return await func(*args, **kwargs) # cho phép chạy tool mà không cần HITL

            # Build visible args (filter hidden + None)
            visible_args = {
                k: v for k, v in kwargs.items()
                if k not in _hidden and v is not None
            }

            # Pause graph — wait for user confirmation (send this to frontend)
            response = interrupt({
                "action": func.__name__,
                "display_name": display_name,
                "args": visible_args,
                "field_labels": {
                    k: v for k, v in FIELD_LABELS.items() if k in visible_args
                },
            })

            # Handle response
            if isinstance(response, dict) and response.get("action") == "approve":
                # Merge user edits into kwargs and track what changed
                edits = response.get("edits", {})
                applied_edits = {}
                for key, value in edits.items():
                    if key in kwargs and value is not None and str(value).strip():
                        old_val = kwargs[key]
                        kwargs[key] = value
                        if str(old_val) != str(value):
                            label = FIELD_LABELS.get(key, key)
                            applied_edits[label] = (old_val, value)

                result = await func(*args, **kwargs)

                # If user edited parameters, prepend a notice to the tool result
                # so the agent knows the ACTUAL values and doesn't hallucinate the old ones
                if applied_edits:
                    edit_lines = [f"  • {label}: {old} → {new}" for label, (old, new) in applied_edits.items()]
                    notice = (
                        "⚠️ USER EDITED PARAMETERS BEFORE EXECUTION. "
                        "You MUST use the updated values below (NOT your original tool call args):\n"
                        + "\n".join(edit_lines)
                        + "\n\n"
                    )
                    return notice + str(result)

                return result

            # Rejected
            return cancel_message

        return wrapper

    return decorator
