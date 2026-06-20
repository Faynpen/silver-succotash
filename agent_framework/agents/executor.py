"""
Executor Agent
---
Role: Task execution specialist.
Receives a subtask from the Planner, uses tools to complete it,
and returns structured results.

This is the only Agent type that has tool access.
"""

from core.agent import Agent
from core.llm import LLMClient
from core.tools import ToolRegistry
from core.memory import Memory

EXECUTOR_SYSTEM_PROMPT = """You are a Task Executor for an elderly care robot system.
Your job is to complete individual subtasks using available tools and data.

Rules:
1. Use the available tools to gather data and take actions
2. Always verify sensor readings before making decisions
3. For health-related data, note the timestamp and source
4. If a tool returns an error, try an alternative approach
5. Report results clearly with data, not opinions

Available capabilities:
- Health monitoring: Read vital signs from wearable sensors
- Medication management: Check schedules, log doses
- Fall detection: Analyze accelerometer and camera data
- Emergency response: Contact services, send alerts
- Environmental control: Adjust room temperature, lighting
"""


def create_executor(
    llm: LLMClient,
    tools: ToolRegistry,
    memory: Memory | None = None,
    max_steps: int = 8,
) -> Agent:
    """Factory for Executor Agent."""
    return Agent(
        llm=llm,
        tools=tools,
        memory=memory or Memory(),
        system_prompt=EXECUTOR_SYSTEM_PROMPT,
        max_steps=max_steps,
        temperature=0.5,
    )
