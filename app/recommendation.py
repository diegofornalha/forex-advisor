"""Recommendation engine with technical analysis and explainability."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import yfinance as yf

from .config import settings
from .models import ClassificationResult, MarketClassification, TechnicalIndicators

# Thread pool for blocking yfinance operations
_executor = ThreadPoolExecutor(max_workers=2)


async def fetch_ohlc() -> pd.DataFrame:
    """Fetch OHLC data via yfinance.

    Returns:
        DataFrame with Open, High, Low, Close, Volume columns
    """
    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(
        _executor,
        lambda: yf.download(settings.symbol, period=settings.period, progress=False),
    )

    if df.empty:
        raise ValueError(f"Could not fetch data for {settings.symbol}")

    return df


def calculate_indicators(df: pd.DataFrame) -> TechnicalIndicators:
    """Calculate technical indicators from OHLC data.

    Indicators:
    - SMA 20 and 50 periods
    - RSI 14 periods
    - Bollinger Bands (SMA20 ± 2σ)

    Args:
        df: DataFrame with OHLC data

    Returns:
        TechnicalIndicators with all calculated values
    """
    close = df["Close"].squeeze()

    # Current price (last close)
    current_price = float(close.iloc[-1])

    # SMA - Simple Moving Averages
    sma20 = float(close.rolling(window=20).mean().iloc[-1])
    sma50 = float(close.rolling(window=50).mean().iloc[-1])

    # RSI - Relative Strength Index (14 periods)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi_series = 100 - (100 / (1 + rs))
    rsi_last = float(rsi_series.iloc[-1])
    if not np.isfinite(rsi_last):
        gain_last = float(gain.iloc[-1])
        loss_last = float(loss.iloc[-1])
        if not np.isfinite(gain_last) or not np.isfinite(loss_last):
            rsi_last = 50.0
        elif loss_last == 0 and gain_last == 0:
            rsi_last = 50.0
        elif loss_last == 0:
            rsi_last = 100.0
        else:
            rsi_last = 50.0
    rsi = rsi_last

    # Bollinger Bands (SMA20 ± 2 standard deviations)
    bb_middle = sma20
    bb_std = float(close.rolling(window=20).std().iloc[-1])
    bb_upper = bb_middle + (2 * bb_std)
    bb_lower = bb_middle - (2 * bb_std)

    return TechnicalIndicators(
        current_price=round(current_price, 4),
        sma20=round(sma20, 4),
        sma50=round(sma50, 4),
        rsi=round(rsi, 2),
        bollinger_upper=round(bb_upper, 4),
        bollinger_lower=round(bb_lower, 4),
        bollinger_middle=round(bb_middle, 4),
    )


def classify(indicators: TechnicalIndicators) -> ClassificationResult:
    """Classify market based on technical indicators.

    Classification logic (explainable):
    - High Volatility: price outside Bollinger Bands
    - Bullish: price > SMA50 + 2% and RSI between 50-70
    - Bearish: price < SMA50 - 2% and RSI between 30-50
    - Neutral: all other cases

    Args:
        indicators: Calculated technical indicators

    Returns:
        ClassificationResult with classification and explainability
    """
    # Calculate normalized features
    features = {}

    # Feature 1: Position relative to SMA50 (%)
    price_vs_sma50 = (indicators.current_price - indicators.sma50) / indicators.sma50
    features["price_vs_sma50"] = round(price_vs_sma50, 4)

    # Feature 2: RSI normalized (-1 to 1)
    rsi_normalized = (indicators.rsi - 50) / 50
    features["rsi_signal"] = round(rsi_normalized, 4)

    # Feature 3: Position in Bollinger Bands (0 to 1, can exceed)
    bb_range = indicators.bollinger_upper - indicators.bollinger_lower
    if bb_range == 0:
        bb_position = 0.5
    else:
        bb_position = (indicators.current_price - indicators.bollinger_lower) / bb_range
    features["bb_position"] = round(bb_position, 4)

    # Rule-based decision (transparent and auditable)
    if bb_position > 1.0 or bb_position < 0.0:
        classification = MarketClassification.HIGH_VOLATILITY
        explanation = (
            f"Preço fora das Bandas de Bollinger "
            f"({'acima' if bb_position > 1.0 else 'abaixo'}). "
            f"BB position: {bb_position:.2f}"
        )
        confidence = min(abs(bb_position - 0.5) * 2, 1.0)

    elif price_vs_sma50 > 0.02 and 50 < indicators.rsi < 70:
        classification = MarketClassification.BULLISH
        explanation = (
            f"Preço {price_vs_sma50 * 100:.1f}% acima da SMA50, "
            f"RSI em {indicators.rsi:.0f} (força compradora moderada)"
        )
        confidence = min((price_vs_sma50 * 10) + (indicators.rsi - 50) / 40, 1.0)

    elif price_vs_sma50 < -0.02 and 30 < indicators.rsi < 50:
        classification = MarketClassification.BEARISH
        explanation = (
            f"Preço {abs(price_vs_sma50) * 100:.1f}% abaixo da SMA50, "
            f"RSI em {indicators.rsi:.0f} (força vendedora moderada)"
        )
        confidence = min((abs(price_vs_sma50) * 10) + (50 - indicators.rsi) / 40, 1.0)

    else:
        classification = MarketClassification.NEUTRAL
        explanation = (
            f"Sem tendência clara. Preço {price_vs_sma50 * 100:+.1f}% vs SMA50, "
            f"RSI em {indicators.rsi:.0f}"
        )
        confidence = 0.5

    # Feature importance (weight of each feature in decision)
    features_importance = {
        "price_vs_sma50": 0.40,
        "rsi_signal": 0.35,
        "bb_position": 0.25,
    }

    return ClassificationResult(
        classification=classification,
        confidence=round(confidence, 2),
        indicators=indicators,
        explanation=explanation,
        features_importance=features_importance,
    )


async def get_classification() -> ClassificationResult:
    """Full pipeline: fetch data, calculate indicators and classify.

    Returns:
        ClassificationResult with full analysis
    """
    df = await fetch_ohlc()
    indicators = calculate_indicators(df)
    return classify(indicators)
