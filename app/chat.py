"""Chat WebSocket endpoint with E2B code execution."""

import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .cache import get_cached, set_cached
from .config import settings
from .llm_router import get_router
from .rag_sdk import SimpleRAG
from .recommendation import get_classification
from .sandbox import execute_analysis_code

logger = logging.getLogger(__name__)

# RAG instance (lazy loaded)
_rag: SimpleRAG | None = None


def get_rag() -> SimpleRAG:
    """Get RAG instance (singleton).

    Returns:
        SimpleRAG instance
    """
    global _rag
    if _rag is None:
        _rag = SimpleRAG(settings.rag_db_path)
    return _rag


async def get_news_context(query: str, top_k: int = 3) -> tuple[str, list[str]]:
    """Search for relevant news context using RAG.

    Args:
        query: User message to find relevant context
        top_k: Number of results to return

    Returns:
        Tuple of (context_text, list_of_sources)
    """
    try:
        rag = get_rag()
        results = await rag.search(query, top_k=top_k)
        logger.info(f"RAG search for '{query[:50]}...' returned {len(results)} results")

        if not results:
            return "", []

        # Build context and extract sources
        context_parts = []
        sources = []

        for r in results:
            if r.similarity > 0.1:  # Lower threshold for Portuguese text
                context_parts.append(f"- {r.content}")
                if r.source not in sources:
                    sources.append(r.source)

        context = "\n".join(context_parts)
        return context, sources

    except Exception as e:
        import traceback
        logger.error(f"RAG search failed: {e}")
        logger.error(traceback.format_exc())
        return "", []

router = APIRouter(tags=["Chat"])


# Models
class ChatMessage(BaseModel):
    """Single chat message."""
    role: str  # "user" | "assistant"
    content: str
    timestamp: str | None = None
    code_result: dict | None = None


class ChatSession(BaseModel):
    """Chat session with history."""
    session_id: str
    messages: list[ChatMessage]
    created_at: str
    last_activity: str


# Code extraction regex
CODE_BLOCK_PATTERN = re.compile(r"```python\n(.*?)```", re.DOTALL)


def extract_python_code(text: str) -> list[str]:
    """Extract Python code blocks from text.

    Args:
        text: Text containing markdown code blocks

    Returns:
        List of code strings
    """
    matches = CODE_BLOCK_PATTERN.findall(text)
    return [m.strip() for m in matches if m.strip()]


def validate_code(code: str) -> tuple[bool, str]:
    """Validate code against whitelist.

    Args:
        code: Python code to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(code) > settings.chat_max_code_length:
        return False, f"Code too long ({len(code)} > {settings.chat_max_code_length})"

    allowed_imports = settings.chat_allowed_imports.split(",")

    # Check for dangerous patterns
    dangerous_patterns = [
        r"\bos\.",
        r"\bsys\.",
        r"\bsubprocess\b",
        r"\beval\b",
        r"\bexec\b",
        r"\bopen\(",
        r"__import__",
        r"\brequests\b",
        r"\burllib\b",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, code):
            return False, f"Código contém operação não permitida: {pattern}"

    # Extract imports and validate
    import_pattern = re.compile(r"(?:from|import)\s+(\w+)")
    imports = import_pattern.findall(code)

    for imp in imports:
        if imp not in allowed_imports:
            return False, f"Import não permitido: {imp}. Permitidos: {allowed_imports}"

    return True, ""


async def get_chat_session(session_id: str) -> ChatSession | None:
    """Get chat session from cache.

    Args:
        session_id: Session identifier

    Returns:
        ChatSession or None if not found
    """
    cache_key = f"chat:session:{session_id}"
    data = await get_cached(cache_key)

    if data:
        return ChatSession(**data)
    return None


async def save_chat_session(session: ChatSession) -> None:
    """Save chat session to cache.

    Args:
        session: Session to save
    """
    cache_key = f"chat:session:{session.session_id}"

    # Update last activity
    session.last_activity = datetime.utcnow().isoformat()

    # Limit history size
    if len(session.messages) > settings.chat_max_history:
        session.messages = session.messages[-settings.chat_max_history:]

    await set_cached(
        cache_key,
        session.model_dump(),
        ttl=settings.chat_session_ttl,
    )


def build_system_prompt(classification: Any, news_context: str = "") -> str:
    """Build system prompt with market context and news.

    Args:
        classification: Current market classification
        news_context: Optional news context from RAG

    Returns:
        System prompt string
    """
    # Base prompt with market data
    prompt = f"""Você é um assistente especializado em análise de câmbio USD/BRL para usuários leigos.

