"""📊 Admin Panel - Sistema de Monitoramento (SEM LLM!)

IMPORTANTE: O admin NUNCA ativa o LLM!
É apenas um painel de observabilidade que lê status via HTTP/REST.

Fluxo do Admin:
1. Frontend carrega /admin
2. useAdminStats() → GET /admin/stats
3. Backend lê status (NÃO gera texto)
4. Exibe métricas em tempo real

Diferencial: Auto-refresh a cada 10-30 segundos
"""

import json
import logging
from typing import Any
from datetime import datetime

from fastapi import APIRouter

from .cache import get_cached, get_cache_status, list_sessions, delete_session
from .llm_router import get_router_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

# Global RAG instance reference (set from main.py)
_rag_instance = None


def set_rag_instance(rag):
    """Set RAG instance for stats access."""
    global _rag_instance
    _rag_instance = rag
    logger.info("📊 Admin: RAG instance configured for monitoring")


@router.get("/sessions")
async def get_sessions() -> dict[str, Any]:
    """📊 LISTA SESSÕES - HTTP GET (SEM LLM!)

    ⚠️ IMPORTANTE: Este endpoint NÃO ativa LLM!
    Apenas lê dados do cache (Redis/Memory) e retorna via HTTP.

    Fluxo:
    1. Frontend: useAdminSessions() → GET /admin/sessions
    2. Backend: Lê do cache (get_cached)
    3. Retorna lista JSON
    4. Frontend exibe em tabela
    5. Auto-refresh a cada 30s

    Returns:
        Lista de sessões com metadados (SEM mensagens completas)
    """
    logger.info("📊 [ADMIN] GET /admin/sessions - Reading from cache (NO LLM ACTIVATION)")

    start_time = datetime.now()
    sessions = await list_sessions()
    duration_ms = (datetime.now() - start_time).total_seconds() * 1000

    # Log stats
    chat_count = len([s for s in sessions if s.get("type") == "chat"])
    docs_count = len([s for s in sessions if s.get("type") == "docs"])

    logger.info(
        f"📊 [ADMIN] Sessions stats: total={len(sessions)}, "
        f"chat={chat_count}, docs={docs_count}, "
        f"duration={duration_ms:.1f}ms"
    )

    return {
        "total": len(sessions),
        "sessions": sessions,
        "metadata": {
            "retrieved_at": datetime.utcnow().isoformat(),
            "duration_ms": duration_ms,
            "cache_source": "redis" if hasattr(get_cached, '__self__') else "memory",
            "llm_activated": False,  # ⚠️ SEMPRE FALSE!
        }
    }


@router.get("/sessions/{session_id}")
async def get_session_detail(session_id: str) -> dict[str, Any]:
    """📋 DETALHES DA SESSÃO - HTTP GET (SEM LLM!)

    ⚠️ IMPORTANTE: Este endpoint NÃO ativa LLM!
    Apenas busca dados específicos do cache e retorna via HTTP.

    Fluxo:
    1. Frontend: useAdminSessionDetail(id) → GET /admin/sessions/{id}
    2. Backend: get_cached(f"chat:session:{id}") ou f"docs_chat:session:{id}"
    3. Calcula estatísticas (chars, tokens estimados)
    4. Retorna JSON com mensagens + stats
    5. Frontend exibe em cards detalhados

    Args:
        session_id: UUID da sessão

    Returns:
        Dados completos da sessão com mensagens e estatísticas
    """
    logger.info(f"📋 [ADMIN] GET /admin/sessions/{session_id} - Reading cache (NO LLM ACTIVATION)")

    # Try both chat types
    data = await get_cached(f"chat:session:{session_id}")
    session_type = "chat"

    if not data:
        data = await get_cached(f"docs_chat:session:{session_id}")
        session_type = "docs"

    if not data:
        logger.warning(f"⚠️ [ADMIN] Session not found: {session_id}")
        return {"error": "Session not found", "session_id": session_id}

    messages = data.get("messages", [])

    # Calculate context size
    total_chars = sum(len(m.get("content", "")) for m in messages)
    estimated_tokens = total_chars // 4  # Rough estimate: 4 chars per token

    logger.info(
        f"📋 [ADMIN] Session {session_id} ({session_type}): "
        f"{len(messages)} msgs, {total_chars} chars, ~{estimated_tokens} tokens"
    )

    return {
        "session_id": session_id,
        "type": session_type,
        "messages": messages,
        "stats": {
            "messages_count": len(messages),
            "total_chars": total_chars,
            "estimated_tokens": estimated_tokens,
            "created_at": data.get("created_at"),
            "last_activity": data.get("last_activity"),
        },
        "metadata": {
            "retrieved_at": datetime.utcnow().isoformat(),
            "llm_activated": False,  # ⚠️ SEMPRE FALSE!
            "is_admin_view": True,
        }
    }


