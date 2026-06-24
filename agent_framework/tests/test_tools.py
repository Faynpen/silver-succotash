"""Unit tests for core/tools.py — ToolRegistry system."""

import pytest
from core.tools import ToolRegistry, ToolResult


class TestToolRegistry:
    def test_register_and_list(self):
        tools = ToolRegistry()

        @tools.register
        def get_weather(city: str) -> str:
            """Get weather for a city."""
            return f"Weather in {city}: sunny"

        assert "get_weather" in tools.list_tools()

    def test_register_generates_schema(self):
        tools = ToolRegistry()

        @tools.register
        def search(query: str, limit: int = 5) -> str:
            """Search the web."""
            return f"results for {query}"

        schema = tools.get_schema("search")
        assert schema is not None
        assert schema["type"] == "function"
        func = schema["function"]
        assert func["name"] == "search"
        assert func["description"] == "Search the web."
        assert "query" in func["parameters"]["properties"]
        assert "limit" in func["parameters"]["properties"]
        assert func["parameters"]["properties"]["query"]["type"] == "string"
        assert func["parameters"]["properties"]["limit"]["type"] == "integer"
        assert func["parameters"]["required"] == ["query"]

    def test_execute_success(self):
        tools = ToolRegistry()

        @tools.register
        def add(a: int, b: int) -> str:
            return str(a + b)

        result = tools.execute("add", {"a": 1, "b": 2})
        assert result.success is True
        assert result.data == "3"
        assert result.execution_time_ms >= 0

    def test_execute_tool_not_found(self):
        tools = ToolRegistry()
        result = tools.execute("nonexistent", {})
        assert result.success is False
        assert "not found" in result.error.lower()

    def test_execute_type_error(self):
        tools = ToolRegistry()

        @tools.register
        def greet(name: str) -> str:
            return f"Hello {name}"

        result = tools.execute("greet", {})  # missing required arg
        assert result.success is False
        assert "argument" in result.error.lower()

    def test_execute_handles_exception(self):
        tools = ToolRegistry()

        @tools.register
        def risky() -> str:
            raise ValueError("boom")

        result = tools.execute("risky", {})
        assert result.success is False
        assert "boom" in result.error

    def test_to_openai_schema(self):
        tools = ToolRegistry()

        @tools.register
        def fn_a():
            return "a"

        @tools.register
        def fn_b():
            return "b"

        schemas = tools.to_openai_schema()
        assert len(schemas) == 2
        names = [s["function"]["name"] for s in schemas]
        assert "fn_a" in names
        assert "fn_b" in names

    def test_schema_default_values(self):
        tools = ToolRegistry()

        @tools.register
        def calc(x: int, y: int = 10) -> str:
            return str(x + y)

        schema = tools.get_schema("calc")
        props = schema["function"]["parameters"]["properties"]
        assert props["y"]["default"] == 10

    def test_multiple_register_no_conflict(self):
        tools = ToolRegistry()

        @tools.register
        def tool_a():
            return "a"

        @tools.register
        def tool_b():
            return "b"

        assert tools.execute("tool_a", {}).data == "a"
        assert tools.execute("tool_b", {}).data == "b"


class TestToolResult:
    def test_success_result(self):
        r = ToolResult(success=True, data="ok")
        assert r.success
        assert r.data == "ok"
        assert r.error == ""

    def test_error_result(self):
        r = ToolResult(success=False, data="", error="fail")
        assert not r.success
        assert r.error == "fail"
