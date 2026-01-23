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
    debug: bool = False

    # Market data
    symbol: str = "USDBRL=X"
    period: str = "5y"

    # Cache
    redis_url: str = "redis://localhost:6379"
    cache_ttl_insight: int = 3600  # 1 hour for full insight
    cache_ttl_technical: int = 14400  # 4 hours for technical only

    # LLM - Minimax (primary)
    llm_timeout: int = 30
    llm_max_tokens: int = 800
    minimax_token: str = ""
    minimax_base_url: str = "https://api.minimax.io/anthropic"
    minimax_model: str = "anthropic/minimax-m2"

    # LLM - Vertex AI (fallback 1)
    vertex_api_key: str = ""
    vertex_model: str = "vertex_ai/gemini-pro"

    # LLM - Anthropic (fallback 2)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-haiku-20240307"

    # Rate limiting
    rate_limit_requests: int = 100  # requests per minute
    rate_limit_window: int = 60  # window in seconds

    # E2B Sandbox (execução isolada de código de análise)
    e2b_api_key: str = ""
    e2b_timeout: int = 180  # segundos

    # News
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

    # Docs Chat - Documentation interactive chat
    docs_chat_enabled: bool = True
    docs_chat_session_ttl: int = 3600  # 1 hour
    docs_chat_max_history: int = 20  # max messages per session


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance (singleton pattern)."""
    return Settings()


settings = get_settings()
