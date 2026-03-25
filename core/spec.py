"""Agent spec parser and validator.

Parses and validates agent.yml files into structured AgentSpec objects.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


VALID_SAFETY_LEVELS = {"strict", "standard", "permissive"}

REQUIRED_FIELDS = {"name", "version", "description", "entrypoint"}


@dataclass
class Constraints:
    """Agent operational constraints."""

    max_cost_per_task: float | None = None
    max_latency: str | None = None
    safety_level: str = "standard"

    def __post_init__(self) -> None:
        if self.safety_level not in VALID_SAFETY_LEVELS:
            raise ValueError(
                f"Invalid safety_level '{self.safety_level}'. "
                f"Must be one of: {', '.join(sorted(VALID_SAFETY_LEVELS))}"
            )


@dataclass
class AgentSpec:
    """Standardised agent specification — the 'application form'."""

    name: str
    version: str
    description: str
    entrypoint: str
    author: str = ""
    tools: list[str] = field(default_factory=list)
    constraints: Constraints = field(default_factory=Constraints)
    expected_behaviors: list[str] = field(default_factory=list)

    # Raw YAML text for storage / forwarding
    _raw_yaml: str = field(default="", repr=False)

    @property
    def id(self) -> str:
        """Generate a deterministic agent id from name + version."""
        slug = self.name.lower().replace(" ", "-")
        return f"{slug}-v{self.version}"


def parse_spec(path: str | Path) -> AgentSpec:
    """Load an agent.yml file and return a validated AgentSpec.

    Args:
        path: Path to agent.yml file.

    Returns:
        Parsed and validated AgentSpec.

    Raises:
        FileNotFoundError: If the spec file does not exist.
        ValueError: If the spec is invalid.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Agent spec not found: {path}")

    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)

    if not isinstance(data, dict):
        raise ValueError("Agent spec must be a YAML mapping (dict).")

    errors = validate_spec_data(data, spec_dir=path.parent)
    if errors:
        raise ValueError(
            "Agent spec validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    constraints_data = data.get("constraints", {})
    constraints = Constraints(
        max_cost_per_task=constraints_data.get("max_cost_per_task"),
        max_latency=constraints_data.get("max_latency"),
        safety_level=constraints_data.get("safety_level", "standard"),
    )

    return AgentSpec(
        name=data["name"],
        version=str(data.get("version", "0.0.1")),
        description=data["description"],
        entrypoint=data["entrypoint"],
        author=data.get("author", ""),
        tools=data.get("tools", []),
        constraints=constraints,
        expected_behaviors=data.get("expected_behaviors", []),
        _raw_yaml=raw,
    )


def validate_spec_data(
    data: dict[str, Any],
    *,
    spec_dir: Path | None = None,
) -> list[str]:
    """Validate raw spec data and return a list of error messages.

    Args:
        data: Parsed YAML dict.
        spec_dir: Directory containing the spec file (used for
                  entrypoint resolution).  If *None*, entrypoint
                  path check is skipped.

    Returns:
        List of validation error strings (empty means valid).
    """
    errors: list[str] = []

    # --- required fields ---
    for field_name in REQUIRED_FIELDS:
        if field_name not in data or not data[field_name]:
            errors.append(f"Missing required field: '{field_name}'")

    # --- type checks ---
    if "name" in data and not isinstance(data["name"], str):
        errors.append("'name' must be a string.")
    if "description" in data and not isinstance(data["description"], str):
        errors.append("'description' must be a string.")
    if "tools" in data and not isinstance(data["tools"], list):
        errors.append("'tools' must be a list.")
    if "expected_behaviors" in data and not isinstance(
        data["expected_behaviors"], list
    ):
        errors.append("'expected_behaviors' must be a list.")

    # --- constraints ---
    constraints = data.get("constraints", {})
    if constraints:
        if not isinstance(constraints, dict):
            errors.append("'constraints' must be a mapping.")
        else:
            sl = constraints.get("safety_level")
            if sl and sl not in VALID_SAFETY_LEVELS:
                errors.append(
                    f"Invalid safety_level '{sl}'. "
                    f"Must be one of: {', '.join(sorted(VALID_SAFETY_LEVELS))}"
                )
            cost = constraints.get("max_cost_per_task")
            if cost is not None:
                try:
                    if float(cost) < 0:
                        errors.append("'max_cost_per_task' must be non-negative.")
                except (TypeError, ValueError):
                    errors.append("'max_cost_per_task' must be a number.")

    # --- entrypoint existence (only when spec_dir known) ---
    entrypoint = data.get("entrypoint")
    if entrypoint and spec_dir is not None:
        ep_path = spec_dir / entrypoint
        if not ep_path.exists() and not entrypoint.startswith("docker://"):
            errors.append(
                f"Entrypoint not found: '{entrypoint}' (looked in {spec_dir})"
            )

    return errors


def spec_to_yaml(spec: AgentSpec) -> str:
    """Serialize an AgentSpec back to YAML string."""
    data: dict[str, Any] = {
        "name": spec.name,
        "version": spec.version,
        "author": spec.author,
        "description": spec.description,
        "tools": spec.tools,
        "constraints": {
            "max_cost_per_task": spec.constraints.max_cost_per_task,
            "max_latency": spec.constraints.max_latency,
            "safety_level": spec.constraints.safety_level,
        },
        "expected_behaviors": spec.expected_behaviors,
        "entrypoint": spec.entrypoint,
    }
    return yaml.dump(data, default_flow_style=False, sort_keys=False)
