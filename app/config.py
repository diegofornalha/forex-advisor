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


    # LLM - POC usa apenas Minimax (v1: adicionar Vertex AI e Anthropic fallbacks)
    llm_timeout: int = 30
    llm_max_tokens: int = 800
    minimax_token: str = ""
    minimax_base_url: str = "https://api.minimax.io/anthropic"
    minimax_model: str = "anthropic/minimax-m2"

    # E2B Sandbox (execução isolada de código de análise)
    e2b_api_key: str = ""
    e2b_timeout: int = 180  # segundos

    # News
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    news_query: str = "dólar real câmbio brasil"
    news_limit: int = 10

    # Chat with E2B
    chat_enabled: bool = True
    chat_session_ttl: int = 3600  # 1 hour
    chat_max_history: int = 50  # max messages per session
    chat_max_code_length: int = 5000  # max chars of code
    chat_allowed_imports: str = "pandas,numpy,json,math,statistics"  # whitelist

    # RAG - Retrieval Augmented Generation
    rag_db_path: str = "./data/rag.db"  # SQLite-vec database
    rag_top_k: int = 3  # Number of results to retrieve
    rag_min_similarity: float = 0.3  # Minimum similarity threshold


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance (singleton pattern)."""
    return Settings()


settings = get_settings()
