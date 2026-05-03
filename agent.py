"""
Doraemon Agent — Main Entrypoint
=================================
Activation flow:
  1. Script starts → ClapDetector begins listening silently (no session yet).
  2. User claps ONCE → agent session starts, greeting fires, news + URL load.
  3. User claps TWICE  → same as single but also opens worldmonitor.app.
  4. User claps THREE times → mute / standby toggle.
"""

import json
import logging
import os
import asyncio
import webbrowser
import subprocess
from datetime import datetime
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation
from livekit.plugins import google

from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION, get_dynamic_instruction
from tools import ALL_TOOLS
from engine.clap_detector import start_clap_detection

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("Doraemon")

# ── Constants ────────────────────────────────────────────────────────────────

BRIEFING_URL   = "https://www.worldmonitor.app/"
CHROME_CMDS    = {
    "darwin": ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"],
    "linux":  ["google-chrome", "google-chrome-stable", "chromium-browser"],
    "win32":  [r"C:\Program Files\Google\Chrome\Application\chrome.exe"],
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
    data = _load_mem()
    import time
    key = f"conversation_{int(time.time())}"
    data[key] = f"User: {user_text.strip()} | Doraemon: {agent_text.strip()}"
    conv_keys = [k for k in data if k.startswith("conversation_")]
    if len(conv_keys) > 50:
        for old_key in sorted(conv_keys)[: len(conv_keys) - 50]:
            del data[old_key]
    json.dump(data, open(MEMORY_FILE, "w"), indent=2)


# ── Chrome launcher ───────────────────────────────────────────────────────────

def _open_in_chrome(url: str):
    """Try to open a URL specifically in Chrome; fall back to default browser."""
    import sys
    platform = sys.platform
    cmds = CHROME_CMDS.get(platform, [])

    for cmd in cmds:
        try:
            subprocess.Popen([cmd, "--new-tab", url])
            logger.info(f"Opened {url} in Chrome.")
            return
        except FileNotFoundError:
            continue

    # Fallback
    logger.warning("Chrome not found; opening in default browser.")
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


# ── Activation sequence ───────────────────────────────────────────────────────

_session_active = False
_active_session: AgentSession | None = None


async def _run_opening_sequence(session: AgentSession, open_url: bool = False):
    """
    Full boot sequence fired after clap activation:
      1. Time-aware greeting
      2. World news briefing
      3. Optionally open worldmonitor.app in Chrome
      4. System health snapshot
    """
    global _session_active

    logger.info("Running opening sequence...")

    # 1 ── Greeting + today's context
    await session.generate_reply(instructions=SESSION_INSTRUCTION)

    # Small pause so speech doesn't stack
    await asyncio.sleep(1.2)

    # 2 ── News briefing
    await session.generate_reply(
        instructions=(
            "Use the fetch_news tool to get the top World headlines right now. "
            "Present them as a crisp 3-bullet voice briefing — no URLs, no fluff. "
            "End with: 'I've pulled up worldmonitor.app for you as well, Sir.'"
        )
    )

    # 3 ── Open briefing URL in Chrome
    if open_url:
        _open_in_chrome(BRIEFING_URL)

    await asyncio.sleep(0.8)

    # 4 ── Quick system health check
    await session.generate_reply(
        instructions=(
            "Use get_system_info to check system resources. "
            "Only mention it if something is above 80% — otherwise say: "
            "'All systems nominal, Sir. What's the first directive?'"
        )
    )

    _session_active = True
    logger.info("Opening sequence complete.")


# ── Clap callbacks ────────────────────────────────────────────────────────────

def _make_clap_callbacks(session: AgentSession):
    """Return async callbacks bound to this session."""

    async def on_single_clap():
        logger.info("Single clap → activating Doraemon.")
        await _run_opening_sequence(session, open_url=True)

    async def on_double_clap():
        """Double clap = same as single but also mutes any ongoing speech first."""
        logger.info("Double clap → activating Doraemon + priority briefing.")
        await _run_opening_sequence(session, open_url=True)

    async def on_triple_clap():
        """Triple clap = standby / mute toggle."""
        logger.info("Triple clap → standby mode.")
        await session.generate_reply(
            instructions="Say: 'Running silent, Sir. Clap once to re-engage.' then go quiet."
        )

    return on_single_clap, on_double_clap, on_triple_clap


# ── LiveKit entrypoint ────────────────────────────────────────────────────────

async def entrypoint(ctx: agents.JobContext):
    logger.info("Doraemon entrypoint starting...")

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

    # ── Clap detection — wires into the running event loop ──────────────────
    loop = asyncio.get_event_loop()
    on_single, on_double, on_triple = _make_clap_callbacks(session)

    clap_detector = start_clap_detection(
        on_single_clap=on_single,
        on_double_clap=on_double,
        on_triple_clap=on_triple,
        loop=loop,
    )

    logger.info(
        "Doraemon is standing by — clap once to activate, "
        "twice for priority briefing, three times for standby."
    )

    # Keep the session alive; cleanup on exit
    try:
        # Block indefinitely — LiveKit workers handle shutdown signals
        await asyncio.Event().wait()
    finally:
        clap_detector.stop()
        logger.info("Doraemon shut down cleanly.")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))