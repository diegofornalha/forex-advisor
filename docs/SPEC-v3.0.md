# Especificação: Forex Advisor v3.0

> Agent Mode - Arquitetura Planejador/Executor/Verificador

## Metadados

| Campo | Valor |
|-------|-------|
| **Versão** | 3.0.0 |
| **Tipo** | Arquitetura de Agente |
| **Prioridade** | Estratégica |
| **Escopo** | Backend (novo core) |
| **Pré-requisito** | v2.0.0 estável |
| **Inspiração** | Manus AI, Claude Agent SDK, ReAct Pattern |

## Visão Geral

A v3.0 transforma o Forex Advisor de um sistema request-response em um **agente autônomo** capaz de planejar, executar e verificar tarefas complexas até entregar um resultado completo e validado ao usuário.

### O Diferencial

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARQUITETURA AGENT MODE                           │
│                                                                     │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐        │
│   │  PLANEJADOR  │───▶│   EXECUTOR   │───▶│ VERIFICADOR  │        │
│   │   (Planner)  │    │   (Actor)    │    │  (Critic)    │        │
│   └──────────────┘    └──────────────┘    └──────┬───────┘        │
│          ▲                                        │                 │
│          │            ┌──────────────┐           │                 │
│          └────────────│   FEEDBACK   │◀──────────┘                 │
│                       │     LOOP     │                             │
│                       └──────────────┘                             │
│                              │                                      │
│                              ▼                                      │
│                    ┌──────────────────┐                            │
│                    │  OUTPUT FINAL    │                            │
│                    │  (Validado)      │                            │
│                    └──────────────────┘                            │
└─────────────────────────────────────────────────────────────────────┘
```

### Comparação: Antes vs Depois

| Aspecto | v0.2-v2.0 (Request-Response) | v3.0 (Agent Mode) |
|---------|------------------------------|-------------------|
| **Fluxo** | Linear, single-shot | Iterativo, loop até completar |
| **Erros** | Retorna erro ao usuário | Auto-corrige e retenta |
| **Complexidade** | Tarefas simples | Tarefas multi-step |
| **Qualidade** | Depende do prompt | Verificada antes de entregar |
| **Autonomia** | Baixa | Alta |

---

## Arquitetura dos 3 Componentes

### 1. PLANEJADOR (Planner)

**Responsabilidade**: Decompor a tarefa do usuário em passos executáveis.

```
┌─────────────────────────────────────────────────────────────┐
│  PLANEJADOR                                                 │
│                                                             │
│  Input: "Analise o impacto da eleição no dólar"            │
│                                                             │
│  Output (Plano):                                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Step 1: Buscar dados OHLC outubro-novembro 2024     │   │
│  │ Step 2: Calcular volatilidade pré/pós eleição       │   │
│  │ Step 3: Buscar notícias relacionadas (RAG)          │   │
│  │ Step 4: Correlacionar dados com eventos             │   │
│  │ Step 5: Gerar visualização comparativa              │   │
│  │ Step 6: Sintetizar conclusão para o usuário         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Capabilities:                                              │
│  • Decomposição de tarefas complexas                       │
│  • Identificação de dependências entre steps               │
│  • Estimativa de ferramentas necessárias                   │
│  • Replanejamento quando verificador rejeita               │
└─────────────────────────────────────────────────────────────┘
```

**Prompt do Planejador**:
```python
PLANNER_SYSTEM_PROMPT = """
Você é o PLANEJADOR do Forex Advisor Agent.

Sua função é decompor a tarefa do usuário em passos executáveis.

Para cada passo, defina:
1. action: tipo de ação (CODE, RAG_SEARCH, API_CALL, SYNTHESIZE)
2. description: o que fazer
3. dependencies: IDs dos passos que devem completar antes
4. expected_output: o que esperar como resultado

Regras:
- Máximo de 10 passos por plano
- Passos devem ser atômicos e verificáveis
- Sempre termine com SYNTHESIZE para consolidar resultado
- Se a tarefa for simples, 1-2 passos são suficientes

Responda em JSON:
{
  "task_understanding": "...",
  "complexity": "low|medium|high",
  "steps": [
    {
      "id": 1,
      "action": "CODE",
      "description": "...",
      "dependencies": [],
      "expected_output": "..."
    }
  ]
}
"""
```

---

### 2. EXECUTOR (Actor)

**Responsabilidade**: Executar cada passo do plano usando as ferramentas disponíveis.

```
┌─────────────────────────────────────────────────────────────┐
│  EXECUTOR                                                   │
│                                                             │
│  Input: Step do plano + Contexto acumulado                 │
│                                                             │
│  Ferramentas Disponíveis:                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🐍 CODE_EXECUTOR    - E2B Sandbox (Python + Shell)  │   │
│  │ 🔍 RAG_SEARCH       - Busca semântica de notícias   │   │
│  │ 📊 DATA_FETCHER     - yfinance, CoinGecko           │   │
│  │ 🧮 INDICATOR_CALC   - SMA, RSI, Bollinger           │   │
│  │ 📝 SYNTHESIZER      - Gerar texto final             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Output:                                                    │
│  {                                                          │
│    "step_id": 1,                                           │
│    "status": "success|error|partial",                      │
│    "result": {...},                                        │
│    "stdout": "...",                                        │
│    "stderr": "...",                                        │
│    "artifacts": ["dataframe", "chart", ...]               │
│  }                                                          │
└─────────────────────────────────────────────────────────────┘
```

**Ferramentas do Executor**:

```python
class ExecutorTools:
    """Ferramentas disponíveis para o Executor"""

    async def execute_code(self, code: str) -> ExecutionResult:
        """Executa código Python no E2B sandbox"""
        # Injeta dados OHLC, indicadores pré-calculados
        # Retorna stdout, stderr, artifacts

    async def search_rag(self, query: str, top_k: int = 5) -> list[Document]:
        """Busca semântica no RAG de notícias"""

    async def fetch_data(self, symbol: str, period: str) -> pd.DataFrame:
        """Busca dados de mercado"""

    async def calculate_indicators(self, df: pd.DataFrame) -> dict:
        """Calcula indicadores técnicos"""

    async def synthesize(self, context: dict, instruction: str) -> str:
        """Gera texto sintetizado com LLM"""
