import json
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation
from livekit.plugins import google

from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION, get_dynamic_instruction
from tools import ALL_TOOLS

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("Doraemon")

# ── Local JSON memory (no OpenAI / mem0 needed) ──
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
    # Keep only last 50 conversation entries
    conv_keys = [k for k in data if k.startswith("conversation_")]
    if len(conv_keys) > 50:
        for old_key in sorted(conv_keys)[:len(conv_keys)-50]:
            del data[old_key]
    json.dump(data, open(MEMORY_FILE, "w"), indent=2)


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


async def entrypoint(ctx: agents.JobContext):
    logger.info("Doraemon entrypoint starting...")

    memory_context = _load_memories_for_context()
    time_context = get_dynamic_instruction()
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

    logger.info("Agent session live. Generating opening reply...")

    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )

    logger.info("Doraemon is online and ready.")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
