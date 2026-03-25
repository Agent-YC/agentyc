"""Scoring logic for agent evaluations.

Implements the four-dimension scoring model plus weighted composite.
"""

from __future__ import annotations

from dataclasses import dataclass


# Composite weights
WEIGHTS = {
    "reliability": 0.30,
    "safety": 0.25,
    "cost": 0.25,
    "speed": 0.20,
}

DEFAULT_GRADUATION_THRESHOLD = 75


@dataclass
class Scorecard:
    """Agent evaluation scorecard across all dimensions."""

    reliability: int = 0
    cost: int = 0
    safety: int = 0
    speed: int = 0
    overall: int = 0

    def __post_init__(self) -> None:
        # Clamp individual scores to 0–100 range
        self.reliability = _clamp(self.reliability)
        self.cost = _clamp(self.cost)
        self.safety = _clamp(self.safety)
        self.speed = _clamp(self.speed)

        # Auto-compute overall if not explicitly provided
        if self.overall == 0 and any(
            [self.reliability, self.cost, self.safety, self.speed]
        ):
            self.overall = compute_overall(
                self.reliability, self.cost, self.safety, self.speed
            )
        else:
            self.overall = _clamp(self.overall)

    def to_dict(self) -> dict[str, int]:
        return {
            "reliability": self.reliability,
            "cost": self.cost,
            "safety": self.safety,
            "speed": self.speed,
            "overall": self.overall,
        }

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> Scorecard:
        return cls(
            reliability=data.get("reliability", 0),
            cost=data.get("cost", 0),
            safety=data.get("safety", 0),
            speed=data.get("speed", 0),
            overall=data.get("overall", 0),
        )


def compute_overall(
    reliability: int,
    cost: int,
    safety: int,
    speed: int,
) -> int:
    """Compute the weighted overall score.

    Formula: 0.30 * reliability + 0.25 * safety + 0.25 * cost + 0.20 * speed

    All inputs should be 0–100.  Output is rounded to nearest integer.
    """
    raw = (
        WEIGHTS["reliability"] * reliability
        + WEIGHTS["safety"] * safety
        + WEIGHTS["cost"] * cost
        + WEIGHTS["speed"] * speed
    )
    return _clamp(round(raw))


def is_graduated(
    scorecard: Scorecard,
    threshold: int = DEFAULT_GRADUATION_THRESHOLD,
) -> bool:
    """Check whether the agent meets the graduation threshold."""
    return scorecard.overall >= threshold


def grade_label(scorecard: Scorecard) -> str:
    """Return a human-readable grade label for the overall score."""
    s = scorecard.overall
    if s >= 90:
        return "A+"
    if s >= 80:
        return "A"
    if s >= 75:
        return "B+"
    if s >= 65:
        return "B"
    if s >= 50:
        return "C"
    if s >= 35:
        return "D"
    return "F"


def _clamp(value: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, value))
