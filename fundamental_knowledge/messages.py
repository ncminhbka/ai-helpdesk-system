# messages contain: Role, Content, Metadata
# Roles: system, user, assistant, tool
# Metadata: arbitrary key-value pairs associated with the message
from langchain_ollama import ChatOllama
from langchain.messages import HumanMessage, AIMessage, SystemMessage

model = ChatOllama(
    model="llama3.1:8b",
    base_url="http://localhost:11434",
    temperature=0
)

system_msg = SystemMessage("You are a helpful assistant.")
human_msg = HumanMessage("Hello, how are you?")

# message prompt
messages = [system_msg, human_msg]
response = model.invoke(messages)  # Returns AIMessage
print("Response:", response.content)
print("Type:", type(response))
# text prompt (hardly used)
# response = model.invoke("Hello, how are you?")

#You can also specify messages directly in OpenAI chat completions format. (hardly used)
'''
messages = [
    {"role": "system", "content": "You are a poetry expert"},
    {"role": "user", "content": "Write a haiku about spring"},
    {"role": "assistant", "content": "Cherry blossoms bloom..."}
]
'''
# in conclusion, langchain messages: SystemMessage, HumanMessage, AIMessage, ToolMessage
# HumanMessage, AIMessage, ToolMessage can contain metadata
#when model make tool calls, they are included in the AIMessage metadata
def get_weather(location: str) -> str:
    """Get the weather at a location."""
    ...

model_with_tools = model.bind_tools([get_weather])
response = model_with_tools.invoke("What's the weather in Paris?")

for tool_call in response.tool_calls:
    print(f"Tool: {tool_call['name']}")
    print(f"Args: {tool_call['args']}")
    print(f"ID: {tool_call['id']}")

# streaming response
# During streaming, you’ll receive AIMessageChunk objects that can be combined into a full message object:
chunks = []
full_message = None
for chunk in model.stream("Hi"):
    chunks.append(chunk)
    print(chunk.text)
    full_message = chunk if full_message is None else full_message + chunk

print("Full message:", full_message)

# Message Content
# String content
human_message = HumanMessage("Hello, how are you?")

# Provider-native format (e.g., OpenAI)
human_message = HumanMessage(content=[
    {"type": "text", "text": "Hello, how are you?"},
    {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
])

# List of standard content blocks
human_message = HumanMessage(content_blocks=[
    {"type": "text", "text": "Hello, how are you?"},
    {"type": "image", "url": "https://example.com/image.jpg"},
])


