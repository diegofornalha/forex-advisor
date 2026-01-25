# Status do Projeto - Forex Advisor

> Mapa completo de tudo que está implementado e funcionando.

**Versão Atual**: v0.4.2
**Última Atualização**: 2026-01-23
**Status**: Pronto para avaliação de produção

---

## 1. Visão Geral

O Forex Advisor é um assistente de análise de câmbio USD/BRL que combina:
- Análise técnica automatizada
- IA generativa para insights
- Chat interativo com execução de código
- RAG para contexto de notícias

---

## 2. Arquitetura Implementada

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│  │  Dashboard  │ │    Chat     │ │  Indicadores│                │
│  │  Insights   │ │  WebSocket  │ │   Técnicos  │                │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘                │
│         │               │               │                        │
│         │    localStorage (persistência chat)                    │
│         │         retry automático WebSocket                     │
└─────────┼───────────────┼───────────────┼────────────────────────┘
          │               │               │
          ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Rate Limiting                         │    │
│  │                  (100 req/min por IP)                    │    │
│  └─────────────────────────────────────────────────────────┘    │
│                              │                                   │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐       │
│  │  /health  │ │ /api/v1/  │ │ /ws/chat  │ │ /metrics  │       │
│  │           │ │  forex/   │ │           │ │   /llm    │       │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘       │
│        │             │             │             │               │
│  ┌─────┴─────────────┴─────────────┴─────────────┴─────┐        │
│  │                    LLM Router                        │        │
│  │    ┌──────────┐   ┌──────────┐   ┌──────────┐      │        │
│  │    │ Minimax  │──▶│ Vertex   │──▶│Anthropic │      │        │
│  │    │(primary) │   │  (2nd)   │   │  (3rd)   │      │        │
│  │    └────┬─────┘   └────┬─────┘   └────┬─────┘      │        │
│  │         │Circuit       │Circuit       │Circuit      │        │
│  │         │Breaker       │Breaker       │Breaker      │        │
│  └─────────┴──────────────┴──────────────┴─────────────┘        │
│                              │                                   │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐       │
│  │  yfinance │ │   Redis   │ │    RAG    │ │    E2B    │       │
│  │  (dados)  │ │  (cache)  │ │(sqlite-vec)│ │ (sandbox) │       │
│  └───────────┘ └───────────┘ └───────────┘ └───────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Endpoints da API

### REST API

| Método | Endpoint | Descrição | Status |
|--------|----------|-----------|--------|
| GET | `/` | Info da API | ✅ |
| GET | `/health` | Health check expandido | ✅ |
| GET | `/docs` | Swagger UI | ✅ |
| GET | `/openapi.json` | OpenAPI schema | ✅ |
| GET | `/api/v1/forex/usdbrl` | Análise completa com insight | ✅ |
| GET | `/api/v1/forex/usdbrl/technical` | Apenas análise técnica | ✅ |
| GET | `/api/v1/chat/session/{id}` | Histórico de sessão | ✅ |
| GET | `/metrics/llm` | Métricas do LLM Router | ✅ |

### WebSocket

| Endpoint | Descrição | Status |
|----------|-----------|--------|
| `/ws/chat/{session_id}` | Chat streaming com execução de código | ✅ |
| `/ws/docs/{session_id}` | Chat de documentação interativa | ✅ |

### SSE (Server-Sent Events)

| Endpoint | Descrição | Status |
|----------|-----------|--------|
| `/sse/docs/{request_id}` | Streaming de resposta do docs chat em tempo real | ✅ |

### Parâmetros de Query

| Endpoint | Parâmetro | Descrição |
|----------|-----------|-----------|
| `/api/v1/forex/usdbrl` | `force_refresh=true` | Ignora cache |
| `/api/v1/forex/usdbrl/technical` | `force_refresh=true` | Ignora cache |

---

## 4. Funcionalidades por Módulo

### 4.1 Análise Técnica

| Feature | Descrição | Status |
|---------|-----------|--------|
| SMA 20 | Média móvel 20 períodos | ✅ |
| SMA 50 | Média móvel 50 períodos | ✅ |
| RSI 14 | Índice de força relativa | ✅ |
| Bollinger Bands | Bandas superior/inferior | ✅ |
| Classificação | Alta/Baixa/Neutro/Volatilidade | ✅ |
| Confiança | Score 0-1 da classificação | ✅ |
| Explicação | Texto explicativo da decisão | ✅ |
| Feature Importance | Peso de cada indicador | ✅ |

