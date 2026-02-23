"""
Search tools for IT Support Agent.
Uses Tavily for web search to find IT troubleshooting solutions.
"""
import os
from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

load_dotenv()


def get_tavily_search():
    """Get Tavily search tool instance."""
    return TavilySearchResults(
        api_key=os.getenv("TAVILY_API_KEY"),
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=False,
    )


def format_search_results(results: list) -> str:
    """Format Tavily search results for display."""
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
            f"🔗 {url}"
        )

    return "\n\n---\n\n".join(formatted)


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
    """
    try:
        tavily = get_tavily_search()
        results = tavily.invoke(query)

        if isinstance(results, str):
            return results

        return format_search_results(results)

    except Exception as e:
        return f"Lỗi khi tìm kiếm: {str(e)}"
