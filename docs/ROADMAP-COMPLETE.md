# Forex Advisor - Roadmap Completo

> Documento mestre de evolução do projeto Forex Advisor da POC (v0.2) até a versão de produção (v2.0).

## Sumário

- [Visão Geral](#visão-geral)
- [Estado Atual (v0.2)](#estado-atual-v02)
- [Roadmap de Versões](#roadmap-de-versões)
- [Matriz de Débitos Técnicos](#matriz-de-débitos-técnicos)
- [Dependências Entre Versões](#dependências-entre-versões)
- [Critérios de Promoção](#critérios-de-promoção)
- [Especificações Detalhadas](#especificações-detalhadas)

---

## Visão Geral

O Forex Advisor é um assistente de análise de câmbio USD/BRL que combina análise técnica com IA generativa para fornecer insights educacionais sobre o mercado de câmbio.

### Arquitetura Atual

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (React + Vite + TypeScript)                       │
│  ├── Componentes shadcn/ui                                  │
│  ├── React Query (cache)                                    │
│  ├── WebSocket (chat streaming)                             │
│  └── Tema dark (Binance-inspired)                           │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP + WebSocket
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  Backend (FastAPI + Python)                                 │
│  ├── /api/v1/forex/usdbrl (análise completa)               │
│  ├── /api/v1/forex/usdbrl/technical (apenas técnico)       │
│  ├── /ws/chat/{session_id} (chat com E2B)                  │
│  ├── LLM Router (Minimax via LiteLLM)                      │
│  ├── RAG SDK (sqlite-vec + fastembed)                      │
│  └── Cache (Redis + memory fallback)                        │
└─────────────────────────────────────────────────────────────┘
```

### Stack Tecnológico

| Camada | Tecnologias |
|--------|-------------|
| **Frontend** | React 18, TypeScript, Vite, TailwindCSS, shadcn/ui, React Query |
| **Backend** | FastAPI, Python 3.11+, LiteLLM, Pydantic |
| **LLM** | Minimax (primary), Vertex AI (fallback), Anthropic (fallback) |
| **Data** | yfinance, Redis, sqlite-vec, fastembed |
| **Sandbox** | E2B Code Interpreter |
| **Infra** | Docker, Docker Compose |

---

## Estado Atual (v0.2)

**Release Date**: 2026-01-23

### Funcionalidades Implementadas

| Categoria | Feature | Status |
|-----------|---------|--------|
| **API** | Endpoint de análise completa | ✅ |
| **API** | Endpoint apenas técnico | ✅ |
| **API** | Health check | ✅ |
| **Análise** | SMA 20/50 | ✅ |
| **Análise** | RSI 14 períodos | ✅ |
| **Análise** | Bollinger Bands | ✅ |
| **Análise** | Classificação automática | ✅ |
| **LLM** | Geração de insights | ✅ |
| **LLM** | Validação de compliance | ✅ |
| **Chat** | WebSocket streaming | ✅ |
| **Chat** | Execução de código (E2B) | ✅ |
| **RAG** | Busca semântica de notícias | ✅ |
| **RAG** | Pipeline de ingestão | ✅ |
| **Cache** | Redis + memory fallback | ✅ |
| **Testes** | 38 testes unitários | ✅ |
| **Frontend** | UI completa | ✅ |
| **Frontend** | Tema dark | ✅ |
| **Frontend** | Mock data para dev | ✅ |

### Débitos Técnicos Acumulados

```
FRONTEND (7 débitos):
├── DT-F1: Supabase configurado mas não usado
├── DT-F2: Recharts importado mas não usado
├── DT-F3: Transformações manuais (positives/risks)
├── DT-F4: Sem testes E2E
├── DT-F5: Sem indicador de LLM ativo
├── DT-F6: Sem retry automático no WebSocket
└── DT-F7: Sem persistência de chat

BACKEND (9 débitos):
├── DT-B1: Fallbacks de LLM não implementados [CRÍTICO]
├── DT-B2: Vertex AI/Anthropic só configurados [CRÍTICO]
├── DT-B3: Sem métricas Prometheus
├── DT-B4: Sem rate limiting
├── DT-B5: News ingestion manual
├── DT-B6: RAG cleanup não automático
├── DT-B7: Circuit breaker não implementado
├── DT-B8: bollinger_middle não exposto
└── DT-B9: Health check incompleto
```

---

## Roadmap de Versões

```
v0.2 (ATUAL)     v0.3           v0.4           v1.0           v2.0           v3.0
    │              │              │              │              │              │
    │  Frontend    │  Backend     │  Produção    │  Expansão    │  Agent       │
    │  Cleanup     │  Resiliência │  Ready       │              │  Mode        │
    │              │              │              │              │              │
    ├─────────────►├─────────────►├─────────────►├─────────────►├─────────────►│
    │              │              │              │              │              │
    │ POC          │ Código       │ LLM          │ Métricas     │ EUR/BRL      │ Planejador
    │ funcional    │ limpo        │ resiliente   │ Testes E2E   │ BTC/BRL      │ Executor
    │ RAG          │ Retry WS     │ Circuit      │ CI/CD        │ Backtesting  │ Verificador
    │ integrado    │ localStorage │ breaker      │ Docs API     │ Alertas      │ Agent Loop
    │              │ Status       │ Rate limit   │              │ Export       │ Auto-correção
```

### Resumo por Versão

| Versão | Foco | Escopo | Pré-requisito |
|--------|------|--------|---------------|
| **v0.3** | Frontend | Limpeza de código morto, UX resiliente | v0.2 |
| **v0.4** | Backend | LLM fallbacks, segurança básica | v0.3 |
| **v1.0** | Produção | Observabilidade, testes, CI/CD | v0.4 |
| **v2.0** | Expansão | Multi-asset, features avançadas | v1.0 |
| **v3.0** | Agent Mode | Planejador/Executor/Verificador | v2.0 |

---

## Matriz de Débitos Técnicos

### Priorização por Impacto vs Esforço

```
           IMPACTO ALTO
                │
    ┌───────────┼───────────┐
    │  DT-B1    │  DT-B3    │
    │  DT-B2    │  DT-B4    │
    │  DT-B7    │           │
    │           │           │
────┼───────────┼───────────┼──── ESFORÇO
    │  DT-F6    │  DT-F4    │
    │  DT-F7    │  DT-F3    │
    │  DT-B5    │           │
    │  DT-B9    │           │
    └───────────┼───────────┘
                │
           IMPACTO BAIXO

Quadrante Superior Esquerdo: FAZER PRIMEIRO (alto impacto, baixo esforço)
Quadrante Superior Direito: PLANEJAR (alto impacto, alto esforço)
Quadrante Inferior Esquerdo: QUICK WINS (baixo impacto, baixo esforço)
Quadrante Inferior Direito: CONSIDERAR (baixo impacto, alto esforço)
```

### Ordem de Resolução

| Ordem | Débito | Versão | Justificativa |
|-------|--------|--------|---------------|
| 1 | DT-F1, DT-F2 | v0.3 | Quick wins, código morto |
| 2 | DT-F6 | v0.3 | UX crítica, reconexão |
| 3 | DT-F7 | v0.3 | UX, persistência básica |
| 4 | DT-F5 | v0.3 | Feedback visual |
| 5 | DT-B1, DT-B2 | v0.4 | **CRÍTICO**: single point of failure |
| 6 | DT-B7 | v0.4 | Resiliência |
| 7 | DT-B9 | v0.4 | Observabilidade básica |
| 8 | DT-B4 | v0.4 | Segurança |
| 9 | DT-B5 | v0.4 | Automação |
| 10 | DT-B3 | v1.0 | Observabilidade completa |
| 11 | DT-F4 | v1.0 | Qualidade |
| 12 | DT-B6 | v1.0 | Manutenção |
| 13 | DT-F3, DT-B8 | v1.0 | Alinhamento API |

---

## Dependências Entre Versões

```mermaid
graph LR
    v02[v0.2 POC] --> v03[v0.3 Frontend]
    v03 --> v04[v0.4 Backend]
    v04 --> v10[v1.0 Produção]
    v10 --> v20[v2.0 Multi-Asset]

    subgraph "Dependências Externas"
        VA[Vertex AI Account]
        AN[Anthropic API Key]
        CG[CoinGecko API]
        PR[Prometheus]
    end

    v04 -.-> VA
    v04 -.-> AN
    v10 -.-> PR
    v20 -.-> CG
```

### Matriz de Dependências

| Versão | Depende de | Bloqueia |
|--------|------------|----------|
| v0.3 | v0.2 completa | v0.4 |
| v0.4 | v0.3, Vertex AI, Anthropic | v1.0 |
| v1.0 | v0.4, Prometheus setup | v2.0 |
| v2.0 | v1.0, CoinGecko API | - |

---

## Critérios de Promoção

### v0.2 → v0.3

- [ ] Código Supabase removido
- [ ] Imports não utilizados limpos
- [ ] WebSocket com retry automático funcionando
- [ ] Chat persiste em localStorage
- [ ] Indicador de status de conexão visível

### v0.3 → v0.4

- [ ] Todos os critérios v0.3 atendidos
- [ ] Fallback para Vertex AI funcionando
- [ ] Fallback para Anthropic funcionando
- [ ] Circuit breaker ativo
- [ ] Health check reporta status de todos os providers
- [ ] Rate limiting ativo (100 req/min por IP)
- [ ] News ingestion rodando via scheduler

### v0.4 → v1.0

- [ ] Todos os critérios v0.4 atendidos
- [ ] Métricas Prometheus exportadas
- [ ] Dashboard básico funcional
- [ ] Testes E2E passando (>80% cobertura de fluxos críticos)
- [ ] Documentação OpenAPI completa
- [ ] CI/CD pipeline funcional
- [ ] 99.5% uptime em staging por 7 dias

### v1.0 → v2.0

- [ ] Todos os critérios v1.0 atendidos
- [ ] v1.0 estável em produção por 30 dias
- [ ] Feedback de usuários coletado
- [ ] Infraestrutura validada para multi-asset

---

## Especificações Detalhadas

Cada versão possui uma especificação detalhada em arquivo separado:

| Versão | Arquivo | Descrição |
|--------|---------|-----------|
| v0.3 | [SPEC-v0.3.md](SPEC-v0.3.md) | Limpeza de débitos técnicos do frontend |
| v0.4 | [SPEC-v0.4.md](SPEC-v0.4.md) | Limpeza de débitos técnicos do backend |
| v1.0 | [SPEC-v1.0.md](SPEC-v1.0.md) | Estabilidade e preparação para produção |
| v2.0 | [SPEC-v2.0.md](SPEC-v2.0.md) | Multi-asset e features avançadas |
| v3.0 | [SPEC-v3.0.md](SPEC-v3.0.md) | Agent Mode - Planejador/Executor/Verificador |

---

## Métricas de Sucesso do Projeto

### Técnicas

| Métrica | v0.4 | v1.0 | v2.0 |
|---------|------|------|------|
| Uptime | 95% | 99.5% | 99.9% |
| Latência P95 (cache miss) | <3s | <2s | <2s |
| Latência P95 (cache hit) | <100ms | <50ms | <50ms |
| Cobertura de testes | 60% | 80% | 85% |
| Fallback success rate | 90% | 99% | 99.5% |

### Negócio

| Métrica | v1.0 | v2.0 |
|---------|------|------|
| Ativos suportados | 1 | 3+ |
| Sessões simultâneas | 50 | 200 |
| Retenção D7 | >30% | >50% |

---

## Histórico de Atualizações

| Data | Versão Doc | Autor | Mudanças |
|------|------------|-------|----------|
| 2026-01-23 | 1.0 | Claude | Criação inicial do roadmap completo |

---

## Links Relacionados

- [CHANGELOG.md](../CHANGELOG.md) - Histórico de releases
- [README.md](../README.md) - Documentação principal
- [ROADMAP-V1.md](ROADMAP-V1.md) - Roadmap original (deprecated)

---

> **Nota**: Este documento é a fonte de verdade para o planejamento de evolução do Forex Advisor. Atualize-o sempre que houver mudanças no roadmap.
