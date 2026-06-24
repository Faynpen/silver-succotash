"""
Structured Logging System
---
JSON-based logging for the entire agent framework.
Tracks: LLM calls, tool executions, agent orchestration steps.

Designed to replace scattered print() statements with
unified, queryable log output.

Interview talking point:
  "I built a structured logging layer that traces every LLM API call,
   tool invocation, and agent decision. All logs are JSON-formatted,
   making them easy to ingest into log aggregation systems like
   Elasticsearch or Datadog."
"""

import json
import time
import logging
import sys
from typing import Any, Optional


class AgentLogger:
    """
    Structured logger for agent framework operations.

    Usage:
        logger = AgentLogger(name="orchestrator", level="INFO")
        logger.log_llm_call(model="deepseek-chat", latency_ms=450, tokens=320)
        logger.log_tool_execution(tool="get_vital_signs", duration_ms=12, ok=True)
        logger.log_agent_step(agent="planner", step=1, action="plan")
    """

    LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}

    def __init__(
        self,
        name: str = "agent",
        level: str = "INFO",
        output_file: Optional[str] = None,
    ):
        self.name = name
        self.level = level
        self.level_value = self.LEVELS.get(level.upper(), 20)

        # Python stdlib logger as backend
        self._logger = logging.getLogger(f"agent.{name}")
        self._logger.setLevel(self.level_value)
        self._logger.propagate = False

        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(
                logging.Formatter("%(message)s")
            )
            self._logger.addHandler(handler)

            if output_file:
                fh = logging.FileHandler(output_file, encoding="utf-8")
                fh.setFormatter(logging.Formatter("%(message)s"))
                self._logger.addHandler(fh)

    def _emit(self, level: str, event: str, **kwargs):
        """Emit a structured log record."""
        if self.LEVELS.get(level.upper(), 20) < self.level_value:
            return

        record = {
            "timestamp": time.time(),
            "logger": self.name,
            "level": level.upper(),
            "event": event,
            **kwargs,
        }
        self._logger.log(
            self.LEVELS.get(level.upper(), 20),
            json.dumps(record, ensure_ascii=False, default=str),
        )

    # ---- LLM operations ----

    def log_llm_call(
        self,
        model: str,
        latency_ms: float,
        tokens_in: int = 0,
        tokens_out: int = 0,
        ok: bool = True,
        error: str = "",
    ):
        self._emit(
            "INFO",
            "llm_call",
            model=model,
            latency_ms=round(latency_ms, 2),
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            success=ok,
            error=error,
        )

    def log_llm_retry(self, model: str, attempt: int, error: str):
        self._emit("WARNING", "llm_retry", model=model, attempt=attempt, error=error)

    # ---- Tool operations ----

    def log_tool_execution(
        self,
        tool: str,
        duration_ms: float,
        ok: bool,
        args: Optional[dict] = None,
        error: str = "",
    ):
        self._emit(
            "INFO",
            "tool_execution",
            tool=tool,
            duration_ms=round(duration_ms, 2),
            success=ok,
            args=args,
            error=error,
        )

    # ---- Agent operations ----

    def log_agent_step(
        self, agent: str, step: int, action: str, detail: str = ""
    ):
        self._emit(
            "DEBUG",
            "agent_step",
            agent=agent,
            step=step,
            action=action,
            detail=detail,
        )

    def log_agent_decision(self, agent: str, decision: str, reason: str = ""):
        self._emit(
            "INFO",
            "agent_decision",
            agent=agent,
            decision=decision,
            reason=reason,
        )

    def log_loop_detected(self, agent: str, tool: str, count: int):
        self._emit(
            "WARNING",
            "loop_detected",
            agent=agent,
            tool=tool,
            consecutive_calls=count,
        )

    def log_max_steps_reached(self, agent: str, max_steps: int):
        self._emit(
            "ERROR",
            "max_steps_reached",
            agent=agent,
            max_steps=max_steps,
        )

    # ---- Orchestrator operations ----

    def log_phase(self, phase: str, status: str = "started"):
        self._emit("INFO", "orchestrator_phase", phase=phase, status=status)

    def log_review_decision(self, round_num: int, passed: bool, feedback: str = ""):
        self._emit(
            "INFO",
            "review_decision",
            round=round_num,
            passed=passed,
            feedback=feedback,
        )

    def log_error(self, component: str, error: str, context: Optional[dict] = None):
        self._emit(
            "ERROR",
            "framework_error",
            component=component,
            error=error,
            context=context or {},
        )

    # ---- Utility ----

    def debug(self, message: str):
        self._emit("DEBUG", "debug", message=message)

    def info(self, message: str):
        self._emit("INFO", "info", message=message)

    def warning(self, message: str):
        self._emit("WARNING", "warning", message=message)

    def error(self, message: str):
        self._emit("ERROR", "error", message=message)
