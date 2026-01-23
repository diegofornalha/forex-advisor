"""Documentation Chat WebSocket endpoint.

Provides an interactive chat interface for navigating the Forex Advisor documentation.
Uses the project's markdown files as knowledge base via system prompt.
"""

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .cache import get_cached, set_cached
from .config import settings
from .llm_router import get_router

logger = logging.getLogger(__name__)


# =============================================================================
# GUARDRAILS - Anti-hallucination validation
# =============================================================================

# Patterns that indicate hallucination (offering to create, suggest, etc.)
HALLUCINATION_PATTERNS = [
    # Ofertas de criar
    r"posso criar",
    r"gostaria que eu cria",
    r"quer que eu cria",
    r"podemos criar",
    r"vou criar",
    r"criarei",
    r"posso gerar",
    r"posso desenvolver",
    r"posso elaborar",
    r"posso preparar",
    r"posso montar",
    r"posso fazer para você",
    r"posso escrever para você",
    # Ofertas de sugestão não documentada
    r"sugiro que",
    r"recomendo que",
    r"minha sugestão",
    r"você poderia considerar",
    r"uma opção seria",
    r"você pode usar",
    r"você deveria",
    # Cloud providers não documentados
    r"\baws\b",
    r"\becs\b",
    r"\blambda\b",
    r"\bs3\b",
    r"\bec2\b",
    r"\bfargate\b",
    r"\bazure\b",
    r"\bgcp\b",
    r"\bheroku\b",
    r"\bvercel\b",
    r"\bnetlify\b",
    r"\brailway\b",
    r"\brender\.com\b",
    r"\bdigitalocean\b",
    # Perguntas para criar
    r"gostaria de um",
    r"quer que eu detalhe",
    r"deseja que eu",
    r"prefere que eu",
    r"quer mais detalhes sobre como",
]

# Resposta padrão quando alucinação é detectada
HALLUCINATION_FALLBACK = (
    "Essa informação não está documentada no projeto. "
    "Consulte a equipe para mais detalhes."
)


def detect_hallucination(response: str) -> tuple[bool, str | None]:
    """Detect if response contains hallucination patterns.

    Args:
        response: LLM response text

    Returns:
        Tuple of (is_hallucination, matched_pattern)
    """
    response_lower = response.lower()

    for pattern in HALLUCINATION_PATTERNS:
        if re.search(pattern, response_lower):
            logger.warning(f"Hallucination detected: pattern '{pattern}' in response")
            return True, pattern

    return False, None


def sanitize_response(response: str) -> str:
    """Sanitize response by removing or replacing hallucinated content.

    If the entire response seems to be hallucination, return fallback.
    Otherwise, try to keep valid parts.

    Args:
        response: Original LLM response

    Returns:
        Sanitized response
    """
    is_hallucination, pattern = detect_hallucination(response)

    if not is_hallucination:
        return response

    # Log for monitoring
    logger.info(f"Sanitizing hallucination (pattern: {pattern})")

    # If response is short and contains hallucination, replace entirely
    if len(response) < 500:
        return HALLUCINATION_FALLBACK

    # For longer responses, try to extract valid parts
    # Split by sentences and filter
    sentences = re.split(r'(?<=[.!?])\s+', response)
    valid_sentences = []

    for sentence in sentences:
        sentence_has_hallucination, _ = detect_hallucination(sentence)
        if not sentence_has_hallucination:
            valid_sentences.append(sentence)

    if not valid_sentences:
        return HALLUCINATION_FALLBACK

    # Reconstruct response
    sanitized = " ".join(valid_sentences)

    # Add fallback note if we removed significant content
    if len(sanitized) < len(response) * 0.5:
        sanitized += f"\n\n{HALLUCINATION_FALLBACK}"

    return sanitized

router = APIRouter(tags=["Documentation"])

# Docs directory path
DOCS_DIR = Path(__file__).parent.parent / "docs"

# Cache for loaded documentation
_docs_cache: dict[str, str] | None = None

# Priority order for loading docs (most important first)
PRIORITY_DOCS = [
    "STATUS.md",
    "CONTRIBUTING.md",
    "ONBOARDING.md",
    "README.md",
    "TECH-DEBT.md",
    "TESTS.md",
    "ROADMAP.md",
]


