"""
MADERA MCP - Configuration
Pydantic Settings pour gestion centralisée des configs
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
import os


class Settings(BaseSettings):
    """Configuration globale MADERA"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # ==================== APPLICATION ====================
    APP_NAME: str = "MADERA MCP Tools"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True

    # ==================== DATABASE ====================
    DATABASE_URL: str = "postgresql+asyncpg://madera_user:madera_pass@localhost/madera_db"
    DATABASE_URL_SYNC: str = "postgresql://madera_user:madera_pass@localhost/madera_db"  # For Alembic
    DB_ECHO: bool = False  # SQL logging
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

    # ==================== REDIS ====================
    REDIS_URL: str = "redis://localhost:6379/0"

    # ==================== AI PROVIDERS ====================
    # Gemini (default)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash-thinking-exp"

    # Claude (option)
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4.5"

    # OpenAI (option)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"

    # Active provider
    TRAINING_AI_PROVIDER: Literal["gemini", "claude", "openai"] = "gemini"

    # ==================== MINIO STORAGE ====================
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "leclasseur"
    MINIO_SECURE: bool = False

    # ==================== LEARNING ====================
    LEARNING_ENABLED: bool = True
    LOW_CONFIDENCE_THRESHOLD: float = 0.75
    LOG_TOOL_EXECUTIONS: bool = True

    # ==================== MCP SERVER ====================
    MCP_SERVER_PORT: int = 8003

    # ==================== WEB UI ====================
    WEB_UI_PORT: int = 8004
    WEB_UI_HOST: str = "0.0.0.0"
    CORS_ORIGINS: str = "http://localhost:8004,http://localhost:3000,http://192.168.2.71:8004"

    # ==================== CELERY ====================
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    CELERY_TASK_TRACK_STARTED: bool = True
    CELERY_TASK_TIME_LIMIT: int = 300  # 5 minutes

    # ==================== TESSERACT ====================
    TESSERACT_CMD: str = "/usr/bin/tesseract"  # Path to tesseract binary

    # ==================== LOGGING ====================
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"

    @property
    def active_ai_config(self) -> dict:
        """Return config for active AI provider"""
        if self.TRAINING_AI_PROVIDER == "gemini":
            return {
                "api_key": self.GEMINI_API_KEY,
                "model": self.GEMINI_MODEL
            }
        elif self.TRAINING_AI_PROVIDER == "claude":
            return {
                "api_key": self.ANTHROPIC_API_KEY,
                "model": self.CLAUDE_MODEL
            }
        elif self.TRAINING_AI_PROVIDER == "openai":
            return {
                "api_key": self.OPENAI_API_KEY,
                "model": self.OPENAI_MODEL
            }
        raise ValueError(f"Unknown AI provider: {self.TRAINING_AI_PROVIDER}")


# Global settings instance
settings = Settings()
