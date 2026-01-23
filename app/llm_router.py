"""LLM Router with fallback chain and circuit breaker.

Providers: Minimax → Vertex AI → Anthropic
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

from litellm import acompletion

from .config import settings

logger = logging.getLogger(__name__)


@dataclass
class CircuitBreaker:
    """Simple circuit breaker for LLM providers."""

    name: str
    failure_threshold: int = 3
    recovery_timeout: int = 60  # seconds
    _failures: int = field(default=0, repr=False)
    _last_failure: float = field(default=0, repr=False)
    _state: str = field(default="closed", repr=False)

    def record_failure(self):
        """Record a failure and potentially open the circuit."""
        self._failures += 1
        self._last_failure = time.time()

        if self._failures >= self.failure_threshold:
            self._state = "open"
            logger.warning(f"Circuit breaker OPEN for {self.name}")

    def record_success(self):
        """Record a success and reset failures."""
        self._failures = 0
        self._state = "closed"

    def is_available(self) -> bool:
        """Check if the circuit is closed (available)."""
        if self._state == "closed":
            return True

        # Check if recovery timeout has passed
        if time.time() - self._last_failure > self.recovery_timeout:
            self._state = "half-open"
            logger.info(f"Circuit breaker HALF-OPEN for {self.name}")
            return True

        return False

    def get_status(self) -> dict:
        """Get circuit breaker status."""
        return {
            "state": self._state,
            "failures": self._failures,
            "last_failure": self._last_failure if self._last_failure else None,
        }


@dataclass
class LLMProvider:
    """LLM Provider configuration."""

    name: str
    model: str
    api_key: str
    api_base: str | None = None
    circuit_breaker: CircuitBreaker = field(default_factory=lambda: CircuitBreaker("default"))

    def is_configured(self) -> bool:
        """Check if provider is configured."""
        return bool(self.api_key)


# Global providers and circuit breakers
_providers: list[LLMProvider] = []
_initialized = False


def _sanitize_error(error: Exception) -> str:
    """Remove sensitive data from error messages."""
    error_str = str(error)
    # Remove API keys from error messages
    sensitive_patterns = [
        settings.minimax_token,
        settings.vertex_api_key if hasattr(settings, 'vertex_api_key') else None,
        settings.anthropic_api_key if hasattr(settings, 'anthropic_api_key') else None,
    ]
    for pattern in sensitive_patterns:
        if pattern:
            error_str = error_str.replace(pattern, "[REDACTED]")
    return error_str


def _init_providers():
    """Initialize LLM providers with circuit breakers."""
    global _providers, _initialized

    if _initialized:
        return

    _providers = []

    # Minimax (primary)
    if settings.minimax_token:
        _providers.append(LLMProvider(
            name="minimax",
            model=settings.minimax_model,
            api_key=settings.minimax_token,
            api_base=settings.minimax_base_url,
            circuit_breaker=CircuitBreaker("minimax"),
        ))

    # Vertex AI (fallback 1)
    vertex_key = getattr(settings, 'vertex_api_key', None) or ""
    if vertex_key:
        _providers.append(LLMProvider(
            name="vertex",
            model=getattr(settings, 'vertex_model', 'vertex_ai/gemini-pro'),
            api_key=vertex_key,
            circuit_breaker=CircuitBreaker("vertex"),
        ))

    # Anthropic (fallback 2)
    anthropic_key = getattr(settings, 'anthropic_api_key', None) or ""
    if anthropic_key:
        _providers.append(LLMProvider(
            name="anthropic",
            model=getattr(settings, 'anthropic_model', 'claude-3-haiku-20240307'),
            api_key=anthropic_key,
            circuit_breaker=CircuitBreaker("anthropic"),
        ))

    _initialized = True
    logger.info(f"LLM Router initialized with {len(_providers)} providers: {[p.name for p in _providers]}")


async def _call_provider(provider: LLMProvider, messages: list, max_tokens: int, stream: bool) -> Any:
    """Call a specific LLM provider."""
    kwargs = {
        "model": provider.model,
        "messages": messages,
        "max_tokens": max_tokens,
        "timeout": settings.llm_timeout,
        "api_key": provider.api_key,
        "stream": stream,
    }

    if provider.api_base:
        kwargs["api_base"] = provider.api_base

    return await acompletion(**kwargs)


async def call_llm(messages: list[dict[str, str]], stream: bool = False, max_tokens: int | None = None) -> Any:
    """Call LLM with automatic fallback.

    Args:
        messages: List of message dicts (role, content)
        stream: Whether to stream response
        max_tokens: Max tokens (uses settings default if not provided)

    Returns:
        Generated text content (or async generator if stream=True)

    Raises:
        ValueError: If no providers configured
        Exception: If all providers fail
    """
    _init_providers()

    if not _providers:
        raise ValueError("Nenhum LLM configurado. Configure pelo menos MINIMAX_TOKEN no .env")

    tokens = max_tokens or settings.llm_max_tokens
    last_error = None
    used_provider = None

    for provider in _providers:
        if not provider.circuit_breaker.is_available():
            logger.debug(f"Skipping {provider.name} - circuit breaker open")
            continue

        try:
            logger.debug(f"Trying provider: {provider.name}")
            response = await _call_provider(provider, messages, tokens, stream)

            provider.circuit_breaker.record_success()
            used_provider = provider.name

            if stream:
                return response

            content = response.choices[0].message.content
            if content:
                logger.info(f"LLM response from {provider.name}")
                return content.strip()

            raise ValueError("Resposta vazia do LLM")

        except Exception as e:
            provider.circuit_breaker.record_failure()
            last_error = e
            logger.warning(f"Provider {provider.name} failed: {_sanitize_error(e)}")
            continue

    # All providers failed
    error_msg = f"Todos os LLMs falharam. Último erro: {_sanitize_error(last_error)}"
    logger.error(error_msg)
    raise Exception(error_msg)


def get_router():
    """Get LLM router (compatibility layer for chat.py).

    Returns mock router that uses call_llm internally.
    """
    _init_providers()

    class FallbackRouter:
        async def acompletion(self, messages: list, max_tokens: int, stream: bool = False):
            # Use call_llm which handles fallback
            if stream:
                return await call_llm(messages, stream=True, max_tokens=max_tokens)

            # For non-streaming, wrap in litellm-compatible format
            _content = await call_llm(messages, stream=False, max_tokens=max_tokens)

            # Return litellm-compatible response
            class MockChoice:
                class Message:
                    content = _content
                message = Message()
                delta = Message()

            class MockResponse:
                choices = [MockChoice()]

            return MockResponse()

    if not _providers:
        return None

    return FallbackRouter()


def get_router_stats() -> dict[str, Any]:
    """Get LLM status for health checks.

    Returns:
        Dict with status information for all providers
    """
    _init_providers()

    if not _providers:
        return {"status": "disabled", "reason": "no_providers_configured"}

    providers_status = {}
    for provider in _providers:
        providers_status[provider.name] = {
            "configured": provider.is_configured(),
            "model": provider.model,
            "circuit_breaker": provider.circuit_breaker.get_status(),
        }

    active_providers = [p.name for p in _providers if p.circuit_breaker.is_available()]

    return {
        "status": "active" if active_providers else "degraded",
        "active_providers": active_providers,
        "total_providers": len(_providers),
        "providers": providers_status,
    }


def reset_circuit_breakers():
    """Reset all circuit breakers (for testing)."""
    for provider in _providers:
        provider.circuit_breaker._failures = 0
        provider.circuit_breaker._state = "closed"
        provider.circuit_breaker._last_failure = 0
