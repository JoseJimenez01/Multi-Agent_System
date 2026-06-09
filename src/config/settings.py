from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # PostgreSQL
    database_url: str = "postgresql://mas_user:mas_pass@localhost:5432/mas_db"

    # Qdrant
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

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
