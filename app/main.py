"""FastAPI application with Forex Advisor endpoints."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .cache import get_cache_status, get_cached, set_cached
from .config import settings
from .insights import generate_insight
from .models import HealthResponse, InsightResponse, TechnicalResponse
from .recommendation import get_classification

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup/shutdown events."""
    # Startup
    logger.info("🚀 Iniciando Forex Advisor API...")
    logger.info(f"   Símbolo: {settings.symbol}")
    logger.info(f"   Cache TTL: {settings.cache_ttl_insight}s")
    yield
    # Shutdown
    logger.info("👋 Encerrando Forex Advisor API...")


app = FastAPI(
    title="Remessa Forex Advisor API",
    description=(
        "API de insights contextualizados para câmbio USD/BRL, "
        "combinando análise técnica com notícias em tempo real.\n\n"
        "**Endpoints principais:**\n"
        "- `/api/v1/forex/usdbrl` - Análise completa com insight IA\n"
        "- `/api/v1/forex/usdbrl/technical` - Apenas análise técnica\n"
        "- `/health` - Status do serviço"
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Cache"],
)


@app.get(
    "/api/v1/forex/usdbrl",
    response_model=InsightResponse,
    summary="Análise completa USD/BRL",
    description=(
        "Retorna análise completa do par USD/BRL incluindo:\n\n"
        "- **Classificação técnica** (Alta, Baixa, Volatilidade, Neutro)\n"
        "- **Indicadores** (SMA20, SMA50, RSI, Bollinger)\n"
        "- **Explicabilidade** (peso de cada feature na decisão)\n"
        "- **Insight contextualizado** gerado por IA com notícias recentes\n\n"
        "O resultado é cacheado por 1 hora. Use `force_refresh=true` para ignorar o cache."
    ),
    tags=["Forex"],
)
async def get_usdbrl_insight(
    force_refresh: bool = Query(
        False,
        description="Forçar atualização, ignorando cache",
    ),
):
    """Return complete USD/BRL analysis with AI-generated insight."""
    cache_key = "forex:usdbrl:latest"

    # Try cache first (unless force_refresh)
    if not force_refresh:
        cached = await get_cached(cache_key)
        if cached:
            cached["cached"] = True
            return JSONResponse(
                content=cached,
                headers={"X-Cache": "HIT"},
            )

    try:
        # 1. Get technical classification
        classification = await get_classification()

        # 2. Generate insight with news context
        insight = await generate_insight(classification)

        # 3. Build response
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
            "cached": False,
        }

        # 4. Save to cache
        await set_cached(cache_key, result, ttl=settings.cache_ttl_insight)

        return JSONResponse(
            content=result,
            headers={"X-Cache": "MISS"},
        )

    except Exception as e:
        logger.error(f"Error generating insight: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar insight: {str(e)}",
        )


@app.get(
    "/api/v1/forex/usdbrl/technical",
    response_model=TechnicalResponse,
    summary="Análise técnica USD/BRL",
    description=(
        "Retorna apenas a análise técnica sem o insight gerado por IA.\n\n"
        "Endpoint mais rápido, útil para:\n"
        "- Verificações rápidas de tendência\n"
        "- Quando a LLM não está disponível\n"
        "- Integrações que precisam apenas dos indicadores\n\n"
        "O resultado é cacheado por 4 horas."
    ),
    tags=["Forex"],
)
async def get_technical_only(
    force_refresh: bool = Query(
        False,
        description="Forçar atualização, ignorando cache",
    ),
):
    """Return only technical analysis without AI insight."""
    cache_key = "forex:usdbrl:technical"

    # Try cache first
    if not force_refresh:
        cached = await get_cached(cache_key)
        if cached:
            return JSONResponse(
                content=cached,
                headers={"X-Cache": "HIT"},
            )

    try:
        classification = await get_classification()

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
        }

        await set_cached(cache_key, result, ttl=settings.cache_ttl_technical)

        return JSONResponse(
            content=result,
            headers={"X-Cache": "MISS"},
        )

    except Exception as e:
        logger.error(f"Error in technical analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erro na análise técnica: {str(e)}",
        )


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description=(
        "Verifica o status do serviço e suas dependências.\n\n"
        "Retorna:\n"
        "- **status**: Estado geral do serviço\n"
        "- **version**: Versão da API\n"
        "- **cache**: Status da conexão com Redis"
    ),
    tags=["Sistema"],
)
async def health_check():
    """Health check endpoint for monitoring."""
    cache_status = await get_cache_status()

    return {
        "status": "healthy",
        "version": "1.0.0",
        "cache": cache_status["redis"],
    }


@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to docs."""
    return {
        "message": "Forex Advisor API - Remessa Online",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "full_analysis": "/api/v1/forex/usdbrl",
            "technical_only": "/api/v1/forex/usdbrl/technical",
        },
    }
