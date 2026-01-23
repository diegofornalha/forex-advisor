# Plano de Onboarding - Novo Desenvolvedor

> Guia estruturado para um novo desenvolvedor se familiarizar com o projeto Forex Advisor.

**Duração estimada**: 3-5 dias
**Pré-requisitos**: Python 3.11+, Node.js 18+, conhecimento básico de FastAPI/React

---

## Visão Geral do Plano

```
Dia 1: Entendimento do Projeto
   │
   ├── Ler documentação
   ├── Entender arquitetura
   └── Setup do ambiente

Dia 2: Exploração do Código
   │
   ├── Backend (FastAPI)
   ├── Frontend (React)
   └── Rodar testes

Dia 3: Hands-on Básico
   │
   ├── Fazer requests na API
   ├── Debugar um fluxo
   └── Modificar algo simples

Dia 4: Tarefas Práticas
   │
   ├── Resolver um bug simulado
   ├── Adicionar um teste
   └── Fazer pequena melhoria

Dia 5: Autonomia
   │
   ├── Pegar tarefa real
   ├── Implementar com supervisão
   └── Code review
```

---

## Fase 1: Entendimento do Projeto

### 1.1 Leitura Obrigatória

| Ordem | Documento | Tempo | Objetivo |
|-------|-----------|-------|----------|
| 1 | [STATUS.md](STATUS.md) | 15 min | Entender o que está implementado |
| 2 | [CONTRIBUTING.md](CONTRIBUTING.md) | 20 min | Setup e padrões |
| 3 | [TECH-DEBT.md](TECH-DEBT.md) | 10 min | Débitos técnicos |
| 4 | [TESTS.md](TESTS.md) | 10 min | Estrutura de testes |
| 5 | [ROADMAP.md](ROADMAP.md) | 15 min | Visão de futuro |

### 1.2 Perguntas para Responder

Após a leitura, o novo dev deve conseguir responder:

- [ ] O que o Forex Advisor faz?
- [ ] Quais são os principais endpoints da API?
- [ ] Como funciona o fallback de LLM?
- [ ] O que é o circuit breaker e para que serve?
- [ ] Onde ficam os testes e quantos são?
- [ ] Qual a versão atual e o que falta para v1.0?

### 1.3 Arquitetura - Componentes Chave

```
Componente          Arquivo              Responsabilidade
─────────────────────────────────────────────────────────
API Principal    → app/main.py        → Rotas, middlewares
Configuração     → app/config.py      → Env vars, settings
Análise Técnica  → app/recommendation.py → SMA, RSI, Bollinger
Geração Insights → app/insights.py    → LLM + notícias
Roteador LLM     → app/llm_router.py  → Fallback, circuit breaker
Chat WebSocket   → app/chat.py        → Streaming, validação
Sandbox          → app/sandbox.py     → E2B, execução código
RAG              → app/rag_sdk/rag.py → Busca semântica
Cache            → app/cache.py       → Redis + fallback
```

---

## Fase 2: Setup do Ambiente

### 2.1 Checklist de Setup

```bash
# Backend
- [ ] Clonar repositório
- [ ] Criar virtualenv Python 3.11+
- [ ] pip install -r requirements-dev.txt
- [ ] Copiar .env.example para .env
- [ ] Configurar pelo menos MINIMAX_TOKEN
- [ ] Rodar pytest tests/ -v (deve passar 79 testes)
- [ ] Rodar uvicorn app.main:app --reload
- [ ] Acessar http://localhost:8000/docs

# Frontend
- [ ] cd forex-advisor-front/prototipo
- [ ] npm install
- [ ] npm run dev
- [ ] Acessar http://localhost:5173
```

### 2.2 Verificação de Saúde

```bash
# Testar health check
curl http://localhost:8000/health | jq

# Resposta esperada:
{
  "status": "healthy",
  "version": "0.4.0",
  "cache": {...},
  "llm": {
    "status": "active",
    "active_providers": ["minimax"],
    ...
  },
  "sandbox": {...}
}
```

### 2.3 Troubleshooting Comum

| Problema | Solução |
|----------|---------|
| "LLM não configurado" | Configure MINIMAX_TOKEN no .env |
| "Redis connection refused" | OK, usa fallback em memória |
| "E2B não disponível" | Configure E2B_API_KEY (opcional) |
| Testes falhando | Verifique se Redis está rodando |

---

## Fase 3: Exploração do Código

### 3.1 Backend - Tour Guiado

**Exercício**: Abra cada arquivo e entenda o que faz.

```
Ordem de leitura recomendada:

1. app/config.py
   └── Entender todas as configurações disponíveis

2. app/main.py
   └── Ver rotas, middlewares, lifespan

3. app/recommendation.py
   └── Seguir o fluxo: dados → indicadores → classificação

4. app/llm_router.py
   └── Entender CircuitBreaker e fallback chain

5. app/chat.py
   └── Ver validação de código e WebSocket

6. app/rag_sdk/rag.py
   └── Entender busca semântica
```

### 3.2 Exercício Prático - Seguir um Request

Trace o fluxo de `/api/v1/forex/usdbrl`:

