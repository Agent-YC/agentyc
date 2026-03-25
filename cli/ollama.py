"""Ollama client wrapper for local LLM inference.

Communicates with the Ollama REST API (default: http://localhost:11434).
"""

from __future__ import annotations

from typing import Any

import httpx


DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.2"
DEFAULT_TIMEOUT = 120.0


class OllamaClient:
    """Synchronous client for the Ollama REST API."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    # -- public API ------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        *,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.7,
        format: str | None = None,
    ) -> str:
        """Generate a completion from a single prompt.

        Args:
            prompt: The user prompt.
            model: Override the default model.
            system: Optional system prompt.
            temperature: Sampling temperature.
            format: Response format, e.g. ``"json"`` for JSON mode.

        Returns:
            The generated text.
        """
        payload: dict[str, Any] = {
            "model": model or self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system
        if format:
            payload["format"] = format

        resp = self._post("/api/generate", payload)
        return resp.get("response", "")

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        system: str | None = None,
        temperature: float = 0.7,
        format: str | None = None,
    ) -> str:
        """Multi-turn chat completion.

        Args:
            messages: List of ``{"role": "user"|"assistant", "content": "..."}`` dicts.
            model: Override the default model.
            system: Optional system prompt (prepended as a system message).
            temperature: Sampling temperature.
            format: Response format, e.g. ``"json"`` for JSON mode.

        Returns:
            The assistant's reply text.
        """
        all_messages: list[dict[str, str]] = []
        if system:
            all_messages.append({"role": "system", "content": system})
        all_messages.extend(messages)

        payload: dict[str, Any] = {
            "model": model or self.model,
            "messages": all_messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if format:
            payload["format"] = format

        resp = self._post("/api/chat", payload)
        message = resp.get("message", {})
        return message.get("content", "")

    def list_models(self) -> list[str]:
        """List locally available model names."""
        resp = self._get("/api/tags")
        models = resp.get("models", [])
        return [m["name"] for m in models]

    def is_available(self) -> bool:
        """Check whether Ollama is running and reachable."""
        try:
            with httpx.Client(timeout=5.0) as client:
                r = client.get(f"{self.base_url}/api/tags")
                return r.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            return False

    # -- internals -------------------------------------------------------------

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            r = client.post(f"{self.base_url}{path}", json=payload)
            r.raise_for_status()
            return r.json()

    def _get(self, path: str) -> dict[str, Any]:
        with httpx.Client(timeout=self.timeout) as client:
            r = client.get(f"{self.base_url}{path}")
            r.raise_for_status()
            return r.json()