```

---

### 3. VERIFICADOR (Critic)

**Responsabilidade**: Validar se o resultado está correto, completo e útil.

```
┌─────────────────────────────────────────────────────────────┐
│  VERIFICADOR                                                │
│                                                             │
│  Input: Resultado do Executor + Expectativa do Plano       │
│                                                             │
│  Checklist de Verificação:                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ✓ Resultado corresponde ao esperado?                │   │
│  │ ✓ Dados estão corretos e consistentes?              │   │
│  │ ✓ Código executou sem erros?                        │   │
│  │ ✓ Output é útil para o usuário?                     │   │
│  │ ✓ Compliance: sem recomendações de compra/venda?    │   │
│  │ ✓ Resposta está em português claro?                 │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Output:                                                    │
│  {                                                          │
│    "verdict": "APPROVED|REJECTED|NEEDS_IMPROVEMENT",       │
│    "score": 0.85,                                          │
│    "issues": ["..."],                                      │
│    "suggestions": ["..."],                                 │
│    "can_deliver": true|false                               │
│  }                                                          │
│                                                             │
│  Se REJECTED → Feedback para Planejador (replanejar)       │
│  Se NEEDS_IMPROVEMENT → Feedback para Executor (reexecutar)│
│  Se APPROVED → Entrega ao usuário                          │
└─────────────────────────────────────────────────────────────┘
```

**Prompt do Verificador**:
```python
VERIFIER_SYSTEM_PROMPT = """
Você é o VERIFICADOR do Forex Advisor Agent.

Sua função é avaliar se o resultado está pronto para entregar ao usuário.

Avalie em 5 dimensões (0-1 cada):
1. correctness: dados e cálculos estão corretos?
2. completeness: responde totalmente à pergunta?
3. clarity: está claro e bem explicado?
4. compliance: não dá recomendações de compra/venda?
5. usefulness: é útil para o usuário?

Score final = média das dimensões

Regras:
- Score >= 0.8: APPROVED (entregar ao usuário)
- Score 0.5-0.8: NEEDS_IMPROVEMENT (executor tenta de novo)
- Score < 0.5: REJECTED (planejador refaz plano)

Responda em JSON:
{
  "dimensions": {
    "correctness": 0.9,
    "completeness": 0.8,
    "clarity": 0.85,
    "compliance": 1.0,
    "usefulness": 0.9
  },
  "score": 0.89,
  "verdict": "APPROVED",
  "issues": [],
  "suggestions": [],
  "can_deliver": true
}
"""
```

---

## Fluxo Completo do Agent Loop

```
┌─────────────────────────────────────────────────────────────────────┐
│                         AGENT LOOP FLOW                             │
│                                                                     │
│  ┌─────────┐                                                        │
│  │  USER   │──── "Analise o impacto da eleição no dólar" ────┐     │
│  └─────────┘                                                  │     │
│                                                               ▼     │
│  ┌────────────────────────────────────────────────────────────────┐│
│  │  ITERATION 1                                                   ││
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐                 ││
│  │  │ PLANNER  │───▶│ EXECUTOR │───▶│ VERIFIER │                 ││
│  │  └──────────┘    └──────────┘    └────┬─────┘                 ││
│  │       │                               │                        ││
│  │       │         Plan: 6 steps         │  Verdict: NEEDS_       ││
│  │       │         Execute: step 1-3     │  IMPROVEMENT           ││
│  │       │         (dados + cálculos)    │  (falta visualização)  ││
│  └───────┼───────────────────────────────┼────────────────────────┘│
│          │                               │                         │
│          │         ◀── FEEDBACK ─────────┘                         │
│          │                                                         │
│  ┌───────┼────────────────────────────────────────────────────────┐│
│  │  ITERATION 2                                                   ││
│  │       │                                                        ││
│  │       ▼                                                        ││
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐                 ││
│  │  │ PLANNER  │───▶│ EXECUTOR │───▶│ VERIFIER │                 ││
│  │  │(ajustado)│    │(step 4-6)│    └────┬─────┘                 ││
│  │  └──────────┘    └──────────┘         │                        ││
│  │                                       │  Verdict: APPROVED     ││
│  │                                       │  Score: 0.92           ││
│  └───────────────────────────────────────┼────────────────────────┘│
│                                          │                         │
│                                          ▼                         │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │  FINAL OUTPUT (Validado)                                    │  │
│  │                                                             │  │
│  │  "A eleição americana de novembro de 2024 teve impacto     │  │
│  │   significativo no dólar. A volatilidade aumentou 23%      │  │
│  │   na semana pré-eleição. Após o resultado, o dólar         │  │
│  │   valorizou 4.2% em relação ao real..."                    │  │
│  │                                                             │  │
│  │  [Gráfico comparativo] [Tabela de dados] [Fontes]          │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                          │                         │
│                                          ▼                         │
│  ┌─────────┐                                                       │
│  │  USER   │◀─────────────────────────────────────────────────────│
│  └─────────┘                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementação Técnica

