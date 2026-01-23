# Plano 01: Recommendation Engine

## Objetivo
Criar `models.py` e `recommendation_engine.py` com tipos bem definidos e lógica explicável.

## Arquivos
- `src/models.py` - Tipos e dataclasses
- `src/recommendation_engine.py` - Lógica de classificação

## models.py

```python
from dataclasses import dataclass
from enum import Enum

class MarketClassification(Enum):
    BULLISH = "Tendência de Alta"
    BEARISH = "Tendência de Baixa"
    HIGH_VOLATILITY = "Alta Volatilidade"
    NEUTRAL = "Neutro"

@dataclass
class TechnicalIndicators:
    current_price: float
    sma20: float
    sma50: float
    rsi: float
    bollinger_upper: float
    bollinger_lower: float
    bollinger_middle: float

@dataclass
class ClassificationResult:
    classification: MarketClassification
    confidence: float
    indicators: TechnicalIndicators
    explanation: str
    features_importance: dict[str, float]
```

## recommendation_engine.py

### Funções

```python
async def fetch_ohlc(symbol: str = "USDBRL=X", period: str = "5y") -> pd.DataFrame:
    """Busca dados OHLC via yfinance."""

def calculate_indicators(df: pd.DataFrame) -> TechnicalIndicators:
    """Calcula indicadores técnicos."""

def classify(indicators: TechnicalIndicators) -> ClassificationResult:
    """Classifica mercado com explicabilidade."""
```

### Lógica de Classificação (Explicável)

```python
def classify(indicators: TechnicalIndicators) -> ClassificationResult:
    features = {}

    # Feature 1: Posição relativa à SMA50
    price_vs_sma50 = (indicators.current_price - indicators.sma50) / indicators.sma50
    features["price_vs_sma50"] = price_vs_sma50

    # Feature 2: RSI normalizado
    rsi_normalized = (indicators.rsi - 50) / 50
    features["rsi_signal"] = rsi_normalized

    # Feature 3: Posição nas Bollinger Bands
    bb_range = indicators.bollinger_upper - indicators.bollinger_lower
    bb_position = (indicators.current_price - indicators.bollinger_lower) / bb_range
    features["bb_position"] = bb_position

    # Decisão baseada em regras (explicável)
    if bb_position > 1.0 or bb_position < 0.0:
        classification = MarketClassification.HIGH_VOLATILITY
        explanation = "Preço fora das Bandas de Bollinger"
    elif price_vs_sma50 > 0.02 and 50 < indicators.rsi < 70:
        classification = MarketClassification.BULLISH
        explanation = f"Preço {price_vs_sma50*100:.1f}% acima da SMA50, RSI em {indicators.rsi:.0f}"
    elif price_vs_sma50 < -0.02 and 30 < indicators.rsi < 50:
        classification = MarketClassification.BEARISH
        explanation = f"Preço {abs(price_vs_sma50)*100:.1f}% abaixo da SMA50, RSI em {indicators.rsi:.0f}"
    else:
        classification = MarketClassification.NEUTRAL
        explanation = "Sem tendência clara definida"

    return ClassificationResult(...)
```

## Cálculo dos Indicadores

| Indicador | Fórmula | Parâmetros |
|-----------|---------|------------|
| SMA | Média móvel simples | 20, 50 períodos |
| RSI | 100 - (100 / (1 + RS)) | 14 períodos |
| Bollinger | SMA20 ± 2*std | 20 períodos, 2 desvios |

## Explicabilidade (Feature Importance)

O modelo retorna `features_importance` mostrando o peso de cada feature na decisão:

```python
features_importance = {
    "price_vs_sma50": 0.4,  # 40% da decisão
    "rsi_signal": 0.35,     # 35% da decisão
    "bb_position": 0.25     # 25% da decisão
}
```

## Dependências
```
yfinance>=0.2.18
pandas>=2.0.0
numpy>=1.24.0
```

## Critérios de Sucesso
- [ ] Enums e dataclasses definidos
- [ ] fetch_ohlc retornando dados
- [ ] Indicadores calculados corretamente
- [ ] Classificação funcionando
- [ ] Explicabilidade documentada
