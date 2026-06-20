"""
LLM Abstraction Layer
---
Unified interface for multiple LLM providers.
Currently supports DeepSeek (OpenAI-compatible API).
Designed for easy extension: add a new provider = add one class.

Interview talking point:
  "I abstracted the LLM layer so the framework is model-agnostic.
   Switching from DeepSeek to GPT or Qwen requires zero changes
   to the Agent, Tool, or Orchestrator layers."
"""

import json
from typing import Optional
from dataclasses import dataclass, field
import httpx


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    finish_reason: str = "stop"
    usage: dict = field(default_factory=dict)


class LLMClient:
    """
    Unified LLM client. Handles:
    - OpenAI-compatible chat completions API
    - Tool/function calling
    - Automatic retry on transient errors
    - Token usage tracking
    - Optional model fallback
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.deepseek.com/v1",
        model: str = "deepseek-chat",
        max_retries: int = 3,
        timeout: float = 60.0,
        fallback_models: Optional[list[str]] = None,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.fallback_models = fallback_models or []
        self._total_tokens = 0  # Track total token consumption

    def chat(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        model: Optional[str] = None,
    ) -> LLMResponse:
        """
        Send a chat request to the LLM.

        Args:
            messages: List of {"role": "...", "content": "..."}
            tools: Optional OpenAI-format tool definitions
            temperature: 0.0 = deterministic, 1.0 = creative
            max_tokens: Maximum tokens in the response
            model: Override the default model

        Returns:
            LLMResponse with content, tool_calls, usage info
        """
        model = model or self.model
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        last_error = None
        models_to_try = [model] + [
            m for m in self.fallback_models if m != model
        ]

        for attempt_model in models_to_try:
            for attempt in range(self.max_retries):
                try:
                    response = httpx.post(
                        url,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json=payload,
                        timeout=self.timeout,
                    )
                    response.raise_for_status()
                    data = response.json()

                    choice = data["choices"][0]
                    message = choice["message"]

                    result = LLMResponse(
                        content=message.get("content") or "",
                        tool_calls=message.get("tool_calls", []),
                        finish_reason=choice.get("finish_reason", "stop"),
                        usage=data.get("usage", {}),
                    )
                    self._total_tokens += result.usage.get("total_tokens", 0)
                    return result

                except httpx.HTTPStatusError as e:
                    last_error = e
                    if e.response.status_code >= 500:
                        # Server error – retry
                        continue
                    else:
                        # Client error – don't retry
                        break
                except httpx.RequestError as e:
                    last_error = e
                    continue

            # If we got here, this model failed all retries.
            if attempt_model != models_to_try[-1]:
                # Try fallback model
                payload["model"] = models_to_try[
                    models_to_try.index(attempt_model) + 1
                ]
                continue

        raise RuntimeError(
            f"LLM request failed after {self.max_retries} retries "
            f"across models {models_to_try}: {last_error}"
        )

    @property
    def total_tokens(self) -> int:
        """Total tokens consumed across all requests."""
        return self._total_tokens

    def tool_call_to_message(self, tool_call: dict, result: str) -> dict:
        """
        Convert a tool call + its result into a message for the next turn.
        """
        return {
            "role": "tool",
            "tool_call_id": tool_call["id"],
            "content": result,
        }
