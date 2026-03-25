"""Cloud API client — stubs for Phase 3.

These functions will be implemented when the cloud layer is built.
For now, they raise NotImplementedError with helpful messages.
"""

from __future__ import annotations


class CloudClient:
    """Client for the Agent YC cloud API."""

    def __init__(self, api_key: str = "", base_url: str = "https://api.agentyc.com"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def verify_eval(self, agent_spec: str, agent_source: str) -> dict:
        """Submit an agent for verified evaluation (Phase 3)."""
        raise NotImplementedError(
            "Verified evaluations require a cloud account. "
            "Run `agent-yc login` to connect, or use `agent-yc eval` for local evaluation."
        )

    def pro_coach(self, agent_id: str, question: str) -> dict:
        """Ask the Pro Coach a question (Phase 3)."""
        raise NotImplementedError(
            "Pro coaching requires a Pro subscription. "
            "Use `agent-yc coach` for free local coaching via Ollama."
        )

    def publish(self, agent_id: str) -> dict:
        """Publish an agent to the marketplace (Phase 4)."""
        raise NotImplementedError(
            "Publishing to the marketplace requires a verified agent and Pro subscription. "
            "Coming soon in a future release."
        )

    def get_leaderboard(self, batch: str = "", limit: int = 50) -> dict:
        """Get the current leaderboard (Phase 3)."""
        raise NotImplementedError(
            "The leaderboard requires a cloud account. Coming soon."
        )
