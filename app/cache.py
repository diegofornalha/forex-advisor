"""Camada de cache com Redis e fallback em memória."""

import json
import logging
import time
from datetime import datetime
from typing import Any

import redis.asyncio as redis

from .config import settings

logger = logging.getLogger(__name__)

# Cliente Redis global (singleton)
_redis_client: redis.Redis | None = None

# Cache em memória como fallback
_memory_cache: dict[str, tuple[dict, float]] = {}


async def get_redis() -> redis.Redis | None:
    """Retorna cliente Redis (singleton).

    Returns:
        Cliente Redis ou None se não conseguir conectar
    """
    global _redis_client

    if _redis_client is None:
        try:
            _redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            # Testa conexão
            await _redis_client.ping()
            logger.info("Conectado ao Redis")
        except Exception as e:
            logger.warning(f"Redis não disponível: {e}. Usando cache em memória.")
            _redis_client = None

    return _redis_client


async def get_cached(key: str) -> dict | None:
    """Busca valor do cache (Redis ou memória).

    Args:
        key: Chave do cache

    Returns:
        Valor deserializado ou None se não encontrado
    """
    # Tenta Redis primeiro
    try:
        client = await get_redis()
        if client:
            value = await client.get(key)
            if value:
                logger.debug(f"Cache HIT (Redis): {key}")
                return json.loads(value)
    except Exception as e:
        logger.warning(f"Erro ao ler Redis: {e}")

    # Fallback: memória
    if key in _memory_cache:
        value, expires_at = _memory_cache[key]
        if time.time() < expires_at:
            logger.debug(f"Cache HIT (memória): {key}")
            return value
        else:
            # Expirou
            del _memory_cache[key]
            logger.debug(f"Cache expirado (memória): {key}")

    logger.debug(f"Cache MISS: {key}")
    return None


async def set_cached(
    key: str,
    value: dict,
    ttl: int | None = None,
) -> bool:
    """Salva valor no cache (Redis e memória).

    Args:
        key: Chave do cache
        value: Valor para cachear (dict)
        ttl: Tempo de vida em segundos (default: settings.cache_ttl_insight)

    Returns:
        True se salvou com sucesso
    """
    ttl = ttl or settings.cache_ttl_insight

    # Adiciona timestamp de cache
    value["_cached_at"] = datetime.utcnow().isoformat()

    # Serializa para JSON
    json_value = json.dumps(value, default=str)

    # Salva no Redis
    try:
        client = await get_redis()
        if client:
            await client.setex(key, ttl, json_value)
            logger.debug(f"Cache SET (Redis): {key} TTL={ttl}s")
    except Exception as e:
        logger.warning(f"Erro ao salvar no Redis: {e}")

    # Sempre salva na memória também (backup)
    _memory_cache[key] = (value, time.time() + ttl)
    logger.debug(f"Cache SET (memória): {key} TTL={ttl}s")

    return True


async def delete_cached(key: str) -> bool:
    """Remove valor do cache.

    Args:
        key: Chave a remover

    Returns:
        True se removeu
    """
    # Remove do Redis
    try:
        client = await get_redis()
        if client:
            await client.delete(key)
    except Exception as e:
        logger.warning(f"Erro ao deletar do Redis: {e}")

    # Remove da memória
    if key in _memory_cache:
        del _memory_cache[key]

    return True


async def clear_forex_cache() -> int:
    """Limpa todas as chaves forex:* do cache.

    Returns:
        Número de chaves removidas
    """
    count = 0

    # Limpa do Redis
    try:
        client = await get_redis()
        if client:
            keys = await client.keys("forex:*")
            if keys:
                count = await client.delete(*keys)
    except Exception as e:
        logger.warning(f"Erro ao limpar Redis: {e}")

    # Limpa da memória
    memory_keys = [k for k in _memory_cache if k.startswith("forex:")]
    for k in memory_keys:
        del _memory_cache[k]
        count += 1

    return count


async def get_cache_status() -> dict[str, Any]:
    """Retorna status do cache para health check.

    Returns:
        Dict com informações de status
    """
    redis_status = "disconnected"
    redis_keys = 0

    try:
        client = await get_redis()
        if client:
            await client.ping()
            redis_status = "connected"
            keys = await client.keys("forex:*")
            redis_keys = len(keys) if keys else 0
    except Exception:
        pass

    return {
        "redis": redis_status,
        "redis_keys": redis_keys,
        "memory_keys": len(_memory_cache),
    }
