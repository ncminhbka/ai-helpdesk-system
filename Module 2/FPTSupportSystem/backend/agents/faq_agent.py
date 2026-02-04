"""
FAQ Agent - Handles policy questions using RAG.
"""
import os
from typing import Optional, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from tools.rag_tools import search_fpt_policies

from dotenv import load_dotenv
load_dotenv()


FAQ_SYSTEM_PROMPT = """You are the FAQ Agent for FPT Customer Support.

Your role is to answer questions about FPT policies, regulations, and guidelines using the knowledge base.

Available information sources:
- FPT Code of Business Conduct
- FPT Human Rights Policy
- Personal Data Protection Regulations

Instructions:
1. Use the search tool to find relevant information
2. Provide accurate answers based on the search results
3. Always cite the source document and page number
4. If information is not found, clearly state that
5. Support both Vietnamese and English

Be professional, accurate, and helpful.
"""


class FAQAgent:
    """FAQ Agent for answering policy questions using RAG."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.2,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.tools = [search_fpt_policies]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
    
    async def process(
        self,
        user_message: str,
        chat_history: list = None,
        language: str = "vi"
    ) -> dict:
        """
        Process a policy question.
        
        Returns:
            Dictionary with response and metadata
        """
        messages = [SystemMessage(content=FAQ_SYSTEM_PROMPT)]
        
        if chat_history:
            messages.extend(chat_history[-6:])  # Last 6 messages for context
        
        messages.append(HumanMessage(content=user_message))
        
        try:
            # First, invoke LLM to decide if tool is needed
            response = await self.llm_with_tools.ainvoke(messages)
            
            # Check if tool call is requested
            if response.tool_calls:
                # Execute the search tool
                tool_call = response.tool_calls[0]
                tool_call_id = tool_call["id"]
                search_query = tool_call["args"].get("query", user_message)
                
                # Execute RAG search
                try:
                    search_results = search_fpt_policies.invoke(search_query)
                except Exception as e:
                    search_results = f"Không thể tìm kiếm: {str(e)}"
                
                # Build proper message chain with ToolMessage
                messages.append(response)  # AI message with tool_calls
                messages.append(ToolMessage(
                    content=str(search_results),
                    tool_call_id=tool_call_id
                ))
                
                final_response = await self.llm.ainvoke(messages)
                
                return {
                    "response": final_response.content,
                    "sources_used": True,
                    "search_query": search_query
                }
            
            # Direct response without tool
            return {
                "response": response.content,
                "sources_used": False
            }
            
        except Exception as e:
            print(f"FAQ Agent error: {e}")
            error_response = (
                "Xin lỗi, tôi không thể tìm thông tin về vấn đề này. "
                "Vui lòng thử lại hoặc đặt câu hỏi cụ thể hơn.\n\n"
                "Sorry, I couldn't find information about this. "
                "Please try again or ask a more specific question."
            )
            return {
                "response": error_response,
                "sources_used": False
            }


# Singleton
_faq_agent: Optional[FAQAgent] = None


def get_faq_agent() -> FAQAgent:
    global _faq_agent
    if _faq_agent is None:
        _faq_agent = FAQAgent()
    return _faq_agent
