"""
Application configuration using pydantic-settings.
All environment variables used by the application are declared here.
Values are loaded from the .env file (or system environment), with safe defaults where appropriate.
"""
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # ── Application ────────────────────────────────
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FPT HelpDesk"

    # ── Database credentials (required, set in .env) ─
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        """Async URL for SQLAlchemy (asyncpg driver)."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field
    @property
    def CHECKPOINT_POSTGRES_URL(self) -> str:
        """Sync URL for LangGraph PostgresSaver (psycopg driver)."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # ── Security (required, set in .env) ────────────
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # ── AI / LLM keys (required, set in .env) ───────
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str

    # ── RAG / Vector store ───────────────────────────
    DOCS_DIR: str = "../docs"
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # ── HITL (Human-in-the-Loop) ─────────────────────
    ENABLE_HITL: bool = True

    # ── LangSmith (optional tracing) ─────────────────
    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "FPTHelpDesk"


settings = Settings()
