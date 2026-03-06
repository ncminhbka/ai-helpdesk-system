"""
Application configuration using pydantic-settings.
All environment variables used by the application are declared here.
Values are loaded from the .env file (or system environment), with safe defaults where appropriate.
"""
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    '''
    BaseSettings sẽ:
    - Đọc các biến môi trường từ file .env
    - Áp dụng các giá trị mặc định nếu không có trong .env
    - Validate kiểu dữ liệu của các biến
    '''

    model_config = SettingsConfigDict(
        # Look for .env first in current dir, then in parent dir (root)
        env_file=(".env", "../.env"),
        env_ignore_empty=True,
        extra="ignore",
    )
    # Các biến môi trường không được định nghĩa ở dưới đây sẽ được bỏ qua
    # ── Application ────────────────────────────────
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FPT HelpDesk"

    # ── Database credentials (required, set in .env) ─
    DB_USER: str # Tên người dùng database
    DB_PASSWORD: str # Mật khẩu database
    DB_HOST: str # Địa chỉ host database
    DB_PORT: str # Cổng kết nối database
    DB_NAME: str # Tên database

    @computed_field # computed_field giúp tạo ra một thuộc tính tính toán từ các thuộc tính khác (ghép chuỗi)
    @property
    def DATABASE_URL(self) -> str: # Trả về URL kết nối database
        """Async URL for SQLAlchemy (asyncpg driver)."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field
    @property
    def CHECKPOINT_POSTGRES_URL(self) -> str: # Trả về URL kết nối database cho LangGraph state
        """Sync URL for LangGraph PostgresSaver (psycopg driver)."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # ── Security (required, set in .env) ────────────
    SECRET_KEY: str # Secret key để mã hóa token
    ALGORITHM: str = "HS256" # Thuật toán mã hóa token
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── AI / LLM keys (required, set in .env) ───────
    OPENAI_API_KEY: str # API key cho OpenAI
    TAVILY_API_KEY: str # API key cho Tavily

    # ── RAG / Vector store ───────────────────────────
    DOCS_DIR: str = "../docs"

    # ── HITL (Human-in-the-Loop) ─────────────────────
    ENABLE_HITL: bool = True

    # ── LangSmith (optional tracing) ─────────────────
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "FPTHelpDesk"


settings = Settings() # Tạo instance của class Settings singleton
