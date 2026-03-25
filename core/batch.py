"""Batch orchestrator — manages agent cohorts through evaluation cycles.

A batch is a time-boxed cohort of agents evaluated together.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from cli.ollama import OllamaClient
    from core.spec import AgentSpec


@dataclass
class Batch:
    """A batch cohort configuration."""

    id: str
    name: str
    start_date: str
    end_date: str
    graduation_threshold: int = 75
    max_agents: int = 50
    challenges: list[str] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)  # agent IDs

    @classmethod
    def from_yaml(cls, path: Path) -> Batch:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            start_date=str(data.get("start_date", "")),
            end_date=str(data.get("end_date", "")),
            graduation_threshold=data.get("graduation_threshold", 75),
            max_agents=data.get("max_agents", 50),
            challenges=data.get("challenges", []),
            agents=data.get("agents", []),
        )

    def to_yaml(self) -> str:
        data = {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "graduation_threshold": self.graduation_threshold,
            "max_agents": self.max_agents,
            "challenges": self.challenges,
            "agents": self.agents,
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False)

    @property
    def is_full(self) -> bool:
        return len(self.agents) >= self.max_agents


def create_batch(
    batch_id: str,
    name: str,
    start_date: str,
    end_date: str,
    *,
    graduation_threshold: int = 75,
    max_agents: int = 50,
    challenge_paths: list[str] | None = None,
) -> Batch:
    """Create a new batch configuration."""
    return Batch(
        id=batch_id,
        name=name,
        start_date=start_date,
        end_date=end_date,
        graduation_threshold=graduation_threshold,
        max_agents=max_agents,
        challenges=challenge_paths or [],
    )


def add_agent_to_batch(batch: Batch, agent_id: str) -> bool:
    """Add an agent to a batch. Returns False if batch is full."""
    if batch.is_full:
        return False
    if agent_id in batch.agents:
        return True  # Already in batch
    batch.agents.append(agent_id)
    return True


def run_batch(
    batch: Batch,
    specs: list[AgentSpec],
    ollama: OllamaClient,
) -> list[dict[str, Any]]:
    """Run all agents in a batch through evaluation.

    Args:
        batch: The batch configuration.
        specs: List of agent specs for agents in the batch.
        ollama: An OllamaClient instance.

    Returns:
        List of evaluation result dicts, one per agent.
    """
    from core.eval_engine import load_challenges, run_eval
    from core.scorer import is_graduated

    # Load challenges specified in the batch config, or all
    challenges = load_challenges()

    results = []
    for spec in specs:
        eval_result = run_eval(
            spec,
            challenges=challenges,
            ollama=ollama,
            batch_id=batch.id,
        )

        graduated = is_graduated(
            eval_result.scorecard,
            threshold=batch.graduation_threshold,
        )

        result_dict = eval_result.to_dict()
        result_dict["graduated"] = graduated
        results.append(result_dict)

    return results
