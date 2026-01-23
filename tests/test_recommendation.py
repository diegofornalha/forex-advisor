"""Tests for recommendation engine."""

import numpy as np
import pandas as pd
import pytest

from app.models import MarketClassification, TechnicalIndicators
from app.recommendation import calculate_indicators, classify


# Test fixtures
@pytest.fixture
def sample_ohlc_data():
    """Create sample OHLC data for testing."""
    # 100 days of data
    dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
    np.random.seed(42)  # Reproducibility

    # Generate realistic price data
    base_price = 5.0
    returns = np.random.normal(0, 0.01, 100).cumsum()
    close_prices = base_price + returns

    df = pd.DataFrame({
        "Open": close_prices * (1 + np.random.uniform(-0.005, 0.005, 100)),
        "High": close_prices * (1 + np.random.uniform(0, 0.01, 100)),
        "Low": close_prices * (1 - np.random.uniform(0, 0.01, 100)),
        "Close": close_prices,
        "Volume": np.random.randint(1000000, 10000000, 100),
    }, index=dates)

    return df


@pytest.fixture
def bullish_indicators():
    """Create bullish market indicators."""
    return TechnicalIndicators(
        current_price=5.50,
        sma20=5.35,
        sma50=5.30,
        rsi=60.0,
        bollinger_upper=5.60,
        bollinger_lower=5.10,
        bollinger_middle=5.35,
    )


@pytest.fixture
def bearish_indicators():
    """Create bearish market indicators."""
    return TechnicalIndicators(
        current_price=5.10,
        sma20=5.25,
        sma50=5.30,
        rsi=40.0,
        bollinger_upper=5.50,
        bollinger_lower=5.00,
        bollinger_middle=5.25,
    )


@pytest.fixture
def volatile_indicators():
    """Create high volatility indicators (price outside Bollinger)."""
    return TechnicalIndicators(
        current_price=5.70,  # Above upper band
        sma20=5.30,
        sma50=5.25,
        rsi=75.0,
        bollinger_upper=5.55,
        bollinger_lower=5.05,
        bollinger_middle=5.30,
    )


class TestCalculateIndicators:
    """Tests for calculate_indicators function."""

    def test_returns_technical_indicators(self, sample_ohlc_data):
        """Should return TechnicalIndicators object."""
        result = calculate_indicators(sample_ohlc_data)
        assert isinstance(result, TechnicalIndicators)

    def test_all_fields_populated(self, sample_ohlc_data):
        """Should populate all indicator fields."""
        result = calculate_indicators(sample_ohlc_data)

        assert result.current_price > 0
        assert result.sma20 > 0
        assert result.sma50 > 0
        assert 0 <= result.rsi <= 100
        assert result.bollinger_upper > result.bollinger_middle
        assert result.bollinger_lower < result.bollinger_middle

    def test_sma_calculation(self, sample_ohlc_data):
        """SMA values should be reasonable."""
        result = calculate_indicators(sample_ohlc_data)

        # SMA should be close to current price (within 10%)
        assert abs(result.sma20 - result.current_price) / result.current_price < 0.10
        assert abs(result.sma50 - result.current_price) / result.current_price < 0.15

    def test_bollinger_band_ordering(self, sample_ohlc_data):
        """Bollinger bands should be ordered correctly."""
        result = calculate_indicators(sample_ohlc_data)

        assert result.bollinger_lower < result.bollinger_middle < result.bollinger_upper


class TestClassify:
    """Tests for classify function."""

    def test_bullish_classification(self, bullish_indicators):
        """Should classify as bullish when conditions met."""
        result = classify(bullish_indicators)
        assert result.classification == MarketClassification.BULLISH
        assert result.confidence > 0.5

    def test_bearish_classification(self, bearish_indicators):
        """Should classify as bearish when conditions met."""
        result = classify(bearish_indicators)
        assert result.classification == MarketClassification.BEARISH
        assert result.confidence > 0.5

    def test_volatile_classification(self, volatile_indicators):
        """Should classify as high volatility when price outside bands."""
        result = classify(volatile_indicators)
        assert result.classification == MarketClassification.HIGH_VOLATILITY

    def test_neutral_classification(self):
        """Should classify as neutral when no clear trend."""
        neutral = TechnicalIndicators(
            current_price=5.30,
            sma20=5.29,
            sma50=5.28,
            rsi=50.0,
            bollinger_upper=5.50,
            bollinger_lower=5.10,
            bollinger_middle=5.30,
        )
        result = classify(neutral)
        assert result.classification == MarketClassification.NEUTRAL

    def test_returns_explanation(self, bullish_indicators):
        """Should return human-readable explanation."""
        result = classify(bullish_indicators)

        assert result.explanation is not None
        assert len(result.explanation) > 10  # Non-trivial explanation

    def test_returns_feature_importance(self, bullish_indicators):
        """Should return feature importance weights."""
        result = classify(bullish_indicators)

        assert "price_vs_sma50" in result.features_importance
        assert "rsi_signal" in result.features_importance
        assert "bb_position" in result.features_importance

        # Weights should sum to 1.0
        total = sum(result.features_importance.values())
        assert abs(total - 1.0) < 0.01

    def test_confidence_bounded(self, bullish_indicators):
        """Confidence should be between 0 and 1."""
        result = classify(bullish_indicators)
        assert 0.0 <= result.confidence <= 1.0


class TestIntegration:
    """Integration tests."""

    def test_full_pipeline(self, sample_ohlc_data):
        """Test full pipeline: indicators -> classification."""
        indicators = calculate_indicators(sample_ohlc_data)
        result = classify(indicators)

        assert result.classification in [
            MarketClassification.BULLISH,
            MarketClassification.BEARISH,
            MarketClassification.NEUTRAL,
            MarketClassification.HIGH_VOLATILITY,
        ]
        assert result.indicators == indicators
