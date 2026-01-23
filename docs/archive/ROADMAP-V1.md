# Plano de Implementação: Forex Advisor v1.0

## Visão Geral
Evolução do MVP (v0.1) para uma versão mais robusta com fallbacks de LLM, suporte a múltiplos ativos, e melhorias de UX baseadas nos testes de stress.

## Especificação Vinculada
- POC v0.1: `/Users/2a/.claude/plans/enumerated-squishing-hamming.md`
- Backend: `/Users/2a/.claude/forex-advisor`
- Frontend: `/Users/2a/.claude/forex-advisor-front/prototipo`

---

## Resumo de Requisitos

### Requisitos Funcionais

#### LLM & Fallbacks
- [ ] Fallback automático para Vertex AI quando Minimax falhar
- [ ] Fallback para Anthropic Claude como terceira opção
- [ ] Health check de providers com circuit breaker
- [ ] Métricas de latência e disponibilidade por provider

#### Suporte a Múltiplos Ativos
- [ ] Adicionar suporte a EUR/BRL
- [ ] Adicionar suporte a BTC/BRL (crypto)
- [ ] Seletor de ativo na interface
- [ ] Dados OHLC por ativo no sandbox

#### Chat Inteligente
- [ ] Detecção automática de intenção (análise vs pergunta geral)
- [ ] Respostas contextuais quando usuário pergunta sobre ativos não suportados
- [ ] Sugestões de perguntas baseadas no ativo selecionado
- [ ] Histórico de chat persistente (além da sessão)

#### RAG - Retrieval Augmented Generation
- [ ] Integrar RAG SDK existente (`app/rag_sdk/`) com o chat
- [ ] Pipeline de ingestão de notícias (fontes: G1, Valor, InfoMoney, etc)
- [ ] Busca semântica de contexto antes de responder
- [ ] Citar fontes nas respostas do chat
- [ ] Atualização automática do índice (cron/scheduler)
- [ ] Cache de embeddings para queries frequentes

#### Análises Avançadas
- [ ] Backtesting de estratégias simples
- [ ] Correlação entre ativos
- [ ] Alertas de preço por email/webhook
- [ ] Exportação de análises (PDF/CSV)

### Requisitos Não Funcionais
- **Performance**: Resposta do chat < 3s para streaming inicial
- **Disponibilidade**: 99.5% uptime com fallbacks de LLM
- **Escalabilidade**: Suportar 100 sessões simultâneas
- **Segurança**: Rate limiting por IP e sessão

### Critérios de Aceitação
- [ ] Chat funciona mesmo quando Minimax está offline (fallback ativo)
- [ ] Usuário pode alternar entre USD/BRL, EUR/BRL e BTC/BRL
- [ ] Código Python executa com dados do ativo selecionado
- [ ] Métricas de uso disponíveis em dashboard

---

## Abordagem Técnica

### Arquitetura v1

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite)                                    │
│  ├── Seletor de Ativo                                       │
│  ├── Chat com histórico persistente                         │
│  ├── Fontes citadas (badges com links)                      │
│  └── Dashboard de métricas                                  │
└─────────────────────┬───────────────────────────────────────┘
                      │ WebSocket + REST API
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                          │
│  ├── LLM Router com Fallback Chain                          │
│  │   ├── Primary: Minimax                                   │
│  │   ├── Secondary: Vertex AI                               │
│  │   └── Tertiary: Anthropic Claude                         │
│  ├── RAG Service (busca semântica de notícias)              │
│  │   ├── sqlite-vec (vetores)                               │
│  │   └── fastembed (embeddings)                             │
│  ├── News Ingestion (pipeline de notícias)                  │
│  ├── Asset Service (USD/BRL, EUR/BRL, BTC/BRL)              │
│  ├── Metrics Collector (Prometheus)                         │
│  └── E2B Sandbox (multi-asset)                              │
└─────────────────────┬───────────────────────────────────────┘
                      │
    ┌─────────┬───────┼───────┬─────────┐
    ▼         ▼       ▼       ▼         ▼
