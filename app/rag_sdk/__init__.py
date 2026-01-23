"""Simple RAG SDK - Versao simplificada para escalar.

Exemplo:
    >>> from app.rag_sdk import SimpleRAG
    >>>
    >>> async def main():
    ...     rag = SimpleRAG("rag.db")
    ...     await rag.add_text("Dolar sobe 2%", source="news")
    ...     results = await rag.search("cambio")
    ...     answer = await rag.query("Como esta o dolar?")
"""

from .rag import SearchResult, SimpleRAG

__version__ = "0.2.0"

__all__ = [
    "SimpleRAG",
    "SearchResult",
]
