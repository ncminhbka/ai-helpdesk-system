#many models support tool call, structured output, multimodality, reasoning
#models can be utilized directly (for text generation, classification, or extraction) or through agents
from langchain_ollama import ChatOllama

# dỉrect model usage
'''
import os
from langchain.chat_models import init_chat_model

os.environ["OPENAI_API_KEY"] = "sk-..."

model = init_chat_model("gpt-4.1")
response = model.invoke("Why do parrots talk?")
'''

model = ChatOllama(
    model="llama3.1:8b",
    base_url="http://localhost:11434",
    temperature=0
)

# params of a model
# max_tokens (number)
#- Limits the total number of tokens in the response, effectively controlling how long the output can be.
# timeout (number)
#- The maximum time (in seconds) to wait for a response from the model before canceling the request.
# max_retries (number)
#- The maximum number of attempts the system will make to resend a request if it fails due to issues like network timeouts or rate limits.

# model invocation: 3 ways
# - invoke, stream, batch

# if we instantiate a model separately (without agent), we have to handle tool calls ourselves
# Bind (potentially multiple) tools to the model
'''
model_with_tools = model.bind_tools([get_weather])

# Step 1: Model generates tool calls
messages = [{"role": "user", "content": "What's the weather in Boston?"}]
ai_msg = model_with_tools.invoke(messages)
messages.append(ai_msg)

# Step 2: Execute tools and collect results
for tool_call in ai_msg.tool_calls:
    # Execute the tool with the generated arguments
    tool_result = get_weather.invoke(tool_call)
    messages.append(tool_result)

# Step 3: Pass results back to model for final response
final_response = model_with_tools.invoke(messages)
print(final_response.text)
# "The current weather in Boston is 72°F and sunny."
'''
# we also can do these following things to tool calls:
# - forcing tool calls
# - parallel tool calls (depending on model support)
# - streaming tool calls

# structured output
# langchain supports structured output schema: Pydantic, TypedDict, JSON Schema
# for example pydantic
from pydantic import BaseModel, Field

class Movie(BaseModel):
    """Một bộ phim với các thông tin chi tiết."""
    title: str = Field(..., description="Tên bộ phim")
    year: int = Field(..., description="Năm phát hành")
    director: str = Field(..., description="Đạo diễn")
    rating: float = Field(..., description="Điểm đánh giá trên thang 10")

model_with_structure = model.with_structured_output(Movie)
response = model_with_structure.invoke("Provide details about the movie Inception")

print(response)
# -> Movie(title="Inception", year=2010, director="Christopher Nolan", rating=8.8)
# See structured_output.py for more details

# =========================
# LANGCHAIN – ADVANCED TOPICS (SUMMARY)
# =========================

# --- MODEL PROFILES ---
# - Yêu cầu: langchain >= 1.1
# - model.profile: dict mô tả capability của model (token limit, multimodal, reasoning, tool calling, ...)
# - Dùng để:
#   + Tự động quyết định chiến lược (summarize khi context nhỏ)
#   + Suy ra structured output strategy
#   + Chặn input không phù hợp (ảnh, audio, token quá lớn)
# - Lưu ý: feature beta, format có thể thay đổi

# --- MULTIMODAL ---
# - Model có thể nhận/trả: text, image, audio, video
# - Truyền dữ liệu qua content blocks
# - Hỗ trợ:
#   + Cross-provider standard format
#   + OpenAI chat format
#   + Provider-native format
# - Output có thể chứa nhiều block (text + image + ...)

# --- REASONING ---
# - Model có thể reasoning nhiều bước
# - Có thể:
#   + Stream reasoning output
#   + Lấy reasoning đầy đủ
#   + Điều chỉnh mức reasoning (low/high hoặc token budget)
# - Phụ thuộc từng provider

# --- LOCAL MODELS ---
# - Chạy model local để:
#   + Bảo mật dữ liệu
#   + Giảm chi phí cloud
#   + Dùng model custom
# - Ollama: lựa chọn phổ biến để chạy local

# --- PROMPT CACHING ---
# - Giảm latency & chi phí khi prompt lặp lại
# - Implicit caching: provider tự xử lý (OpenAI, Gemini)
# - Explicit caching: user chỉ định cache point
# - Chỉ kích hoạt khi vượt ngưỡng token tối thiểu
# - Thông tin cache nằm trong usage metadata

# --- SERVER-SIDE TOOL USE ---
# - Tool calling diễn ra hoàn toàn phía server (1 turn)
# - Không cần ToolMessage như client-side
# - Response chứa:
#   + server_tool_call
#   + server_tool_result
#   + text (có thể kèm citation)

# --- RATE LIMITING ---
# - Provider giới hạn số request / thời gian
# - Dùng rate_limiter khi init model để kiểm soát tốc độ

# --- BASE URL / PROXY ---
# - Có thể cấu hình base_url (API tương thích OpenAI)
# - Hỗ trợ proxy server cho môi trường enterprise

# --- LOG PROBABILITIES ---
# - Một số model trả về logprob từng token
# - Bật bằng: bind(logprobs=True)
# - Dùng cho phân tích xác suất, debugging

# --- TOKEN USAGE ---
# - Provider có thể trả về token usage
# - Theo dõi bằng:
#   + Callback handler
#   + Context manager
# - Quan trọng để kiểm soát chi phí production

# --- INVOCATION CONFIG ---
# - Truyền config runtime khi invoke:
#   + run_name
#   + tags
#   + metadata
#   + callbacks
# - Hữu ích cho logging, tracing, monitoring, LangSmith

# --- CONFIGURABLE MODELS ---
# - Cho phép chọn model runtime (dynamic)
# - Có thể đổi model/provider ngay lúc invoke
# - Quan trọng cho middleware & multi-provider setup

