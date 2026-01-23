# Guia do Desenvolvedor - Forex Advisor

> Tudo que você precisa saber para começar a trabalhar neste projeto.

---

## Sumário

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Setup do Ambiente](#2-setup-do-ambiente)
3. [Estrutura do Projeto](#3-estrutura-do-projeto)
4. [Arquitetura](#4-arquitetura)
5. [Fluxo de Dados](#5-fluxo-de-dados)
6. [Padrões de Código](#6-padrões-de-código)
7. [Testes](#7-testes)
8. [Fluxo de Trabalho](#8-fluxo-de-trabalho)
9. [Troubleshooting](#9-troubleshooting)
10. [Documentação Relacionada](#10-documentação-relacionada)

---

## 1. Visão Geral do Projeto

### O que é?

Forex Advisor é um assistente de análise de câmbio USD/BRL que:
- Calcula indicadores técnicos (SMA, RSI, Bollinger)
- Classifica tendência de mercado (Alta/Baixa/Neutro/Volatilidade)
- Gera insights usando IA (LLM)
- Oferece chat interativo com execução de código Python

### Stack

| Camada | Tecnologias |
|--------|-------------|
| Frontend | React 18, TypeScript, Vite, TailwindCSS, shadcn/ui |
| Backend | FastAPI, Python 3.11+, Pydantic |
| LLM | LiteLLM (Minimax, Vertex AI, Anthropic) |
| Dados | yfinance, Redis, sqlite-vec |
| Sandbox | E2B Code Interpreter |

### Versão Atual

**v0.4** - Backend resiliente com fallback chain e 79 testes passando.

---

## 2. Setup do Ambiente

### Pré-requisitos

- Python 3.11+
- Node.js 18+
- Redis (opcional, tem fallback em memória)
- Conta Minimax, Vertex AI ou Anthropic (pelo menos uma)

### Backend

```bash
# 1. Clone e entre no diretório
cd /Users/2a/.claude/forex-advisor

# 2. Crie e ative virtualenv
python -m venv .venv
source .venv/bin/activate

# 3. Instale dependências
pip install -r requirements-dev.txt

# 4. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas API keys

# 5. Rode os testes
pytest tests/ -v

# 6. Inicie o servidor
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
# 1. Entre no diretório
cd /Users/2a/.claude/forex-advisor-front/prototipo

# 2. Instale dependências
npm install

# 3. Inicie o dev server
npm run dev
# Acesse http://localhost:5173
```

### Variáveis de Ambiente Essenciais

```bash
# Mínimo para funcionar (escolha pelo menos um LLM)
MINIMAX_TOKEN=seu_token_aqui

# Opcional - fallbacks
VERTEX_API_KEY=...
ANTHROPIC_API_KEY=...

# Opcional - para execução de código no chat
E2B_API_KEY=...

# Opcional - cache (tem fallback em memória)
REDIS_URL=redis://localhost:6379
```

---

## 3. Estrutura do Projeto

```
forex-advisor/
├── app/                      # Código principal do backend
│   ├── __init__.py
│   ├── main.py              # FastAPI app, middlewares, rotas
│   ├── config.py            # Settings (Pydantic, env vars)
│   ├── models.py            # Pydantic models (request/response)
│   ├── chat.py              # WebSocket, validação de código
│   ├── llm_router.py        # Fallback chain, circuit breaker
│   ├── recommendation.py    # Cálculo de indicadores, classificação
│   ├── insights.py          # Geração de insights com LLM
│   ├── sandbox.py           # Integração E2B
│   ├── cache.py             # Redis + memory fallback
│   └── rag_sdk/
│       ├── __init__.py
│       └── rag.py           # RAG com sqlite-vec
│
├── tests/                   # Testes automatizados
│   ├── conftest.py          # Fixtures pytest
│   ├── test_api.py          # Testes de endpoints
│   ├── test_chat.py         # Testes de validação de código
│   ├── test_llm_router.py   # Testes de circuit breaker
│   ├── test_rag.py          # Testes de RAG
│   └── test_recommendation.py # Testes de análise técnica
│
├── docs/                    # Documentação
│   ├── STATUS.md            # O que está implementado
│   ├── TECH-DEBT.md         # Débitos técnicos
│   ├── TESTS.md             # Documentação dos 79 testes
│   ├── CONTRIBUTING.md      # Este arquivo
│   ├── ROADMAP.md           # Roadmap de versões
│   ├── specs/               # Especificações por versão
│   └── archive/             # Documentos históricos
│
├── data/                    # Dados locais
│   └── rag.db               # Banco sqlite-vec do RAG
│
├── requirements.txt         # Dependências de produção
├── requirements-dev.txt     # Dependências de desenvolvimento
├── .env.example             # Template de configuração
├── README.md
└── CHANGELOG.md
```

---

## 4. Arquitetura

### Diagrama de Componentes

```
                    ┌─────────────┐
                    │   Frontend  │
                    │   (React)   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │  REST   │  │WebSocket│  │  Docs   │
        │  API    │  │  Chat   │  │ OpenAPI │
        └────┬────┘  └────┬────┘  └─────────┘
             │            │
             ▼            ▼
        ┌─────────────────────────────────┐
        │           Rate Limiter          │
        │         (100 req/min)           │
        └────────────────┬────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐     ┌─────────┐     ┌─────────┐
   │ Analysis│     │   LLM   │     │   RAG   │
   │ Engine  │     │ Router  │     │  Search │
   └────┬────┘     └────┬────┘     └────┬────┘
        │               │               │
        ▼               ▼               ▼
   ┌─────────┐     ┌─────────┐     ┌─────────┐
   │ yfinance│     │ Minimax │     │sqlite-vec│
   │         │     │ Vertex  │     │         │
   │         │     │Anthropic│     │         │
   └─────────┘     └─────────┘     └─────────┘
```

### Componentes Principais

| Componente | Arquivo | Responsabilidade |
|------------|---------|------------------|
| **API** | `main.py` | Rotas, middlewares, CORS |
| **Config** | `config.py` | Todas as configurações (env vars) |
| **Analysis** | `recommendation.py` | SMA, RSI, Bollinger, classificação |
| **Insights** | `insights.py` | Gera texto com LLM + notícias |
| **LLM Router** | `llm_router.py` | Fallback chain, circuit breaker |
| **Chat** | `chat.py` | WebSocket, validação de código |
| **Sandbox** | `sandbox.py` | Execução isolada via E2B |
| **RAG** | `rag_sdk/rag.py` | Busca semântica de notícias |
| **Cache** | `cache.py` | Redis com fallback em memória |

---

## 5. Fluxo de Dados

### Endpoint `/api/v1/forex/usdbrl`

```
1. Request chega
   │
2. Rate limiter verifica (100 req/min)
   │
3. Verifica cache Redis
   │
   ├── Cache HIT → Retorna resposta cacheada
   │
   └── Cache MISS ↓
       │
4. recommendation.py: Baixa dados yfinance
   │
5. recommendation.py: Calcula indicadores
   │
6. recommendation.py: Classifica tendência
   │
7. insights.py: Busca notícias no RAG
   │
8. insights.py: Gera insight com LLM
   │
9. Salva no cache
   │
10. Retorna resposta
```

### Chat WebSocket

```
1. Cliente conecta em /ws/chat/{session_id}
   │
2. Valida session_id (UUID)
   │
3. Cliente envia mensagem
   │
4. Verifica tamanho (<10KB)
   │
5. Busca contexto no RAG
   │
6. Gera resposta com LLM (streaming)
   │
7. Se resposta contém código Python:
   │   │
   │   ├── Valida código (whitelist)
   │   │
   │   └── Executa no E2B sandbox
   │
8. Envia resultado ao cliente
```

---

## 6. Padrões de Código

### Python

- **Tipagem**: Usar type hints sempre
- **Docstrings**: Formato Google
- **Async**: Funções de I/O devem ser async
- **Validação**: Pydantic para input/output
- **Erros**: Logar com sanitização (sem API keys)

```python
# Exemplo de função bem escrita
async def get_classification() -> ClassificationResult:
    """Calcula classificação de mercado.

    Returns:
        ClassificationResult com indicadores e classificação.

    Raises:
        ValueError: Se dados de mercado indisponíveis.
    """
    ...
```

### Testes

- Usar pytest
- Fixtures em `conftest.py`
- Nomear `test_<funcionalidade>.py`
- Classes agrupam testes relacionados

```python
class TestCodeValidation:
    def test_valid_pandas_code(self):
        ...

    def test_rejects_eval(self):
        ...
```

---

## 7. Testes

### Rodar Todos

```bash
pytest tests/ -v
```

### Rodar Categoria Específica

```bash
# Só testes de API
pytest tests/test_api.py -v

# Só testes de validação de código
pytest tests/test_chat.py::TestCodeValidation -v

# Com cobertura
pytest tests/ --cov=app --cov-report=html
```

### Estrutura de Testes

| Arquivo | O que testa | Quantidade |
|---------|-------------|------------|
| `test_api.py` | Endpoints REST | 16 |
| `test_chat.py` | Validação, UUID, extração | 25 |
| `test_llm_router.py` | Circuit breaker | 11 |
| `test_rag.py` | CRUD, busca semântica | 10 |
| `test_recommendation.py` | Indicadores, classificação | 17 |

Ver detalhes em [TESTS.md](TESTS.md).

---

## 8. Fluxo de Trabalho

### Antes de Começar

1. Leia [STATUS.md](STATUS.md) - O que está implementado
2. Leia [TECH-DEBT.md](TECH-DEBT.md) - Débitos técnicos
3. Confira o [ROADMAP.md](ROADMAP.md)

### Para Adicionar Feature

1. Verifique se existe spec relacionada em [specs/](specs/)
2. Crie branch: `feature/nome-da-feature`
3. Implemente com testes
4. Rode `pytest tests/ -v`
5. Atualize documentação se necessário
6. Abra PR

### Para Corrigir Bug

1. Crie branch: `fix/nome-do-bug`
2. Escreva teste que reproduz o bug
3. Corrija o bug
4. Confirme que teste passa
5. Abra PR

### Para Resolver Débito Técnico

1. Confira [TECH-DEBT.md](TECH-DEBT.md)
2. Atualize status do débito
3. Implemente correção
4. Marque como ✅ no TECH-DEBT.md

---

## 9. Troubleshooting

### "LLM não configurado"

```
ValueError: Nenhum LLM configurado. Configure pelo menos MINIMAX_TOKEN no .env
```

**Solução**: Configure pelo menos uma API key de LLM no `.env`.

### "Redis connection refused"

```
redis.exceptions.ConnectionError: Connection refused
```

**Solução**: Sistema usa fallback em memória automaticamente. Para usar Redis:
```bash
# macOS
brew install redis && brew services start redis

# Linux
sudo apt install redis-server && sudo systemctl start redis
```

### "E2B Sandbox não disponível"

```
ValueError: E2B Sandbox não disponível
```

**Solução**: Configure `E2B_API_KEY` no `.env`. Sem isso, execução de código no chat não funciona.

### Testes falhando com timeout

```bash
# Aumentar timeout do pytest
pytest tests/ -v --timeout=120
```

### Verificar saúde do sistema

```bash
curl http://localhost:8000/health | jq
```

---

## 10. Documentação Relacionada

| Documento | Descrição |
|-----------|-----------|
| [STATUS.md](STATUS.md) | Mapa de tudo que está implementado |
| [TECH-DEBT.md](TECH-DEBT.md) | Débitos técnicos e política |
| [TESTS.md](TESTS.md) | Documentação dos 79 testes |
| [ROADMAP.md](ROADMAP.md) | Roadmap de versões |
| [specs/v0.3-frontend-cleanup.md](specs/v0.3-frontend-cleanup.md) | Spec do frontend cleanup |
| [specs/v0.4-backend-resiliente.md](specs/v0.4-backend-resiliente.md) | Spec do backend resiliente |
| [specs/v1.0-producao.md](specs/v1.0-producao.md) | Spec de produção |
| [specs/v2.0-multi-asset.md](specs/v2.0-multi-asset.md) | Spec multi-asset |
| [specs/v3.0-agent-mode.md](specs/v3.0-agent-mode.md) | Spec agent mode |

---

## Contato

Dúvidas? Abra uma issue ou fale com o time.

---

> **Dica**: Comece rodando os testes (`pytest tests/ -v`) para garantir que seu ambiente está funcionando.
