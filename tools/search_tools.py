"""
search_tools.py — DuckDuckGo Web Search
=========================================
Replaces the broken langchain-community DuckDuckGoSearchRun with a direct
call to the `ddgs` library (package: ddgs, formerly duckduckgo-search).

Features:
  - Async-safe (runs blocking I/O in thread executor)
  - Configurable result count and search type
  - Graceful error handling with informative fallback messages
  - Structured result formatting for voice readback
"""

import asyncio
import logging
import time
from typing import Optional

from livekit.agents import function_tool, RunContext
from ddgs import DDGS

logger = logging.getLogger("SearchTools")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_text_search(query: str, max_results: int) -> list[dict]:
    """Blocking DuckDuckGo text search — run in thread executor."""
    with DDGS() as ddgs:
        return list(ddgs.text(query, max_results=max_results))


def _run_news_search(query: str, max_results: int) -> list[dict]:
    """Blocking DuckDuckGo news search — run in thread executor."""
    with DDGS() as ddgs:
        return list(ddgs.news(query, max_results=max_results))


def _format_results(results: list[dict], search_type: str) -> str:
    """Convert raw DDG results into a clean voice-friendly string."""
    if not results:
        return "No results found for that query, Sir."

    lines = []
    for i, r in enumerate(results, 1):
        title   = r.get("title", "Untitled")
        body    = r.get("body") or r.get("excerpt") or r.get("snippet", "No snippet available.")
        source  = r.get("source") or r.get("url") or r.get("href", "")

        # Trim body for voice readback
        body = body[:200].strip()
        if len(body) == 200:
            body += "…"

        lines.append(f"{i}. {title}\n   {body}")
        if source:
            lines.append(f"   Source: {source}\n")

    header = f"Search results ({search_type}) for your query, Sir:\n\n"
    return header + "\n".join(lines)


# ── Tool ──────────────────────────────────────────────────────────────────────

@function_tool()
async def search_web(
    context: RunContext,  # type: ignore
    query: str,
    max_results: int = 5,
    search_type: str = "text",  # "text" | "news"
) -> str:
    """
    Search the web using DuckDuckGo.

    Args:
        query:       The search query.
        max_results: Number of results to return (1–10).
        search_type: 'text' for general web search, 'news' for recent news articles.

    Returns:
        Formatted search results as a readable string.
    """
    if not query or not query.strip():
        return "I need a search query to proceed, Sir."

    max_results = max(1, min(max_results, 10))
    query       = query.strip()

    logger.info(f"search_web: type={search_type}, max={max_results}, query='{query}'")

    loop = asyncio.get_event_loop()
    t0   = time.monotonic()

    try:
        if search_type == "news":
            results = await loop.run_in_executor(
                None, _run_news_search, query, max_results
            )
        else:
            results = await loop.run_in_executor(
                None, _run_text_search, query, max_results
            )

        elapsed = time.monotonic() - t0
        logger.info(f"search_web: returned {len(results)} results in {elapsed:.2f}s")
        return _format_results(results, search_type)

    except Exception as e:
        elapsed = time.monotonic() - t0
        logger.error(f"search_web: failed after {elapsed:.2f}s — {e}")
        return (
            f"The web search encountered an issue, Sir: {str(e)}. "
            "You might try rephrasing the query or checking the network connection."
        )