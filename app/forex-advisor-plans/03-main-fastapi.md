# Plano 03: Main FastAPI

## Objetivo
Criar aplicação FastAPI com endpoint principal e integração de todos os módulos.

## Arquivo
`app/main.py`

## Estrutura do App

```python
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .config import settings
from .models import InsightResponse, HealthResponse
from .recommendation import get_classification
from .insights import generate_insight
from .cache import get_cached, set_cached

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: inicializa RAG, carrega modelo embedding
    print("🚀 Iniciando Forex Advisor API...")
    yield
    # Shutdown
    print("👋 Encerrando...")

app = FastAPI(
    title="Remessa Forex Advisor API",
    description="API de insights contextualizados para câmbio BRL/USD",
    version="1.0.0",
    lifespan=lifespan
)
```

## Endpoints

### GET /api/v1/forex/usdbrl

```python
@app.get("/api/v1/forex/usdbrl", response_model=InsightResponse)
async def get_usdbrl_insight(
    force_refresh: bool = Query(False, description="Ignorar cache")
):
    """
    Retorna análise técnica + insight contextualizado do par USD/BRL.

    - **classification**: Tendência atual (Alta, Baixa, Volatilidade, Neutro)
    - **indicators**: Valores dos indicadores técnicos
    - **explanation**: Explicação da classificação
    - **insight**: Parágrafo contextualizado com notícias
    - **cached**: Se veio do cache ou foi gerado agora
    """
    cache_key = "forex:usdbrl:latest"

    # Tenta cache primeiro
    if not force_refresh:
        cached = await get_cached(cache_key)
        if cached:
            cached["cached"] = True
            return JSONResponse(
                content=cached,
                headers={"X-Cache": "HIT"}
            )

    try:
        # 1. Classificação técnica
        classification = await get_classification()

        # 2. Gera insight com RAG
        insight = await generate_insight(classification)

        # 3. Monta response
        result = {
            "symbol": "USD/BRL",
            "classification": classification.classification.value,
            "confidence": classification.confidence,
            "indicators": {
                "current_price": classification.indicators.current_price,
                "sma20": classification.indicators.sma20,
                "sma50": classification.indicators.sma50,
                "rsi": classification.indicators.rsi,
                "bollinger_upper": classification.indicators.bollinger_upper,
                "bollinger_lower": classification.indicators.bollinger_lower,
            },
            "explanation": classification.explanation,
            "features_importance": classification.features_importance,
            "insight": insight.text,
            "news_sources": insight.news_sources,
            "generated_at": insight.generated_at.isoformat(),
            "cached": False
        }

        # 4. Salva no cache
        await set_cached(cache_key, result, ttl=settings.cache_ttl)

        return JSONResponse(
            content=result,
            headers={"X-Cache": "MISS"}
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar insight: {str(e)}"
        )
```

### GET /health

```python
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check para monitoramento."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "cache": "connected"  # TODO: verificar Redis
    }
```

### GET /api/v1/forex/usdbrl/technical

```python
@app.get("/api/v1/forex/usdbrl/technical")
async def get_technical_only():
    """Retorna apenas análise técnica (sem insight LLM)."""
    classification = await get_classification()
    return {
        "symbol": "USD/BRL",
        "classification": classification.classification.value,
        "indicators": {...},
        "explanation": classification.explanation
    }
```

## Response Model (Pydantic)

```python
# Em models.py
from pydantic import BaseModel
from datetime import datetime

class IndicatorsResponse(BaseModel):
    current_price: float
    sma20: float
    sma50: float
    rsi: float
    bollinger_upper: float
    bollinger_lower: float

class InsightResponse(BaseModel):
    symbol: str
    classification: str
    confidence: float
    indicators: IndicatorsResponse
    explanation: str
    features_importance: dict[str, float]
    insight: str
    news_sources: list[str]
    generated_at: datetime
    cached: bool

class HealthResponse(BaseModel):
    status: str
    version: str
    cache: str
```

## Exemplo de Response

```json
{
  "symbol": "USD/BRL",
  "classification": "Tendência de Alta",
  "confidence": 0.75,
  "indicators": {
    "current_price": 5.18,
    "sma20": 5.12,
    "sma50": 5.05,
    "rsi": 62.3,
    "bollinger_upper": 5.25,
    "bollinger_lower": 4.95
  },
  "explanation": "Preço 2.6% acima da SMA50, RSI em 62",
  "features_importance": {
    "price_vs_sma50": 0.4,
    "rsi_signal": 0.35,
    "bb_position": 0.25
  },
  "insight": "O dólar apresenta tendência de alta frente ao real, com preço acima das médias móveis. Notícias recentes sobre política monetária do Fed e tensões comerciais podem estar influenciando o movimento. O RSI em 62 indica força compradora moderada sem sobrecompra.",
  "news_sources": ["InfoMoney", "Valor Econômico"],
  "generated_at": "2025-01-21T22:30:00Z",
  "cached": false
}
```

## Swagger UI
Acessível em `http://localhost:8000/docs`

## Dependências
```
fastapi>=0.109.0
uvicorn>=0.27.0
pydantic>=2.5.0
pydantic-settings>=2.1.0
```

## Critérios de Sucesso
- [ ] App FastAPI rodando
- [ ] Endpoint /api/v1/forex/usdbrl funcionando
- [ ] Cache hit/miss com header X-Cache
- [ ] Swagger UI acessível
- [ ] Health check respondendo
- [ ] Response validado por Pydantic
