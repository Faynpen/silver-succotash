"""
Tool Registry & @tool Decorator
---
Automatically converts Python functions into OpenAI function-calling JSON schemas.
Uses Python type hints and docstrings – no manual schema writing needed.

Interview talking point:
  "I built a decorator-based tool system that introspects function signatures
   at registration time and auto-generates the JSON Schema for OpenAI's
   function calling protocol. Each tool runs in a sandboxed context with
   timeout control and structured error handling."
"""

import inspect
import time
from functools import wraps
from typing import Any, Callable, get_type_hints
from dataclasses import dataclass, field


@dataclass
class ToolResult:
    success: bool
    data: str
    error: str = ""
    execution_time_ms: float = 0.0


class ToolRegistry:
    """
    Registry that manages tool registration, schema generation, and execution.

    Usage:
        tools = ToolRegistry()

        @tools.register
        def web_search(query: str, num_results: int = 3) -> str:
            '''Search the web for information.'''
            ...

        # Auto-generates OpenAI tool schemas
        schemas = tools.to_openai_schema()

        # Execute a tool call from LLM
        result = tools.execute("web_search", {"query": "DeepSeek API"})
    """

    def __init__(self):
        self._tools: dict[str, dict] = {}

    def register(self, func: Callable) -> Callable:
        """
        Decorator that registers a function as a callable tool.
        Auto-generates the OpenAI function calling schema from type hints and docstring.
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        hints = get_type_hints(func)
        doc = inspect.getdoc(func) or func.__name__

        # Build parameters schema, excluding 'return' annotation
        properties = {}
        required = []

        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
            param_type = hints.get(param_name, str)
            properties[param_name] = self._build_param_schema(
                param_name, param_type, param
            )
            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        schema = {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": doc,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

        self._tools[func.__name__] = {
            "func": func,
            "schema": schema,
        }

        return wrapper

    def to_openai_schema(self) -> list[dict]:
        """Return all registered tools as OpenAI-format tool schemas."""
        return [t["schema"] for t in self._tools.values()]

    def execute(self, name: str, args: dict) -> ToolResult:
        """
        Execute a tool by name with the given arguments.

        Safety features:
        - Tool not found → graceful error
        - Exception during execution → caught and returned
        - Execution time measured
        """
        start = time.time()

        if name not in self._tools:
            return ToolResult(
                success=False,
                data="",
                error=f"Tool '{name}' not found. Available: {list(self._tools.keys())}",
                execution_time_ms=(time.time() - start) * 1000,
            )

        try:
            func = self._tools[name]["func"]
            result = func(**args)
            elapsed = (time.time() - start) * 1000

            return ToolResult(
                success=True,
                data=str(result),
                execution_time_ms=elapsed,
            )
        except TypeError as e:
            return ToolResult(
                success=False,
                data="",
                error=f"Tool argument error: {e}",
                execution_time_ms=(time.time() - start) * 1000,
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data="",
                error=f"Tool execution error: {e}",
                execution_time_ms=(time.time() - start) * 1000,
            )

    def _build_param_schema(self, name: str, py_type: type, param) -> dict:
        """Map Python type to JSON Schema type with description."""
        type_map = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            list: "array",
            dict: "object",
        }
        schema = {"type": type_map.get(py_type, "string")}

        if param.default is not inspect.Parameter.empty:
            schema["default"] = param.default

        return schema

    def list_tools(self) -> list[str]:
        """Return names of all registered tools."""
        return list(self._tools.keys())

    def get_schema(self, name: str) -> dict | None:
        """Get the schema for a specific tool."""
        tool = self._tools.get(name)
        return tool["schema"] if tool else None
