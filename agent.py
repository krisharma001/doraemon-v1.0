"""
Doraemon Agent — Main Entrypoint
=================================
Activation flow:
  1. Script starts → ClapDetector begins listening silently.
  2. User claps ONCE  → wake sound plays, agent greets, news + URL load.
  3. User claps TWICE → same + priority briefing mode.
  4. User claps THREE → standby / mute toggle.
"""

import json
import logging
import os
import asyncio
import webbrowser
import subprocess
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation
from livekit.plugins import google

from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION, get_dynamic_instruction
from tools import ALL_TOOLS
from engine.clap_detector import start_clap_detection
from engine.wake import play_wake_sound

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("Doraemon")

# ── Constants ─────────────────────────────────────────────────────────────────

BRIEFING_URL = "https://www.worldmonitor.app/"
CHROME_PATHS = {
    "darwin": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "linux":  "google-chrome",
    "win32":  r"C:\Program Files\Google\Chrome\Application\chrome.exe",
}

# ── Local JSON memory ─────────────────────────────────────────────────────────

MEMORY_FILE = "db/memory.json"
os.makedirs("db", exist_ok=True)


def _load_mem() -> dict:
    if os.path.exists(MEMORY_FILE):
        try:
            return json.load(open(MEMORY_FILE))
        except Exception:
            return {}
    return {}


def _load_memories_for_context() -> str:
    data = _load_mem()
    if not data:
        return ""
    block = "\n=== Long-Term Memory (Recalled at Session Start) ===\n"
    block += "The following facts are known about Krish from previous sessions:\n"
    for i, (k, v) in enumerate(list(data.items())[:20], 1):
        block += f"  {i}. {k}: {v}\n"
    block += "=== End of Memory ===\n"
    logger.info(f"Loaded {len(data)} memories into session context.")
    return block


def _save_conversation_to_memory(user_text: str, agent_text: str):
    if len(user_text.strip()) < 20:
        return
    import time
    data = _load_mem()
    key = f"conversation_{int(time.time())}"
    data[key] = f"User: {user_text.strip()} | Doraemon: {agent_text.strip()}"
    conv_keys = sorted([k for k in data if k.startswith("conversation_")])
    if len(conv_keys) > 50:
        for old_key in conv_keys[: len(conv_keys) - 50]:
            del data[old_key]
    json.dump(data, open(MEMORY_FILE, "w"), indent=2)


# ── Chrome launcher ───────────────────────────────────────────────────────────

def _open_in_chrome(url: str):
    """Open URL in Chrome, fall back to default browser."""
    import sys
    chrome = CHROME_PATHS.get(sys.platform)
    if chrome:
        try:
            subprocess.Popen([chrome, "--new-tab", url])
            logger.info(f"Opened {url} in Chrome.")
            return
        except FileNotFoundError:
            pass
    logger.warning("Chrome not found; using default browser.")
    webbrowser.open(url)


# ── Agent class ───────────────────────────────────────────────────────────────

class Assistant(Agent):
    def __init__(self, injected_instructions: str) -> None:
        super().__init__(
            instructions=injected_instructions,
            llm=google.beta.realtime.RealtimeModel(
                voice="Aoede",
                temperature=0.8,
            ),
            tools=ALL_TOOLS,
        )
        self._last_user_speech: str = ""

    async def on_user_speech_committed(self, message):
        try:
            self._last_user_speech = str(message)
        except Exception as e:
            logger.error(f"on_user_speech_committed error: {e}")

    async def on_agent_speech_committed(self, message):
        try:
            agent_text = str(message)
            if self._last_user_speech:
                _save_conversation_to_memory(self._last_user_speech, agent_text)
                self._last_user_speech = ""
        except Exception as e:
            logger.error(f"on_agent_speech_committed error: {e}")


# ── Opening sequence ──────────────────────────────────────────────────────────

async def _run_opening_sequence(session: AgentSession, priority: bool = False):
    """
    Full boot sequence fired after clap activation:
      1. Tony Stark wake sound
      2. Time-aware greeting
      3. World news briefing
      4. Open worldmonitor.app in Chrome
      5. System health check
    """
    logger.info(f"Running opening sequence (priority={priority}).")

    # 1 — Play wake sound immediately
    play_wake_sound()

    # Small pause so sound starts before agent speaks
    await asyncio.sleep(1.8)

    # 2 — Time-aware greeting
    await session.generate_reply(instructions=SESSION_INSTRUCTION)
    await asyncio.sleep(1.0)

    # 3 — News briefing
    news_instruction = (
        "Use the fetch_news tool to get the top World headlines right now. "
        "Present them as a crisp 3-bullet voice briefing — no URLs, no fluff. "
        "End with: 'I've also pulled up worldmonitor.app for you, Sir.'"
    )
    if priority:
        news_instruction = (
            "PRIORITY MODE: Use fetch_news for World AND Tech headlines. "
            "Give me the top 5 combined in a fast, punchy briefing. No fluff."
        )
    await session.generate_reply(instructions=news_instruction)

    # 4 — Open briefing URL
    _open_in_chrome(BRIEFING_URL)

    await asyncio.sleep(0.8)

    # 5 — System health check
    await session.generate_reply(
        instructions=(
            "Use get_system_info to check system resources. "
            "Only mention it if CPU or RAM is above 80%. "
            "Otherwise just say: 'All systems nominal, Sir. What's the first directive?'"
        )
    )

    logger.info("Opening sequence complete.")


# ── Clap callbacks ────────────────────────────────────────────────────────────

def _make_clap_callbacks(session: AgentSession):

    async def on_single_clap():
        logger.info("Single clap → standard activation.")
        await _run_opening_sequence(session, priority=False)

    async def on_double_clap():
        logger.info("Double clap → priority activation.")
        await _run_opening_sequence(session, priority=True)

    async def on_triple_clap():
        logger.info("Triple clap → standby mode.")
        play_wake_sound()
        await asyncio.sleep(1.5)
        await session.generate_reply(
            instructions=(
                "Say exactly: 'Running silent, Sir. "
                "Clap once when you need me back.' Then go quiet."
            )
        )

    return on_single_clap, on_double_clap, on_triple_clap


# ── LiveKit entrypoint ────────────────────────────────────────────────────────

async def entrypoint(ctx: agents.JobContext):
    logger.info("Doraemon entrypoint starting...")

    # Build memory + time enriched instructions
    memory_context    = _load_memories_for_context()
    time_context      = get_dynamic_instruction()
    full_instructions = AGENT_INSTRUCTION + "\n" + memory_context + "\n" + time_context

    session = AgentSession()

    await session.start(
        room=ctx.room,
        agent=Assistant(injected_instructions=full_instructions),
        room_input_options=RoomInputOptions(
            video_enabled=True,
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    await ctx.connect()

    # Wire clap detection into the running event loop
    loop = asyncio.get_event_loop()
    on_single, on_double, on_triple = _make_clap_callbacks(session)

    clap_detector = start_clap_detection(
        on_single_clap=on_single,
        on_double_clap=on_double,
        on_triple_clap=on_triple,
        loop=loop,
    )

    logger.info(
        "Doraemon standing by — "
        "clap once to activate, twice for priority briefing, "
        "three times for standby."
    )

    try:
        await asyncio.Event().wait()  # Block until shutdown
    finally:
        clap_detector.stop()
        logger.info("Doraemon shut down cleanly.")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
