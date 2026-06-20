"""
Planner Agent
---
Role: Task decomposition specialist.
Analyzes user requests and breaks them into ordered subtasks.

Does NOT execute subtasks or call tools – pure reasoning.
Output format: numbered list of actionable subtasks.
"""

from core.agent import Agent
from core.llm import LLMClient
from core.memory import Memory

PLANNER_SYSTEM_PROMPT = """You are a Task Planner for an elderly care robot system.
Your job is to break down complex healthcare tasks into ordered, actionable subtasks.

Rules:
1. Output a numbered list of subtasks, each with a clear goal
2. Each subtask should be specific enough for the Executor Agent to complete
3. Consider safety: always include a validation/confirmation step
4. For medical scenarios, prioritize urgency assessment first

Format your response as:
TASK PLAN:
1. [Subtask name]: [Specific goal and what data/action is needed]
2. [Subtask name]: [Specific goal and what data/action is needed]
...

Example:
Input: "Patient Li fell at home, unresponsive"
TASK PLAN:
1. Confirm fall: Check accelerometer and camera data for fall confirmation
2. Assess severity: Check if patient responds to voice call, check vital signs
3. Emergency decision: Based on data, decide if ambulance is needed
4. Notification: If emergency, contact emergency contacts and provide location
"""


def create_planner(
    llm: LLMClient,
    memory: Memory | None = None,
    max_steps: int = 5,
) -> Agent:
    """Factory for Planner Agent."""
    return Agent(
        llm=llm,
        tools=None,  # Planner reasons, doesn't act
        memory=memory or Memory(),
        system_prompt=PLANNER_SYSTEM_PROMPT,
        max_steps=max_steps,
        temperature=0.3,  # Low temp for structured planning
    )
