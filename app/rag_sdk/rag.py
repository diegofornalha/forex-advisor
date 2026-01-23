"""Simple RAG SDK - Ingest and Search."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

import apsw
import sqlite_vec
from fastembed import TextEmbedding


@dataclass
class SearchResult:
    """Resultado de busca."""
    doc_id: int
    source: str
    content: str
    similarity: float


class SimpleRAG:
    """RAG simplificado: ingest + search.

    Exemplo:
        >>> rag = SimpleRAG("rag.db")
        >>> await rag.add_text("Dolar sobe com tensoes", source="news")
        >>> results = await rag.search("cambio dolar")
    """

    EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

    def __init__(self, db_path: str = "rag.db"):
        self.db_path = Path(db_path)
        self._model: TextEmbedding | None = None
        self._ensure_database()

    @property
    def model(self) -> TextEmbedding:
        """Lazy load do modelo de embedding."""
        if self._model is None:
            self._model = TextEmbedding(self.EMBEDDING_MODEL)
        return self._model

    def _get_connection(self) -> apsw.Connection:
        """Cria conexao com sqlite-vec."""
        conn = apsw.Connection(str(self.db_path))
        conn.enableloadextension(True)
        conn.loadextension(sqlite_vec.loadable_path())
        conn.enableloadextension(False)
        return conn

    def _ensure_database(self):
        """Cria schema do banco."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Tabela de documentos
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documentos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    content TEXT NOT NULL,
                    hash TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Tabela de vetores (384 dims para bge-small)
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS vec_docs USING vec0(
                    doc_id INTEGER PRIMARY KEY,
                    embedding FLOAT[384]
                )
            """)
        finally:
            conn.close()

    def _compute_hash(self, content: str) -> str:
        """Hash para deduplicacao."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    async def add_text(self, content: str, source: str = "unknown") -> int | None:
        """Adiciona texto ao indice.

        Args:
            content: Texto para indexar
            source: Identificador da fonte

        Returns:
            doc_id se sucesso, None se duplicado
        """
        if not content.strip():
            return None

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Verifica duplicado
            content_hash = self._compute_hash(content)
            for row in cursor.execute("SELECT id FROM documentos WHERE hash = ?", (content_hash,)):
                return None  # Ja existe

            # Insere documento
            cursor.execute(
                "INSERT INTO documentos (source, content, hash) VALUES (?, ?, ?)",
                (source, content, content_hash)
            )
            doc_id = conn.last_insert_rowid()

            # Gera e insere embedding
            embeddings = list(self.model.embed([content]))
            embedding_bytes = sqlite_vec.serialize_float32(embeddings[0].tolist())
            cursor.execute(
                "INSERT INTO vec_docs (doc_id, embedding) VALUES (?, ?)",
                (doc_id, embedding_bytes)
            )

            return doc_id
        finally:
            conn.close()

    async def search(self, query: str, top_k: int = 5) -> list[SearchResult]:
        """Busca semantica.

        Args:
            query: Texto de busca
            top_k: Numero de resultados

        Returns:
            Lista de SearchResult
        """
        # Gera embedding da query
        embeddings = list(self.model.embed([query]))
        query_vec = sqlite_vec.serialize_float32(embeddings[0].tolist())

        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            results = []
            for row in cursor.execute("""
                SELECT v.doc_id, v.distance, d.source, d.content
                FROM vec_docs v
                JOIN documentos d ON d.id = v.doc_id
                WHERE v.embedding MATCH ? AND k = ?
            """, (query_vec, top_k)):
                doc_id, distance, source, content = row
                similarity = max(0, 1 - distance)

                results.append(SearchResult(
                    doc_id=doc_id,
                    source=source,
                    content=content,
                    similarity=round(similarity, 4)
                ))

            return results
        finally:
            conn.close()

    async def clear(self) -> int:
        """Remove todos os documentos.

        Returns:
            Numero de documentos removidos
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM documentos")
            count = cursor.fetchone()[0]

            cursor.execute("DELETE FROM vec_docs")
            cursor.execute("DELETE FROM documentos")

            return count
        finally:
            conn.close()

    def stats(self) -> dict:
        """Estatisticas do indice."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM documentos")
            total_docs = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM vec_docs")
            total_vecs = cursor.fetchone()[0]

            return {
                "total_docs": total_docs,
                "total_embeddings": total_vecs,
                "status": "ok" if total_docs == total_vecs else "inconsistent"
            }
        finally:
            conn.close()
