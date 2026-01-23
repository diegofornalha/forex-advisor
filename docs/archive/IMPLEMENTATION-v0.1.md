# Plano de Implementação: Forex Advisor

## Versionamento

| Versão | Status | Descrição |
|--------|--------|-----------|
| **v0.0** | ✅ Atual | POC básica - estrutura implementada |
| **v0.1** | 🚧 Próxima | POC funcional - testes e polish |
| **v1.0** | 📋 Planejado | Produção - fallbacks, métricas, auth |

---

## Visão Geral

MVP funcional de análise USD/BRL com chat interativo via IA, capaz de executar código Python customizado em ambiente isolado.

**Objetivo**: Validar a proposta de valor com usuários reais antes de investir em infraestrutura robusta.

## Arquitetura v0.1

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React + Vite)                                │
│  localhost:8080                                         │
│  ├── Página de Insights (análise USD/BRL)               │
│  ├── Chat com IA (WebSocket)                            │
│  └── Execução de código (resultados do E2B)             │
└─────────────────────┬───────────────────────────────────┘
                      │ REST + WebSocket
                      ▼
┌─────────────────────────────────────────────────────────┐
│  Backend (FastAPI)                                      │
│  localhost:8000                                         │
│  ├── /api/v1/forex/usdbrl (análise completa)            │
│  ├── /api/v1/forex/usdbrl/technical (só indicadores)    │
│  ├── /ws/chat/{session_id} (WebSocket streaming)        │
│  └── /health (status)                                   │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
┌───────────┐  ┌───────────┐  ┌───────────┐
│  Minimax  │  │   Redis   │  │    E2B    │
│   (LLM)   │  │  (Cache)  │  │ (Sandbox) │
└───────────┘  └───────────┘  └───────────┘
```

---

## Requisitos Funcionais

### Core (P0 - Obrigatório)
- [x] Análise técnica USD/BRL (SMA, RSI, Bollinger)
- [x] Classificação de tendência (Alta/Baixa/Volatilidade/Neutro)
- [x] Geração de insights via LLM (Minimax)
- [x] Cache de respostas (Redis + Memory fallback)
- [x] Chat via WebSocket com streaming
- [x] Execução de código Python no E2B
- [x] Interface web responsiva

### Secundário (P1 - Importante)
- [x] Validação de compliance (proibir recomendações)
- [x] Histórico de chat no Redis (TTL 1h)
- [x] Whitelist de imports Python
- [ ] Tratamento de erros amigável no chat
- [ ] Loading states consistentes

### Nice-to-have (P2 - Desejável)
- [ ] Sugestões de perguntas dinâmicas
- [ ] Syntax highlighting no código
- [ ] Copiar resposta do chat
- [ ] Tema escuro completo

---

## Requisitos Não Funcionais

### Performance
- Response time análise: < 3s (cache miss) / < 100ms (cache hit)
- Response time chat: < 2s primeiro token (streaming)
- Cache TTL: 1h (insights), 4h (técnico)

### Segurança
- Código executado em sandbox isolado (E2B)
- Whitelist de imports: pandas, numpy, json, math, statistics
- Timeout de execução: 180s
- Validação de tamanho de código: max 5000 chars

### Disponibilidade
- POC: single instance, sem redundância
- v1: considerar load balancing

---

## Componentes Implementados

### Backend (`/Users/2a/.claude/forex-advisor/app/`)

| Arquivo | Status | Descrição |
|---------|--------|-----------|
| `main.py` | ✅ | FastAPI app, rotas, CORS, lifespan |
| `config.py` | ✅ | Pydantic settings (simplificado para POC) |
| `recommendation.py` | ✅ | Análise técnica (SMA, RSI, BB) |
| `insights.py` | ✅ | Geração de insights + compliance |
| `llm_router.py` | ✅ | Cliente Minimax (simplificado) |
| `cache.py` | ✅ | Redis + Memory fallback |
| `sandbox.py` | ✅ | E2B code execution |
| `chat.py` | ✅ | WebSocket endpoint + streaming |
| `models.py` | ✅ | Pydantic models |

### Frontend (`/Users/2a/.claude/forex-advisor-front/prototipo/src/`)

| Pasta/Arquivo | Status | Descrição |
|---------------|--------|-----------|
| `pages/Insights.tsx` | ✅ | Página principal |
| `components/insights/` | ✅ | Cards, indicadores, FAQ |
| `components/chat/` | ✅ | ChatPanel, ChatMessage, ChatInput |
| `hooks/useInsights.ts` | ✅ | React Query para API |
| `hooks/useChat.ts` | ✅ | WebSocket hook |
| `lib/api.ts` | ✅ | Cliente HTTP |
| `lib/chat-api.ts` | ✅ | Utilitários de chat |
| `types/` | ✅ | TypeScript interfaces |

---

## v0.0 → v0.1: Tarefas de Evolução

### Fase 1: Validação (v0.0 → v0.1-alpha)
- [ ] Testar WebSocket no browser
- [ ] Verificar streaming de chunks
- [ ] Testar execução de código no E2B
- [ ] Validar tratamento de erros
- [ ] Corrigir bugs encontrados

### Fase 2: Polish (v0.1-alpha → v0.1-beta)
- [ ] Melhorar mensagens de erro no chat
- [ ] Adicionar loading state no envio
- [ ] Verificar responsividade mobile
- [ ] Testar cache Redis
- [ ] UX de reconexão WebSocket

### Fase 3: Release (v0.1-beta → v0.1)
- [ ] Atualizar README com instruções
- [ ] Documentar variáveis de ambiente
- [ ] Criar .env.example atualizado
- [ ] Tag git v0.1

---

## Variáveis de Ambiente (v0.1)

```env
# Backend (.env)
DEBUG=false

