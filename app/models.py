"""Modelos de dados e tipos para a API."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MarketClassification(str, Enum):
    """Classificação do mercado baseada em análise técnica."""

    BULLISH = "Tendência de Alta"
    BEARISH = "Tendência de Baixa"
    HIGH_VOLATILITY = "Alta Volatilidade"
    NEUTRAL = "Neutro"


@dataclass
class TechnicalIndicators:
    """Indicadores técnicos calculados."""

    current_price: float
    sma20: float
    sma50: float
    rsi: float
    bollinger_upper: float
    bollinger_lower: float
    bollinger_middle: float


@dataclass
class ClassificationResult:
    """Resultado da classificação com explicabilidade."""

    classification: MarketClassification
    confidence: float
    indicators: TechnicalIndicators
    explanation: str
    features_importance: dict[str, float] = field(default_factory=dict)


@dataclass
class NewsItem:
    """Item de notícia para contexto."""

    title: str
    description: str
    source: str
    url: str
    published_at: datetime


@dataclass
class InsightResult:
    """Resultado da geração de insight."""

    text: str
    classification: MarketClassification
    news_sources: list[str]
    generated_at: datetime


# Pydantic models para API responses


class IndicatorsResponse(BaseModel):
    """Response model para indicadores técnicos."""

    current_price: float = Field(..., description="Preço atual do ativo")
    sma20: float = Field(..., description="Média móvel simples de 20 períodos")
    sma50: float = Field(..., description="Média móvel simples de 50 períodos")
    rsi: float = Field(..., description="Índice de Força Relativa (14 períodos)")
    bollinger_upper: float = Field(..., description="Banda de Bollinger superior")
    bollinger_lower: float = Field(..., description="Banda de Bollinger inferior")


class InsightResponse(BaseModel):
    """Response model completo para endpoint principal."""

    symbol: str = Field(..., description="Par de moedas")
    classification: str = Field(..., description="Classificação do mercado")
    confidence: float = Field(..., ge=0, le=1, description="Confiança da classificação")
    indicators: IndicatorsResponse = Field(..., description="Indicadores técnicos")
    explanation: str = Field(..., description="Explicação da classificação")
    features_importance: dict[str, float] = Field(
        ..., description="Importância das features na decisão"
    )
    insight: str = Field(..., description="Insight contextualizado gerado pela IA")
    news_sources: list[str] = Field(..., description="Fontes de notícias utilizadas")
    generated_at: datetime = Field(..., description="Timestamp da geração")
    cached: bool = Field(..., description="Se o resultado veio do cache")


class TechnicalResponse(BaseModel):
    """Response model para endpoint de análise técnica apenas."""

    symbol: str = Field(..., description="Par de moedas")
    classification: str = Field(..., description="Classificação do mercado")
    confidence: float = Field(..., ge=0, le=1, description="Confiança da classificação")
    indicators: IndicatorsResponse = Field(..., description="Indicadores técnicos")
    explanation: str = Field(..., description="Explicação da classificação")
    features_importance: dict[str, float] = Field(
        ..., description="Importância das features na decisão"
    )


class HealthResponse(BaseModel):
    """Response model para health check."""

    status: str = Field(..., description="Status do serviço")
    version: str = Field(..., description="Versão da API")
    cache: str = Field(..., description="Status da conexão com cache")
