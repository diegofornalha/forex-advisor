"""Insight generator with news context and Claude LLM."""

import logging
from datetime import datetime
from urllib.parse import quote

import anthropic
import feedparser

from .config import settings
from .models import ClassificationResult, InsightResult, NewsItem

logger = logging.getLogger(__name__)

# Global Anthropic client (singleton)
_anthropic_client: anthropic.Anthropic | None = None

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


def get_anthropic_client() -> anthropic.Anthropic:
    """Return Anthropic client (singleton pattern)."""
    global _anthropic_client

    if _anthropic_client is None:
        _anthropic_client = anthropic.Anthropic(
            api_key=settings.anthropic_api_key,
        )

    return _anthropic_client


async def fetch_news(
    query: str = None,
    limit: int = None,
) -> list[NewsItem]:
    """Fetch news from Google News RSS feed.

    Args:
        query: Search term (default: settings.news_query)
        limit: Max number of news items (default: settings.news_limit)

    Returns:
        List of NewsItem objects
    """
    query = query or settings.news_query
    limit = limit or settings.news_limit

    # Google News RSS URL for Brazil
    encoded_query = quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=pt-BR&gl=BR&ceid=BR:pt-419"

    try:
        feed = feedparser.parse(url)
        news_items = []

        for entry in feed.entries[:limit]:
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

        logger.info(f"Fetched {len(news_items)} news items for '{query}'")
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
    """Generate contextualized insight using Claude LLM.

    Pipeline:
    1. Fetch news if not provided
    2. Build prompt with technical classification + news context
    3. Call Claude to generate insight
    4. Validate compliance (no investment recommendations)
    5. Regenerate if validation fails

    Args:
        classification: Technical analysis classification result
        news: List of news items (fetched automatically if not provided)

    Returns:
        InsightResult with generated text and metadata
    """
    # Fetch news if not provided
    if news is None:
        news = await fetch_news()

    # Build news context for prompt
    news_context = build_news_context(news)

    # Build full prompt
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

    # Call Claude API
    try:
        client = get_anthropic_client()
        response = client.messages.create(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        insight_text = response.content[0].text.strip()

        # Validate compliance
        if not validate_insight(insight_text):
            # Regenerate with stronger instruction if failed
            logger.warning("Insight failed validation, regenerating...")
            response = client.messages.create(
                model=settings.llm_model,
                max_tokens=settings.llm_max_tokens,
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
                ],
            )
            insight_text = response.content[0].text.strip()

        # Extract unique news sources
        news_sources = list({item.source for item in news[:5]})

        return InsightResult(
            text=insight_text,
            classification=classification.classification,
            news_sources=news_sources,
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Error generating insight: {e}")
        # Fallback: basic insight without LLM
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
