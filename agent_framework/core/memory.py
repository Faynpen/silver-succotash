"""
Multi-Level Memory System
---
Three memory tiers for Agent cognition:

1. Short-term:  Conversation context window (list of messages)
2. Working:     Task-scoped key-value store (cleared per task)
3. Long-term:   Persistent facts across sessions (file-backed)

Interview talking point:
  "I designed a three-tier memory architecture. Short-term manages the
   LLM context window with automatic trimming. Working memory stores
   intermediate task state. Long-term persists critical facts like
   patient health baselines across sessions."
"""

import json
from pathlib import Path
from typing import Any, Optional


class Memory:
    """
    Three-tier memory for an Agent.

    Short-term (context window):
        Messages exchanged in the current conversation.
        Auto-trims oldest turns when exceeding max_turns.

    Working (task state):
        Key-value pairs that survive across tool calls within a single task.
        Cleared when a new task starts.

    Long-term (persistent):
        Facts persisted to disk. Survives process restarts.
        Used for: patient profiles, medication history, preferences.
    """

    def __init__(
        self,
        max_turns: int = 20,
        storage_dir: Optional[str] = None,
    ):
        self.short_term: list[dict] = []
        self.working: dict[str, Any] = {}
        self.max_turns = max_turns

        if storage_dir:
            self._storage_path = Path(storage_dir) / "long_term_memory.json"
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.long_term: dict[str, Any] = self._load_long_term()
        else:
            self._storage_path = None
            self.long_term: dict[str, Any] = {}

    # ---- Short-term memory (context window) ----

    def add_message(self, role: str, content: str):
        """Add a message to the conversation context."""
        self.short_term.append({"role": role, "content": content})
        self._trim()

    def add_tool_message(self, role: str, content: str,
                         tool_call_id: str, name: str = ""):
        """Add a tool result message."""
        msg = {"role": role, "content": content,
               "tool_call_id": tool_call_id}
        if name:
            msg["name"] = name
        self.short_term.append(msg)
        self._trim()

    def add_assistant_tool_calls(self, tool_calls: list[dict]):
        """Record the assistant's tool call decision."""
        self.short_term.append({
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls,
        })
        self._trim()

    def get_context(self, turns: int | None = None) -> list[dict]:
        """Return recent conversation context for the LLM."""
        n = turns or self.max_turns
        return self.short_term[-n * 2:]  # Each turn = user + assistant

    def _trim(self):
        """Keep context window within max_turns by removing oldest turns."""
        max_messages = self.max_turns * 2
        if len(self.short_term) > max_messages:
            self.short_term = self.short_term[-max_messages:]

    # ---- Working memory (task-scoped) ----

    def set_working(self, key: str, value: Any):
        """Store intermediate task state."""
        self.working[key] = value

    def get_working(self, key: str, default: Any = None) -> Any:
        """Retrieve intermediate task state."""
        return self.working.get(key, default)

    def clear_working(self):
        """Reset working memory for a new task."""
        self.working.clear()

    # ---- Long-term memory (persistent) ----

    def remember(self, key: str, value: Any):
        """Persist a fact to long-term memory."""
        self.long_term[key] = value
        self._save_long_term()

    def recall(self, key: str, default: Any = None) -> Any:
        """Retrieve a fact from long-term memory."""
        return self.long_term.get(key, default)

    def forget(self, key: str):
        """Remove a fact from long-term memory."""
        self.long_term.pop(key, None)
        self._save_long_term()

    def _load_long_term(self) -> dict:
        """Load long-term memory from disk."""
        if self._storage_path and self._storage_path.exists():
            return json.loads(self._storage_path.read_text(encoding="utf-8"))
        return {}

    def _save_long_term(self):
        """Persist long-term memory to disk."""
        if self._storage_path:
            self._storage_path.write_text(
                json.dumps(self.long_term, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

    # ---- Utility ----

    def summarize_context(self) -> str:
        """Debug: return a summary of current memory state."""
        return (
            f"Memory state:\n"
            f"  Short-term messages: {len(self.short_term)}\n"
            f"  Working keys: {list(self.working.keys())}\n"
            f"  Long-term keys: {list(self.long_term.keys())}"
        )

    def reset(self):
        """Full reset – clear all memory tiers."""
        self.short_term.clear()
        self.working.clear()
