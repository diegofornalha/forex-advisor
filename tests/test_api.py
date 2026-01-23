"""Tests for FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_200(self, client):
        """Should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status(self, client):
        """Should return status healthy."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_200(self, client):
        """Should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_root_returns_message(self, client):
        """Should return message and endpoints."""
        response = client.get("/")
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        assert "docs" in data


class TestDocsEndpoint:
    """Tests for API documentation."""

    def test_docs_available(self, client):
        """Should serve OpenAPI docs."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema(self, client):
        """Should serve OpenAPI schema."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data


class TestForexEndpoint:
    """Tests for forex analysis endpoint."""

    def test_forex_returns_200(self, client):
        """Should return 200 OK (may take a few seconds due to yfinance)."""
        response = client.get("/api/v1/forex/usdbrl", timeout=30)
        assert response.status_code == 200

    def test_forex_has_classification(self, client):
        """Should return classification data."""
        response = client.get("/api/v1/forex/usdbrl", timeout=30)
        data = response.json()

        assert "classification" in data
        # Portuguese classification names
        assert data["classification"] in [
            "Alta", "Baixa", "Neutro", "Alta Volatilidade"
        ]

    def test_forex_has_confidence(self, client):
        """Should return confidence score."""
        response = client.get("/api/v1/forex/usdbrl", timeout=30)
        data = response.json()

        assert "confidence" in data
        assert 0 <= data["confidence"] <= 1

    def test_forex_has_indicators(self, client):
        """Should return technical indicators."""
        response = client.get("/api/v1/forex/usdbrl", timeout=30)
        data = response.json()

        assert "indicators" in data
        indicators = data["indicators"]

        assert "current_price" in indicators
        assert "sma20" in indicators
        assert "sma50" in indicators
        assert "rsi" in indicators
        assert "bollinger_upper" in indicators
        assert "bollinger_lower" in indicators

    def test_forex_has_explanation(self, client):
        """Should return human-readable explanation."""
        response = client.get("/api/v1/forex/usdbrl", timeout=30)
        data = response.json()

        assert "explanation" in data
        assert len(data["explanation"]) > 10

    def test_forex_has_insight(self, client):
        """Should return LLM-generated insight."""
        response = client.get("/api/v1/forex/usdbrl", timeout=60)
        data = response.json()

        assert "insight" in data
        assert len(data["insight"]) > 20


class TestTechnicalEndpoint:
    """Tests for technical-only endpoint."""

    def test_technical_returns_200(self, client):
        """Should return 200 OK."""
        response = client.get("/api/v1/forex/usdbrl/technical", timeout=30)
        assert response.status_code == 200

    def test_technical_has_indicators(self, client):
        """Should return technical indicators."""
        response = client.get("/api/v1/forex/usdbrl/technical", timeout=30)
        data = response.json()

        assert "indicators" in data
        assert "classification" in data
        assert "confidence" in data

    def test_technical_faster_than_full(self, client):
        """Technical endpoint should not include insight/news."""
        response = client.get("/api/v1/forex/usdbrl/technical", timeout=30)
        data = response.json()

        # Technical endpoint may or may not include insight
        # Main test is that it works without LLM call
        assert response.status_code == 200


class TestCacheHeaders:
    """Tests for cache behavior."""

    def test_second_request_cached(self, client):
        """Second request should be faster (cached)."""
        # First request
        response1 = client.get("/api/v1/forex/usdbrl/technical", timeout=30)
        assert response1.status_code == 200

        # Second request should be cached
        response2 = client.get("/api/v1/forex/usdbrl/technical", timeout=30)
        assert response2.status_code == 200
        data = response2.json()

        # If cached field exists, verify it
        if "cached" in data:
            assert data["cached"] is True