┌───────┐ ┌───────┐ ┌─────┐ ┌─────┐ ┌───────┐
│ Redis │ │ RAG   │ │ yf  │ │ E2B │ │ News  │
│ Cache │ │sqlite │ │+API │ │ Box │ │ Sites │
└───────┘ └───────┘ └─────┘ └─────┘ └───────┘
```

### Stack Tecnológico
- **Backend**: FastAPI, LiteLLM, Redis, Prometheus
- **Frontend**: React, Vite, TailwindCSS, shadcn/ui
- **LLMs**: Minimax (primary), Vertex AI (fallback), Anthropic (fallback)
- **Data**: yfinance, CoinGecko API (crypto)
- **Sandbox**: E2B

### Decisões de Design Principais

1. **Fallback Chain Pattern**: LiteLLM já suporta fallbacks nativamente via `fallbacks` config
2. **Multi-Asset via Strategy Pattern**: Cada ativo implementa interface comum de data fetching
3. **Métricas com Prometheus**: Fácil integração e visualização com Grafana

---

## Fases de Implementação

### Fase 1: Fallbacks de LLM

**Objetivo**: Garantir disponibilidade do chat mesmo com falhas de provider

**Tarefas**:
- [ ] Configurar Vertex AI no LiteLLM router
- [ ] Configurar Anthropic Claude no LiteLLM router
- [ ] Implementar fallback chain com ordem de prioridade
- [ ] Adicionar circuit breaker para providers com falha
- [ ] Criar health check endpoint `/api/v1/health/llm`
- [ ] Logging de qual provider foi usado em cada request

**Entregáveis**: Chat resiliente com 3 providers

---

### Fase 2: Métricas e Observabilidade

**Objetivo**: Visibilidade sobre uso e performance do sistema

**Tarefas**:
- [ ] Integrar Prometheus client no FastAPI
- [ ] Métricas de latência por endpoint
- [ ] Métricas de uso de LLM (tokens, provider, tempo)
- [ ] Métricas de execução de código (sucesso/falha, tempo)
- [ ] Dashboard básico com métricas principais
- [ ] Endpoint `/metrics` para Prometheus scraping

**Entregáveis**: Dashboard de métricas operacionais

---

### Fase 3: Suporte a Múltiplos Ativos

**Objetivo**: Expandir análises para EUR/BRL e BTC/BRL

**Tarefas**:
- [ ] Criar `AssetService` com interface comum
- [ ] Implementar `UsdBrlAsset`, `EurBrlAsset`, `BtcBrlAsset`
- [ ] Integrar CoinGecko API para dados de crypto
- [ ] Atualizar sandbox para receber ativo como parâmetro
- [ ] Atualizar prompt do chat com contexto do ativo selecionado
- [ ] Criar seletor de ativo no frontend
- [ ] Persistir ativo selecionado na sessão

**Entregáveis**: Análise funcional para 3 ativos

---

### Fase 4: RAG - Integração com Chat

**Objetivo**: Enriquecer respostas do chat com contexto de notícias via busca semântica

**Contexto**: RAG SDK já existe em `app/rag_sdk/rag.py` (sqlite-vec + fastembed)

**Tarefas**:

#### 4.1 Pipeline de Ingestão de Notícias
- [ ] Criar `app/news_ingestion.py` - serviço de coleta de notícias
- [ ] Implementar scrapers para fontes (G1 Economia, Valor, InfoMoney, BCB)
- [ ] Filtrar notícias relevantes (USD, dólar, câmbio, Selic, Fed)
- [ ] Agendar ingestão periódica (cron: a cada 2h)
- [ ] Deduplicação via hash de conteúdo (já existe no RAG SDK)
- [ ] Limitar índice aos últimos 7 dias (cleanup automático)

#### 4.2 Integração RAG no Chat
- [ ] Importar `SimpleRAG` em `chat.py`
- [ ] Criar função `get_news_context(query)` para buscar contexto
- [ ] Injetar contexto de notícias no system prompt
- [ ] Adicionar campo `sources` na resposta do chat
- [ ] Exibir fontes citadas no frontend (badge com links)

#### 4.3 Otimizações
- [ ] Cache de embeddings para queries frequentes (Redis)
- [ ] Limite de tokens no contexto injetado (max 500 tokens)
- [ ] Fallback gracioso se RAG estiver vazio/offline
- [ ] Métricas de uso do RAG (hits, latência, relevância)

**Arquivos a criar/modificar**:
```
app/
├── news_ingestion.py      # NOVO - pipeline de ingestão
├── chat.py                # MODIFICAR - integrar RAG
├── rag_sdk/
│   └── rag.py             # EXISTENTE - já funcional
└── config.py              # MODIFICAR - configs RAG
```

**Exemplo de integração no chat.py**:
```python
from .rag_sdk import SimpleRAG

