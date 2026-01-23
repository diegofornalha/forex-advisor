# Especificação: Forex Advisor v2.0

> Multi-Asset e Features Avançadas

## Metadados

| Campo | Valor |
|-------|-------|
| **Versão** | 2.0.0 |
| **Tipo** | Feature Release |
| **Prioridade** | Média |
| **Escopo** | Full Stack |
| **Pré-requisito** | v1.0.0 estável por 30 dias |
| **Bloqueia** | - |

## Visão Geral

A v2.0 expande o Forex Advisor para suportar múltiplos ativos (EUR/BRL, BTC/BRL), adiciona features de valor agregado como backtesting e alertas, e refina a UX com visualizações interativas.

### Objetivos

1. **Multi-Asset**: Suporte a EUR/BRL e BTC/BRL além de USD/BRL
2. **Análises Avançadas**: Backtesting de estratégias simples
3. **Alertas**: Notificações de preço por email/webhook
4. **Visualização**: Gráficos interativos com Recharts
5. **Exportação**: Relatórios em PDF/CSV

---

## Requisitos

### Requisitos Funcionais

#### RF-01: Suporte Multi-Asset
**Prioridade**: Alta

Expandir o sistema para suportar múltiplos pares de moedas.

**Ativos Suportados**:

| Ativo | Símbolo | Fonte de Dados | Prioridade |
|-------|---------|----------------|------------|
| Dólar/Real | USD/BRL | yfinance | Existente |
| Euro/Real | EUR/BRL | yfinance | Alta |
| Bitcoin/Real | BTC/BRL | CoinGecko | Média |

**Critérios de Aceitação**:
- [ ] API aceita parâmetro `symbol` (USDBRL, EURBRL, BTCBRL)
- [ ] Indicadores técnicos calculados por ativo
- [ ] Classificação específica por tipo de ativo
- [ ] Cache separado por ativo
- [ ] Frontend com seletor de ativo
- [ ] Chat contextualizado por ativo selecionado
- [ ] E2B sandbox recebe dados do ativo correto

**Arquivos a Criar/Modificar**:
```
app/
├── assets/                    [CRIAR]
│   ├── __init__.py
│   ├── base.py               # Interface IAssetDataProvider
│   ├── yfinance_provider.py  # USD/BRL, EUR/BRL
│   └── coingecko_provider.py # BTC/BRL
├── main.py                    [MODIFICAR]
├── recommendation.py          [MODIFICAR]
├── chat.py                    [MODIFICAR]
└── config.py                  [MODIFICAR]

frontend/
├── src/hooks/useAsset.ts      [CRIAR]
├── src/components/AssetSelector.tsx [CRIAR]
└── src/pages/Insights.tsx     [MODIFICAR]
```

---

#### RF-02: Seletor de Ativo no Frontend
**Prioridade**: Alta

UI para selecionar qual ativo analisar.

**Critérios de Aceitação**:
- [ ] Dropdown/tabs para selecionar ativo
- [ ] Ativo selecionado persistido (localStorage)
- [ ] Dados recarregam ao trocar ativo
- [ ] Chat mantém histórico separado por ativo
- [ ] URL reflete ativo selecionado

---

#### RF-03: Backtesting de Estratégias
**Prioridade**: Média

Permitir backtesting de estratégias simples via chat.

**Estratégias Suportadas**:
- SMA Crossover
- RSI Reversal
- Bollinger Bounce

**Critérios de Aceitação**:
- [ ] Usuário pede backtesting via chat
- [ ] Sistema executa via E2B sandbox
- [ ] Retorna métricas: retorno total, sharpe ratio, max drawdown
- [ ] Disclaimer de resultados passados

---

#### RF-04: Sistema de Alertas
**Prioridade**: Média

Notificações quando preço atinge determinado valor.

**Tipos de Alerta**:
| Tipo | Descrição |
|------|-----------|
| Price Above | Notifica quando preço > valor |
| Price Below | Notifica quando preço < valor |
| Percent Change | Notifica em variação % |
| RSI Level | Notifica quando RSI atinge nível |

**Canais de Notificação**:
- Email (via SendGrid/SES)
- Webhook (para integrações)
- Push (futuro)

**Critérios de Aceitação**:
- [ ] CRUD de alertas via API
- [ ] UI para criar/gerenciar alertas
- [ ] Worker verifica condições periodicamente
- [ ] Notificação enviada quando condição atendida
- [ ] Limite de alertas por usuário (10 free)
- [ ] Histórico de alertas disparados

**Arquivos a Criar**:
```
app/
├── alerts/
│   ├── __init__.py
│   ├── models.py          # AlertConfig, AlertHistory
│   ├── service.py         # AlertService
│   ├── worker.py          # Background worker
│   └── notifiers/
│       ├── email.py
│       └── webhook.py
├── main.py                # Endpoints CRUD

frontend/
├── src/components/alerts/
│   ├── AlertForm.tsx
│   ├── AlertList.tsx
│   └── AlertHistory.tsx
└── src/hooks/useAlerts.ts
```

---

#### RF-05: Gráficos Interativos
**Prioridade**: Baixa

Visualização de dados com Recharts (já instalado).

**Gráficos**:
- Candlestick chart (preço)
- Line chart (indicadores)
- Area chart (volatilidade)

**Critérios de Aceitação**:
- [ ] Gráfico de preço com SMA overlays
- [ ] Gráfico de RSI separado
- [ ] Tooltip interativo
- [ ] Zoom e pan
- [ ] Período selecionável (1M, 3M, 1Y, 5Y)

---

#### RF-06: Exportação de Relatórios
**Prioridade**: Baixa

Exportar análises em diferentes formatos.