class DocsMessage(BaseModel):
    """A single message in the docs chat."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str


class DocsSession(BaseModel):
    """Docs chat session state."""
    session_id: str
    messages: list[DocsMessage]
    created_at: str
    last_activity: str


# In-memory sessions (can be moved to Redis later)
_sessions: dict[str, DocsSession] = {}

# Pending SSE streams - stores asyncio.Queue for each request_id
_pending_streams: dict[str, asyncio.Queue] = {}

# Pending requests metadata (message, session, etc.)
_pending_requests: dict[str, dict[str, Any]] = {}

# Events to signal when SSE client has connected
_sse_connected_events: dict[str, asyncio.Event] = {}


def load_documentation() -> dict[str, str]:
    """Load all documentation files from docs directory.

    Returns:
        Dict mapping filename to content
    """
    global _docs_cache

    if _docs_cache is not None:
        return _docs_cache

    docs = {}

    # Load priority docs first
    for filename in PRIORITY_DOCS:
        filepath = DOCS_DIR / filename
        if filepath.exists():
            try:
                content = filepath.read_text(encoding="utf-8")
                docs[filename] = content
                logger.debug(f"Loaded doc: {filename} ({len(content)} chars)")
            except Exception as e:
                logger.warning(f"Failed to load {filename}: {e}")

    # Load specs index
    specs_readme = DOCS_DIR / "specs" / "README.md"
    if specs_readme.exists():
        try:
            docs["specs/README.md"] = specs_readme.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to load specs/README.md: {e}")

    _docs_cache = docs
    logger.info(f"Loaded {len(docs)} documentation files")

    return docs


def build_docs_system_prompt() -> str:
    """Build system prompt with embedded documentation.

    Returns:
        System prompt string with docs content
    """
    docs = load_documentation()

    prompt_parts = [
        "Você é um assistente especializado na documentação do Forex Advisor.",
        "Seu objetivo é ajudar desenvolvedores a entenderem o projeto, sua arquitetura e como contribuir.",
        "",
        "DOCUMENTAÇÃO DISPONÍVEL:",
        "",
    ]

    # Add each document
    for filename, content in docs.items():
        prompt_parts.append(f"=== {filename} ===")
        prompt_parts.append(content)
        prompt_parts.append("")

    prompt_parts.extend([
        "INSTRUÇÕES CRÍTICAS:",
        "1. Responda sempre em português brasileiro",
        "2. Responda APENAS com informações que estão EXPLICITAMENTE na documentação acima",
        "3. Cite o documento fonte (ex: 'Conforme STATUS.md...')",
        "",
        "REGRAS ANTI-ALUCINAÇÃO (OBRIGATÓRIAS):",
        "- Se a informação NÃO está na documentação, responda APENAS: 'Essa informação não está documentada no projeto. Consulte a equipe para mais detalhes.'",
        "- NUNCA invente, sugira ou especule sobre informações não documentadas",
        "- NUNCA ofereça criar documentação, arquivos ou guias",
        "- NUNCA faça sugestões de tecnologias, arquiteturas ou soluções",
        "- NUNCA pergunte sobre preferências do usuário para criar algo",
        "- Seu papel é APENAS responder com base nos docs existentes, não criar novos",
    ])

    return "\n".join(prompt_parts)


async def get_docs_session(session_id: str) -> DocsSession | None:
    """Get docs session from cache.

    Args:
        session_id: Session UUID

    Returns:
        DocsSession if found, None otherwise
    """
    # Try memory first
    if session_id in _sessions:
        return _sessions[session_id]

    # Try Redis cache
    cache_key = f"docs_chat:session:{session_id}"
    cached = await get_cached(cache_key)

    if cached:
        session = DocsSession(**cached)
        _sessions[session_id] = session
        return session

    return None


async def save_docs_session(session: DocsSession) -> None:
    """Save docs session to cache.

    Args:
        session: Session to save
    """
    # Save to memory
    _sessions[session.session_id] = session

    # Save to Redis
    cache_key = f"docs_chat:session:{session.session_id}"
    await set_cached(
        cache_key,
        session.model_dump(),
        ttl=settings.docs_chat_session_ttl,
    )


async def generate_docs_response(
    message: str,
    session: DocsSession,
    websocket: WebSocket,
) -> str:
    """Generate response for docs chat with guardrails.

    Uses non-streaming to validate response before sending.
    This prevents hallucinated content from reaching the user.

    Args:
        message: User message
        session: Chat session with history
        websocket: WebSocket connection for streaming

    Returns:
        Full response text (sanitized)
    """
    llm_router = get_router()

    if llm_router is None:
        return "Erro: LLM não configurado."

    try:
        # Build messages with history
        messages = [
            {"role": "system", "content": build_docs_system_prompt()},
        ]

        # Add history (last N messages)
        max_history = getattr(settings, 'docs_chat_max_history', 20)
        for msg in session.messages[-max_history:]:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        # Add current message
        messages.append({"role": "user", "content": message})

        # Log context size for debugging
        total_chars = sum(len(m.get("content", "")) for m in messages)
        logger.info(f"Docs chat: {len(messages)} messages, {total_chars} total chars")

        # Generate response with timeout (non-streaming for guardrail validation)
        try:
            response = await asyncio.wait_for(
                llm_router.acompletion(
                    messages=messages,
                    max_tokens=settings.llm_max_tokens,
                    stream=False,  # Non-streaming to validate before sending
                ),
                timeout=60.0,  # 60 second timeout
            )
        except asyncio.TimeoutError:
            logger.error("Docs chat: LLM timeout after 60 seconds")
            return "Desculpe, a resposta demorou muito. Tente uma pergunta mais curta ou limpe o histórico."

        full_response = response.choices[0].message.content or ""
        logger.info(f"Docs chat: LLM response received, {len(full_response)} chars")

        # Apply guardrails - sanitize hallucinations
        sanitized_response = sanitize_response(full_response)

        # Log if response was modified
        if sanitized_response != full_response:
            logger.info(
                f"Guardrail activated: original={len(full_response)} chars, "
                f"sanitized={len(sanitized_response)} chars"
            )

        # Send response to client (simulated streaming for UX)
        # Split into chunks for better UX
        logger.info(f"Sending response to client: {len(sanitized_response)} chars")
        chunk_size = 50
        chunks_sent = 0
        for i in range(0, len(sanitized_response), chunk_size):
            chunk = sanitized_response[i:i + chunk_size]
            try:
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk,
                })
                chunks_sent += 1
            except Exception as e:
                logger.error(f"Failed to send chunk {chunks_sent}: {e}")
                break

        logger.info(f"Sent {chunks_sent} chunks to client")
        return sanitized_response

    except Exception as e:
        logger.error(f"Error generating docs response: {e}")
        return f"Erro ao gerar resposta: {str(e)}"


async def generate_docs_response_streaming(
    request_id: str,
    message: str,
    session: DocsSession,
) -> None:
    """Generate response for docs chat with real-time streaming via SSE.

    Streams chunks to the SSE queue in real-time.
    Applies guardrails at the end and sends sanitized flag.

    Args:
        request_id: Unique ID for this request
        message: User message
        session: Chat session with history
    """
    queue = _pending_streams.get(request_id)
    if not queue:
        logger.error(f"SSE queue not found for request_id: {request_id}")
        return

    # Wait for SSE client to connect (max 10 seconds)
    connected_event = _sse_connected_events.get(request_id)
    if connected_event:
        try:
            await asyncio.wait_for(connected_event.wait(), timeout=10.0)
            logger.info(f"SSE client ready, starting generation for request_id: {request_id}")
        except asyncio.TimeoutError:
            logger.warning(f"SSE client did not connect in time for request_id: {request_id}")
            await queue.put({"type": "error", "message": "Cliente SSE não conectou a tempo."})
            await queue.put({"type": "done"})
            return

    llm_router = get_router()

    if llm_router is None:
        await queue.put({"type": "error", "message": "LLM não configurado."})
        await queue.put({"type": "done"})
        return

    try:
        # Build messages with history
        messages = [
            {"role": "system", "content": build_docs_system_prompt()},
        ]

        # Add history (last N messages)
        max_history = getattr(settings, 'docs_chat_max_history', 20)
        for msg in session.messages[-max_history:]:
            messages.append({
                "role": msg.role,
                "content": msg.content,
            })

        # Add current message
        messages.append({"role": "user", "content": message})

        # Log context size for debugging
        total_chars = sum(len(m.get("content", "")) for m in messages)
        logger.info(f"Docs chat SSE: {len(messages)} messages, {total_chars} total chars")

        # Generate response with streaming
        full_response = ""
        try:
            response = await asyncio.wait_for(
                llm_router.acompletion(
                    messages=messages,
                    max_tokens=settings.llm_max_tokens,
                    stream=True,  # Real streaming!
                ),
                timeout=60.0,
            )

            # Stream chunks in real-time
            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    await queue.put({"type": "chunk", "content": content})

        except asyncio.TimeoutError:
            logger.error("Docs chat SSE: LLM timeout after 60 seconds")
            await queue.put({
                "type": "error",
                "message": "Resposta demorou muito. Tente novamente.",
            })
            await queue.put({"type": "done"})
            return

        logger.info(f"Docs chat SSE: LLM response complete, {len(full_response)} chars")

        # Apply guardrails at the end
        sanitized_response = sanitize_response(full_response)
        was_sanitized = sanitized_response != full_response

        if was_sanitized:
            logger.info(
                f"SSE Guardrail activated: original={len(full_response)} chars, "
                f"sanitized={len(sanitized_response)} chars"
            )

        # Store final response for session save
        _pending_requests[request_id]["response"] = sanitized_response
        _pending_requests[request_id]["was_sanitized"] = was_sanitized

        # Send done with sanitization info
        await queue.put({
            "type": "done",
            "sanitized": was_sanitized,
            "final_response": sanitized_response if was_sanitized else None,
        })

    except Exception as e:
        logger.error(f"Error in SSE streaming: {e}")
        await queue.put({"type": "error", "message": str(e)})
        await queue.put({"type": "done"})


@router.get("/sse/docs/{request_id}")
async def docs_sse_stream(request_id: str):
    """SSE endpoint for streaming docs chat responses.

    The client connects here after receiving stream_url from WebSocket.
    Streams LLM chunks in real-time.

    Args:
        request_id: Unique request ID from WebSocket

    Returns:
        StreamingResponse with SSE events
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        # Get or create queue for this request
        queue = _pending_streams.get(request_id)
        if not queue:
            yield f"event: error\ndata: {json.dumps({'message': 'Request not found'})}\n\n"
            return

        # Signal that SSE client has connected
        if request_id in _sse_connected_events:
            _sse_connected_events[request_id].set()
            logger.info(f"SSE client connected for request_id: {request_id}")

        try:
            while True:
                # Wait for next item from queue
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=65.0)
                except asyncio.TimeoutError:
                    yield f"event: error\ndata: {json.dumps({'message': 'Stream timeout'})}\n\n"
                    break

                if item["type"] == "chunk":
                    yield f"data: {json.dumps({'content': item['content']})}\n\n"
                elif item["type"] == "error":
                    yield f"event: error\ndata: {json.dumps({'message': item['message']})}\n\n"
                elif item["type"] == "done":
                    done_data = {"sanitized": item.get("sanitized", False)}
                    if item.get("final_response"):
                        done_data["final_response"] = item["final_response"]
                    yield f"event: done\ndata: {json.dumps(done_data)}\n\n"
                    break

        finally:
            # Cleanup
            if request_id in _pending_streams:
                del _pending_streams[request_id]

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


