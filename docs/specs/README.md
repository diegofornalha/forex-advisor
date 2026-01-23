# Especificações por Versão

> Documentos detalhados de cada versão do Forex Advisor.

---

## Índice de Especificações

| Versão | Arquivo | Status | Descrição |
|--------|---------|--------|-----------|
| v0.3 | [v0.3-frontend-cleanup.md](v0.3-frontend-cleanup.md) | ✅ Concluída | Limpeza de código morto, retry WebSocket, localStorage |
| v0.4 | [v0.4-backend-resiliente.md](v0.4-backend-resiliente.md) | ✅ Concluída | Fallback chain LLM, circuit breaker, rate limiting |
| v1.0 | [v1.0-producao.md](v1.0-producao.md) | ⏳ Próxima | Prometheus, testes E2E, CI/CD |
| v2.0 | [v2.0-multi-asset.md](v2.0-multi-asset.md) | 📋 Planejada | EUR/BRL, BTC/BRL, backtesting, alertas |
| v3.0 | [v3.0-agent-mode.md](v3.0-agent-mode.md) | 📋 Planejada | Planejador/Executor/Verificador |

---

## Legenda de Status

| Status | Significado |
|--------|-------------|
| ✅ Concluída | Implementação completa |
| ⏳ Próxima | Em desenvolvimento ou próxima na fila |
| 📋 Planejada | Especificação pronta, aguardando implementação |

---

## Estrutura de uma SPEC

Cada especificação segue o formato:

1. **Visão Geral** - Objetivo da versão
2. **Requisitos** - O que deve ser implementado
3. **Abordagem Técnica** - Como será implementado
4. **Tarefas** - Checklist detalhado
5. **Critérios de Aceitação** - Quando está "pronto"

---

[← Voltar para docs](../README.md)
