"""News ingestion pipeline for RAG.

Simple and scalable approach:
- Fetch news from Google News RSS
- Ingest into RAG (SQLite-vec + embeddings)
- Can be run manually or scheduled

Usage:
    python -m app.news_ingestion          # Ingest news
    python -m app.news_ingestion --stats  # Show stats
    python -m app.news_ingestion --clear  # Clear all data
"""

import asyncio
import logging
import sys
from datetime import datetime

from .config import settings
from .insights import fetch_news
from .rag_sdk import SimpleRAG

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def ingest_news_to_rag(limit: int = 10) -> dict:
    """Fetch news and ingest into RAG.

    Args:
        limit: Max news items to fetch

    Returns:
        Stats dict with ingested/duplicates/errors counts
    """
    rag = SimpleRAG(settings.rag_db_path)
    stats = {"fetched": 0, "ingested": 0, "duplicates": 0, "errors": 0}

    try:
        # Fetch news from RSS
        logger.info(f"Fetching news for query: '{settings.news_query}'")
        news_items = await fetch_news(query=settings.news_query, limit=limit)
        stats["fetched"] = len(news_items)

        # Ingest each news item
        for item in news_items:
            try:
                # Combine title + description for better context
                content = f"{item.title}. {item.description}"
                source = item.source

                doc_id = await rag.add_text(content, source=source)

                if doc_id:
                    stats["ingested"] += 1
                    logger.debug(f"Ingested: {item.title[:50]}...")
                else:
                    stats["duplicates"] += 1

            except Exception as e:
                stats["errors"] += 1
                logger.warning(f"Error ingesting news: {e}")

        logger.info(
            f"Ingestion complete: {stats['ingested']} new, "
            f"{stats['duplicates']} duplicates, {stats['errors']} errors"
        )

    except Exception as e:
        logger.error(f"News fetch failed: {e}")
        stats["errors"] += 1

    return stats


async def get_rag_stats() -> dict:
    """Get RAG database statistics.

    Returns:
        Stats dict from RAG
    """
    rag = SimpleRAG(settings.rag_db_path)
    return rag.stats()


async def clear_rag() -> int:
    """Clear all data from RAG.

    Returns:
        Number of documents removed
    """
    rag = SimpleRAG(settings.rag_db_path)
    count = await rag.clear()
    logger.info(f"Cleared {count} documents from RAG")
    return count


async def search_rag(query: str, top_k: int = 5) -> list:
    """Search RAG for testing.

    Args:
        query: Search query
        top_k: Number of results

    Returns:
        List of search results
    """
    rag = SimpleRAG(settings.rag_db_path)
    results = await rag.search(query, top_k=top_k)
    return results


def main():
    """CLI entry point."""
    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "--stats":
            stats = asyncio.run(get_rag_stats())
            print(f"\n📊 RAG Statistics:")
            print(f"   Documents: {stats['total_docs']}")
            print(f"   Embeddings: {stats['total_embeddings']}")
            print(f"   Status: {stats['status']}")

        elif cmd == "--clear":
            confirm = input("⚠️  Clear all RAG data? (yes/no): ")
            if confirm.lower() == "yes":
                count = asyncio.run(clear_rag())
                print(f"✅ Cleared {count} documents")
            else:
                print("Cancelled")

        elif cmd == "--search":
            if len(sys.argv) > 2:
                query = " ".join(sys.argv[2:])
                results = asyncio.run(search_rag(query))
                print(f"\n🔍 Search results for '{query}':")
                for i, r in enumerate(results, 1):
                    print(f"\n{i}. [{r.source}] (sim: {r.similarity:.2f})")
                    print(f"   {r.content[:100]}...")
            else:
                print("Usage: python -m app.news_ingestion --search <query>")

        else:
            print(f"Unknown command: {cmd}")
            print("Usage:")
            print("  python -m app.news_ingestion          # Ingest news")
            print("  python -m app.news_ingestion --stats  # Show stats")
            print("  python -m app.news_ingestion --search <query>  # Test search")
            print("  python -m app.news_ingestion --clear  # Clear all data")

    else:
        # Default: ingest news
        print(f"\n🚀 Starting news ingestion at {datetime.now()}")
        stats = asyncio.run(ingest_news_to_rag(limit=settings.news_limit))
        print(f"\n✅ Done!")
        print(f"   Fetched: {stats['fetched']}")
        print(f"   Ingested: {stats['ingested']}")
        print(f"   Duplicates: {stats['duplicates']}")
        print(f"   Errors: {stats['errors']}")


if __name__ == "__main__":
    main()