@router.delete("/sessions/{session_id}")
async def delete_session_endpoint(session_id: str) -> dict[str, Any]:
    """🗑️ DELETAR SESSÃO - HTTP DELETE (SEM LLM!)

    ⚠️ IMPORTANTE: Este endpoint NÃO ativa LLM!
    Apenas remove dados do cache.

    Fluxo:
    1. Frontend: useDeleteSession() → DELETE /admin/sessions/{id}
    2. Backend: delete_session(id) remove do cache
    3. Retorna status da remoção
    4. Frontend atualiza lista automaticamente

    Args:
        session_id: UUID da sessão para deletar

    Returns:
        Status da remoção (sucesso/erro)
    """
    logger.info(f"🗑️ [ADMIN] DELETE /admin/sessions/{session_id} - Removing from cache (NO LLM ACTIVATION)")

    result = await delete_session(session_id)

    if not result["deleted"]:
        logger.warning(f"⚠️ [ADMIN] Failed to delete session: {session_id}")
        return {"error": "Session not found", "session_id": session_id}

    logger.info(f"✅ [ADMIN] Session deleted successfully: {session_id}")
    return result


@router.get("/stats")
async def get_stats() -> dict[str, Any]:
    """📊 ESTATÍSTICAS CONSOLIDADAS - HTTP GET (SEM LLM!)

    ⚠️ IMPORTANTE: Este endpoint NÃO ativa LLM!
    Apenas lê status e métricas do sistema.

    🚀 FLUXO COMPLETO:
    1. Frontend: useAdminStats() → GET /admin/stats
    2. Backend: Coleta métricas de 4 fontes
    3. Retorna JSON consolidado
    4. Frontend exibe em dashboard
    5. Auto-refresh a cada 10s

    📋 FONTES DE DADOS:
    - LLM: get_router_stats() → Status (NÃO ativa geração!)
    - Cache: get_cache_status() → Redis/Memory
    - RAG: _rag_instance.get_detailed_stats() → DB stats
    - Sessions: list_sessions() → Contadores

    Returns:
        Estatísticas consolidadas de LLM, RAG, Cache e Sessions
    """
    logger.info("📊 [ADMIN] GET /admin/stats - Collecting system metrics (NO LLM ACTIVATION)")

    start_time = datetime.now()

    # ============================================================
    # 📊 LLM STATS - Só LÊ status, NÃO ativa geração!
    # ============================================================
    logger.debug("📊 [ADMIN] Reading LLM router stats...")
    llm_stats = get_router_stats()
    logger.debug(f"📊 [ADMIN] LLM stats: {llm_stats.get('status', 'unknown')} state")

    # ============================================================
    # 💾 CACHE STATS - Redis/Memory
    # ============================================================
    logger.debug("📊 [ADMIN] Reading cache status...")
    cache_stats = await get_cache_status()
    logger.debug(f"📊 [ADMIN] Cache stats: {cache_stats.get('redis', 'unknown')}")

    # ============================================================
    # 🗄️ RAG STATS - Database
    # ============================================================
    logger.debug("📊 [ADMIN] Reading RAG stats...")
    rag_stats = {}
    if _rag_instance:
        try:
            rag_stats = _rag_instance.get_detailed_stats()
            logger.debug(f"📊 [ADMIN] RAG stats: {rag_stats.get('total_docs', 0)} docs")
        except Exception as e:
            logger.warning(f"⚠️ [ADMIN] Error getting RAG stats: {e}")
            rag_stats = {"error": str(e)}
    else:
        logger.debug("📊 [ADMIN] RAG not initialized")
        rag_stats = {"status": "not_initialized"}

    # ============================================================
    # 💬 SESSIONS SUMMARY
    # ============================================================
    logger.debug("📊 [ADMIN] Counting sessions...")
    sessions = await list_sessions()
    sessions_summary = {
        "total": len(sessions),
        "chat": len([s for s in sessions if s.get("type") == "chat"]),
        "docs": len([s for s in sessions if s.get("type") == "docs"]),
    }
    logger.debug(f"📊 [ADMIN] Sessions: {sessions_summary}")

    duration_ms = (datetime.now() - start_time).total_seconds() * 1000

    # ============================================================
    # 📦 RETURN CONSOLIDATED STATS
    # ============================================================
    stats = {
        "llm": llm_stats,
        "cache": cache_stats,
        "rag": rag_stats,
        "sessions": sessions_summary,
        "metadata": {
            "retrieved_at": datetime.utcnow().isoformat(),
            "duration_ms": duration_ms,
            "llm_activated": False,  # ⚠️ SEMPRE FALSE!
            "refresh_interval": 10000,  # 10 segundos
            "is_admin_view": True,
        }
    }

    logger.info(
        f"📊 [ADMIN] Stats collected successfully in {duration_ms:.1f}ms - "
        f"LLM: {llm_stats.get('status', '?')}, "
        f"Cache: {cache_stats.get('redis', '?')}, "
        f"Sessions: {sessions_summary['total']}"
    )

    return stats
