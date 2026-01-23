# Plano 02: Insights Generator

## Objetivo
Criar `insights_generator.py` usando o RAG simplificado para buscar notícias e gerar insights.

## Arquivo
`src/insights_generator.py`

## Integração com RAG SDK

```python
import sys
sys.path.insert(0, "/Users/2a/.claude")
from claude_rag_sdk_python import SimpleRAG
```

## Fluxo

```
1. Buscar notícias (scraping/API)
2. Ingerir no RAG (add_text)
3. Buscar contexto relevante (search)
4. Gerar insight com LLM (query ou direto)
```

## Funções

### 1. News Fetcher

```python
async def fetch_news(query: str = "dólar real câmbio", limit: int = 5) -> list[NewsItem]:
    """Busca notícias recentes.

    Opções:
    - Google News RSS (grátis, sem API key)
    - NewsAPI (requer key)
    - Web scraping simples
    """
```

### 2. News Ingestor

```python
async def ingest_news(rag: SimpleRAG, news: list[NewsItem]) -> int:
    """Ingere notícias no RAG.

    Returns:
        Número de notícias indexadas
    """
    count = 0
    for item in news:
        doc_id = await rag.add_text(
            content=f"{item.title}. {item.description}",
            source=item.source
        )
        if doc_id:
            count += 1
    return count
```

### 3. Insight Generator

```python
async def generate_insight(
    classification: ClassificationResult,
    rag: SimpleRAG
) -> InsightResult:
    """Gera insight contextualizado.

    1. Busca notícias relevantes no RAG
    2. Combina com classificação técnica
    3. Gera parágrafo via LLM
    """
```

## Prompt Template

```python
INSIGHT_PROMPT = """
Você é um analista de mercado da Remessa Online.

CLASSIFICAÇÃO TÉCNICA:
- Status: {classification}
- Indicadores: {indicators}
- Explicação: {explanation}

NOTÍCIAS RECENTES:
{news_context}

TAREFA:
Escreva um parágrafo de 3-4 frases explicando o cenário atual do dólar.
Combine a análise técnica com o contexto das notícias.

IMPORTANTE: NÃO faça recomendações de compra ou venda.
Apenas INFORME e CONTEXTUALIZE o cenário.
"""
```

## Models (em models.py)

```python
@dataclass
class NewsItem:
    title: str
    description: str
    source: str
    published_at: datetime

@dataclass
class InsightResult:
    text: str
    classification: MarketClassification
    news_sources: list[str]
    generated_at: datetime
```

## Validação de Output

```python
def validate_insight(text: str) -> bool:
    """Garante que não há recomendações."""
    forbidden = ["compre", "venda", "invista", "recomendo", "sugiro"]
    return not any(word in text.lower() for word in forbidden)
```

## Dependências
```
anthropic>=0.18.0
requests>=2.31.0
feedparser>=6.0.0  # Para RSS
```

## Critérios de Sucesso
- [ ] fetch_news funcionando
- [ ] Notícias ingeridas no RAG
- [ ] Busca semântica retornando contexto
- [ ] Insight gerado sem recomendações
- [ ] Validação de output funcionando
