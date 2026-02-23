"""
Application configuration using pydantic-settings.
Loads from .env file with sensible defaults.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FPT HelpDesk"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./fpt_helpdesk.db"

    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour

    # HITL (Human-in-the-Loop)
    ENABLE_HITL: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )


settings = Settings()
