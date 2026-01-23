# Documentação de Testes - Forex Advisor

Este documento descreve todos os 79 testes automatizados do projeto Forex Advisor.

## Sumário

| Arquivo | Categoria | Testes |
|---------|-----------|--------|
| `test_api.py` | Endpoints da API | 16 |
| `test_chat.py` | Chat e Validação de Código | 25 |
| `test_llm_router.py` | LLM Router e Circuit Breaker | 11 |
| `test_rag.py` | RAG (Retrieval Augmented Generation) | 10 |
| `test_recommendation.py` | Análise Técnica e Classificação | 17 |
| **Total** | | **79** |

---

## test_api.py - Endpoints da API (16 testes)

Testes de integração para os endpoints REST da API FastAPI.

### TestHealthEndpoint (2 testes)

| # | Teste | Descrição |
|---|-------|-----------|
| 1 | `test_health_returns_200` | Verifica se o endpoint `/health` retorna status HTTP 200 |
| 2 | `test_health_returns_status` | Verifica se o JSON retornado contém `status: "healthy"` |

### TestRootEndpoint (2 testes)

| # | Teste | Descrição |
|---|-------|-----------|
| 3 | `test_root_returns_200` | Verifica se o endpoint `/` retorna status HTTP 200 |
| 4 | `test_root_returns_message` | Verifica se o JSON contém `message`, `endpoints` e `docs` |

### TestDocsEndpoint (2 testes)

| # | Teste | Descrição |
|---|-------|-----------|
| 5 | `test_docs_available` | Verifica se `/docs` (Swagger UI) está acessível |
| 6 | `test_openapi_schema` | Verifica se `/openapi.json` retorna schema válido com `openapi` e `paths` |

### TestForexEndpoint (6 testes)

| # | Teste | Descrição |
|---|-------|-----------|
| 7 | `test_forex_returns_200` | Verifica se `/api/v1/forex/usdbrl` retorna 200 (timeout 30s devido ao yfinance) |
| 8 | `test_forex_has_classification` | Verifica se retorna classificação válida: `Alta`, `Baixa`, `Neutro` ou `Alta Volatilidade` |
| 9 | `test_forex_has_confidence` | Verifica se retorna `confidence` entre 0 e 1 |
| 10 | `test_forex_has_indicators` | Verifica presença de todos indicadores: `current_price`, `sma20`, `sma50`, `rsi`, `bollinger_upper`, `bollinger_lower` |
| 11 | `test_forex_has_explanation` | Verifica se retorna explicação com mais de 10 caracteres |
| 12 | `test_forex_has_insight` | Verifica se retorna insight gerado por LLM com mais de 20 caracteres |

### TestTechnicalEndpoint (3 testes)

| # | Teste | Descrição |
|---|-------|-----------|
| 13 | `test_technical_returns_200` | Verifica se `/api/v1/forex/usdbrl/technical` retorna 200 |
| 14 | `test_technical_has_indicators` | Verifica presença de `indicators`, `classification` e `confidence` |
| 15 | `test_technical_faster_than_full` | Verifica que endpoint técnico funciona sem chamar LLM |

### TestCacheHeaders (1 teste)

| # | Teste | Descrição |
|---|-------|-----------|
| 16 | `test_second_request_cached` | Verifica se segunda requisição é servida do cache |

---

## test_chat.py - Chat e Validação de Código (25 testes)

Testes para o módulo de chat, validação de código Python e segurança do sandbox.

### TestCodeValidation (19 testes)

Testes de segurança para validação de código antes da execução no sandbox E2B.

#### Códigos Válidos (3 testes)

| # | Teste | Descrição |
|---|-------|-----------|
| 17 | `test_valid_simple_code` | Aceita código pandas simples (`import pandas`, `df['Close'].mean()`) |
| 18 | `test_valid_numpy_code` | Aceita código numpy (`import numpy`, `np.array()`) |
| 19 | `test_valid_math_code` | Aceita código math/statistics (`import math`, `import statistics`) |

#### Códigos Rejeitados - Módulos Perigosos (6 testes)

| # | Teste | Descrição |
|---|-------|-----------|
| 20 | `test_rejects_os_module` | Rejeita `import os` e `os.system()` |
| 21 | `test_rejects_sys_module` | Rejeita `import sys` |
| 22 | `test_rejects_subprocess` | Rejeita `import subprocess` |
| 23 | `test_rejects_requests` | Rejeita `import requests` (acesso à rede) |
| 24 | `test_rejects_urllib` | Rejeita `import urllib` (acesso à rede) |
| 25 | `test_rejects_importlib` | Rejeita `import importlib` (importação dinâmica) |

