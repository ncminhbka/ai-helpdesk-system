"""
IT Support Agent - Handles technical troubleshooting using Tavily search.
"""
import os
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

from tools.search_tools import search_it_solutions, search_it_solutions_vietnamese

from dotenv import load_dotenv
load_dotenv()


IT_SUPPORT_SYSTEM_PROMPT = """You are the IT Support Agent for FPT Customer Support.

Your role is to help users troubleshoot technical issues:
1. Computer hardware problems (screen, keyboard, mouse, etc.)
2. Software issues (crashes, errors, installation problems)
3. Network connectivity issues
4. Printer and peripheral problems
5. Operating system errors (Windows, macOS, Linux)
6. Mobile device issues

Available tools:
- search_it_solutions: Search for troubleshooting guides in English
- search_it_solutions_vietnamese: Search for solutions in Vietnamese

Instructions:
1. Understand the user's technical problem
2. Search for relevant solutions using the appropriate tool
3. Provide clear, step-by-step troubleshooting instructions
4. Cite sources when providing solutions
5. Suggest creating a support ticket if the issue cannot be resolved

Support both Vietnamese and English based on user's language.
"""


class ITSupportAgent:
    """IT Support Agent for technical troubleshooting."""
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.tools = [search_it_solutions, search_it_solutions_vietnamese]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
    
    async def process(
        self,
        user_message: str,
        chat_history: list = None,
        language: str = "vi"
    ) -> dict:
        """
        Process an IT support request.
        
        Returns:
            Dictionary with troubleshooting response
        """
        messages = [SystemMessage(content=IT_SUPPORT_SYSTEM_PROMPT)]
        
        if chat_history:
            messages.extend(chat_history[-6:])
        
        messages.append(HumanMessage(content=user_message))
        
        try:
            # Invoke LLM with tools
            response = await self.llm_with_tools.ainvoke(messages)
            
            # Check if tool call is requested
            if response.tool_calls:
                tool_call = response.tool_calls[0]
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                tool_call_id = tool_call["id"]
                
                # Execute the search tool
                try:
                    if tool_name == "search_it_solutions_vietnamese":
                        search_results = search_it_solutions_vietnamese.invoke(tool_args)
                    else:
                        search_results = search_it_solutions.invoke(tool_args)
                except Exception as e:
                    search_results = f"Không thể tìm kiếm: {str(e)} / Search failed: {str(e)}"
                
                # Build proper message chain with ToolMessage
                messages.append(response)  # AI message with tool_calls
                messages.append(ToolMessage(
                    content=str(search_results),
                    tool_call_id=tool_call_id
                ))
                
                # Generate final response based on search results
                final_response = await self.llm.ainvoke(messages)
                
                return {
                    "type": "message",
                    "response": final_response.content,
                    "sources_used": True
                }
            
            # No tool call - direct response
            return {
                "type": "message",
                "response": response.content,
                "sources_used": False
            }
            
        except Exception as e:
            print(f"IT Support Agent error: {e}")
            error_response = (
                "Xin lỗi, tôi gặp sự cố khi xử lý yêu cầu của bạn. "
                "Vui lòng thử lại hoặc mô tả vấn đề chi tiết hơn.\n\n"
                "Sorry, I encountered an issue processing your request. "
                "Please try again or describe your problem in more detail."
            )
            return {
                "type": "message",
                "response": error_response,
                "sources_used": False
            }


# Singleton
_it_support_agent: Optional[ITSupportAgent] = None


def get_it_support_agent() -> ITSupportAgent:
    global _it_support_agent
    if _it_support_agent is None:
        _it_support_agent = ITSupportAgent()
    return _it_support_agent
