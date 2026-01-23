# Política de Débitos Técnicos - Forex Advisor

> Documento que define como identificar, classificar e priorizar débitos técnicos no projeto.

**Última atualização**: 2026-01-23

---

## 1. Filosofia

Débitos técnicos são **inevitáveis** em qualquer projeto de software. O objetivo não é eliminá-los completamente, mas sim:

1. **Identificar** - Documentar todos os débitos conhecidos
2. **Classificar** - Avaliar severidade e impacto
3. **Priorizar** - Resolver os críticos, gerenciar os demais
4. **Aceitar** - Alguns débitos podem existir indefinidamente

### Princípios

- **Não bloquear progresso** por débitos de baixa severidade
- **Débito crítico = bloqueante** para a próxima versão
- **Débito médio = desejável** resolver, mas não obrigatório
- **Débito baixo = backlog** resolver quando conveniente
- **Transparência** - Todo débito deve estar documentado

---

## 2. Classificação de Severidade

### CRÍTICO (P0)

**Definição**: Impede funcionamento básico ou representa risco de segurança grave.

**Características**:
- Sistema não funciona sem resolver
- Vulnerabilidade de segurança exploitável
- Perda de dados possível
- Single point of failure em componente essencial

**Ação**: Resolver ANTES de qualquer release.

**Exemplos**:
- LLM sem fallback (sistema para se Minimax cair)
- SQL injection não tratado
- Credenciais expostas em logs

---

### MÉDIO (P1)

**Definição**: Afeta qualidade, performance ou experiência, mas sistema funciona.

**Características**:
- Degradação de performance
- UX prejudicada mas funcional
- Falta de observabilidade
- Código difícil de manter

**Ação**: Planejar para próxima versão, pode ser adiado 1x.

**Exemplos**:
- Sem métricas Prometheus
- Sem testes E2E
- Cache não otimizado

---

### BAIXO (P2)

**Definição**: Melhorias desejáveis que não afetam funcionamento.

**Características**:
- Code smell / código feio
- Dependência não utilizada
- Documentação incompleta
- Feature menor faltando

**Ação**: Backlog, resolver quando conveniente.

**Exemplos**:
- Import não utilizado
- Variável com nome ruim
- Campo da API não exposto

---

## 3. Matriz de Débitos Atual

### Legenda de Status

| Status | Significado |
|--------|-------------|
| ✅ | Resolvido |
| ⏳ | Pendente |
| 🚫 | Cancelado / Não aplicável |

### Frontend

| ID | Débito | Severidade | Versão Target | Notas |
|----|--------|------------|---------------|-------|
| DT-F3 | Transformações manuais (positives/risks) | Baixo | v1.x | Funciona, só não é elegante |
| DT-F4 | Sem testes E2E | Médio | v1.0 | Desejável para produção |
| DT-F5 | Sem indicador LLM ativo | Baixo | v1.x | Backend não expõe info |

### Backend

| ID | Débito | Severidade | Versão Target | Notas |
|----|--------|------------|---------------|-------|
| DT-B3 | Sem Prometheus | Médio | v1.0 | Observabilidade |
| DT-B5 | News ingestion manual | Baixo | v1.x | Funciona manualmente |
| DT-B6 | RAG cleanup manual | Baixo | v1.x | Funciona manualmente |
| DT-B8 | bollinger_middle não exposto | Baixo | v1.x | API funciona sem isso |

---

## 4. Critérios de Bloqueio por Versão

### Para ir para Produção (v1.0)

**Obrigatório** (bloqueia release):
- [ ] Zero débitos CRÍTICOS
- [ ] Testes unitários passando (✅ 79 testes)
- [ ] API funcional e documentada
- [ ] Segurança básica implementada (✅)
- [ ] Fallbacks de dependências externas (✅)

**Desejável** (não bloqueia):
- [ ] Testes E2E
- [ ] Métricas Prometheus
- [ ] CI/CD pipeline
- [ ] 99.5% uptime em staging

### Para ir para v2.0

**Obrigatório**:
- [ ] v1.0 estável em produção
- [ ] Arquitetura suporta multi-asset
- [ ] Sem débitos CRÍTICOS

**Desejável**:
- [ ] Débitos MÉDIOS < 5
- [ ] Cobertura testes > 80%

---

## 5. Resumo Executivo

### Estado Atual (v0.5)

```
Débitos Pendentes por Severidade:
├── CRÍTICO:  0 ✅
├── MÉDIO:    2 (Prometheus, E2E)
└── BAIXO:    5 (transformações, indicador LLM, news, RAG, bollinger)

Total: 7 pendentes
```

### Débitos por Versão Target

| Versão | Débitos | IDs |
|--------|---------|-----|
| v1.0 | 2 médios | DT-F4, DT-B3 |
| v1.x | 5 baixos | DT-F3, DT-F5, DT-B5, DT-B6, DT-B8 |

### Status para v1.0

| Critério | Status |
|----------|--------|
| Zero débitos críticos | ✅ |
| Testes passando | ✅ 79 testes |
| API funcional | ✅ |
| Segurança básica | ✅ |
| Fallbacks | ✅ |

**Veredicto: ✅ PODE ir para v1.0**

Os débitos pendentes são MÉDIOS ou BAIXOS e podem ser resolvidos em v1.1/v1.2.

---

## 6. Processo de Gestão

### Ao Identificar Novo Débito

1. Adicionar nesta matriz com ID único
2. Classificar severidade (Crítico/Médio/Baixo)
3. Definir versão target
4. Se CRÍTICO, bloquear próximo release

### Ao Resolver Débito

1. Marcar como ✅ na matriz
2. Anotar versão em que foi resolvido
3. Atualizar ROADMAP se necessário

### Revisão Periódica

- **Antes de cada release**: Revisar débitos críticos
- **Mensalmente**: Revisar débitos médios
- **Trimestralmente**: Avaliar débitos baixos (resolver ou aceitar)

---

## 7. Histórico

| Data | Mudança |
|------|---------|
| 2026-01-23 | Documento criado com política e matriz completa |
| 2026-01-23 | Limpeza: removidos 13 débitos resolvidos, mantidos 7 pendentes |

---

> **Nota**: Este documento deve ser atualizado sempre que débitos forem identificados ou resolvidos.