### 4.2 LLM e IA

| Feature | Descrição | Status |
|---------|-----------|--------|
| Geração de Insights | Texto contextualizado | ✅ |
| Validação Compliance | Sem recomendação de compra/venda | ✅ |
| Fallback Chain | Minimax → Vertex AI → Anthropic | ✅ |
| Circuit Breaker | 3 falhas = open, 60s recovery | ✅ |
| Streaming | Resposta em tempo real | ✅ |
| Sanitização | API keys não expostas em logs | ✅ |

### 4.3 Chat Interativo

| Feature | Descrição | Status |
|---------|-----------|--------|
| WebSocket Streaming | Resposta chunk a chunk | ✅ |
| Execução de Código | Via E2B sandbox | ✅ |
| Validação de Código | Whitelist de imports | ✅ |
| Padrões Perigosos | Bloqueio de eval, exec, etc | ✅ |
| Sessões | UUID validado | ✅ |
| Limite de Mensagem | 10KB máximo | ✅ |
| Retry Automático | Reconexão em falha | ✅ |
| Persistência | localStorage 24h | ✅ |

### 4.4 RAG (Retrieval Augmented Generation)

| Feature | Descrição | Status |
|---------|-----------|--------|
| Embeddings | BAAI/bge-small-en-v1.5 | ✅ |
| Vector Store | sqlite-vec | ✅ |
| Busca Semântica | Top-K por similaridade | ✅ |
| Deduplicação | Hash de conteúdo | ✅ |
| Connection Pool | Conexão persistente | ✅ |
| WAL Mode | Melhor concorrência | ✅ |
| Preload Model | Carrega no startup | ✅ |
| News Ingestion | CLI para ingerir notícias do Google News RSS | ✅ |
| News Automático | Scheduler para ingestion periódico | ⏳ v1.x |

**⚠️ Onde o RAG é usado:**

| Funcionalidade | Usa RAG? | Fonte de dados |
|----------------|----------|----------------|
| **Chat Principal** (`/ws/chat`) | ✅ Sim | Notícias ingeridas (Google News RSS) |
| **Docs Chat** (`/ws/docs`) | ❌ Não | Arquivos .md direto no prompt |

O RAG atualmente é usado **apenas para notícias** no chat principal de análise de mercado.
O Docs Chat lê arquivos .md diretamente (context stuffing) - ver seção 4.5.

**Banco Vetorial: SQLite-Vec**

| Solução | Tipo | Complexidade | Custo | Melhor para |
|---------|------|-------------|-------|-------------|
| **SQLite-Vec** (atual) | Extensão SQLite | ⭐ Simples | Grátis | MVP, projetos pequenos |
| Milvus | Banco vetorial dedicado | ⭐⭐⭐ Complexo | Grátis/Self-host | Escala média |
| Pinecone | Cloud service | ⭐⭐ Moderado | $$$ Pago | Escala enterprise |

**Por que SQLite-Vec para v0.x?**
- ✅ **Leve**: Extensão do SQLite, não precisa serviço separado
- ✅ **Simples**: Zero dependências externas, tudo em 1 arquivo
- ✅ **MVP**: Ideal para validar a POC sem over-engineering
- ✅ **Integrado**: Roda no mesmo processo do FastAPI

**Migração futura (v1.x+):**
- Quando escalar em volume de dados ou usuários
- Avaliar custo-benefício vs. complexidade
- Opções: Milvus (self-host) ou Pinecone (cloud)

**CLI de News Ingestion:**
```bash
python -m app.news_ingestion              # Ingesta notícias (Google News RSS)
python -m app.news_ingestion --stats      # Mostra estatísticas do RAG
python -m app.news_ingestion --search "dólar"  # Testa busca semântica
python -m app.news_ingestion --clear      # Limpa todos os dados
```

### 4.5 Docs Chat (Documentação Interativa)

| Feature | Descrição | Status |
|---------|-----------|--------|
| Hybrid Streaming (WebSocket + SSE) | WebSocket para envio, SSE para recebimento em tempo real | ✅ |
| Knowledge Base | Docs .md como contexto no system prompt | ✅ |
| Guardrails Anti-Alucinação | Validação de respostas antes de enviar | ✅ |
| Detecção de Padrões | Regex para ofertas de criar, cloud providers | ✅ |
| Fallback Response | Mensagem padrão se info não documentada | ✅ |
| Sessões Persistentes | Redis + memory fallback | ✅ |
| Sugestões Pré-definidas | Perguntas comuns para começar | ✅ |
| Indicador de Conexão | Status visual do WebSocket | ✅ |

