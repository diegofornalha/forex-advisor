"""Motor de recomendação com análise técnica e explicabilidade."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pandas as pd
import yfinance as yf

from .config import settings
from .models import ClassificationResult, MarketClassification, TechnicalIndicators

# Thread pool para operações bloqueantes do yfinance
_executor = ThreadPoolExecutor(max_workers=2)


async def fetch_ohlc(
    symbol: str = None,
    period: str = None,
) -> pd.DataFrame:
    """Busca dados OHLC via yfinance.

    Args:
        symbol: Símbolo do ativo (default: settings.symbol)
        period: Período de dados (default: settings.period)

    Returns:
        DataFrame com colunas Open, High, Low, Close, Volume
    """
    symbol = symbol or settings.symbol
    period = period or settings.period

    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(
        _executor,
        lambda: yf.download(symbol, period=period, progress=False),
    )

    if df.empty:
        raise ValueError(f"Não foi possível obter dados para {symbol}")

    return df


def calculate_indicators(df: pd.DataFrame) -> TechnicalIndicators:
    """Calcula indicadores técnicos a partir dos dados OHLC.

    Indicadores calculados:
    - SMA 20 e 50 períodos
    - RSI 14 períodos
    - Bandas de Bollinger (SMA20 ± 2σ)

    Args:
        df: DataFrame com dados OHLC

    Returns:
        TechnicalIndicators com todos os valores calculados
    """
    close = df["Close"].squeeze()

    # Preço atual (último fechamento)
    current_price = float(close.iloc[-1])

    # SMA - Médias Móveis Simples
    sma20 = float(close.rolling(window=20).mean().iloc[-1])
    sma50 = float(close.rolling(window=50).mean().iloc[-1])

    # RSI - Relative Strength Index (14 períodos)
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = float(100 - (100 / (1 + rs)).iloc[-1])

    # Bandas de Bollinger (SMA20 ± 2 desvios padrão)
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
    """Classifica o mercado com base nos indicadores técnicos.

    Lógica de classificação (explicável):
    - Alta Volatilidade: preço fora das Bandas de Bollinger
    - Tendência de Alta: preço > SMA50 + 2% e RSI entre 50-70
    - Tendência de Baixa: preço < SMA50 - 2% e RSI entre 30-50
    - Neutro: demais casos

    Args:
        indicators: Indicadores técnicos calculados

    Returns:
        ClassificationResult com classificação e explicabilidade
    """
    # Calcula features normalizadas
    features = {}

    # Feature 1: Posição relativa à SMA50 (%)
    price_vs_sma50 = (indicators.current_price - indicators.sma50) / indicators.sma50
    features["price_vs_sma50"] = round(price_vs_sma50, 4)

    # Feature 2: RSI normalizado (-1 a 1)
    rsi_normalized = (indicators.rsi - 50) / 50
    features["rsi_signal"] = round(rsi_normalized, 4)

    # Feature 3: Posição nas Bandas de Bollinger (0 a 1, pode sair)
    bb_range = indicators.bollinger_upper - indicators.bollinger_lower
    bb_position = (indicators.current_price - indicators.bollinger_lower) / bb_range
    features["bb_position"] = round(bb_position, 4)

    # Decisão baseada em regras (transparente e auditável)
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

    # Feature importance (peso de cada feature na decisão)
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


async def get_classification(
    symbol: str = None,
    period: str = None,
) -> ClassificationResult:
    """Pipeline completo: busca dados, calcula indicadores e classifica.

    Args:
        symbol: Símbolo do ativo
        period: Período de dados

    Returns:
        ClassificationResult com toda a análise
    """
    df = await fetch_ohlc(symbol, period)
    indicators = calculate_indicators(df)
    return classify(indicators)
