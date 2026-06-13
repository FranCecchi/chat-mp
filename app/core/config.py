from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Chat MP API"
    environment: str = "development"

    google_genai_api_key: str = ""
    google_genai_model: str = "gemini-3.1-flash-lite"
    google_genai_default_max_output_tokens: int = 600
    openwebui_api_key: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