**⚠️ Importante: Docs Chat NÃO usa RAG**

O Docs Chat usa **context stuffing** (arquivos .md direto no system prompt), não RAG:

```
docs/*.md → load_documentation() → System Prompt → LLM
```

| Aspecto | Docs Chat | Chat Principal |
|---------|-----------|----------------|
| **Usa RAG?** | ❌ Não | ✅ Sim |
| **Como funciona** | Lê .md e coloca no prompt | Busca semântica no RAG |
| **Escalabilidade** | Limitado (tokens) | Escala bem |
| **Atualização** | Automática (lê arquivos) | Precisa re-ingerir |

**Por que não usa RAG?**
- **POC/Desenvolvimento**: Docs mudam frequentemente, context stuffing é mais prático
- **Tamanho atual**: Docs cabem no limite de tokens do LLM
- **Simplicidade**: Não precisa re-ingerir a cada mudança de documentação

**Evolução futura (v2.0+)**:
- Quando documentação estiver consolidada e estável
- Migrar para RAG híbrido (docs críticos no prompt + RAG para o resto)
- Permite escalar para documentação maior

**Arquitetura de Streaming SSE Híbrido:**

```
┌─────────────────┐     WebSocket      ┌─────────────────┐
│    Frontend     │ ──────────────────▶│     Backend     │
│  (useDocsChat)  │   envio mensagem   │  (docs_chat.py) │
│                 │                     │                 │
│                 │◀────────────────── │                 │
│                 │   stream_url       │                 │
│                 │                     │                 │
│                 │        SSE         │                 │
│   EventSource   │◀═══════════════════│ /sse/docs/{id}  │
│                 │   chunks em tempo  │                 │
│                 │       real         │                 │
└─────────────────┘                     └─────────────────┘
```

**Fluxo:**
1. Cliente envia mensagem via WebSocket
2. Backend gera `request_id` único e envia `stream_url` via WebSocket
3. Cliente conecta ao endpoint SSE `/sse/docs/{request_id}`
4. Backend aguarda conexão SSE antes de iniciar geração LLM
5. Chunks são enviados em tempo real via SSE
6. Evento `done` finaliza o streaming com validação de guardrails

**Arquivos envolvidos:**
- Backend: `app/docs_chat.py` - endpoint SSE, geração streaming
- Frontend: `src/hooks/useDocsChat.ts` - EventSource, acúmulo de chunks
- Frontend: `src/components/chat/ChatMessage.tsx` - renderização progressiva

**Guardrails implementados:**
- Bloqueia ofertas de criar documentação
- Bloqueia sugestões de tecnologias não documentadas
- Bloqueia menções a cloud providers (AWS, Azure, GCP, etc.)
- Substitui respostas com alucinação pela mensagem padrão

### 4.6 Cache

| Feature | Descrição | Status |
|---------|-----------|--------|
| Redis | Cache principal | ✅ |
| Memory Fallback | Se Redis indisponível | ✅ |
| TTL Insight | 1 hora | ✅ |
| TTL Technical | 4 horas | ✅ |
| TTL yfinance | 5 minutos | ✅ |
| Header X-Cache | HIT/MISS | ✅ |

### 4.7 Segurança

| Feature | Descrição | Status |
|---------|-----------|--------|
| Rate Limiting | 100 req/min por IP | ✅ |
| CORS Restrito | Lista de origens permitidas | ✅ |
| UUID Validation | Session ID validado | ✅ |
| Code Sandbox | E2B isolado | ✅ |
| Input Validation | Pydantic models | ✅ |
| Error Sanitization | Sem API keys em logs | ✅ |

---

## 5. Testes

| Categoria | Quantidade | Cobertura |
|-----------|------------|-----------|
| test_api.py | 16 | Endpoints REST |
| test_chat.py | 25 | Validação, UUID, extração |
| test_llm_router.py | 11 | Circuit breaker, sanitização |
| test_rag.py | 10 | CRUD, busca semântica |
| test_recommendation.py | 17 | Indicadores, classificação |
| **TOTAL** | **79** | ✅ **100% passando** |

Ver detalhes em [TESTS.md](TESTS.md).

---

## 6. Configuração

### Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|----------|-------------|-----------|
| `MINIMAX_TOKEN` | Sim* | Token do Minimax |
| `VERTEX_API_KEY` | Não | API key Vertex AI |
| `ANTHROPIC_API_KEY` | Não | API key Anthropic |
| `REDIS_URL` | Não | URL Redis (default: localhost) |
| `E2B_API_KEY` | Não | Para execução de código |
| `RATE_LIMIT_REQUESTS` | Não | Limite por minuto (default: 100) |

*Pelo menos um LLM deve estar configurado.

Ver `.env.example` para lista completa.

---

## 7. Dependências Externas

| Serviço | Obrigatório | Uso |
|---------|-------------|-----|
| Redis | Não (tem fallback) | Cache |
| Minimax | Sim* | LLM primário |
| Vertex AI | Não | LLM fallback |
| Anthropic | Não | LLM fallback |
| E2B | Não | Execução de código |
| yfinance | Sim | Dados de mercado |

---

## 8. O que NÃO está implementado (ou parcialmente)

| Feature | Status Atual | Versão Planejada | Notas |
|---------|--------------|------------------|-------|
| Prometheus | ❌ Não existe | v1.0 | Débito médio |
| Testes E2E | ❌ Não existe | v1.0 | Débito médio |
| CI/CD | ❌ Não existe | v1.0 | Débito médio |
| News Scheduler | ⏳ CLI existe, falta automação | v1.x | `python -m app.news_ingestion` funciona |
| RAG Cleanup | ⏳ CLI existe, falta automação | v1.x | `--clear` funciona manual |
| Docs Chat via RAG | ⏳ Usa context stuffing | v2.0 | Migrar quando docs estiverem consolidados |
| SQLite-Vec Migration | ⏳ Leve, simples, funcional | v2.x+ | Migrar para Milvus/Pinecone quando escalar |
| Multi-asset (EUR, BTC) | ❌ Não existe | v2.0 | Feature futura |
| Backtesting | ❌ Não existe | v2.0 | Feature futura |
| Alertas | ❌ Não existe | v2.0 | Feature futura |
| Agent Mode | ❌ Não existe | v3.0 | Feature futura |

---

## 9. Como Executar

### Backend

```bash
cd /Users/2a/.claude/forex-advisor
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd /Users/2a/.claude/forex-advisor-front/prototipo
npm install
npm run dev
```

### Testes

```bash
pytest tests/ -v
```

---

## 10. Arquivos Principais

```
forex-advisor/
├── app/
│   ├── main.py           # FastAPI app, rate limiting
│   ├── config.py         # Configurações (env vars)
│   ├── chat.py           # WebSocket, validação código
│   ├── docs_chat.py      # Docs chat com guardrails
│   ├── llm_router.py     # Fallback chain, circuit breaker
│   ├── recommendation.py # Análise técnica
│   ├── insights.py       # Geração de insights
│   ├── sandbox.py        # E2B integration
│   ├── cache.py          # Redis + fallback
│   ├── models.py         # Pydantic models
│   └── rag_sdk/
│       └── rag.py        # RAG com sqlite-vec
├── tests/
│   ├── test_api.py
│   ├── test_chat.py
│   ├── test_llm_router.py
│   ├── test_rag.py
│   └── test_recommendation.py
├── docs/
│   ├── STATUS.md         # Este arquivo
│   ├── TECH-DEBT.md      # Débitos técnicos
│   ├── TESTS.md          # Documentação de testes
│   ├── ROADMAP.md           # Roadmap de versões
│   ├── specs/               # Especificações por versão
│   └── archive/             # Docs históricos
├── requirements.txt      # Prod dependencies
├── requirements-dev.txt  # Dev dependencies
├── .env.example
├── README.md
└── CHANGELOG.md
```

---

## 11. Histórico

| Data | Versão | Mudanças |
|------|--------|----------|
| 2026-01-22 | v0.2 | POC funcional |
| 2026-01-23 | v0.3 | Frontend cleanup, localStorage |
| 2026-01-23 | v0.4 | Fallback chain, circuit breaker, 79 testes |
| 2026-01-23 | v0.4.1 | Docs Chat com guardrails anti-alucinação |
| 2026-01-23 | v0.4.2 | SSE Hybrid Streaming para Docs Chat em tempo real |
| 2026-01-23 | v0.4.2 | Documentação: RAG vs Docs Chat, escolha SQLite-Vec, migração futura |

---

> **Próximo passo**: Avaliar se está pronto para v1.0 (produção). Ver [TECH-DEBT.md](TECH-DEBT.md) para análise de débitos.
