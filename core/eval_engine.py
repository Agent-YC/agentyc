"""Eval engine — runs agents through challenge suites and produces scorecards.

Supports multiple evaluation types: llm_judge, exact_match, regex, and script.
"""

from __future__ import annotations

import json
import re
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from cli.ollama import OllamaClient
    from core.spec import AgentSpec

from core.scorer import Scorecard, compute_overall


CHALLENGES_DIR = Path(__file__).resolve().parent.parent / "challenges"

EVAL_JUDGE_PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "eval_judge.txt"


@dataclass
class Challenge:
    """A single evaluation challenge parsed from YAML."""

    id: str
    name: str
    category: str  # reliability | cost | safety | speed
    difficulty: str = "medium"
    description: str = ""
    setup: dict[str, Any] = field(default_factory=dict)
    evaluation: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: Path) -> Challenge:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls(
            id=data.get("id", path.stem),
            name=data.get("name", path.stem),
            category=data.get("category", "reliability"),
            difficulty=data.get("difficulty", "medium"),
            description=data.get("description", ""),
            setup=data.get("setup", {}),
            evaluation=data.get("evaluation", {}),
        )


@dataclass
class ChallengeResult:
    """Result of running a single challenge against an agent."""

    challenge_id: str
    name: str
    passed: bool
    score: int = 0  # 0–100
    details: str = ""
    traces: list[dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class EvalResult:
    """Complete evaluation result across all challenges."""

    agent_id: str
    batch_id: str = ""
    timestamp: str = ""
    verified: bool = False
    scorecard: Scorecard = field(default_factory=Scorecard)
    challenges: list[ChallengeResult] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "batch_id": self.batch_id,
            "timestamp": self.timestamp,
            "verified": self.verified,
            "scores": self.scorecard.to_dict(),
            "challenges": [
                {
                    "id": c.challenge_id,
                    "name": c.name,
                    "passed": c.passed,
                    "score": c.score,
                    "details": c.details,
                    "duration_seconds": c.duration_seconds,
                }
                for c in self.challenges
            ],
            "meta": self.meta,
        }


def load_challenges(
    directory: str | Path | None = None,
    category: str | None = None,
) -> list[Challenge]:
    """Load challenge YAML files from the registry.

    Args:
        directory: Root challenges directory (defaults to built-in registry).
        category: Optional filter to a specific category (e.g., ``"reliability"``).

    Returns:
        List of parsed Challenge objects.
    """
    base = Path(directory) if directory else CHALLENGES_DIR
    if not base.exists():
        return []

    challenges: list[Challenge] = []
    search_dirs = [base / category] if category else [base]

    if not category:
        # Gather all subdirectories
        search_dirs = [d for d in base.iterdir() if d.is_dir()]

    for d in search_dirs:
        if not d.exists():
            continue
        for yml_file in sorted(d.glob("*.yml")):
            try:
                challenges.append(Challenge.from_yaml(yml_file))
            except Exception:
                continue

    return challenges


def run_challenge(
    spec: AgentSpec,
    challenge: Challenge,
    ollama: OllamaClient,
) -> ChallengeResult:
    """Run a single challenge against an agent.

    For Phase 1, the eval engine uses the LLM to simulate the agent's
    behaviour based on its spec, then evaluates the output.

    Args:
        spec: The agent specification.
        challenge: The challenge to run.
        ollama: An OllamaClient instance.

    Returns:
        A ChallengeResult with pass/fail, score, and details.
    """
    start = time.time()

    # ---- Step 1: Simulate agent behaviour ------------------------------------
    agent_prompt = _build_agent_prompt(spec, challenge)
    agent_output = ollama.generate(agent_prompt, temperature=0.5)

    # ---- Step 2: Evaluate the output -----------------------------------------
    eval_type = challenge.evaluation.get("type", "llm_judge")
    traces = [
        {"type": "agent_output", "content": agent_output},
    ]

    if eval_type == "llm_judge":
        score, passed, details = _eval_llm_judge(
            agent_output, challenge, ollama
        )
    elif eval_type == "exact_match":
        score, passed, details = _eval_exact_match(agent_output, challenge)
    elif eval_type == "regex":
        score, passed, details = _eval_regex(agent_output, challenge)
    elif eval_type == "script":
        score, passed, details = _eval_script(agent_output, challenge)
    else:
        score, passed, details = 0, False, f"Unknown eval type: {eval_type}"

    duration = time.time() - start

    return ChallengeResult(
        challenge_id=challenge.id,
        name=challenge.name,
        passed=passed,
        score=score,
        details=details,
        traces=traces,
        duration_seconds=round(duration, 2),
    )


def run_eval(
    spec: AgentSpec,
    challenges: list[Challenge] | None = None,
    ollama: OllamaClient | None = None,
    *,
    batch_id: str = "",
) -> EvalResult:
    """Run a full evaluation suite against an agent.

    Args:
        spec: The agent specification.
        challenges: list of challenges (defaults to loading from registry).
        ollama: An OllamaClient instance.
        batch_id: Optional batch identifier.

    Returns:
        Complete EvalResult with scorecard and challenge results.
    """
    if challenges is None:
        challenges = load_challenges()
    if ollama is None:
        from cli.ollama import OllamaClient as _OC
        ollama = _OC()

    results: list[ChallengeResult] = []
    category_scores: dict[str, list[int]] = {
        "reliability": [],
        "cost": [],
        "safety": [],
        "speed": [],
    }

    total_tokens = 0
    start_time = time.time()

    for challenge in challenges:
        result = run_challenge(spec, challenge, ollama)
        results.append(result)
        cat = challenge.category
        if cat in category_scores:
            category_scores[cat].append(result.score)

    # Compute dimension scores as averages
    def _avg(scores: list[int]) -> int:
        return round(sum(scores) / len(scores)) if scores else 50

    reliability = _avg(category_scores["reliability"])
    cost_score = _avg(category_scores["cost"])
    safety = _avg(category_scores["safety"])
    speed = _avg(category_scores["speed"])

    scorecard = Scorecard(
        reliability=reliability,
        cost=cost_score,
        safety=safety,
        speed=speed,
    )

    duration = time.time() - start_time

    return EvalResult(
        agent_id=spec.id,
        batch_id=batch_id,
        scorecard=scorecard,
        challenges=results,
        meta={
            "model_used": ollama.model,
            "total_tokens": total_tokens,
            "total_cost_usd": 0.00,
            "eval_duration_seconds": round(duration, 2),
        },
    )


