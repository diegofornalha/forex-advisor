# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

## [0.2.0] - 2026-01-23

### Adicionado
- **RAG integrado ao Chat**: Notícias relevantes agora são buscadas automaticamente e incluídas no contexto do LLM
- **Pipeline de Ingestão de Notícias** (`app/news_ingestion.py`):
  - CLI: `python -m app.news_ingestion` para ingerir notícias
  - `--stats`: Mostra estatísticas do RAG
  - `--search <query>`: Testa busca semântica
  - `--clear`: Limpa todos os documentos
- **Testes Unitários Completos** (38 testes):
  - `tests/test_recommendation.py`: Testes de classificação de mercado
  - `tests/test_rag.py`: Testes do RAG SDK
  - `tests/test_api.py`: Testes de endpoints HTTP
- Configuração pytest (`pytest.ini`, `tests/conftest.py`)

### Melhorado
- Chat agora responde usando contexto real de notícias do mercado
- Threshold de similaridade RAG ajustado para melhor performance com português

## [0.1.0] - 2026-01-21

### Adicionado
- API FastAPI com endpoints `/api/v1/forex/usdbrl` e `/api/v1/forex/usdbrl/technical`
- Motor de recomendação com análise técnica (SMA, RSI, Bollinger Bands)
- Integração LLM via LiteLLM (Minimax)
- RAG SDK com sqlite-vec e fastembed
- Cache Redis com estratégia de TTL
- Chat WebSocket com execução de código E2B
- Containerização Docker & Compose
- Documentação OpenAPI automática
