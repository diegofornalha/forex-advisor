"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Set environment variables for testing."""
    # Use test Redis (can be mocked if needed)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/1")  # Use DB 1 for tests
    monkeypatch.setenv("DEBUG", "false")