#### Códigos Rejeitados - Funções Perigosas (5 testes)

| # | Teste | Descrição |
|---|-------|-----------|
| 26 | `test_rejects_eval` | Rejeita chamadas `eval()` |
| 27 | `test_rejects_exec` | Rejeita chamadas `exec()` |
| 28 | `test_rejects_open` | Rejeita `open()` para acesso a arquivos |
| 29 | `test_rejects_dunder_import` | Rejeita `__import__()` |
| 30 | `test_rejects_compile` | Rejeita `compile()` |

#### Códigos Rejeitados - Acesso a Internos (4 testes)

| # | Teste | Descrição |
|---|-------|-----------|
| 31 | `test_rejects_builtins_access` | Rejeita acesso a `__builtins__` |
| 32 | `test_rejects_globals` | Rejeita `globals()` |
| 33 | `test_rejects_getattr` | Rejeita `getattr()` (bypass de restrições) |
| 34 | `test_rejects_class_dunder` | Rejeita `__class__`, `__mro__`, `__subclasses__` (escape de sandbox) |

#### Limites (1 teste)

| # | Teste | Descrição |
|---|-------|-----------|
| 35 | `test_rejects_too_long_code` | Rejeita código maior que 5000 caracteres |

### TestCodeExtraction (4 testes)

Testes para extração de blocos de código Python do markdown.

