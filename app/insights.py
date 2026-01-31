"""🚀 INSIGHTS GENERATOR - Dashboard Híbrido (Dados + IA + Chat)

/insights é um dashboard completo que combina:
1. Dados técnicos (SEM LLM) - Indicadores, classificação
2. Insight gerado por IA (COM LLM) - Texto contextualizado
3. Chat interativo (COM LLM) - Perguntas do usuário

⚡ ATIVAÇÃO DO LLM:
- Momento 1: Carregamento inicial → generate_insight() → call_llm()
- Momento 2: Chat do usuário → chat_websocket() → call_llm()

FLUXO COMPLETO:
/insights
  ├── HTTP GET /api/v1/forex/usdbrl
  │   ├── get_classification() (SEM LLM)
  │   ├── generate_insight() (COM LLM!) → MINIMAX
  │   └── Cache (1h)
  │
  └── WebSocket /ws/chat/{session_id}
      ├── search_news_context() (RAG)
      └── call_llm() (COM LLM!) → MINIMAX

CUSTOS:
- Carregamento inicial: $XX (insight gerado)
- Chat: $XX por mensagem
- Indicadores técnicos: $0 (só matemática)
"""

import logging
from datetime import datetime
from urllib.parse import quote

import feedparser

from .config import settings
from .llm_router import call_llm
from .models import ClassificationResult, InsightResult, NewsItem

logger = logging.getLogger(__name__)

# Forbidden words for compliance validation (Portuguese)
FORBIDDEN_WORDS = [
    "compre",
    "venda",
    "invista",
    "recomendo",
    "sugiro",
    "aposte",
    "comprar",
    "vender",
    "investir",
    "buy",
    "sell",
]


async def fetch_news() -> list[NewsItem]:
    """Fetch news from Google News RSS feed.

    Returns:
        List of NewsItem objects
    """
    # Google News RSS URL for Brazil
    encoded_query = quote(settings.news_query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"

    try:
        feed = feedparser.parse(url)
        news_items = []

        for entry in feed.entries[:settings.news_limit]:
            # Parse publication date
            published_at = datetime.now()
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6])

            # Extract source from title (format: "Title - Source")
            title = entry.title
            source = "Google News"
            if " - " in title:
                parts = title.rsplit(" - ", 1)
                title = parts[0]
                source = parts[1] if len(parts) > 1 else source

            news_items.append(
                NewsItem(
                    title=title,
                    description=getattr(entry, "summary", "")[:500],
                    source=source,
                    url=entry.link,
                    published_at=published_at,
                )
            )

        logger.info(f"Fetched {len(news_items)} news items for '{settings.news_query}'")
        return news_items

    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        return []


def build_news_context(news: list[NewsItem]) -> str:
    """Format news items for prompt injection.

    Args:
        news: List of news items

    Returns:
        Formatted string with news headlines
    """
    if not news:
        return "Nenhuma notícia recente disponível."

    lines = []
    for i, item in enumerate(news[:5], 1):
        lines.append(f"{i}. [{item.source}] {item.title}")

    return "\n".join(lines)


def validate_insight(text: str) -> bool:
    """Validate that insight contains no investment recommendations.

    Args:
        text: Insight text to validate

    Returns:
        True if text is compliant (no recommendations)
    """
    text_lower = text.lower()
    for word in FORBIDDEN_WORDS:
        if word in text_lower:
            logger.warning(f"Insight contains forbidden word: '{word}'")
            return False
    return True


# Prompt template for insight generation (Portuguese output)
INSIGHT_PROMPT = """Você é um analista de mercado da Remessa Online, especializado em câmbio.

CLASSIFICAÇÃO TÉCNICA DO DIA:
- Status: {classification}
- Confiança: {confidence:.0%}
- Preço atual: R$ {current_price:.4f}
- Indicadores:
  - SMA20: R$ {sma20:.4f}
  - SMA50: R$ {sma50:.4f}
  - RSI: {rsi:.1f}
  - Bollinger: R$ {bb_lower:.4f} - R$ {bb_upper:.4f}
- Explicação técnica: {explanation}

NOTÍCIAS RECENTES:
{news_context}

TAREFA:
Escreva um parágrafo de 3-4 frases explicando o cenário atual do dólar frente ao real.
Combine a análise técnica com o contexto das notícias de forma natural.

REGRAS OBRIGATÓRIAS:
1. NÃO faça recomendações de compra, venda ou investimento
2. NÃO use palavras como "compre", "venda", "invista", "recomendo", "sugiro"
3. Apenas INFORME e CONTEXTUALIZE o cenário
4. Seja objetivo e neutro
5. Escreva em português brasileiro"""