### Estrutura de Arquivos

```
app/
├── agent/                           [CRIAR]
│   ├── __init__.py
│   ├── core.py                     # AgentCore - orquestrador
│   ├── planner.py                  # Planejador
│   ├── executor.py                 # Executor
│   ├── verifier.py                 # Verificador
│   ├── tools/                      # Ferramentas do Executor
│   │   ├── __init__.py
│   │   ├── code_executor.py        # E2B integration
│   │   ├── rag_search.py           # RAG search
│   │   ├── data_fetcher.py         # Market data
│   │   └── synthesizer.py          # Text generation
│   ├── memory.py                   # Contexto entre iterações
│   ├── models.py                   # Pydantic models
│   └── prompts.py                  # System prompts
├── chat.py                          [MODIFICAR]
│   └── Integrar AgentCore
└── config.py                        [MODIFICAR]
    └── Agent settings
```

### Classes Principais

```python
# app/agent/models.py
from pydantic import BaseModel
from enum import Enum
from typing import Optional

class ActionType(str, Enum):
    CODE = "CODE"
    RAG_SEARCH = "RAG_SEARCH"
    DATA_FETCH = "DATA_FETCH"
    INDICATOR_CALC = "INDICATOR_CALC"
    SYNTHESIZE = "SYNTHESIZE"

class PlanStep(BaseModel):
    id: int
    action: ActionType
    description: str
    dependencies: list[int] = []
    expected_output: str

class Plan(BaseModel):
    task_understanding: str
    complexity: str  # low, medium, high
    steps: list[PlanStep]

class ExecutionResult(BaseModel):
    step_id: int
    status: str  # success, error, partial
    result: Optional[dict] = None
    stdout: str = ""
    stderr: str = ""
    artifacts: list[str] = []

class VerificationResult(BaseModel):
    dimensions: dict[str, float]
    score: float
    verdict: str  # APPROVED, NEEDS_IMPROVEMENT, REJECTED
    issues: list[str] = []
    suggestions: list[str] = []
    can_deliver: bool

class AgentState(BaseModel):
    task: str
    plan: Optional[Plan] = None
    executions: list[ExecutionResult] = []
    verifications: list[VerificationResult] = []
    iteration: int = 0
    status: str = "planning"  # planning, executing, verifying, complete, failed
    final_output: Optional[str] = None
```

