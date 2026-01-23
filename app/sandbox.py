"""E2B Sandbox Manager for secure code execution.

Executa código de análise em ambiente isolado para proteção contra:
- Prompt injection que tente executar código malicioso
- Vazamento de dados do servidor principal
- Manipulação de recomendações via código injetado
"""

import logging
import os
from typing import Any

from .config import settings

logger = logging.getLogger(__name__)

# Singleton sandbox instance
_sandbox = None


def _get_sandbox():
    """Get or create E2B Sandbox singleton.

    Returns:
        Sandbox instance, or None if E2B not configured
    """
    global _sandbox

    if not settings.e2b_api_key:
        logger.debug("E2B não configurado (E2B_API_KEY ausente)")
        return None

    if _sandbox is not None:
        return _sandbox

    try:
        # Import apenas quando necessário (E2B pode não estar instalado)
        from e2b_code_interpreter import Sandbox

        os.environ.setdefault("E2B_API_KEY", settings.e2b_api_key)

        _sandbox = Sandbox.create(timeout=settings.e2b_timeout)
        logger.info(f"E2B Sandbox criado (timeout={settings.e2b_timeout}s)")
        return _sandbox

    except ImportError:
        logger.warning("e2b-code-interpreter não instalado")
        return None
    except Exception as e:
        logger.error(f"Erro ao criar E2B Sandbox: {e}")
        return None


def execute_analysis_code(code: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute analysis code in isolated E2B sandbox.

    Args:
        code: Python code to execute (analysis/calculations only)
        data: Optional data dict to inject into sandbox namespace

    Returns:
        Dict with 'result', 'output', 'error' keys

    Raises:
        ValueError: If E2B not configured
    """
    global _sandbox
    sandbox = _get_sandbox()

    if sandbox is None:
        raise ValueError(
            "E2B Sandbox não disponível. "
            "Configure E2B_API_KEY no .env ou instale e2b-code-interpreter"
        )

    try:
        # Preparar código com dados injetados (se houver)
        full_code = _prepare_code(code, data)

        logger.debug(f"Executando código no sandbox ({len(code)} chars)")

        # Executar no sandbox isolado
        try:
            result = sandbox.run_code(full_code)
        except Exception as e:
            # Se sandbox expirou, recriar e tentar novamente
            if "not found" in str(e).lower() or "502" in str(e):
                logger.warning("Sandbox expirado, recriando...")
                _sandbox = None
                sandbox = _get_sandbox()
                if sandbox is None:
                    raise ValueError("Não foi possível recriar o sandbox")
                result = sandbox.run_code(full_code)
            else:
                raise

        # Extrair output dos logs (nova API E2B 2.x)
        stdout = ""
        if result.logs and result.logs.stdout:
            stdout = "".join(result.logs.stdout)

        # Extrair resultado (pode estar em Results ou text)
        result_text = result.text
        if not result_text and result.results:
            result_text = str(result.results[0]) if result.results else None

        response = {
            "result": result_text,
            "output": stdout,
            "error": str(result.error) if result.error else None,
            "sandbox_id": sandbox.sandbox_id,
        }

        if result.error:
            logger.warning(f"Sandbox retornou erro: {result.error}")
        else:
            logger.debug("Sandbox executou com sucesso")

        return response

    except Exception as e:
        logger.error(f"Erro na execução do sandbox: {e}")
        return {
            "result": None,
            "output": "",
            "error": str(e),
            "sandbox_id": None,
        }


def _prepare_code(code: str, data: dict[str, Any] | None) -> str:
    """Prepare code with injected data.

    Args:
        code: Original code
        data: Data to inject

    Returns:
        Code with data setup prepended
    """
    if not data:
        return code

    # Serializar dados de forma segura e criar DataFrame df
    data_setup = """import json
import pandas as pd

_injected_data = json.loads('''{json_data}''')

# Create DataFrame from OHLC data
if 'ohlc_data' in _injected_data:
    df = pd.DataFrame(_injected_data['ohlc_data'])
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date').reset_index(drop=True)

""".format(json_data=_safe_json_dumps(data))

    return data_setup + code


def _safe_json_dumps(data: Any) -> str:
    """Safely serialize data to JSON string.

    Args:
        data: Data to serialize

    Returns:
        JSON string with escaped quotes
    """
    import json

    return json.dumps(data, default=str).replace("'", "\\'")


def close_sandbox() -> None:
    """Close and cleanup sandbox instance."""
    global _sandbox

    if _sandbox is not None:
        try:
            _sandbox.close()
            logger.info("E2B Sandbox fechado")
        except Exception as e:
            logger.warning(f"Erro ao fechar sandbox: {e}")
        finally:
            _sandbox = None


def get_sandbox_status() -> dict[str, Any]:
    """Get sandbox status for health checks.

    Returns:
        Dict with status information
    """
    if not settings.e2b_api_key:
        return {"status": "disabled", "reason": "no_api_key"}

    sandbox = _get_sandbox()

    if sandbox is None:
        return {"status": "error", "reason": "failed_to_create"}

    return {
        "status": "active",
        "sandbox_id": sandbox.sandbox_id,
        "timeout": settings.e2b_timeout,
    }
