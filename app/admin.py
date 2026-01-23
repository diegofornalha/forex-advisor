"""Admin endpoints for debugging and monitoring."""

import json
import logging
from typing import Any

from fastapi import APIRouter

from .cache import get_cached, get_cache_status, list_sessions
from .llm_router import get_router_stats

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])

# Global RAG instance reference (set from main.py)
_rag_instance = None


def set_rag_instance(rag):
    """Set RAG instance for stats access."""
    global _rag_instance
    _rag_instance = rag


@router.get("/sessions")
async def get_sessions() -> dict[str, Any]:
    """List all chat sessions.

    Returns summary of all chat and docs sessions.
    """
    sessions = await list_sessions()

    return {
        "total": len(sessions),
        "sessions": sessions,
    }


@router.get("/sessions/{session_id}")
async def get_session_detail(session_id: str) -> dict[str, Any]:
    """Get detailed session information.

    Args:
        session_id: UUID of the session

    Returns:
        Full session data with messages and stats
    """
    # Try both chat types
    data = await get_cached(f"chat:session:{session_id}")
    session_type = "chat"

    if not data:
        data = await get_cached(f"docs_chat:session:{session_id}")
        session_type = "docs"

    if not data:
        return {"error": "Session not found", "session_id": session_id}

    messages = data.get("messages", [])

    # Calculate context size
    total_chars = sum(len(m.get("content", "")) for m in messages)
    estimated_tokens = total_chars // 4  # Rough estimate: 4 chars per token

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
        }
    }


@router.get("/stats")
async def get_stats() -> dict[str, Any]:
    """Get consolidated stats for admin panel.

    Returns:
        LLM, RAG, and cache statistics
    """
    # LLM stats
    llm_stats = get_router_stats()

    # Cache stats
    cache_stats = await get_cache_status()

    # RAG stats
    rag_stats = {}
    if _rag_instance:
        try:
            rag_stats = _rag_instance.get_detailed_stats()
        except Exception as e:
            logger.warning(f"Error getting RAG stats: {e}")
            rag_stats = {"error": str(e)}
    else:
        rag_stats = {"status": "not_initialized"}

    # Sessions summary
    sessions = await list_sessions()
    sessions_summary = {
        "total": len(sessions),
        "chat": len([s for s in sessions if s["type"] == "chat"]),
        "docs": len([s for s in sessions if s["type"] == "docs"]),
    }

    return {
        "llm": llm_stats,
        "cache": cache_stats,
        "rag": rag_stats,
        "sessions": sessions_summary,
    }