**Formatos**:
- PDF (relatório completo)
- CSV (dados brutos)
- JSON (API response)

**Critérios de Aceitação**:
- [ ] Botão de exportação na UI
- [ ] PDF com branding e formatação
- [ ] CSV com todos os indicadores
- [ ] Download imediato

---

### Requisitos Não Funcionais

#### RNF-01: Performance
- Troca de ativo < 500ms (cache hit)
- Backtesting < 10s para 5 anos de dados
- Alertas verificados a cada 1 minuto

#### RNF-02: Escalabilidade
- Suportar 200 sessões simultâneas
- 1000 alertas ativos no sistema

#### RNF-03: Custos
- CoinGecko free tier: 50 calls/min
- Alertas email: ~$0.001/email (SendGrid)

---

## Fases de Implementação

### Fase 1: Multi-Asset Backend
**Tarefas**:
- [ ] 1.1 Criar interface `IAssetDataProvider`
- [ ] 1.2 Implementar `YFinanceProvider`
- [ ] 1.3 Implementar `CoinGeckoProvider`
- [ ] 1.4 Refatorar `recommendation.py` para multi-asset
- [ ] 1.5 Atualizar endpoints da API
- [ ] 1.6 Cache por ativo
- [ ] 1.7 Testes unitários
- [ ] 1.8 Commit: "feat: multi-asset backend support"

### Fase 2: Multi-Asset Frontend
**Tarefas**:
- [ ] 2.1 Criar `AssetSelector` component
- [ ] 2.2 Criar `useAsset` hook
- [ ] 2.3 Integrar com React Query
- [ ] 2.4 Persistir seleção em localStorage
- [ ] 2.5 Atualizar chat para contexto por ativo
- [ ] 2.6 Testes E2E
- [ ] 2.7 Commit: "feat: multi-asset frontend"

### Fase 3: Backtesting
**Tarefas**:
- [ ] 3.1 Criar templates de estratégias no chat
- [ ] 3.2 Implementar lógica de backtesting (pandas)
- [ ] 3.3 Calcular métricas (retorno, sharpe, drawdown)
- [ ] 3.4 Gerar código para E2B
- [ ] 3.5 Adicionar disclaimer
- [ ] 3.6 Commit: "feat: backtesting via chat"

### Fase 4: Sistema de Alertas
**Tarefas**:
- [ ] 4.1 Criar models de alertas
- [ ] 4.2 Implementar CRUD API
- [ ] 4.3 Implementar worker de verificação
- [ ] 4.4 Integrar SendGrid para emails
- [ ] 4.5 Implementar webhook notifier
- [ ] 4.6 Criar UI de alertas
- [ ] 4.7 Testes de integração
- [ ] 4.8 Commit: "feat: price alerts system"

### Fase 5: Visualização
**Tarefas**:
- [ ] 5.1 Criar componente de gráfico de preço
- [ ] 5.2 Adicionar overlays de indicadores
- [ ] 5.3 Implementar zoom/pan
- [ ] 5.4 Seletor de período
- [ ] 5.5 Commit: "feat: interactive charts"

### Fase 6: Exportação
**Tarefas**:
- [ ] 6.1 Implementar geração de PDF (react-pdf)
- [ ] 6.2 Implementar exportação CSV
- [ ] 6.3 Adicionar botões na UI
- [ ] 6.4 Commit: "feat: export reports"

### Fase 7: Release
**Tarefas**:
- [ ] 7.1 Testes completos
- [ ] 7.2 Documentação atualizada
- [ ] 7.3 CHANGELOG
- [ ] 7.4 Tag: v2.0.0

---

## Dependências

### Externas
- **CoinGecko API**: Dados de crypto (free tier)
- **SendGrid/SES**: Envio de emails para alertas
- **react-pdf**: Geração de PDFs

### Bloqueios
| Bloqueio | Impacto | Mitigação |
|----------|---------|-----------|
| CoinGecko rate limit | Dados crypto limitados | Cache agressivo |
| Sem autenticação | Alertas por sessão apenas | Considerar auth na v3 |

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| CoinGecko API changes | Baixa | Alto | Versionar API calls |
| Backtesting lento | Média | Médio | Limitar período, cache |
| Email spam | Baixa | Alto | Rate limit por sessão |
| Custo de alertas | Média | Médio | Limite free tier |

---

## Critérios de Aceitação da Release

### Checklist de Release v2.0.0

**Multi-Asset**:
- [ ] USD/BRL, EUR/BRL, BTC/BRL funcionando
- [ ] Seletor de ativo na UI
- [ ] Chat contextualizado

**Features**:
- [ ] Backtesting básico funcional
- [ ] Alertas configuráveis
- [ ] Gráficos interativos
- [ ] Exportação PDF/CSV

**Qualidade**:
- [ ] Testes passando
- [ ] Performance targets atingidos
- [ ] Zero regressões

---

## Métricas de Sucesso

| Métrica | Baseline (v1.0) | Target (v2.0) |
|---------|-----------------|---------------|
| Ativos suportados | 1 | 3 |
| Features de valor | 0 | 4 (backtest, alerts, charts, export) |
| Sessões simultâneas | 50 | 200 |
| Alertas ativos | 0 | 1000 |

---

## Referências

- [Roadmap Completo](ROADMAP-COMPLETE.md)
- [SPEC-v1.0](SPEC-v1.0.md)
- [CoinGecko API Docs](https://www.coingecko.com/en/api/documentation)
- [Recharts Docs](https://recharts.org/)
- [SendGrid Docs](https://docs.sendgrid.com/)

---

## Histórico

| Data | Versão | Autor | Mudanças |
|------|--------|-------|----------|
| 2026-01-23 | 1.0 | Claude | Criação inicial |
