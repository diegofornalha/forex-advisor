"""Configurações da aplicação usando Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação carregadas de variáveis de ambiente."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API
    app_name: str = "Forex Advisor API"
    debug: bool = False
    api_version: str = "v1"

    # Dados de mercado
    symbol: str = "USDBRL=X"
    period: str = "5y"

    # Cache
    redis_url: str = "redis://localhost:6379"
    cache_ttl_insight: int = 3600  # 1 hora para insight completo
    cache_ttl_technical: int = 14400  # 4 horas para análise técnica
    cache_ttl_news: int = 86400  # 24 horas para notícias

    # LLM
    anthropic_api_key: str = ""
    llm_model: str = "claude-3-haiku-20240307"
    llm_max_tokens: int = 500

    # RAG
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    news_query: str = "dólar real câmbio brasil"
    news_limit: int = 10


@lru_cache
def get_settings() -> Settings:
    """Retorna instância cacheada das configurações."""
    return Settings()


settings = get_settings()
