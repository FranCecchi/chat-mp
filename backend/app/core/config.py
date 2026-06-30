from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Chat Movimientos de Pensamiento API"
    environment: str = "development"

    # Provider & Model selection (configurable from .env)
    llm_provider: str = "gemini"  # "gemini" or "deepseek"
    llm_model: str = "gemini-1.5-flash"

    # Provider configuration
    gemini_api_key: str = ""
    
    deepseek_api_key: str = ""
    deepseek_api_base: str = "https://api.deepseek.com/v1"
    deepseek_thinking: bool = True

    # Teacher dashboard
    teacher_password: str = ""
    db_path: str = "chat_mp.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
