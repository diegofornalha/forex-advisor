"""LLM client - Minimax."""

import logging
from typing import Any

from litellm import acompletion

from .config import settings

logger = logging.getLogger(__name__)


async def call_llm(messages: list[dict[str, str]], stream: bool = False) -> Any:
    """Call Minimax LLM.

    Args:
        messages: List of message dicts (role, content)
        stream: Whether to stream response

    Returns:
        Generated text content (or async generator if stream=True)

    Raises:
        ValueError: If Minimax not configured
        Exception: If LLM call fails
    """
    if not settings.minimax_token:
        raise ValueError(
            "Minimax não configurado. Configure MINIMAX_TOKEN no .env"
        )

    try:
        response = await acompletion(
            model=settings.minimax_model,
            messages=messages,
            max_tokens=settings.llm_max_tokens,
            timeout=settings.llm_timeout,
            api_key=settings.minimax_token,
            api_base=settings.minimax_base_url,
            stream=stream,
        )

        if stream:
            return response

        content = response.choices[0].message.content
        if content:
            return content.strip()
        raise ValueError("Resposta vazia do LLM")

    except Exception as e:
        logger.error(f"Erro no Minimax: {e}")
        raise


def get_router():
    """Get LLM router (compatibility layer for chat.py).

    Returns mock router that uses call_llm internally.
    """
    class MinimaxRouter:
        async def acompletion(self, messages: list, max_tokens: int, stream: bool = False):
            return await acompletion(
                model=settings.minimax_model,
                messages=messages,
                max_tokens=max_tokens,
                timeout=settings.llm_timeout,
                api_key=settings.minimax_token,
                api_base=settings.minimax_base_url,
                stream=stream,
            )

    if not settings.minimax_token:
        return None
    return MinimaxRouter()


def get_router_stats() -> dict[str, Any]:
    """Get LLM status for health checks.

    Returns:
        Dict with status information
    """
    if not settings.minimax_token:
        return {"status": "disabled", "reason": "no_minimax_token"}

    return {
        "status": "active",
        "provider": "minimax",
        "model": settings.minimax_model,
    }
