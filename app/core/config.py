from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Chat MP API"
    environment: str = "development"

    telegram_bot_token: str = ""
    telegram_webhook_secret: str = "dev-secret"

    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    database_url: str = "postgresql://chatmp:chatmp@localhost:5432/chatmp"
    rag_enabled: bool = True
    rag_top_k: int = 5
    rag_fail_open: bool = True
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_dimension: int = 384

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