```python
# app/agent/core.py
from .planner import Planner
from .executor import Executor
from .verifier import Verifier
from .models import AgentState, VerificationResult

class AgentCore:
    """Orquestrador do Agent Loop"""

    def __init__(
        self,
        llm_router,
        sandbox,
        rag,
        max_iterations: int = 5,
        min_score: float = 0.8,
    ):
        self.planner = Planner(llm_router)
        self.executor = Executor(sandbox, rag)
        self.verifier = Verifier(llm_router)
        self.max_iterations = max_iterations
        self.min_score = min_score

    async def run(self, task: str, on_progress: callable = None) -> str:
        """
        Executa o agent loop até completar a tarefa.

        Args:
            task: Tarefa do usuário
            on_progress: Callback para streaming de progresso

        Returns:
            Resultado final validado
        """
        state = AgentState(task=task)

        for iteration in range(self.max_iterations):
            state.iteration = iteration + 1

            # 1. PLANEJAR
            if on_progress:
                await on_progress({"phase": "planning", "iteration": iteration + 1})

            state.plan = await self.planner.create_plan(
                task=task,
                previous_executions=state.executions,
                feedback=self._get_last_feedback(state),
            )
            state.status = "executing"

            # 2. EXECUTAR
            if on_progress:
                await on_progress({"phase": "executing", "plan": state.plan})

            for step in state.plan.steps:
                # Verificar dependências
                if not self._dependencies_met(step, state.executions):
                    continue

                result = await self.executor.execute_step(
                    step=step,
                    context=self._build_context(state),
                )
                state.executions.append(result)

                if on_progress:
                    await on_progress({"phase": "step_complete", "step": step.id, "result": result})

            state.status = "verifying"

            # 3. VERIFICAR
            if on_progress:
                await on_progress({"phase": "verifying"})

            verification = await self.verifier.verify(
                task=task,
                plan=state.plan,
                executions=state.executions,
            )
            state.verifications.append(verification)

            # 4. DECIDIR
            if verification.verdict == "APPROVED":
                state.status = "complete"
                state.final_output = await self._synthesize_output(state)

                if on_progress:
                    await on_progress({"phase": "complete", "score": verification.score})

                return state.final_output

            elif verification.verdict == "REJECTED":
                # Limpar execuções e replanejar do zero
                state.executions = []
                if on_progress:
                    await on_progress({"phase": "replanning", "reason": verification.issues})

            else:  # NEEDS_IMPROVEMENT
                # Manter execuções, apenas continuar de onde parou
                if on_progress:
                    await on_progress({"phase": "improving", "suggestions": verification.suggestions})

        # Limite de iterações atingido
        state.status = "failed"
        return await self._synthesize_partial_output(state)

    def _get_last_feedback(self, state: AgentState) -> Optional[VerificationResult]:
        return state.verifications[-1] if state.verifications else None

    def _dependencies_met(self, step, executions) -> bool:
        completed_ids = {e.step_id for e in executions if e.status == "success"}
        return all(dep in completed_ids for dep in step.dependencies)

    def _build_context(self, state: AgentState) -> dict:
        return {
            "task": state.task,
            "completed_steps": [e.dict() for e in state.executions if e.status == "success"],
            "artifacts": self._collect_artifacts(state.executions),
        }

    def _collect_artifacts(self, executions) -> dict:
        artifacts = {}
        for e in executions:
            if e.result:
                artifacts[f"step_{e.step_id}"] = e.result
        return artifacts

    async def _synthesize_output(self, state: AgentState) -> str:
        """Gera output final consolidado"""
        return await self.executor.tools.synthesize(
            context=self._build_context(state),
            instruction="Gere uma resposta completa e bem formatada para o usuário.",
        )

    async def _synthesize_partial_output(self, state: AgentState) -> str:
        """Gera output parcial quando limite é atingido"""
        return await self.executor.tools.synthesize(
            context=self._build_context(state),
            instruction="Gere uma resposta com o que foi possível analisar, indicando limitações.",
        )
```

