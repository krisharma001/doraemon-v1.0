import logging
import os
from livekit.agents import function_tool, RunContext
from mem0 import Memory

# Initialize mem0 Memory
# This will create a default local database if no config is provided
memory = Memory()

@function_tool()
async def remember_fact(
    context: RunContext, # type: ignore
    fact: str
) -> str:
    """
    Remember a piece of information about Krish or his preferences.
    """
    try:
        logging.info(f"Remembering fact: {fact}")
        # mem0.add stores information into the long-term memory
        memory.add(fact, user_id="Krish")
        return "I've committed that to long-term memory, Sir."
    except Exception as e:
        logging.error(f"Remember fact failed: {e}")
        return f"I had trouble remembering that: {str(e)}"

@function_tool()
async def recall_fact(
    context: RunContext, # type: ignore
    query: str
) -> str:
    """
    Retrieve a stored fact or memory based on a query.
    """
    try:
        logging.info(f"Recalling fact for query: {query}")
        # mem0.search retrieves relevant memories
        results = memory.search(query, user_id="Krish")
        if not results:
            return "I'm afraid I have no record of that, Sir."

        # Combine memory strings
        facts = [r['text'] for r in results]
        return "My records indicate:\n" + "\n".join(facts)
    except Exception as e:
        logging.error(f"Recall fact failed: {e}")
        return f"Error retrieving memory: {str(e)}"

@function_tool()
async def list_memories(
    context: RunContext, # type: ignore
) -> str:
    """
    List all stored memories for the user.
    """
    try:
        # Using mem0's get_all if available or a manual search for common keywords
        # Since mem0 provides search, we'll use a broad search as a workaround
        memories = memory.get_all(user_id="Krish")
        if not memories:
            return "Your memory vault is currently empty, Sir."

        output = "Stored Memories, Sir:\n"
        for i, m in enumerate(memories, 1):
            output += f"{i}. {m.get('text', 'Unknown')}\n"
        return output
    except Exception as e:
        logging.error(f"List memories failed: {e}")
        return f"Error listing memories: {str(e)}"
