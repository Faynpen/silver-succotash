"""
Agent Base Class with ReAct Loop
---
The core intelligence engine. Implements the ReAct (Reasoning + Acting) pattern:

    Think → Act (call tools) → Observe (tool results) → Think → ...

The loop continues until:
  (a) The LLM returns a final answer (no tool calls)
  (b) Maximum steps reached (safety limit)
  (c) Three consecutive identical tool calls (loop detection)

Interview talking point:
  "I implemented the ReAct loop from scratch – not wrapping LangChain.
   This gave me full control over the prompt engineering, loop termination
   conditions, and tool call parsing. The loop detector catches infinite
   loops, and the step limiter prevents runaway token consumption."
"""

import json
from typing import Optional, Callable

from core.llm import LLMClient, LLMResponse
from core.tools import ToolRegistry, ToolResult
from core.memory import Memory


class Agent:
    """
    A single AI Agent powered by an LLM, with tool access and memory.

    The Agent does NOT know about other Agents. Multi-agent coordination
    happens at the Orchestrator level.
    """

    def __init__(
        self,
        llm: LLMClient,
        tools: Optional[ToolRegistry] = None,
        memory: Optional[Memory] = None,
        system_prompt: str = "You are a helpful AI assistant.",
        max_steps: int = 10,
        temperature: float = 0.7,
    ):
        self.llm = llm
        self.tools = tools or ToolRegistry()
        self.memory = memory or Memory()
        self.system_prompt = system_prompt
        self.max_steps = max_steps
        self.temperature = temperature

        # Execution state
        self.steps_taken: int = 0
        self.last_tool_calls: list[str] = []
        self.execution_log: list[dict] = []

    def run(self, task: str) -> dict:
        """
        Execute a task using the ReAct loop.

        Returns:
            {
                "success": bool,
                "result": str,         # Final answer
                "steps": int,          # Steps taken
                "tool_calls": int,     # Total tool invocations
                "log": list[dict],     # Step-by-step execution log
            }
        """
        # Reset per-run state
        self.steps_taken = 0
        self.last_tool_calls = []
        self.execution_log = []

        # Add user task to memory
        self.memory.add_message("user", task)

        tool_schemas = self.tools.to_openai_schema() if self.tools._tools else None
        tool_call_count = 0

        for step in range(self.max_steps):
            self.steps_taken = step + 1

            # Build full message list: system + context + current turn
            messages = self._build_messages()

            # --- THINK: Call LLM ---
            response = self.llm.chat(
                messages=messages,
                tools=tool_schemas,
                temperature=self.temperature,
            )

            # --- DECIDE: Tool call or final answer? ---
            if response.tool_calls:
                # The LLM wants to use tools
                self._log_step("tool_call", {
                    "calls": [
                        {"name": tc["function"]["name"],
                         "args": tc["function"]["arguments"]}
                        for tc in response.tool_calls
                    ]
                })

                # Record assistant's tool call decision
                self.memory.add_assistant_tool_calls(response.tool_calls)

                # --- ACT: Execute each tool ---
                for tc in response.tool_calls:
                    tool_name = tc["function"]["name"]
                    tool_args = json.loads(tc["function"]["arguments"])
                    tool_id = tc["id"]

                    # Loop detection
                    self.last_tool_calls.append(tool_name)
                    if (len(self.last_tool_calls) >= 3 and
                        len(set(self.last_tool_calls[-3:])) == 1):
                        # Same tool called 3 times in a row – likely stuck
                        self.memory.add_message(
                            "user",
                            "[System: You've called the same tool 3 times. "
                            "Stop and provide your best answer now.]"
                        )
                        self.last_tool_calls.clear()

                    # Execute
                    result = self.tools.execute(tool_name, tool_args)
                    tool_call_count += 1

                    # --- OBSERVE: Feed result back ---
                    self.memory.add_tool_message(
                        role="tool",
                        content=result.data if result.success
                                else f"Error: {result.error}",
                        tool_call_id=tool_id,
                        name=tool_name,
                    )

                    self._log_step("tool_result", {
                        "tool": tool_name,
                        "success": result.success,
                        "time_ms": result.execution_time_ms,
                    })
            else:
                # Final answer – no tool calls
                final_answer = response.content
                self.memory.add_message("assistant", final_answer)
                self._log_step("final_answer", {"content": final_answer})

                return {
                    "success": True,
                    "result": final_answer,
                    "steps": self.steps_taken,
                    "tool_calls": tool_call_count,
                    "log": self.execution_log,
                }

        # Max steps reached without final answer
        return {
            "success": False,
            "result": (
                f"Task exceeded maximum steps ({self.max_steps}). "
                "The Agent may be stuck in a loop or the task is too complex."
            ),
            "steps": self.steps_taken,
            "tool_calls": tool_call_count,
            "log": self.execution_log,
        }

    def _build_messages(self) -> list[dict]:
        """Build message list for the LLM: system prompt + context."""
        messages = [{"role": "system", "content": self.system_prompt}]
        messages.extend(self.memory.get_context())
        return messages

    def _log_step(self, step_type: str, data: dict):
        """Record a step in the execution log."""
        self.execution_log.append({
            "step": self.steps_taken,
            "type": step_type,
            **data,
        })

    def reset(self):
        """Reset agent state for a new conversation."""
        self.memory.reset()
        self.steps_taken = 0
        self.last_tool_calls.clear()
        self.execution_log.clear()
