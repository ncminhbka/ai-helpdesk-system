"""LangGraph implementation of IGraphRunner."""
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command

from app.domain.interfaces.graph_runner import IGraphRunner


class LangGraphRunner(IGraphRunner):
    def __init__(self, graph):
        self._graph = graph

    async def is_interrupted(self, session_id: str) -> bool:
        config = {"configurable": {"thread_id": session_id}}
        state = await self._graph.aget_state(config)
        return bool(state.next)

    async def invoke(self, session_id: str, user_id: int, user_email: str, message: str) -> dict:
        config = {"configurable": {"thread_id": session_id}}
        input_state = {
            "messages": [HumanMessage(content=message)],
            "user_id": user_id,
            "user_email": user_email,
            "session_id": session_id,
        }
        return await self._graph.ainvoke(input_state, config)

    async def resume(self, session_id: str, payload: dict) -> dict:
        config = {"configurable": {"thread_id": session_id}}
        return await self._graph.ainvoke(Command(resume=payload), config)

    def extract_response(self, result: dict) -> str:
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