```
1. Request chega em main.py
   ↓
2. Passa pelo RateLimitMiddleware
   ↓
3. Função get_usdbrl_insight() é chamada
   ↓
4. Verifica cache (get_cached)
   ↓
5. Se cache miss:
   ├── get_classification() → recommendation.py
   └── generate_insight() → insights.py
   ↓
6. Salva no cache (set_cached)
   ↓
7. Retorna resposta
```

**Tarefa**: Adicione um `logger.debug()` em cada etapa e observe os logs.

### 3.3 Frontend - Tour Guiado

```
Ordem de leitura:

1. src/App.tsx
   └── Rotas da aplicação

2. src/pages/Insights.tsx
   └── Página principal

3. src/hooks/useInsights.ts
   └── Busca de dados

4. src/hooks/useChat.ts
   └── WebSocket, localStorage

5. src/components/chat/ChatPanel.tsx
   └── Interface do chat
```

---

## Fase 4: Testes

### 4.1 Rodar e Entender os Testes

```bash
# Rodar todos
pytest tests/ -v

# Rodar com output detalhado
pytest tests/ -v -s

# Rodar apenas uma categoria
pytest tests/test_chat.py -v

# Rodar um teste específico
pytest tests/test_chat.py::TestCodeValidation::test_rejects_eval -v
```

### 4.2 Exercício - Adicionar um Teste

**Tarefa**: Adicione um novo teste em `test_chat.py`:

```python
def test_rejects_pickle(self):
    """Should reject pickle module (deserialization attack)."""
    code = """
import pickle
pickle.loads(data)
"""
    is_valid, error = validate_code(code)
    assert is_valid is False
```

Passos:
1. Abra `tests/test_chat.py`
2. Adicione o teste na classe `TestCodeValidation`
3. Rode `pytest tests/test_chat.py::TestCodeValidation::test_rejects_pickle -v`
4. O teste deve falhar (pickle não está bloqueado)
5. Adicione `r"\bpickle\b"` na lista de `dangerous_patterns` em `chat.py`
6. Rode o teste novamente - deve passar

---

## Fase 5: Tarefas Práticas Progressivas

### Nível 1: Observação (Dia 1-2)

| Tarefa | Descrição | Arquivo |
|--------|-----------|---------|
| T1.1 | Adicionar log em endpoint | `main.py` |
| T1.2 | Mudar mensagem de erro | `chat.py` |
| T1.3 | Ajustar timeout de config | `config.py` |

### Nível 2: Modificação Simples (Dia 2-3)

| Tarefa | Descrição | Arquivo |
|--------|-----------|---------|
| T2.1 | Adicionar novo teste unitário | `tests/` |
| T2.2 | Adicionar campo no health check | `main.py` |
| T2.3 | Bloquear novo padrão perigoso | `chat.py` |

### Nível 3: Feature Pequena (Dia 3-4)

| Tarefa | Descrição | Arquivos |
|--------|-----------|----------|
| T3.1 | Adicionar endpoint `/api/v1/status` | `main.py`, `models.py` |
| T3.2 | Expor `bollinger_middle` na API | `recommendation.py`, `models.py` |
| T3.3 | Adicionar métrica de latência | `main.py` |

### Nível 4: Tarefa Real (Dia 4-5)

Pegar um item do [TECH-DEBT.md](TECH-DEBT.md) com severidade BAIXA:

- DT-B8: Expor bollinger_middle na API
- DT-F3: Melhorar transformações no frontend

---

## Fase 6: Checklist de Conclusão

### O novo dev está pronto quando:

**Conhecimento**:
- [ ] Consegue explicar a arquitetura do projeto
- [ ] Sabe onde fica cada componente
- [ ] Entende o fluxo de um request
- [ ] Conhece os débitos técnicos

**Prático**:
- [ ] Ambiente funcionando (backend + frontend)
- [ ] Consegue rodar e adicionar testes
- [ ] Fez pelo menos uma modificação no código
- [ ] Fez commit seguindo o padrão

**Autonomia**:
- [ ] Consegue debugar um problema sozinho
- [ ] Sabe onde buscar informação (docs)
- [ ] Pode pegar uma tarefa do backlog

---

## Recursos Adicionais

### Documentação do Projeto

| Documento | Quando Consultar |
|-----------|------------------|
| [STATUS.md](STATUS.md) | "O que está implementado?" |
| [TECH-DEBT.md](TECH-DEBT.md) | "O que precisa melhorar?" |
| [TESTS.md](TESTS.md) | "Como funcionam os testes?" |
| [CONTRIBUTING.md](CONTRIBUTING.md) | "Como contribuir?" |
| [ROADMAP.md](ROADMAP.md) | "Para onde o projeto vai?" |

### Documentação Externa

| Tecnologia | Link |
|------------|------|
| FastAPI | https://fastapi.tiangolo.com/ |
| Pydantic | https://docs.pydantic.dev/ |
| LiteLLM | https://docs.litellm.ai/ |
| React Query | https://tanstack.com/query |
| shadcn/ui | https://ui.shadcn.com/ |

---

## Feedback

Após completar o onboarding, o novo dev deve:

1. Documentar dificuldades encontradas
2. Sugerir melhorias neste documento
3. Apontar documentação faltante

---

> **Dica final**: Não tenha medo de perguntar. É melhor perguntar do que assumir errado.
