"""
Search tools for IT Support Agent.
Uses Tavily for web search to find IT troubleshooting solutions.
"""
import os
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults

from dotenv import load_dotenv
load_dotenv()


# Initialize Tavily search
def get_tavily_search():
    """Get Tavily search tool instance."""
    return TavilySearchResults(
        api_key=os.getenv("TAVILY_API_KEY"),
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=False
    )


def format_search_results(results: list) -> str:
    """Format Tavily search results."""
    if not results:
        return "Không tìm thấy kết quả phù hợp."
    
    formatted = []
    for i, result in enumerate(results, 1):
        title = result.get("title", "No title")
        content = result.get("content", "No content")
        url = result.get("url", "")
        
        formatted.append(
            f"**[{i}] {title}**\n"
            f"{content}\n"
            f"🔗 {url}\n"
        )
    
    return "\n---\n".join(formatted)


@tool
def search_it_solutions(query: str) -> str:
    """
    Search for IT troubleshooting solutions on the web.
    Use this tool to find solutions for:
    - Computer hardware issues (screen, keyboard, mouse, etc.)
    - Software problems (crashes, errors, installation)
    - Network connectivity issues
    - Printer and peripheral problems
    - Operating system errors (Windows, macOS, Linux)
    
    Args:
        query: The technical issue or error message to search for
    
    Returns:
        Relevant troubleshooting guides and solutions
    """
    try:
        tavily = get_tavily_search()
        
        # Enhance query for better IT results
        enhanced_query = f"how to fix {query} troubleshooting guide solution"
        
        results = tavily.invoke(enhanced_query)
        
        if isinstance(results, str):
            return results
        
        return format_search_results(results)
        
    except Exception as e:
        return f"Lỗi khi tìm kiếm: {str(e)}"


@tool
def search_it_solutions_vietnamese(query: str) -> str:
    """
    Tìm kiếm giải pháp khắc phục sự cố IT bằng tiếng Việt.
    Sử dụng công cụ này để tìm giải pháp cho:
    - Sự cố phần cứng máy tính
    - Lỗi phần mềm
    - Sự cố kết nối mạng
    - Lỗi hệ điều hành
    
    Args:
        query: Mô tả sự cố hoặc thông báo lỗi cần tìm kiếm
    
    Returns:
        Hướng dẫn khắc phục sự cố và giải pháp
    """
    try:
        tavily = get_tavily_search()
        
        # Search in both Vietnamese and English for better results
        enhanced_query = f"{query} cách khắc phục hướng dẫn sửa lỗi"
        
        results = tavily.invoke(enhanced_query)
        
        if isinstance(results, str):
            return results
        
        return format_search_results(results)
        
    except Exception as e:
        return f"Lỗi khi tìm kiếm: {str(e)}"
