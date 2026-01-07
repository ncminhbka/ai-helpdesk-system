from langchain_ollama import ChatOllama
from langchain.tools import tool
from langchain.agents import create_agent
import os
from dotenv import load_dotenv
from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage

load_dotenv()

#langchain agents = model + tools

#define model
llm = ChatOllama(
    model="llama3.1",
    base_url=os.getenv("OLLAMA_HOST"),
    temperature=0
)

#define tools
@tool
def add_numbers(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b
@tool
def multiply_numbers(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b

tools = [add_numbers, multiply_numbers]



#tool error handling
@wrap_tool_call
def handle_tool_errors(request, handler):
    """Handle tool execution errors with custom messages."""
    try:
        return handler(request)
    except Exception as e:
        # Return a custom error message to the model
        return ToolMessage(
            content=f"Tool error: Please check your input and try again. ({str(e)})",
            tool_call_id=request.tool_call["id"]
        )
def handler(request):
    print("Error has been handled.")

#the create_agent api (backend langgraph)
#note that pre-bound models (models with bind_tools already called) are not supported when using structured output.
agent = create_agent(llm, tools, middleware=[handle_tool_errors])

#the system prompt accepts either a string or SystemMessage