# LLM (obrigatório)
MINIMAX_TOKEN=sk-...

# Cache (opcional - fallback memory)
REDIS_URL=redis://localhost:6379

# E2B (obrigatório para chat com código)
E2B_API_KEY=e2b_...

# Frontend (.env)
VITE_API_URL=http://localhost:8000
```

---

## Como Executar

```bash
# 1. Backend
cd /Users/2a/.claude/forex-advisor
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. Frontend
cd /Users/2a/.claude/forex-advisor-front/prototipo
npm install
npm run dev

# 3. Redis (opcional)
docker run -d -p 6379:6379 redis:alpine
```

---

## Critérios de Sucesso v0.1

- [ ] Usuário consegue ver análise USD/BRL
- [ ] Usuário consegue fazer perguntas no chat
- [ ] Chat responde com streaming
- [ ] Código Python executa no sandbox
- [ ] Resultados de código aparecem no chat
- [ ] Cache funciona (Redis ou Memory)
- [ ] Nenhum erro crítico no console

---

## Roadmap: v0.1 → v1

| Feature | v0.1 (POC) | v1 |
|---------|------------|-----|
| LLM | Minimax apenas | + Vertex AI, Anthropic fallbacks |
| Cache | Redis + Memory | + TTL inteligente |
| Métricas | Básico (/health) | Prometheus, latências |
| Auth | Nenhuma | JWT, rate limiting |
| Deploy | Local | Docker, Kubernetes |
| Testes | Manual | Pytest, Cypress |
| Logs | Console | Estruturado (JSON) |

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Minimax indisponível | Média | Alto | v1: fallbacks |
| E2B timeout | Baixa | Médio | Limite de código, timeout |
| Redis falha | Baixa | Baixo | Memory fallback |
| Código malicioso | Média | Alto | Whitelist, sandbox |

---

## Notas de Implementação

### Decisões Tomadas
1. **WebSocket vs SSE**: WebSocket escolhido para bidirecionalidade
2. **Sandbox por sessão vs por request**: Singleton para POC (v1: por request)
3. **Histórico no Redis**: TTL 1h, max 50 mensagens

### Débitos Técnicos
1. Streaming LLM pode falhar silenciosamente
2. Reconexão WebSocket básica (v1: exponential backoff)
3. Sem validação de session_id no frontend