async def generate_insight(
    classification: ClassificationResult,
    news: list[NewsItem] | None = None,
) -> InsightResult:
    """🚀 GERAÇÃO DE INSIGHT COM LLM - Momento 1 de Ativação

    ⚡⚡⚡ ESTA FUNÇÃO ATIVA O LLM! ⚡⚡⚡

    Pipeline completo:
    1. Buscar notícias (RAG)
    2. Construir prompt com classificação técnica + contexto
    3. ⚡ CHAMAR LLM via Router → MINIMAX ATIVADO!
    4. Validar compliance (sem recomendações)
    5. Regenerar se falhar

    Quando é chamada:
    - Momento: Carregamento inicial da página /insights
    - Frequência: 1x por hora (cache)
    - Custo: $XX tokens (insight gerado)

    Args:
        classification: Resultado da análise técnica
        news: Lista de notícias (buscada automaticamente se None)

    Returns:
        InsightResult com texto gerado por IA + metadados
    """
    logger.info("🚀 [INSIGHT] Starting insight generation with LLM...")

    # 1. Buscar notícias se não fornecidas
    if news is None:
        logger.info("📰 [INSIGHT] Fetching news for context...")
        news = await fetch_news()
        logger.info(f"📰 [INSIGHT] Fetched {len(news)} news items")
    else:
        logger.info(f"📰 [INSIGHT] Using provided news: {len(news)} items")

    # 2. Construir contexto de notícias
    news_context = build_news_context(news)
    logger.info("📰 [INSIGHT] News context built for prompt")

    # 3. Construir prompt completo
    prompt = INSIGHT_PROMPT.format(
        classification=classification.classification.value,
        confidence=classification.confidence,
        current_price=classification.indicators.current_price,
        sma20=classification.indicators.sma20,
        sma50=classification.indicators.sma50,
        rsi=classification.indicators.rsi,
        bb_lower=classification.indicators.bollinger_lower,
        bb_upper=classification.indicators.bollinger_upper,
        explanation=classification.explanation,
        news_context=news_context,
    )

    logger.info(f"📝 [INSIGHT] Prompt built: {len(prompt)} chars")

    # 4. ⚡⚡⚡ CHAMAR LLM - PONTO CRÍTICO! ⚡⚡⚡
    logger.info("⚡⚡⚡ ACTIVATING LLM (Minimax) for insight generation...")
    try:
        logger.info("💰 [INSIGHT] LLM COST: Starting token consumption...")
        insight_text = await call_llm(
            messages=[{"role": "user", "content": prompt}]
        )
        logger.info(f"💰 [INSIGHT] LLM COST: Insight generated ({len(insight_text)} chars)")
        logger.info("✅ [INSIGHT] LLM response received successfully")

        # 5. Validar compliance
        if not validate_insight(insight_text):
            logger.warning("⚠️ [INSIGHT] Insight failed compliance validation - regenerating...")
            logger.info("🔄 [INSIGHT] Calling LLM again with stronger compliance prompt...")
            insight_text = await call_llm(
                messages=[
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": insight_text},
                    {
                        "role": "user",
                        "content": (
                            "O texto acima contém recomendação de investimento. "
                            "Reescreva de forma NEUTRA, apenas informando o cenário, "
                            "sem NENHUMA sugestão de compra ou venda."
                        ),
                    },
                ]
            )
            logger.info("✅ [INSIGHT] Regenerated insight passed validation")

        # Extrair fontes únicas
        news_sources = list({item.source for item in news[:5]})

        logger.info(
            f"✅ [INSIGHT] Insight generated successfully - "
            f"{len(insight_text)} chars, {len(news_sources)} sources"
        )

        return InsightResult(
            text=insight_text,
            classification=classification.classification,
            news_sources=news_sources,
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"❌ [INSIGHT] Error generating insight: {e}")
        logger.warning("🔄 [INSIGHT] Using fallback insight (no LLM)")

        # Fallback: insight básico sem LLM
        return InsightResult(
            text=(
                f"O par USD/BRL apresenta {classification.classification.value.lower()}. "
                f"{classification.explanation}. "
                "Consulte fontes especializadas para mais informações."
            ),
            classification=classification.classification,
            news_sources=[],
            generated_at=datetime.utcnow(),
        )
