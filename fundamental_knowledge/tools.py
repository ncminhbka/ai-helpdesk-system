# Type hints are required when declaring functions that will be used as tools.
#By default, the tool name comes from the function name. Override it when you need something more descriptive:
from langchain.tools import tool
@tool("web_search")  # Custom name
def search(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

print(search.name)  # web_search