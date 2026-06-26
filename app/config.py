from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    port: int = 8000
    log_level: str = "info"
    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.1-8b-instruct"
    openrouter_fallback_model: str = "google/gemini-2.0-flash-001"
    openrouter_app_name: str = "QueueStorm Investigator"
    openrouter_app_url: str = "http://localhost:8000"
    llm_enabled: bool = True
    llm_confidence_threshold: float = 0.7
    llm_timeout_seconds: float = 12.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