```python
# app/agent/planner.py
from .models import Plan, PlanStep
from .prompts import PLANNER_SYSTEM_PROMPT

class Planner:
    def __init__(self, llm_router):
        self.llm = llm_router

    async def create_plan(
        self,
        task: str,
        previous_executions: list = None,
        feedback: VerificationResult = None,
    ) -> Plan:
        """Cria ou ajusta plano de execução"""

        messages = [
            {"role": "system", "content": PLANNER_SYSTEM_PROMPT},
            {"role": "user", "content": self._build_prompt(task, previous_executions, feedback)},
        ]

        response = await self.llm.acompletion(
            messages=messages,
            response_format={"type": "json_object"},
        )

        plan_data = json.loads(response.choices[0].message.content)
        return Plan(**plan_data)

    def _build_prompt(self, task, executions, feedback) -> str:
        prompt = f"TAREFA DO USUÁRIO:\n{task}\n\n"

        if executions:
            prompt += "EXECUÇÕES ANTERIORES:\n"
            for e in executions:
                prompt += f"- Step {e.step_id}: {e.status}\n"
            prompt += "\n"

        if feedback:
            prompt += f"FEEDBACK DO VERIFICADOR:\n"
            prompt += f"- Verdict: {feedback.verdict}\n"
            prompt += f"- Issues: {feedback.issues}\n"
            prompt += f"- Suggestions: {feedback.suggestions}\n"
            prompt += "\nAjuste o plano considerando este feedback.\n"

        return prompt
```

```python
# app/agent/executor.py
from .tools import CodeExecutor, RAGSearch, DataFetcher, Synthesizer
from .models import PlanStep, ExecutionResult

class Executor:
    def __init__(self, sandbox, rag):
        self.tools = ExecutorTools(sandbox, rag)

    async def execute_step(self, step: PlanStep, context: dict) -> ExecutionResult:
        """Executa um step do plano"""

        try:
            if step.action == "CODE":
                result = await self._execute_code(step, context)
            elif step.action == "RAG_SEARCH":
                result = await self._execute_rag(step, context)
            elif step.action == "DATA_FETCH":
                result = await self._execute_data_fetch(step, context)
            elif step.action == "INDICATOR_CALC":
                result = await self._execute_indicators(step, context)
            elif step.action == "SYNTHESIZE":
                result = await self._execute_synthesis(step, context)
            else:
                raise ValueError(f"Unknown action: {step.action}")

            return ExecutionResult(
                step_id=step.id,
                status="success",
                result=result.get("data"),
                stdout=result.get("stdout", ""),
                stderr=result.get("stderr", ""),
                artifacts=result.get("artifacts", []),
            )

        except Exception as e:
            return ExecutionResult(
                step_id=step.id,
                status="error",
                stderr=str(e),
            )

    async def _execute_code(self, step: PlanStep, context: dict) -> dict:
        # Gera código baseado na descrição do step
        code = await self._generate_code(step.description, context)
        return await self.tools.code_executor.execute(code, context)

    async def _generate_code(self, description: str, context: dict) -> str:
        # Usa LLM para gerar código Python
        # Similar ao chat atual, mas mais estruturado
        pass
```

