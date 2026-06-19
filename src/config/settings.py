from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path
import os

_ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"


class Settings(BaseSettings):
    # PostgreSQL
    database_url: str = "postgresql://postgres@localhost:5434/mas_db"

    # Qdrant
    qdrant_version: str = "1.12.0"
    qdrant_url: str = "http://localhost:6333"
    qdrant_grpc_port: int = 6334

    # Langfuse
    langfuse_host: str = "http://localhost:3000"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""

    # Anthropic Claude 
    anthropic_api_key: str = ""
    claude_model_primary: str = "claude-sonnet-4-6"  
    claude_model_fast: str = "claude-haiku-4-5"  

    # OpenAI
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def configure_langfuse_env() -> None:
    settings = get_settings()
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        os.environ["LANGFUSE_TRACING_ENABLED"] = "true"
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host
        os.environ["LANGFUSE_BASE_URL"] = settings.langfuse_host
    else:
        os.environ["LANGFUSE_TRACING_ENABLED"] = "false"


configure_langfuse_env()
