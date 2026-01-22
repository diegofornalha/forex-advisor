"""Application configuration using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API
    app_name: str = "Forex Advisor API"
    debug: bool = False
    api_version: str = "v1"

    # Market data
    symbol: str = "USDBRL=X"
    period: str = "5y"

    # Cache
    redis_url: str = "redis://localhost:6379"
    cache_ttl_insight: int = 3600  # 1 hour for full insight
    cache_ttl_technical: int = 14400  # 4 hours for technical only
    cache_ttl_news: int = 86400  # 24 hours for news

    # LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-3-haiku-20240307"
    llm_max_tokens: int = 500

    # News
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    news_query: str = "dólar real câmbio brasil"
    news_limit: int = 10


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance (singleton pattern)."""
    return Settings()


settings = get_settings()