```python
# app/agent/verifier.py
from .models import VerificationResult
from .prompts import VERIFIER_SYSTEM_PROMPT

class Verifier:
    def __init__(self, llm_router):
        self.llm = llm_router

    async def verify(
        self,
        task: str,
        plan: Plan,
        executions: list[ExecutionResult],
    ) -> VerificationResult:
        """Verifica se o resultado está pronto para entregar"""

        messages = [
            {"role": "system", "content": VERIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": self._build_prompt(task, plan, executions)},
        ]

        response = await self.llm.acompletion(
            messages=messages,
            response_format={"type": "json_object"},
        )

        result_data = json.loads(response.choices[0].message.content)
        return VerificationResult(**result_data)

    def _build_prompt(self, task, plan, executions) -> str:
        prompt = f"TAREFA ORIGINAL:\n{task}\n\n"
        prompt += f"PLANO EXECUTADO:\n{plan.json(indent=2)}\n\n"
        prompt += "RESULTADOS DAS EXECUÇÕES:\n"

        for e in executions:
            prompt += f"\n--- Step {e.step_id} ---\n"
            prompt += f"Status: {e.status}\n"
            if e.stdout:
                prompt += f"Output:\n{e.stdout[:1000]}\n"
            if e.stderr:
                prompt += f"Errors:\n{e.stderr[:500]}\n"

        prompt += "\nAvalie se o resultado está pronto para entregar ao usuário."
        return prompt
```

---

## Integração com WebSocket

```python
# app/chat.py (modificado)

from .agent import AgentCore

@router.websocket("/ws/chat/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()

    agent = AgentCore(
        llm_router=get_router(),
        sandbox=get_sandbox(),
        rag=get_rag(),
    )

    async def on_progress(update: dict):
        """Callback para streaming de progresso"""
        await websocket.send_json({
            "type": "agent_progress",
            "phase": update.get("phase"),
            "data": update,
        })

    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "").strip()

            if not user_message:
                continue

            # Detectar se precisa de agent mode ou resposta simples
            if await should_use_agent(user_message):
                # Agent Mode: loop completo
                result = await agent.run(
                    task=user_message,
                    on_progress=on_progress,
                )
            else:
                # Simple Mode: resposta direta (como antes)
                result = await simple_response(user_message)

            await websocket.send_json({
                "type": "done",
                "content": result,
            })

    except WebSocketDisconnect:
        pass


async def should_use_agent(message: str) -> bool:
    """Detecta se a mensagem precisa do agent mode"""

    # Heurísticas para ativar agent mode:
    complex_keywords = [
        "analise", "análise", "compare", "correlacione",
        "histórico", "impacto", "backtest", "período",
        "calcule e mostre", "faça uma análise completa",
    ]

    message_lower = message.lower()

    # Ativa se mensagem é longa ou contém keywords
    if len(message) > 100:
        return True

    for keyword in complex_keywords:
        if keyword in message_lower:
            return True

    return False
```

---

## UI de Progresso no Frontend

```typescript
// src/components/chat/AgentProgress.tsx

interface AgentProgressProps {
  phase: string;
  data: any;
}

export function AgentProgress({ phase, data }: AgentProgressProps) {
  const phases = {
    planning: { icon: "🎯", label: "Planejando análise...", color: "blue" },
    executing: { icon: "⚡", label: "Executando...", color: "yellow" },
    step_complete: { icon: "✓", label: `Step ${data?.step} completo`, color: "green" },
    verifying: { icon: "🔍", label: "Verificando qualidade...", color: "purple" },
    improving: { icon: "🔄", label: "Melhorando resultado...", color: "orange" },
    replanning: { icon: "📋", label: "Replanejando...", color: "red" },
    complete: { icon: "✅", label: "Análise completa!", color: "green" },
  };

  const current = phases[phase] || { icon: "⏳", label: phase, color: "gray" };

  return (
    <div className={`flex items-center gap-2 p-2 rounded bg-${current.color}-900/20`}>
      <span className="text-lg">{current.icon}</span>
      <span className="text-sm">{current.label}</span>
      {phase === "executing" && data?.plan && (
        <span className="text-xs text-muted-foreground">
          ({data.plan.steps.length} steps)
        </span>
      )}
      {phase === "complete" && data?.score && (
        <span className="text-xs text-green-400">
          Score: {(data.score * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
}
```

---

## Configurações

```env
# .env - Agent Settings

# Agent Core
AGENT_ENABLED=true
AGENT_MAX_ITERATIONS=5
AGENT_MIN_SCORE=0.8
AGENT_TIMEOUT=120

# Planner
PLANNER_MODEL=claude-haiku
PLANNER_MAX_STEPS=10

# Executor
EXECUTOR_CODE_TIMEOUT=30
EXECUTOR_MAX_CODE_LENGTH=5000

# Verifier
VERIFIER_MODEL=claude-haiku
VERIFIER_DIMENSIONS=correctness,completeness,clarity,compliance,usefulness
```