def _is_valid_uuid(value: str) -> bool:
    """Validate if string is a valid UUID."""
    if not value:
        return False
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


# Max message size (10KB)
MAX_MESSAGE_SIZE = 10 * 1024


@router.get("/api/docs/session/{session_id}")
async def get_docs_session_endpoint(session_id: str):
    """Get docs chat session history.

    Used by frontend to sync messages after reconnection.

    Args:
        session_id: Session UUID

    Returns:
        Session with messages or error
    """
    if not _is_valid_uuid(session_id):
        return {"error": "Invalid session_id format", "session_id": session_id}

    session = await get_docs_session(session_id)

    if not session:
        return {"error": "Session not found", "session_id": session_id}

    return {
        "session_id": session.session_id,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
            }
            for msg in session.messages
        ],
        "created_at": session.created_at,
        "last_activity": session.last_activity,
    }


@router.websocket("/ws/docs/{session_id}")
async def docs_chat_websocket(websocket: WebSocket, session_id: str | None = None):
    """WebSocket endpoint for documentation chat with streaming.

    Protocol:
    - Client sends: {"message": "user message"}
    - Server sends: {"type": "session", "session_id": "..."}
    - Server sends: {"type": "chunk", "content": "..."} (multiple)
    - Server sends: {"type": "done"}
    - Server sends: {"type": "error", "message": "..."} (on error)
    """
    # Check if docs chat is enabled
    if not getattr(settings, 'docs_chat_enabled', True):
        await websocket.close(code=1013)  # Try again later
        return

    await websocket.accept()
    logger.info(f"Docs WebSocket connected: {session_id}")

    # Validate session_id format
    if session_id and session_id != "new" and not _is_valid_uuid(session_id):
        logger.warning(f"Invalid docs session_id format: {session_id}")
        await websocket.send_json({
            "type": "error",
            "message": "Invalid session_id format. Must be a valid UUID.",
        })
        await websocket.close(code=1008)  # Policy Violation
        return

    # Create or get session
    if not session_id or session_id == "new":
        session_id = str(uuid.uuid4())
        session = DocsSession(
            session_id=session_id,
            messages=[],
            created_at=datetime.utcnow().isoformat(),
            last_activity=datetime.utcnow().isoformat(),
        )
    else:
        session = await get_docs_session(session_id)
        if not session:
            session = DocsSession(
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

            # Check message size
            if len(user_message) > MAX_MESSAGE_SIZE:
                logger.warning(f"Docs message too large: {len(user_message)} bytes")
                await websocket.send_json({
                    "type": "error",
                    "message": f"Mensagem muito grande. Máximo: {MAX_MESSAGE_SIZE} bytes.",
                })
                continue

            logger.debug(f"Docs chat message: {user_message[:100]}...")

            # Add user message to session
            session.messages.append(DocsMessage(
                role="user",
                content=user_message,
                timestamp=datetime.utcnow().isoformat(),
            ))

            # Create unique request ID for SSE streaming
            request_id = str(uuid.uuid4())

            # Create queue for this request
            _pending_streams[request_id] = asyncio.Queue()

            # Create event to signal when SSE client connects
            _sse_connected_events[request_id] = asyncio.Event()

            # Store request metadata
            _pending_requests[request_id] = {
                "session": session,
                "message": user_message,
                "response": None,
                "was_sanitized": False,
            }

            # Send stream_url to client
            stream_url = f"/sse/docs/{request_id}"
            await websocket.send_json({
                "type": "stream_url",
                "url": stream_url,
                "request_id": request_id,
            })

            # Start streaming generation in background
            asyncio.create_task(
                generate_docs_response_streaming(request_id, user_message, session)
            )

            # Wait for streaming to complete (poll the request)
            while request_id in _pending_requests:
                await asyncio.sleep(0.1)
                # Check if response is ready
                if _pending_requests[request_id].get("response") is not None:
                    break

            # Get final response
            response_text = _pending_requests.get(request_id, {}).get("response", "")

            # Cleanup request metadata and events
            if request_id in _pending_requests:
                del _pending_requests[request_id]
            if request_id in _sse_connected_events:
                del _sse_connected_events[request_id]

            # Add assistant message to session
            if response_text:
                session.messages.append(DocsMessage(
                    role="assistant",
                    content=response_text,
                    timestamp=datetime.utcnow().isoformat(),
                ))

            # Update session activity
            session.last_activity = datetime.utcnow().isoformat()

            # Save session
            await save_docs_session(session)

    except WebSocketDisconnect:
        logger.info(f"Docs WebSocket disconnected: {session_id}")
    except Exception as e:
        logger.error(f"Docs WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": "Erro interno do servidor.",
            })
        except Exception:
            pass


# Preload documentation on module import
def _preload_docs():
    """Preload documentation into cache."""
    try:
        docs = load_documentation()
        logger.info(f"Preloaded {len(docs)} documentation files")
    except Exception as e:
        logger.warning(f"Failed to preload docs: {e}")


# Uncomment to preload on startup
# _preload_docs()
