"""Simple RAG SDK - Ingest and Search."""

import hashlib
import logging
import threading
from dataclasses import dataclass
from pathlib import Path

import apsw
import sqlite_vec
from fastembed import TextEmbedding

logger = logging.getLogger(__name__)


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
        self._conn: apsw.Connection | None = None
        self._lock = threading.Lock()
        self._ensure_database()

    @property
    def model(self) -> TextEmbedding:
        """Lazy load do modelo de embedding."""
        if self._model is None:
            self._model = TextEmbedding(self.EMBEDDING_MODEL)
        return self._model

    def preload_model(self) -> None:
        """Pre-carrega o modelo de embedding (para uso no startup)."""
        logger.info(f"Pre-carregando modelo de embedding: {self.EMBEDDING_MODEL}")
        _ = self.model  # Força o carregamento
        logger.info("Modelo de embedding carregado com sucesso")

    def _get_connection(self) -> apsw.Connection:
        """Retorna conexão persistente (singleton com thread safety)."""
        if self._conn is None:
            with self._lock:
                if self._conn is None:
                    self._conn = apsw.Connection(str(self.db_path))
                    self._conn.enableloadextension(True)
                    self._conn.loadextension(sqlite_vec.loadable_path())
                    self._conn.enableloadextension(False)
                    # Enable WAL mode for better concurrency
                    self._conn.cursor().execute("PRAGMA journal_mode=WAL")
                    self._conn.cursor().execute("PRAGMA synchronous=NORMAL")
                    logger.debug(f"Conexão SQLite criada: {self.db_path}")
        return self._conn

    def close(self) -> None:
        """Fecha a conexão persistente."""
        if self._conn is not None:
            with self._lock:
                if self._conn is not None:
                    self._conn.close()
                    self._conn = None
                    logger.debug("Conexão SQLite fechada")

    def _ensure_database(self):
        """Cria schema do banco."""
        conn = self._get_connection()
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

    async def clear(self) -> int:
        """Remove todos os documentos.

        Returns:
            Numero de documentos removidos
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM documentos")
        count = cursor.fetchone()[0]

        cursor.execute("DELETE FROM vec_docs")
        cursor.execute("DELETE FROM documentos")

        return count

    def stats(self) -> dict:
        """Estatisticas do indice."""
        conn = self._get_connection()
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

    def get_detailed_stats(self) -> dict:
        """Estatísticas detalhadas para admin panel."""
        import os

        conn = self._get_connection()
        cursor = conn.cursor()

        # Contagens básicas
        cursor.execute("SELECT COUNT(*) FROM documentos")
        total_docs = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM vec_docs")
        total_vecs = cursor.fetchone()[0]

        # Contagem por fonte
        sources = {}
        for row in cursor.execute(
            "SELECT source, COUNT(*) FROM documentos GROUP BY source ORDER BY COUNT(*) DESC"
        ):
            sources[row[0]] = row[1]

        # Tamanho do banco
        db_size = 0
        if self.db_path.exists():
            db_size = os.path.getsize(self.db_path)

        # Últimos documentos
        recent_docs = []
        for row in cursor.execute(
            "SELECT id, source, substr(content, 1, 100), created_at FROM documentos ORDER BY created_at DESC LIMIT 5"
        ):
            recent_docs.append({
                "id": row[0],
                "source": row[1],
                "preview": row[2] + ("..." if len(row[2]) >= 100 else ""),
                "created_at": row[3],
            })

        return {
            "total_docs": total_docs,
            "total_embeddings": total_vecs,
            "status": "ok" if total_docs == total_vecs else "inconsistent",
            "db_path": str(self.db_path),
            "db_size_bytes": db_size,
            "db_size_mb": round(db_size / (1024 * 1024), 2) if db_size > 0 else 0,
            "sources": sources,
            "recent_docs": recent_docs,
            "embedding_model": self.EMBEDDING_MODEL,
        }
