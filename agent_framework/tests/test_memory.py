"""Unit tests for core/memory.py — Three-tier memory system."""

import json
import tempfile
from pathlib import Path
import pytest
from core.memory import Memory


class TestShortTermMemory:
    def test_add_message(self):
        m = Memory()
        m.add_message("user", "hello")
        assert len(m.short_term) == 1
        assert m.short_term[0]["role"] == "user"
        assert m.short_term[0]["content"] == "hello"

    def test_add_tool_message(self):
        m = Memory()
        m.add_tool_message("tool", "result", tool_call_id="123", name="search")
        assert m.short_term[0]["tool_call_id"] == "123"
        assert m.short_term[0]["name"] == "search"

    def test_add_assistant_tool_calls(self):
        m = Memory()
        tool_calls = [{"function": {"name": "search", "arguments": "{}"}}]
        m.add_assistant_tool_calls(tool_calls)
        assert m.short_term[0]["role"] == "assistant"
        assert m.short_term[0]["content"] is None
        assert len(m.short_term[0]["tool_calls"]) == 1

    def test_auto_trim(self):
        m = Memory(max_turns=3)
        for i in range(10):
            m.add_message("user", f"msg{i}")
            m.add_message("assistant", f"reply{i}")
        assert len(m.short_term) <= 6  # 3 turns * 2 messages

    def test_get_context(self):
        m = Memory(max_turns=10)
        m.add_message("user", "q1")
        m.add_message("assistant", "a1")
        m.add_message("user", "q2")
        m.add_message("assistant", "a2")
        ctx = m.get_context(turns=1)
        assert len(ctx) == 2
        assert ctx[0]["content"] == "q2"
        assert ctx[1]["content"] == "a2"


class TestWorkingMemory:
    def test_set_get(self):
        m = Memory()
        m.set_working("patient_id", "P001")
        assert m.get_working("patient_id") == "P001"

    def test_default_value(self):
        m = Memory()
        assert m.get_working("nonexistent", "fallback") == "fallback"

    def test_clear(self):
        m = Memory()
        m.set_working("key", "value")
        m.clear_working()
        assert m.get_working("key") is None

    def test_clear_working_does_not_affect_short_term(self):
        m = Memory()
        m.add_message("user", "hello")
        m.set_working("key", "val")
        m.clear_working()
        assert len(m.short_term) == 1


class TestLongTermMemory:
    def test_remember_and_recall(self):
        m = Memory()
        m.remember("patient", {"name": "test", "age": 70})
        assert m.recall("patient")["age"] == 70

    def test_forget(self):
        m = Memory()
        m.remember("key", "value")
        m.forget("key")
        assert m.recall("key") is None

    def test_file_persistence(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            m = Memory(storage_dir=tmpdir)
            m.remember("test", "data")
            assert Path(tmpdir, "long_term_memory.json").exists()

            m2 = Memory(storage_dir=tmpdir)
            assert m2.recall("test") == "data"

    def test_no_file_without_storage_dir(self):
        m = Memory()
        m.remember("key", "value")
        assert m.recall("key") == "value"
        assert m._storage_path is None


class TestMemoryReset:
    def test_reset_clears_short_term(self):
        m = Memory()
        m.add_message("user", "hello")
        m.reset()
        assert len(m.short_term) == 0

    def test_reset_clears_working(self):
        m = Memory()
        m.set_working("key", "val")
        m.reset()
        assert m.get_working("key") is None

    def test_reset_preserves_long_term(self):
        m = Memory()
        m.remember("persistent", True)
        m.reset()
        assert m.recall("persistent") is True
