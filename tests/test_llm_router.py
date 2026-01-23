"""Tests for LLM Router with circuit breaker and fallback."""

import pytest
import time

from app.llm_router import (
    CircuitBreaker,
    _sanitize_error,
    get_router_stats,
    reset_circuit_breakers,
)


class TestCircuitBreaker:
    """Tests for circuit breaker functionality."""

    def test_initial_state_closed(self):
        """Circuit should start closed."""
        cb = CircuitBreaker("test")
        assert cb.is_available() is True
        assert cb._state == "closed"

    def test_opens_after_threshold_failures(self):
        """Circuit should open after failure threshold."""
        cb = CircuitBreaker("test", failure_threshold=3)

        cb.record_failure()
        assert cb.is_available() is True

        cb.record_failure()
        assert cb.is_available() is True

        cb.record_failure()
        assert cb.is_available() is False
        assert cb._state == "open"

    def test_success_resets_failures(self):
        """Success should reset failure count."""
        cb = CircuitBreaker("test", failure_threshold=3)

        cb.record_failure()
        cb.record_failure()
        cb.record_success()

        assert cb._failures == 0
        assert cb._state == "closed"

    def test_half_open_after_recovery_timeout(self):
        """Circuit should become half-open after timeout."""
        cb = CircuitBreaker("test", failure_threshold=1, recovery_timeout=1)

        cb.record_failure()
        assert cb.is_available() is False

        # Wait for recovery
        time.sleep(1.1)

        assert cb.is_available() is True
        assert cb._state == "half-open"

    def test_get_status(self):
        """Should return status dict."""
        cb = CircuitBreaker("test")
        status = cb.get_status()

        assert "state" in status
        assert "failures" in status
        assert "last_failure" in status


class TestErrorSanitization:
    """Tests for error message sanitization."""

    def test_sanitizes_api_key(self, monkeypatch):
        """Should redact API keys from error messages."""
        monkeypatch.setenv("MINIMAX_TOKEN", "secret-api-key-12345")

        # Reimport to get new settings
        from app.config import Settings
        settings = Settings()

        # Mock the module-level settings
        import app.llm_router as router
        original_settings = router.settings
        router.settings = settings

        try:
            error = Exception("Failed with key: secret-api-key-12345")
            sanitized = _sanitize_error(error)

            assert "secret-api-key-12345" not in sanitized
            assert "[REDACTED]" in sanitized
        finally:
            router.settings = original_settings

    def test_preserves_safe_error_messages(self):
        """Should preserve error messages without sensitive data."""
        error = Exception("Connection timeout after 30 seconds")
        sanitized = _sanitize_error(error)

        assert "Connection timeout" in sanitized
        assert "30 seconds" in sanitized


class TestRouterStats:
    """Tests for router status endpoint."""

    def test_returns_dict(self):
        """Should return a dict."""
        stats = get_router_stats()
        assert isinstance(stats, dict)

    def test_has_status_field(self):
        """Should have status field."""
        stats = get_router_stats()
        assert "status" in stats

    def test_status_values(self):
        """Status should be valid value."""
        stats = get_router_stats()
        assert stats["status"] in ["active", "disabled", "degraded"]


class TestResetCircuitBreakers:
    """Tests for circuit breaker reset function."""

    def test_reset_clears_failures(self):
        """Reset should clear all failure counts."""
        # This test assumes providers are initialized
        reset_circuit_breakers()
        stats = get_router_stats()

        if "providers" in stats:
            for provider_name, provider_info in stats["providers"].items():
                if "circuit_breaker" in provider_info:
                    assert provider_info["circuit_breaker"]["failures"] == 0
                    assert provider_info["circuit_breaker"]["state"] == "closed"