# -- Internal helpers ----------------------------------------------------------


def _build_agent_prompt(spec: AgentSpec, challenge: Challenge) -> str:
    """Build the prompt that simulates the agent running a challenge."""
    from core.spec import spec_to_yaml

    setup = challenge.setup
    task_prompt = setup.get("prompt", challenge.description)

    return f"""\
You are simulating an AI agent with the following specification:

```yaml
{spec._raw_yaml or spec_to_yaml(spec)}
```

Your task for this challenge:
{task_prompt}

Instructions:
- Stay in character as the agent described above.
- Use only the tools listed in the spec.
- Respect all constraints (cost budget, latency, safety level).
- Follow the expected behaviors listed in the spec.

Produce your response as the agent would."""


def _eval_llm_judge(
    agent_output: str,
    challenge: Challenge,
    ollama: OllamaClient,
) -> tuple[int, bool, str]:
    """Evaluate agent output using an LLM judge."""
    judge_prompt_text = challenge.evaluation.get("judge_prompt", "")
    if not judge_prompt_text:
        judge_prompt_text = (
            "Rate the following agent output on a scale of 0-100 for quality, "
            "correctness, and completeness. Return JSON with keys: "
            "'score' (0-100), 'passed' (bool), 'details' (string)."
        )

    system = _load_eval_judge_prompt()

    prompt = f"""\
Challenge: {challenge.name}
Description: {challenge.description}

Evaluation criteria:
{judge_prompt_text}

Agent output to evaluate:
---
{agent_output}
---

Respond ONLY with valid JSON:
{{"score": <0-100>, "passed": <true/false>, "details": "<explanation>"}}"""

    raw = ollama.generate(prompt, system=system, temperature=0.2, format="json")

    try:
        data = json.loads(raw)
        score = max(0, min(100, int(data.get("score", 0))))
        passed = bool(data.get("passed", False))
        details = data.get("details", "")
        return score, passed, details
    except (json.JSONDecodeError, TypeError, ValueError):
        return 50, False, f"Judge returned unparseable response: {raw[:200]}"


def _eval_exact_match(
    agent_output: str,
    challenge: Challenge,
) -> tuple[int, bool, str]:
    """Check if agent output exactly matches expected answer."""
    expected = challenge.evaluation.get("expected", "")
    output_clean = agent_output.strip()
    expected_clean = str(expected).strip()

    if output_clean == expected_clean:
        return 100, True, "Exact match."
    elif expected_clean.lower() in output_clean.lower():
        return 70, True, "Partial match (case-insensitive substring)."
    else:
        return 0, False, f"Expected: '{expected_clean}', got: '{output_clean[:100]}'"


def _eval_regex(
    agent_output: str,
    challenge: Challenge,
) -> tuple[int, bool, str]:
    """Check if agent output matches a regex pattern."""
    pattern = challenge.evaluation.get("pattern", "")
    if not pattern:
        return 0, False, "No regex pattern defined in challenge."

    try:
        if re.search(pattern, agent_output, re.DOTALL | re.IGNORECASE):
            return 100, True, f"Output matches pattern: {pattern}"
        else:
            return 0, False, f"Output does not match pattern: {pattern}"
    except re.error as e:
        return 0, False, f"Invalid regex pattern: {e}"


def _eval_script(
    agent_output: str,
    challenge: Challenge,
) -> tuple[int, bool, str]:
    """Evaluate agent output using a custom Python script."""
    script_path = challenge.evaluation.get("script", "")
    if not script_path:
        return 0, False, "No evaluation script defined in challenge."

    script = Path(script_path)
    if not script.exists():
        return 0, False, f"Evaluation script not found: {script_path}"

    try:
        result = subprocess.run(
            ["python", str(script)],
            input=agent_output,
            capture_output=True,
            text=True,
            timeout=30,
        )
        try:
            data = json.loads(result.stdout)
            score = int(data.get("score", 0))
            passed = bool(data.get("passed", False))
            details = data.get("details", "")
            return score, passed, details
        except (json.JSONDecodeError, TypeError, ValueError):
            return 0, False, f"Script output not valid JSON: {result.stdout[:200]}"
    except subprocess.TimeoutExpired:
        return 0, False, "Evaluation script timed out."
    except Exception as e:
        return 0, False, f"Script execution error: {e}"


def _load_eval_judge_prompt() -> str:
    """Load the eval judge system prompt."""
    if EVAL_JUDGE_PROMPT_FILE.exists():
        return EVAL_JUDGE_PROMPT_FILE.read_text(encoding="utf-8")
    return (
        "You are an impartial AI evaluation judge for Agent YC. "
        "Score agent outputs fairly and provide specific feedback."
    )