CONTEXTO ATUAL DO MERCADO:
- Classificação: {classification.classification.value}
- Confiança: {classification.confidence:.1%}
- Preço atual: R$ {classification.indicators.current_price:.4f}
- SMA20: R$ {classification.indicators.sma20:.4f}
- SMA50: R$ {classification.indicators.sma50:.4f}
- RSI: {classification.indicators.rsi:.1f}
- Bollinger Superior: R$ {classification.indicators.bollinger_upper:.4f}
- Bollinger Inferior: R$ {classification.indicators.bollinger_lower:.4f}

Explicação técnica: {classification.explanation}
"""

    # Add news context if available
    if news_context:
        prompt += f"""
NOTÍCIAS RECENTES SOBRE CÂMBIO:
{news_context}

Use estas notícias para contextualizar suas respostas quando relevante.
"""

    # Instructions
    prompt += f"""
INSTRUÇÕES IMPORTANTES PARA SUAS RESPOSTAS:
1. Use linguagem SIMPLES e acessível - o usuário é leigo em finanças
2. Apresente os resultados de forma clara e amigável, com valores em Reais formatados
3. Você NÃO deve dar recomendações de compra/venda - apenas análises educacionais
4. Responda sempre em português brasileiro
5. Se usar informações das notícias, mencione a fonte

