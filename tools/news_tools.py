import logging
import feedparser
import asyncio
from livekit.agents import function_tool, RunContext
from ddgs import DDGS
from typing import List, Dict
import os

# RSS Feed Configuration
RSS_FEEDS = {
    "World": [
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://feeds.reuters.com/reuters/worldNews",
        "https://www.aljazeera.com/xml/rss/all.xml"
    ],
    "Tech": [
        "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY",
        "https://www.theverge.com/rss/index.xml"
    ],
    "India": [
        "https://news.google.com/rss/headlines/section/topic/INDIA"
    ]
}

async def _fetch_rss_feed(url: str) -> List[Dict]:
    """Fetch and parse an RSS feed."""
    try:
        # feedparser is synchronous, run in thread to avoid blocking
        loop = asyncio.get_event_loop()
        feed = await loop.run_in_executor(None, feedparser.parse, url)

        results = []
        for entry in feed.entries[:5]:
            results.append({
                "title": entry.get("title", "No Title"),
                "link": entry.get("link", ""),
                "summary": entry.get("summary", "No summary available")
            })
        return results
    except Exception as e:
        logging.error(f"Error fetching feed {url}: {e}")
        return []

async def _ddg_fallback(query: str, max_results: int = 5) -> List[Dict]:
    """Fallback search using DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
            return [{"title": r.get("title"), "link": r.get("href"), "summary": r.get("body")} for r in results]
    except Exception as e:
        logging.error(f"DDG fallback failed for {query}: {e}")
        return []

@function_tool()
async def fetch_news(
    context: RunContext, # type: ignore
    category: str = "World"
) -> str:
    """
    Fetch the latest news headlines.
    Categories: World, Tech, India.
    """
    logging.info(f"Fetching news for category: {category}")

    feeds = RSS_FEEDS.get(category, RSS_FEEDS["World"])
    all_articles = []

    for url in feeds:
        articles = await _fetch_rss_feed(url)
        all_articles.extend(articles)

    # Fallback to DDG if no RSS results
    if not all_articles:
        logging.info(f"RSS failed for {category}, trying DDG fallback")
        all_articles = await _ddg_fallback(f"latest {category} news")

    if not all_articles:
        return "Sir, I couldn't retrieve any news headlines at the moment. All systems are silent."

    # Deduplicate and limit
    seen_titles = set()
    unique_articles = []
    for art in all_articles:
        if art["title"] not in seen_titles:
            unique_articles.append(art)
            seen_titles.add(art["title"])

    top_articles = unique_articles[:5]

    briefing = f"Here are the top {category} headlines, Sir:\n\n"
    for i, art in enumerate(top_articles, 1):
        briefing += f"{i}. {art['title']}\n"

    briefing += "\nShall I dive deeper into any of these, Sir?"
    return briefing
