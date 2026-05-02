import json
import os
import logging
from livekit.agents import function_tool, RunContext

MEMORY_FILE = "db/memory.json"
os.makedirs("db", exist_ok=True)

def _load() -> dict:
    if os.path.exists(MEMORY_FILE):
        try:
            return json.load(open(MEMORY_FILE))
        except:
            return {}
    return {}

def _save(data: dict):
    json.dump(data, open(MEMORY_FILE, "w"), indent=2)

@function_tool()
async def remember_fact(context: RunContext, key: str, value: str) -> str:  # type: ignore
    """Remember a fact about Krish. key = short label, value = the information."""
    data = _load()
    data[key] = value
    _save(data)
    logging.info(f"Memory saved: {key} = {value}")
    return f"Committed to memory, Sir: '{key}' → '{value}'"

@function_tool()
async def recall_fact(context: RunContext, key: str) -> str:  # type: ignore
    """Recall a stored fact by its key."""
    data = _load()
    if key in data:
        return f"On record, Sir: '{key}' → '{data[key]}'"
    # Fuzzy match — check if key appears in any stored key
    matches = {k: v for k, v in data.items() if key.lower() in k.lower()}
    if matches:
        result = "\n".join(f"  {k}: {v}" for k, v in matches.items())
        return f"Closest matches, Sir:\n{result}"
    return f"No record found for '{key}', Sir."

@function_tool()
async def list_memories(context: RunContext) -> str:  # type: ignore
    """List all stored memories."""
    data = _load()
    if not data:
        return "Memory vault is empty, Sir."
    lines = "\n".join(f"  {i+1}. {k}: {v}" for i, (k, v) in enumerate(data.items()))
    return f"Memory vault ({len(data)} entries), Sir:\n{lines}"
