import logging
import requests
from livekit.agents import function_tool, RunContext
from typing import Optional

# Import all modular tools
from tools.news_tools import fetch_news
from tools.search_tools import search_web
from tools.system_tools import (
    open_application,
    open_url,
    open_multiple_urls,
    take_screenshot,
    get_system_info,
    set_volume,
    get_clipboard,
    set_clipboard,
)
from tools.communication_tools import (
    send_whatsapp_message,
    send_sms,
    send_email,
)
from tools.productivity_tools import (
    create_file,
    read_file,
    list_directory,
    search_files,
    open_file,
    add_reminder,
    get_reminders,
    delete_reminder,
)
from tools.memory_tools import (
    remember_fact,
    recall_fact,
    list_memories,
)


@function_tool()
async def get_weather(
    context: RunContext,  # type: ignore
    city: str,
) -> str:
    """Get the current weather for a given city."""
    try:
        response = requests.get(f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            logging.info(f"Weather for {city}: {response.text.strip()}")
            return response.text.strip()
        logging.error(f"Weather fetch failed for {city}: {response.status_code}")
        return f"Could not retrieve weather for {city}."
    except Exception as e:
        logging.error(f"Weather error for {city}: {e}")
        return f"An error occurred while retrieving weather for {city}."


# ── Aggregate all tools ────────────────────────────────────────────────────────
ALL_TOOLS = [
    get_weather,
    fetch_news,
    search_web,          # ← web search (DuckDuckGo)
    open_application,
    open_url,
    open_multiple_urls,
    take_screenshot,
    get_system_info,
    set_volume,
    get_clipboard,
    set_clipboard,
    send_whatsapp_message,
    send_sms,
    send_email,
    create_file,
    read_file,
    list_directory,
    search_files,
    open_file,
    add_reminder,
    get_reminders,
    delete_reminder,
    remember_fact,
    recall_fact,
    list_memories,
]