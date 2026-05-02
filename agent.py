import logging
import asyncio
from datetime import datetime
from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions
from livekit.plugins import noise_cancellation
from livekit.plugins import google

from prompts import AGENT_INSTRUCTION, SESSION_INSTRUCTION, get_dynamic_instruction
from tools import ALL_TOOLS

# Memory integration
try:
    from mem0 import Memory
    memory = Memory()
    MEMORY_ENABLED = True
except Exception as e:
    logging.warning(f"mem0 not available: {e}")
    memory = None
    MEMORY_ENABLED = False

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("Doraemon")


def _load_memories_for_context() -> str:
    """Load stored mem0 memories and format them for system prompt injection."""
    if not MEMORY_ENABLED or memory is None:
        return ""
    try:
        memories = memory.get_all(user_id="Krish")
        if not memories:
            return ""
        facts = [m.get("memory", m.get("text", "")) for m in memories if m.get("memory") or m.get("text")]
        if not facts:
            return ""
        memory_block = "\n=== Long-Term Memory (Recalled at Session Start) ===\n"
        memory_block += "The following facts are known about Krish from previous sessions:\n"
        for i, fact in enumerate(facts[:20], 1):  # Cap at 20 most recent
            memory_block += f"  {i}. {fact}\n"
        memory_block += "=== End of Memory ===\n"
        logger.info(f"Loaded {len(facts)} memories into session context.")
        return memory_block
    except Exception as e:
        logger.error(f"Failed to load memories: {e}")
        return ""


def _save_conversation_to_memory(user_text: str, assistant_text: str):
    """Persist key conversation turns to mem0 for future recall."""
    if not MEMORY_ENABLED or memory is None:
        return
    try:
        # Only save substantive exchanges (not short acks)
        if len(user_text.strip()) > 20:
            combined = f"User said: {user_text.strip()} | Doraemon responded: {assistant_text.strip()}"
            memory.add(combined, user_id="Krish")
            logger.info("Conversation turn saved to memory.")
    except Exception as e:
        logger.error(f"Failed to save conversation to memory: {e}")


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
        """Hook: fires when user speech is finalized. Save context to memory."""
        try:
            self._last_user_speech = str(message)
            logger.info(f"User speech committed: {self._last_user_speech[:80]}...")
        except Exception as e:
            logger.error(f"on_user_speech_committed error: {e}")

    async def on_agent_speech_committed(self, message):
        """Hook: fires when agent finishes speaking. Persist conversation."""
        try:
            agent_text = str(message)
            if self._last_user_speech:
                _save_conversation_to_memory(self._last_user_speech, agent_text)
                self._last_user_speech = ""
        except Exception as e:
            logger.error(f"on_agent_speech_committed error: {e}")


async def entrypoint(ctx: agents.JobContext):
    logger.info("Doraemon entrypoint starting...")

    # 1. Build dynamic, memory-enriched instruction set
    memory_context = _load_memories_for_context()
    time_context = get_dynamic_instruction()
    full_instructions = AGENT_INSTRUCTION + "\n" + memory_context + "\n" + time_context

    logger.info("Instructions assembled with memory context.")

    # 2. Create session
    session = AgentSession()

    # 3. Start the agent
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

    # 4. Generate opening reply with time-aware session instruction
    await session.generate_reply(
        instructions=SESSION_INSTRUCTION,
    )

    logger.info("Doraemon is online and ready.")


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))