QUANDO O USUÁRIO PEDIR CÁLCULOS OU ANÁLISES:
1. Diga brevemente "Vou analisar os dados..."
2. SEMPRE gere código Python em um bloco ```python para executar a análise
3. O código DEVE usar print() para mostrar os resultados
4. IMPORTANTE: O DataFrame `df` contém dados REAIS e ATUALIZADOS do USD/BRL dos últimos 3 meses
   - Colunas disponíveis: Date, Open, High, Low, Close, Volume
   - NÃO simule dados - use df diretamente!
5. Imports permitidos: {settings.chat_allowed_imports}

EXEMPLO DE RESPOSTA COM CÓDIGO:
Vou analisar os dados para calcular a média.

```python
import pandas as pd
media = df['Close'].tail(10).mean()
print(f"Média dos últimos 10 dias: R$ {{media:.4f}}")
```
"""
    return prompt


async def generate_response_stream(
    message: str,
    session: ChatSession,
    websocket: WebSocket,
) -> str:
    """Generate streaming response using LLM.

    Args:
        message: User message
        session: Chat session with history
        websocket: WebSocket connection for streaming

    Returns:
        Full response text
    """
    llm_router = get_router()

    if llm_router is None:
        return "Erro: LLM não configurado."

    try:
        # Get current market context
        classification = await get_classification()

        # Get news context from RAG (async, graceful fallback)
        news_context, news_sources = await get_news_context(message, top_k=3)
        if news_context:
            logger.debug(f"RAG found {len(news_sources)} relevant sources")

        # Build messages with history
        messages = [
            {"role": "system", "content": build_system_prompt(classification, news_context)},
        ]

        # Add history (last N messages)
        for msg in session.messages[-10:]:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        # Add current message
        messages.append({"role": "user", "content": message})

        # Stream response
        full_response = ""

        response = await llm_router.acompletion(
            messages=messages,
            max_tokens=settings.llm_max_tokens,
            stream=True,
        )

        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_response += content

                # Send chunk to client
                await websocket.send_json({
                    "type": "chunk",
                    "content": content,
                })

        return full_response

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return f"Erro ao gerar resposta: {str(e)}"


@router.websocket("/ws/chat/{session_id}")
async def chat_websocket(websocket: WebSocket, session_id: str | None = None):
    """WebSocket endpoint for chat with streaming.

    Protocol:
    - Client sends: {"message": "user message"}
    - Server sends: {"type": "chunk", "content": "..."} (multiple)
    - Server sends: {"type": "execution", "result": {...}} (if code executed)
    - Server sends: {"type": "done"}
    """
    await websocket.accept()
    logger.info(f"WebSocket connected: {session_id}")

    # Create or get session
    if not session_id or session_id == "new":
        session_id = str(uuid.uuid4())
        session = ChatSession(
            session_id=session_id,
            messages=[],
            created_at=datetime.utcnow().isoformat(),
            last_activity=datetime.utcnow().isoformat(),
        )
    else:
        session = await get_chat_session(session_id)
        if not session:
            session = ChatSession(
                session_id=session_id,
                messages=[],
                created_at=datetime.utcnow().isoformat(),
                last_activity=datetime.utcnow().isoformat(),
            )

    # Send session info
    await websocket.send_json({
        "type": "session",
        "session_id": session.session_id,
    })

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()
            user_message = data.get("message", "").strip()

            if not user_message:
                continue

            logger.debug(f"Chat message: {user_message[:100]}...")

            # Add user message to session
            session.messages.append(ChatMessage(
                role="user",
                content=user_message,
                timestamp=datetime.utcnow().isoformat(),
            ))

            # Generate streaming response
            response_text = await generate_response_stream(
                user_message,
                session,
                websocket,
            )

            # Check for code blocks in response
            code_blocks = extract_python_code(response_text)
            code_result = None

            if code_blocks:
                # Execute first code block
                code = code_blocks[0]
                is_valid, error = validate_code(code)

                if is_valid:
                    try:
                        # Get OHLC data for injection
                        import yfinance as yf
                        import pandas as pd
                        df = yf.download(
                            settings.symbol,
                            period="3mo",
                            progress=False,
                        )
                        # Flatten multi-level columns if present
                        if hasattr(df.columns, 'levels'):
                            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

                        # Filter out weekends (Saturday=5, Sunday=6)
                        df = df.reset_index()
                        df['Date'] = pd.to_datetime(df['Date'])
                        df = df[df['Date'].dt.dayofweek < 5]  # Keep only Mon-Fri

                        # Convert to JSON-serializable format
                        df['Date'] = df['Date'].astype(str)
                        ohlc_data = df.to_dict(orient="records")

                        # Execute in sandbox
                        code_result = execute_analysis_code(
                            code,
                            {"ohlc_data": ohlc_data},
                        )

                        # Send execution result
                        await websocket.send_json({
                            "type": "execution",
                            "result": code_result,
                        })

                    except Exception as e:
                        logger.error(f"Code execution error: {e}")
                        code_result = {"error": str(e)}
                        await websocket.send_json({
                            "type": "execution",
                            "result": code_result,
                        })
                else:
                    code_result = {"error": error}
                    await websocket.send_json({
                        "type": "execution",
                        "result": code_result,
                    })

            # Add assistant message to session
            session.messages.append(ChatMessage(
                role="assistant",
                content=response_text,
                timestamp=datetime.utcnow().isoformat(),
                code_result=code_result,
            ))

            # Save session
            await save_chat_session(session)

            # Signal completion
            await websocket.send_json({"type": "done"})

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass


@router.get("/api/v1/chat/session/{session_id}")
async def get_session_history(session_id: str):
    """Get chat session history.

    Args:
        session_id: Session identifier

    Returns:
        Session data or 404
    """
    session = await get_chat_session(session_id)

    if not session:
        return {"error": "Session not found"}

    return session.model_dump()
