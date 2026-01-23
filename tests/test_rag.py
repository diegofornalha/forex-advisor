"""Tests for RAG SDK."""

import os
import tempfile

import pytest

from app.rag_sdk import SimpleRAG


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)


@pytest.fixture
def rag(temp_db):
    """Create RAG instance with temp database."""
    return SimpleRAG(temp_db)


class TestSimpleRAG:
    """Tests for SimpleRAG class."""

    @pytest.mark.asyncio
    async def test_add_text(self, rag):
        """Should add text and return document ID."""
        doc_id = await rag.add_text(
            "O dolar subiu 5% hoje devido a instabilidade",
            source="Test Source"
        )
        assert doc_id is not None
        assert isinstance(doc_id, (int, str))  # doc_id can be int or str

    @pytest.mark.asyncio
    async def test_add_duplicate_text(self, rag):
        """Should return None for duplicate text."""
        text = "Texto duplicado para teste"

        # First add should succeed
        doc_id1 = await rag.add_text(text, source="Test")
        assert doc_id1 is not None

        # Second add should return None (duplicate)
        doc_id2 = await rag.add_text(text, source="Test")
        assert doc_id2 is None

    @pytest.mark.asyncio
    async def test_search_returns_results(self, rag):
        """Should return search results."""
        # Add some documents
        await rag.add_text(
            "O dolar fechou em alta de 2% contra o real brasileiro",
            source="CNN Brasil"
        )
        await rag.add_text(
            "Mercado de cambio apresenta volatilidade no inicio do ano",
            source="G1"
        )
        await rag.add_text(
            "Previsao do tempo indica chuvas fortes no sul do pais",
            source="Clima"
        )

        # Search for dollar-related content
        results = await rag.search("dolar cambio", top_k=2)

        assert len(results) > 0
        assert results[0].content is not None
        assert results[0].source is not None
        assert 0 <= results[0].similarity <= 1

    @pytest.mark.asyncio
    async def test_search_empty_database(self, rag):
        """Should return empty list for empty database."""
        results = await rag.search("qualquer coisa")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_top_k(self, rag):
        """Should respect top_k parameter."""
        # Add multiple documents
        for i in range(10):
            await rag.add_text(
                f"Documento numero {i} sobre o mercado de cambio",
                source=f"Source {i}"
            )

        results = await rag.search("mercado cambio", top_k=3)
        assert len(results) <= 3

    def test_stats_empty_db(self, rag):
        """Should return stats for empty database."""
        stats = rag.stats()

        assert "total_docs" in stats
        assert "total_embeddings" in stats
        assert "status" in stats
        assert stats["total_docs"] == 0

    @pytest.mark.asyncio
    async def test_stats_with_docs(self, rag):
        """Should return correct stats after adding docs."""
        await rag.add_text("Documento 1", source="S1")
        await rag.add_text("Documento 2", source="S2")

        stats = rag.stats()
        assert stats["total_docs"] == 2
        assert stats["total_embeddings"] == 2

    @pytest.mark.asyncio
    async def test_clear(self, rag):
        """Should clear all documents."""
        # Add documents
        await rag.add_text("Documento 1", source="S1")
        await rag.add_text("Documento 2", source="S2")

        # Verify docs exist
        assert rag.stats()["total_docs"] == 2

        # Clear
        count = await rag.clear()
        assert count == 2

        # Verify empty
        assert rag.stats()["total_docs"] == 0


class TestSearchResult:
    """Tests for search result structure."""

    @pytest.mark.asyncio
    async def test_result_has_all_fields(self, rag):
        """Search result should have all required fields."""
        await rag.add_text(
            "Dolar em alta no mercado brasileiro",
            source="Economia"
        )

        results = await rag.search("dolar")

        if results:  # Only test if results exist
            result = results[0]
            assert hasattr(result, "content")
            assert hasattr(result, "source")
            assert hasattr(result, "similarity")
            assert hasattr(result, "doc_id")

    @pytest.mark.asyncio
    async def test_results_ordered_by_similarity(self, rag):
        """Results should be ordered by descending similarity."""
        await rag.add_text("Dolar sobe forte", source="S1")
        await rag.add_text("Cambio estavel", source="S2")
        await rag.add_text("Dolar em queda", source="S3")

        results = await rag.search("dolar", top_k=3)

        if len(results) > 1:
            for i in range(len(results) - 1):
                assert results[i].similarity >= results[i + 1].similarity
