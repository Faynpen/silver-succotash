"""
Multi-Agent Orchestrator
---
Coordinates the Plan → Execute → Review → Revise workflow.

Flow:
  1. Planner decomposes user input into subtasks
  2. Executor completes each subtask (can call tools)
  3. Reviewer checks quality and safety
  4. If REVIEW fails → back to Executor with feedback (max 3 rounds)
  5. If PASS → return final result

This architecture maps directly to real-world processes:
  - Healthcare: Doctor orders → Nurse executes → Senior doctor reviews
  - DevOps: Incident commander → Engineer fixes → SRE validates
  - Code: Architect designs → Developer implements → Reviewer approves
"""

import json
import re
from typing import Optional

from core.llm import LLMClient
from core.tools import ToolRegistry
from core.memory import Memory
from agents.planner import create_planner
from agents.executor import create_executor
from agents.reviewer import create_reviewer


class Orchestrator:
    """
    Manages the full Plan-Execute-Review lifecycle.

    Each agent gets its own Memory instance for isolation,
    but the Orchestrator's shared memory bridges them.
    """

    def __init__(
        self,
        llm: LLMClient,
        tools: ToolRegistry,
        storage_dir: Optional[str] = None,
        max_revise_rounds: int = 3,
    ):
        self.llm = llm
        self.tools = tools
        self.max_revise_rounds = max_revise_rounds

        # Shared context that flows between agents
        self.shared_memory = Memory(storage_dir=storage_dir)

        # Create agents (each with independent short-term memory)
        self.planner = create_planner(llm, memory=Memory())
        self.executor = create_executor(llm, tools, memory=Memory())
        self.reviewer = create_reviewer(llm, memory=Memory())

    def run(self, user_input: str) -> dict:
        """
        Execute the full Plan-Execute-Review cycle.

        Returns:
            {
                "success": bool,
                "plan": str,           # Planner output
                "subtasks": list[str], # Parsed subtasks
                "results": list[str],  # Executor results per subtask
                "review_rounds": int,  # How many review cycles needed
                "final_output": str,   # Final response to user
                "execution_log": dict, # Full trace for debugging
            }
        """
        execution_log = {"phase": [], "errors": []}

        # ---- PHASE 1: PLAN ----
        execution_log["phase"].append("PLAN")
        plan_result = self.planner.run(user_input)
        plan_text = plan_result["result"] if plan_result["success"] else (
            f"Planning failed: {plan_result['result']}\nDefaulting to single-task execution."
        )

        subtasks = self._parse_subtasks(plan_text) or [user_input]
        self.shared_memory.set_working("plan", plan_text)
        self.shared_memory.set_working("subtasks", subtasks)

        execution_log["plan"] = {
            "raw_output": plan_text,
            "parsed_subtasks": subtasks,
        }

        # ---- PHASE 2: EXECUTE ----
        execution_log["phase"].append("EXECUTE")
        results = []
        for i, subtask in enumerate(subtasks):
            self.shared_memory.set_working("current_subtask", i + 1)
            exec_result = self.executor.run(subtask)
            results.append({
                "index": i + 1,
                "subtask": subtask,
                "result": exec_result["result"],
                "success": exec_result["success"],
                "tool_calls": exec_result["tool_calls"],
            })

        self.shared_memory.set_working("execution_results", results)
        execution_log["execution"] = results

        # ---- PHASE 3: REVIEW + REVISE ----
        execution_log["phase"].append("REVIEW")
        review_ok = False
        review_rounds = 0

        for round_num in range(self.max_revise_rounds):
            review_rounds = round_num + 1

            # Build review prompt
            review_prompt = self._build_review_prompt(user_input, results)
            review_result = self.reviewer.run(review_prompt)
            review_text = review_result["result"]

            execution_log[f"review_round_{review_rounds}"] = review_text

            # Parse the review decision
            if self._is_pass(review_text):
                review_ok = True
                break
            else:
                # Extract feedback and send back to Executor
                feedback = self._extract_feedback(review_text)
                revised_results = []
                for item in results:
                    revision_task = (
                        f"Original task: {item['subtask']}\n"
                        f"Your previous result: {item['result']}\n"
                        f"REVIEW FEEDBACK: {feedback}\n"
                        f"Please revise your result to address this feedback."
                    )
                    revised = self.executor.run(revision_task)
                    revised_results.append({
                        **item,
                        "result": revised["result"],
                        "revised": True,
                    })
                results = revised_results
                self.shared_memory.set_working("execution_results", results)

        execution_log["review"] = {
            "rounds": review_rounds,
            "passed": review_ok,
        }

        # ---- PHASE 4: FORMAT FINAL OUTPUT ----
        final_output = self._format_output(user_input, results, review_ok)

        return {
            "success": True,
            "plan": plan_text,
            "subtasks": subtasks,
            "results": results,
            "review_rounds": review_rounds,
            "final_output": final_output,
            "execution_log": execution_log,
        }

    def _parse_subtasks(self, plan_text: str) -> list[str]:
        """Extract numbered subtasks from the Planner's output."""
        lines = plan_text.split("\n")
        subtasks = []
        in_plan = False

        for line in lines:
            line = line.strip()
            if not line:
                continue
            if "TASK PLAN" in line.upper():
                in_plan = True
                continue
            if in_plan:
                match = re.match(r"^\d+\.?\s*(.+)$", line)
                if match:
                    subtasks.append(match.group(1).strip())

        return subtasks

    def _build_review_prompt(self, original_task: str,
                             results: list[dict]) -> str:
        """Build the prompt for the Reviewer Agent."""
        results_text = "\n".join(
            f"Subtask {r['index']}: {r['subtask']}\nResult: {r['result']}\n"
            for r in results
        )
        return (
            f"Original user request: {original_task}\n\n"
            f"Execution results:\n{results_text}\n\n"
            f"Please review these results. Check for completeness, "
            f"accuracy, safety (critical in healthcare!), and clarity.\n"
            f"Output DECISION: PASS or DECISION: REVISE with FEEDBACK."
        )

    def _is_pass(self, review_text: str) -> bool:
        """Determine if the review passed."""
        text_upper = review_text.upper()
        if "DECISION: PASS" in text_upper or "DECISION:PASS" in text_upper:
            return True
        if "DECISION: REVISE" in text_upper or "DECISION:REVISE" in text_upper:
            return False
        # Fallback: check for positive indicators
        return "PASS" in text_upper and "REVISE" not in text_upper

    def _extract_feedback(self, review_text: str) -> str:
        """Extract feedback from a REVISE decision."""
        lines = review_text.split("\n")
        capturing = False
        feedback = []

        for line in lines:
            if "FEEDBACK:" in line.upper():
                capturing = True
                feedback.append(line.split(":", 1)[-1].strip())
            elif capturing and line.strip():
                feedback.append(line.strip())

        return "\n".join(feedback) if feedback else review_text

    def _format_output(self, task: str, results: list[dict],
                       review_ok: bool) -> str:
        """Format the final output for the user."""
        parts = [f"Task: {task}\n"]
        parts.append("=" * 50)
        parts.append("EXECUTION RESULTS:\n")

        for r in results:
            status = "✅" if r.get("success", True) else "❌"
            revised = " [REVISED]" if r.get("revised") else ""
            parts.append(f"\n{status} Subtask {r['index']}{revised}:")
            parts.append(f"   Request: {r['subtask']}")
            parts.append(f"   Result: {r['result']}")

        parts.append(f"\n{'=' * 50}")
        parts.append(f"Review: {'PASSED' if review_ok else 'REVISED'}")
        parts.append(f"Total subtasks: {len(results)}")
        return "\n".join(parts)
