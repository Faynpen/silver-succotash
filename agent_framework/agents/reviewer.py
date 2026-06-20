"""
Reviewer Agent
---
Role: Quality assurance specialist.
Reviews Executor results against the original task requirements.
Decides: PASS (return to user) or REVISE (send back with feedback).

This is the SAFETY GATE – especially critical in healthcare scenarios.
"""

from core.agent import Agent
from core.llm import LLMClient
from core.memory import Memory

REVIEWER_SYSTEM_PROMPT = """You are a Safety Reviewer for an elderly care robot system.
Your job is to review execution results and ensure quality and safety.

Review criteria:
1. COMPLETENESS: Did the executor address ALL parts of the task?
2. ACCURACY: Are the data and conclusions correct and consistent?
3. SAFETY: Are there any risky recommendations or missing precautions?
4. CLARITY: Is the response clear and actionable for caregivers/family?

For HEALTHCARE scenarios, apply EXTRA scrutiny:
- Medication: Double-check dosage, timing, interactions
- Emergency: Verify severity assessment is appropriate
- Vitals: Flag any abnormal readings with urgency level

Output format:
DECISION: [PASS / REVISE]
REASON: [Brief explanation of why]
[If REVISE]
FEEDBACK: [Specific instructions for the executor to improve]
"""


def create_reviewer(
    llm: LLMClient,
    memory: Memory | None = None,
    max_steps: int = 3,
) -> Agent:
    """Factory for Reviewer Agent."""
    return Agent(
        llm=llm,
        tools=None,  # Reviewer reasons, doesn't act
        memory=memory or Memory(),
        system_prompt=REVIEWER_SYSTEM_PROMPT,
        max_steps=max_steps,
        temperature=0.2,  # Very low temp – safety-critical
    )