---

## Fases de Implementação

### Fase 1: Core do Agent
**Tarefas**:
- [ ] 1.1 Criar estrutura `app/agent/`
- [ ] 1.2 Implementar `models.py` com Pydantic
- [ ] 1.3 Implementar `prompts.py`
- [ ] 1.4 Implementar `AgentCore` básico
- [ ] 1.5 Testes unitários do core
- [ ] 1.6 Commit: "feat: agent core structure"

### Fase 2: Planejador
**Tarefas**:
- [ ] 2.1 Implementar `Planner` class
- [ ] 2.2 Prompt engineering para decomposição
- [ ] 2.3 Suporte a replanejamento
- [ ] 2.4 Testes do planejador
- [ ] 2.5 Commit: "feat: agent planner component"

### Fase 3: Executor
**Tarefas**:
- [ ] 3.1 Implementar `Executor` class
- [ ] 3.2 Integrar ferramentas existentes (E2B, RAG)
- [ ] 3.3 Adicionar novas ferramentas
- [ ] 3.4 Context management entre steps
- [ ] 3.5 Testes do executor
- [ ] 3.6 Commit: "feat: agent executor component"

### Fase 4: Verificador
**Tarefas**:
- [ ] 4.1 Implementar `Verifier` class
- [ ] 4.2 Sistema de scoring multi-dimensional
- [ ] 4.3 Feedback loop para planner/executor
- [ ] 4.4 Testes do verificador
- [ ] 4.5 Commit: "feat: agent verifier component"

### Fase 5: Integração WebSocket
**Tarefas**:
- [ ] 5.1 Modificar `chat.py` para usar AgentCore
- [ ] 5.2 Implementar detecção de complexidade
- [ ] 5.3 Streaming de progresso
- [ ] 5.4 Fallback para modo simples
- [ ] 5.5 Testes de integração
- [ ] 5.6 Commit: "feat: integrate agent with websocket"

### Fase 6: Frontend Progress UI
**Tarefas**:
- [ ] 6.1 Criar `AgentProgress` component
- [ ] 6.2 Integrar no `ChatPanel`
- [ ] 6.3 Animações de estado
- [ ] 6.4 Testes E2E
- [ ] 6.5 Commit: "feat: agent progress UI"

### Fase 7: Refinamento e Release
**Tarefas**:
- [ ] 7.1 Tune de prompts
- [ ] 7.2 Ajuste de thresholds
- [ ] 7.3 Métricas de agent
- [ ] 7.4 Documentação
- [ ] 7.5 Tag: v3.0.0

---

## Métricas de Sucesso

| Métrica | Target |
|---------|--------|
| Taxa de aprovação do verificador (1ª tentativa) | > 70% |
| Taxa de aprovação (até 3 iterações) | > 95% |
| Tempo médio para tarefa complexa | < 60s |
| Satisfação do usuário com respostas | > 4.5/5 |
| Redução de "respostas incompletas" | > 80% |

---

## Riscos e Mitigações

| Risco | Probabilidade | Impacto | Mitigação |
|-------|---------------|---------|-----------|
| Loop infinito | Baixa | Alto | max_iterations, timeout |
| Custo de LLM alto | Média | Médio | Cache, modelo menor para planner/verifier |
| Latência | Média | Médio | Streaming de progresso, paralelização |
| Verificador muito crítico | Média | Médio | Ajustar min_score, tune prompts |
| Planejador over-engineering | Média | Baixo | Limitar steps, detectar simplicidade |

---

## Referências

- [Roadmap Completo](ROADMAP-COMPLETE.md)
- [SPEC-v2.0](SPEC-v2.0.md)
- [Manus AI Architecture](https://manus.ai/docs)
- [ReAct Paper](https://arxiv.org/abs/2210.03629)
- [Claude Agent SDK](https://docs.anthropic.com/en/docs/agents)
- [E2B Docs](https://e2b.dev/docs)

---

## Histórico

| Data | Versão | Autor | Mudanças |
|------|--------|-------|----------|
| 2026-01-23 | 1.0 | Claude | Criação inicial |