async def get_news_context(query: str, top_k: int = 3) -> str:
    rag = SimpleRAG(settings.rag_db_path)
    results = await rag.search(query, top_k=top_k)
    if not results:
        return ""
    return "\n".join([f"[{r.source}]: {r.content}" for r in results])

# No build_system_prompt():
news_context = await get_news_context(user_message)
prompt += f"\n\nNOTÍCIAS RECENTES:\n{news_context}"
```

**Configurações novas (.env)**:
```env
RAG_DB_PATH=./data/rag.db
RAG_TOP_K=3
RAG_MAX_TOKENS=500
NEWS_SOURCES=g1,valor,infomoney,bcb
NEWS_UPDATE_INTERVAL=7200  # 2 horas
```

**Entregáveis**: Chat com contexto de notícias, fontes citadas

**Dependências**:
- beautifulsoup4, httpx (scraping)
- APScheduler ou similar (agendamento)

**Riscos**:
| Risco | Mitigação |
|-------|-----------|
| Sites bloquearem scraping | Usar headers realistas, rate limiting |
| Notícias irrelevantes no contexto | Filtro de relevância por similaridade |
| Latência adicional no chat | Cache agressivo, busca async |

---

### Fase 5: Melhorias de UX (baseadas no stress test)

**Objetivo**: Refinar experiência baseado nos aprendizados da POC

**Tarefas**:
- [ ] Melhorar detecção de intenção (análise vs conversa)
- [ ] Respostas mais informativas para perguntas fora do escopo
- [ ] Sugestões de perguntas dinâmicas por ativo
- [ ] Indicador visual de qual LLM está respondendo
- [ ] Retry automático no frontend em caso de erro
- [ ] Mensagens de erro mais amigáveis

**Entregáveis**: UX refinada e resiliente

---

### Fase 6: Features Avançadas (opcional)

**Objetivo**: Funcionalidades diferenciadas

**Tarefas**:
- [ ] Backtesting de estratégias simples via chat
- [ ] Correlação entre ativos selecionados
- [ ] Alertas de preço (email/webhook)
- [ ] Exportação de análises para PDF/CSV
- [ ] Histórico de chat persistente (banco de dados)

**Entregáveis**: Features de valor agregado

---

## Dependências

### Dependências Externas
- Vertex AI: Requer conta GCP com billing
- Anthropic: Requer API key
- CoinGecko: API pública (rate limited)

### Dependências Internas
- POC v0.1 estável e funcional

### Bloqueios
- Nenhum no momento (POC em fase final de testes)

---

## Riscos e Mitigação

### Risco 1: Rate limits de APIs externas
- **Probabilidade**: Alta
- **Impacto**: Médio
- **Mitigação**: Cache agressivo, fallbacks, retry com backoff

### Risco 2: Custos de LLM em produção
- **Probabilidade**: Alta
- **Impacto**: Alto
- **Mitigação**: Usar Minimax (mais barato) como primary, limitar tokens, cache de respostas

### Risco 3: Latência com múltiplos fallbacks
- **Probabilidade**: Média
- **Impacto**: Médio
- **Mitigação**: Streaming desde o início, timeout agressivo, health checks proativos

---

## Configurações Novas (.env)

```env
# LLM Fallbacks
VERTEX_AI_PROJECT=your-project
VERTEX_AI_LOCATION=us-central1
ANTHROPIC_API_KEY=sk-ant-...

# Multi-Asset
COINGECKO_API_KEY=optional-for-higher-limits
SUPPORTED_ASSETS=USDBRL,EURBRL,BTCBRL

# Metrics
PROMETHEUS_ENABLED=true
METRICS_PORT=9090