| # | Teste | Descrição |
|---|-------|-----------|
| 36 | `test_extracts_single_block` | Extrai um bloco \`\`\`python corretamente |
| 37 | `test_extracts_multiple_blocks` | Extrai múltiplos blocos de código |
| 38 | `test_returns_empty_for_no_blocks` | Retorna lista vazia quando não há blocos |
| 39 | `test_ignores_other_languages` | Ignora blocos de outras linguagens (ex: javascript) |

### TestUUIDValidation (6 testes)

Testes para validação de session_id como UUID.

| # | Teste | Descrição |
|---|-------|-----------|
| 40 | `test_valid_uuid` | Aceita UUID válido em lowercase |
| 41 | `test_valid_uuid_uppercase` | Aceita UUID válido em uppercase |
| 42 | `test_invalid_uuid_short` | Rejeita string curta demais |
| 43 | `test_invalid_uuid_format` | Rejeita formato inválido |
| 44 | `test_invalid_uuid_empty` | Rejeita string vazia |
| 45 | `test_invalid_uuid_none` | Trata None graciosamente (retorna False) |

### TestMessageSizeLimit (1 teste)

| # | Teste | Descrição |
|---|-------|-----------|
| 46 | `test_message_size_constant_exists` | Verifica que `MAX_MESSAGE_SIZE` = 10KB está definido |

---

## test_llm_router.py - LLM Router e Circuit Breaker (11 testes)

Testes para o roteador de LLM com fallback chain e circuit breaker.

### TestCircuitBreaker (5 testes)

Testes do padrão Circuit Breaker para resiliência de providers.

| # | Teste | Descrição |
|---|-------|-----------|
| 47 | `test_initial_state_closed` | Circuit breaker inicia fechado (disponível) |
| 48 | `test_opens_after_threshold_failures` | Abre após 3 falhas consecutivas |
| 49 | `test_success_resets_failures` | Sucesso reseta contador de falhas |
| 50 | `test_half_open_after_recovery_timeout` | Entra em half-open após 60s de recovery |
| 51 | `test_get_status` | Retorna dict com `state`, `failures`, `last_failure` |

### TestErrorSanitization (2 testes)

Testes para remoção de dados sensíveis dos logs.

| # | Teste | Descrição |
|---|-------|-----------|
| 52 | `test_sanitizes_api_key` | Remove API keys das mensagens de erro (substitui por `[REDACTED]`) |
| 53 | `test_preserves_safe_error_messages` | Preserva mensagens sem dados sensíveis |

### TestRouterStats (3 testes)

Testes para o endpoint de status do router.

| # | Teste | Descrição |
|---|-------|-----------|
| 54 | `test_returns_dict` | `get_router_stats()` retorna dict |
| 55 | `test_has_status_field` | Retorno contém campo `status` |
| 56 | `test_status_values` | Status é `active`, `disabled` ou `degraded` |

### TestResetCircuitBreakers (1 teste)

| # | Teste | Descrição |
|---|-------|-----------|
| 57 | `test_reset_clears_failures` | Reset zera contadores de todos circuit breakers |

---

## test_rag.py - RAG (Retrieval Augmented Generation) (10 testes)

Testes para o sistema de RAG com SQLite-vec e embeddings.

### TestSimpleRAG (8 testes)

| # | Teste | Descrição |
|---|-------|-----------|
| 58 | `test_add_text` | Adiciona texto ao índice e retorna doc_id |
| 59 | `test_add_duplicate_text` | Detecta duplicatas via hash e retorna None |
| 60 | `test_search_returns_results` | Busca semântica retorna resultados relevantes |
| 61 | `test_search_empty_database` | Busca em banco vazio retorna lista vazia |
| 62 | `test_search_top_k` | Respeita parâmetro `top_k` para limitar resultados |
| 63 | `test_stats_empty_db` | `stats()` funciona com banco vazio |
| 64 | `test_stats_with_docs` | `stats()` retorna contagem correta de documentos |
| 65 | `test_clear` | `clear()` remove todos documentos e retorna contagem |

### TestSearchResult (2 testes)

| # | Teste | Descrição |
|---|-------|-----------|
| 66 | `test_result_has_all_fields` | SearchResult contém `doc_id`, `source`, `content`, `similarity` |
| 67 | `test_results_ordered_by_similarity` | Resultados ordenados por similaridade (maior primeiro) |

---

## test_recommendation.py - Análise Técnica e Classificação (17 testes)

Testes para cálculo de indicadores técnicos e classificação de mercado.

### TestCalculateIndicators (4 testes)

Testes para cálculo de indicadores técnicos (SMA, RSI, Bollinger).

| # | Teste | Descrição |
|---|-------|-----------|
| 68 | `test_returns_technical_indicators` | Retorna objeto TechnicalIndicators válido |
| 69 | `test_all_fields_populated` | Todos campos preenchidos (current_price, sma20, sma50, rsi, bollinger) |
| 70 | `test_sma_calculation` | SMA20 e SMA50 são calculados corretamente |
| 71 | `test_bollinger_band_ordering` | Bollinger: lower < current_price < upper |

### TestClassify (7 testes)

Testes para classificação do mercado (Alta, Baixa, Neutro, Volatilidade).

| # | Teste | Descrição |
|---|-------|-----------|
| 72 | `test_bullish_classification` | Detecta tendência de alta (preço > SMA20 > SMA50, RSI > 50) |
| 73 | `test_bearish_classification` | Detecta tendência de baixa (preço < SMA20 < SMA50, RSI < 50) |
| 74 | `test_volatile_classification` | Detecta alta volatilidade (preço fora das Bollinger Bands) |
| 75 | `test_neutral_classification` | Detecta mercado neutro (sem tendência clara) |
| 76 | `test_returns_explanation` | Retorna explicação em português |
| 77 | `test_returns_feature_importance` | Retorna importância das features na decisão |
| 78 | `test_confidence_bounded` | Confiança está entre 0 e 1 |

### TestIntegration (1 teste)

| # | Teste | Descrição |
|---|-------|-----------|
| 79 | `test_full_pipeline` | Teste de integração: dados reais → indicadores → classificação |

---

## Como Executar os Testes

### Todos os testes
```bash
pytest tests/ -v
```

### Com cobertura
```bash
pytest tests/ -v --cov=app --cov-report=html
```

### Apenas um arquivo
```bash
pytest tests/test_chat.py -v
```

### Apenas uma classe
```bash
pytest tests/test_chat.py::TestCodeValidation -v
```

### Apenas um teste
```bash
pytest tests/test_chat.py::TestCodeValidation::test_rejects_eval -v
```

---

## Cobertura por Módulo

| Módulo | Cobertura Estimada |
|--------|-------------------|
| `app/chat.py` | Alta (validação, extração, UUID) |
| `app/llm_router.py` | Alta (circuit breaker, sanitização) |
| `app/rag_sdk/rag.py` | Alta (CRUD, busca, stats) |
| `app/recommendation.py` | Alta (indicadores, classificação) |
| `app/main.py` | Média (endpoints cobertos) |
| `app/sandbox.py` | Baixa (requer E2B) |

---

## Requisitos para Testes

### Dependências
```bash
pip install -r requirements-dev.txt
```

### Serviços Externos
- **Redis**: Necessário para testes de cache (usa DB 1 para isolamento)
- **E2B**: Opcional (testes de sandbox são skipped se não configurado)
- **LLM**: Necessário para testes de insight (Minimax ou fallbacks)

### Variáveis de Ambiente
```bash
# Mínimo para testes
REDIS_URL=redis://localhost:6379/1
MINIMAX_TOKEN=seu_token_aqui

# Opcional (fallbacks)
VERTEX_API_KEY=...
ANTHROPIC_API_KEY=...
```

---

## Histórico

| Data | Testes | Autor |
|------|--------|-------|
| 2026-01-23 | 79 | Claude |
