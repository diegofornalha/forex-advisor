# Plano 04: Cache Redis

## Objetivo
Criar camada de cache com Redis para performance em produção.

## Arquivo
`app/cache.py`

## Implementação

```python
"""Cache layer com Redis."""

import json
from typing import Any
from datetime import datetime

import redis.asyncio as redis

from .config import settings

# Cliente Redis global
_redis_client: redis.Redis | None = None


async def get_redis() -> redis.Redis:
    """Retorna cliente Redis (singleton)."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
    return _redis_client


async def get_cached(key: str) -> dict | None:
    """Busca valor do cache.

    Args:
        key: Chave do cache

    Returns:
        Valor deserializado ou None
    """
    try:
        client = await get_redis()
        value = await client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception:
        # Cache miss silencioso em caso de erro
        return None


async def set_cached(key: str, value: dict, ttl: int = 3600) -> bool:
    """Salva valor no cache.

    Args:
        key: Chave do cache
        value: Valor para cachear (dict)
        ttl: Tempo de vida em segundos (default 1h)

    Returns:
        True se salvou, False se erro
    """
    try:
        client = await get_redis()
        # Adiciona timestamp
        value["_cached_at"] = datetime.utcnow().isoformat()
        await client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception:
        return False


async def delete_cached(key: str) -> bool:
    """Remove valor do cache."""
    try:
        client = await get_redis()
        await client.delete(key)
        return True
    except Exception:
        return False


async def clear_all() -> int:
    """Limpa todo o cache (cuidado!)."""
    try:
        client = await get_redis()
        keys = await client.keys("forex:*")
        if keys:
            return await client.delete(*keys)
        return 0
    except Exception:
        return 0
```

## Fallback sem Redis

Para rodar localmente sem Redis, criar fallback em memória:

```python
# Cache em memória como fallback
_memory_cache: dict[str, tuple[dict, float]] = {}

async def get_cached(key: str) -> dict | None:
    """Busca com fallback para memória."""
    # Tenta Redis primeiro
    try:
        client = await get_redis()
        value = await client.get(key)
        if value:
            return json.loads(value)
    except Exception:
        pass

    # Fallback: memória
    if key in _memory_cache:
        value, expires_at = _memory_cache[key]
        if time.time() < expires_at:
            return value
        del _memory_cache[key]

    return None


async def set_cached(key: str, value: dict, ttl: int = 3600) -> bool:
    """Salva com fallback para memória."""
    try:
        client = await get_redis()
        await client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception:
        # Fallback: memória
        _memory_cache[key] = (value, time.time() + ttl)
        return True
```

## Estratégia de Cache

| Dado | TTL | Chave |
|------|-----|-------|
| Insight completo | 1 hora | `forex:usdbrl:latest` |
| Classificação técnica | 4 horas | `forex:usdbrl:technical` |
| Notícias indexadas | 24 horas | `forex:news:indexed_at` |

## Configuração

```env
# .env
REDIS_URL=redis://localhost:6379
CACHE_TTL=3600
```

## Docker Compose (Redis)

```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## Métricas de Cache

```python
async def cache_stats() -> dict:
    """Retorna estatísticas do cache."""
    try:
        client = await get_redis()
        info = await client.info("stats")
        keys = await client.keys("forex:*")
        return {
            "total_keys": len(keys),
            "hits": info.get("keyspace_hits", 0),
            "misses": info.get("keyspace_misses", 0),
            "hit_rate": info.get("keyspace_hits", 0) /
                       max(1, info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0))
        }
    except Exception:
        return {"error": "Redis não disponível"}
```

## Dependências
```
redis>=5.0.0
```

## Critérios de Sucesso
- [ ] get_cached funcionando
- [ ] set_cached com TTL
- [ ] Fallback em memória funcionando
- [ ] Header X-Cache: HIT/MISS
- [ ] Stats de cache disponíveis