# Feature Flags
FEATURE_MULTI_ASSET=false
FEATURE_BACKTESTING=false
```

---

## Decisões Pendentes para v1

### Personalização do Agente
**Questão**: O agente deve ser mais flexível/aberto ou mais limitado/focado?

| Opção | Prós | Contras |
|-------|------|---------|
| **Aberto/Flexível** | Responde mais perguntas, UX mais natural | Mais difícil controlar qualidade, pode "alucinar" |
| **Limitado/Focado** | Respostas mais precisas, menos erros | Pode frustrar usuário com muitas recusas |
| **Híbrido** | Flexível para educação, limitado para análises | Mais complexo de implementar |

**Decisão**: A definir na v1 após mais feedback de usuários

### Escopo de Ativos
- Manter apenas USD/BRL ou expandir para outros?
- Se expandir, quais priorizar? (EUR/BRL, BTC/BRL, ações?)

### Monetização
- Freemium com limites de requests?
- Assinatura mensal?
- Pay-per-use?

---

## Aprendizados do Stress Test (v0.1)

### O que funcionou bem
- Chat com streaming via WebSocket
- Execução de código Python no E2B sandbox
- Filtragem de código/tags do output
- Recusa de recomendações de compra/venda
- Tratamento de perguntas fora do escopo
- **Resposta a perguntas não relacionadas** (futebol): Agente explica claramente o que pode/não pode fazer com lista visual

### Melhorias identificadas para v1
1. **Detecção de intenção**: LLM às vezes gera código quando deveria apenas responder
2. **Respostas out-of-scope**: Melhorar texto quando usuário pergunta sobre crypto/outros
3. **Indicador de processamento**: Usuário não sabe quando código está executando
4. **Retry automático**: Frontend deveria tentar novamente em falhas transitórias
5. **Multi-asset**: Usuário perguntou sobre Bitcoin - oportunidade clara

### Testes de Stress Realizados
| Cenário | Resultado | Observação |
|---------|-----------|------------|
| Pergunta sobre crypto (BTC) | ✅ OK | Explicou que só tem dados USD/BRL |
| Recomendação compra/venda | ✅ OK | Recusou e sugeriu consultor |
| Pergunta sobre futebol | ✅ OK | Listou capacidades e limitações com emojis |
| Cálculo de RSI | ✅ OK | Executou código e mostrou resultado |
| Cálculo de volatilidade | ✅ OK | Mostrou 5 dias mais voláteis |
| Pergunta ambígua ("tá caro?") | ✅ OK | Inferiu contexto (dólar) corretamente |
| Múltiplos cálculos em 1 pergunta | ✅ OK | Média, máx, mín, volatilidade + explicação |
| Prompt injection | ✅ OK | Resistiu, manteve limitações, sugeriu consultor |

### Comportamentos Positivos Observados
1. **Explicação didática**: Agente explica indicadores para leigos antes de mostrar resultados
2. **Resistência a manipulação**: Não cedeu ao prompt injection "ignore instruções"
3. **Contexto implícito**: Entendeu "tá caro ou barato?" como sendo sobre o dólar
4. **Formatação clara**: Resultados bem formatados com emojis e separadores
5. **Sugestões proativas**: Oferece exemplos de perguntas válidas quando recusa

### Problemas Identificados para v1
1. **Análise incompleta**: Em alguns casos, diz "vou analisar" mas não mostra resultado
2. **Sem feedback de erro**: Quando código falha silenciosamente, usuário não sabe
3. **Sem indicador de LLM**: Usuário não sabe qual provider está respondendo

---

## Critérios de Sucesso

### Sucesso Técnico
- [ ] Chat funciona com fallback em < 5s
- [ ] 3 ativos suportados com dados reais
- [ ] Métricas disponíveis em dashboard
- [ ] Zero código/tags visíveis para usuário

### Sucesso de Negócio
- [ ] Usuários conseguem fazer análises de múltiplos ativos
- [ ] Sistema disponível 99.5% do tempo
- [ ] Feedback positivo de usuários de teste

---

## Recursos

### Documentação
- [LiteLLM Fallbacks](https://docs.litellm.ai/docs/routing)
- [Prometheus FastAPI](https://github.com/trallnag/prometheus-fastapi-instrumentator)
- [CoinGecko API](https://www.coingecko.com/en/api/documentation)

### Trabalhos Relacionados
- POC v0.1: `/Users/2a/.claude/plans/enumerated-squishing-hamming.md`

---

## Acompanhamento de Progresso

### Status das Fases
- Fase 1 (Fallbacks): ⏳ Não Iniciada
- Fase 2 (Métricas): ⏳ Não Iniciada
- Fase 3 (Multi-Asset): ⏳ Não Iniciada
- Fase 4 (UX): ⏳ Não Iniciada
- Fase 5 (Avançadas): ⏳ Não Iniciada

**Progresso Geral**: 0% concluído

### Pré-requisito
- [x] POC v0.1 funcional e testada
