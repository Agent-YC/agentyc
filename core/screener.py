"""Screening agent — reviews agent specs for batch admission.

Uses Ollama (local) to evaluate an agent spec against four criteria:
clarity, feasibility, safety, and market fit. Produces a verdict of
ADMIT, CONDITIONAL, or REJECT.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cli.ollama import OllamaClient
    from core.spec import AgentSpec


SCREENER_PROMPT_FILE = (
    Path(__file__).resolve().parent.parent / "prompts" / "screener.txt"
)


@dataclass
class ScreeningResult:
    """Result of screening an agent spec."""

    verdict: str  # ADMIT | CONDITIONAL | REJECT
    clarity: int = 0  # 0–100
    feasibility: int = 0
    safety: int = 0
    market_fit: int = 0
    feedback: str = ""

    @property
    def overall(self) -> int:
        return round(
            0.25 * self.clarity
            + 0.25 * self.feasibility
            + 0.30 * self.safety
            + 0.20 * self.market_fit
        )

    def to_dict(self) -> dict:
        return {
            "verdict": self.verdict,
            "scores": {
                "clarity": self.clarity,
                "feasibility": self.feasibility,
                "safety": self.safety,
                "market_fit": self.market_fit,
                "overall": self.overall,
            },
            "feedback": self.feedback,
        }


def _load_system_prompt() -> str:
    """Load the screener system prompt from disk."""
    if SCREENER_PROMPT_FILE.exists():
        return SCREENER_PROMPT_FILE.read_text(encoding="utf-8")
    # Inline fallback
    return _DEFAULT_PROMPT


_DEFAULT_PROMPT = """\
You are the Screening Agent for Agent YC. You review agent specifications \
and decide whether they should be admitted into a batch program.

You evaluate on four criteria (0-100 each):
1. **Clarity** (25%) — Is the use case well-defined? Is the description specific?
2. **Feasibility** (25%) — Can this agent realistically work with the listed tools?
3. **Safety** (30%) — Are there guardrails? Could this agent cause harm?
4. **Market Fit** (20%) — Is this solving a real problem someone would pay for?

Based on total weighted score:
- >= 70: ADMIT — Ready for batch
- 50-69: CONDITIONAL — Promising but has issues
- < 50: REJECT — Fundamentally flawed or unsafe

Respond ONLY with valid JSON in this exact format:
{
  "verdict": "ADMIT" | "CONDITIONAL" | "REJECT",
  "clarity": <0-100>,
  "feasibility": <0-100>,
  "safety": <0-100>,
  "market_fit": <0-100>,
  "feedback": "<2-4 sentences of specific, actionable feedback>"
}
"""


def screen_agent(
    spec: AgentSpec,
    ollama: OllamaClient,
) -> ScreeningResult:
    """Screen an agent spec using Ollama.

    Args:
        spec: The parsed agent specification.
        ollama: An OllamaClient instance.

    Returns:
        A ScreeningResult with verdict, scores, and feedback.
    """
    from core.spec import spec_to_yaml

    system = _load_system_prompt()
    spec_text = spec._raw_yaml or spec_to_yaml(spec)

    prompt = f"Review this agent specification:\n\n```yaml\n{spec_text}\n```"

    raw = ollama.generate(
        prompt,
        system=system,
        temperature=0.3,
        format="json",
    )

    return _parse_response(raw)


def _parse_response(raw: str) -> ScreeningResult:
    """Parse the LLM JSON response into a ScreeningResult."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return ScreeningResult(
            verdict="CONDITIONAL",
            feedback=f"Screening agent returned unparseable response. Raw: {raw[:200]}",
        )

    verdict = data.get("verdict", "CONDITIONAL").upper()
    if verdict not in ("ADMIT", "CONDITIONAL", "REJECT"):
        verdict = "CONDITIONAL"

    return ScreeningResult(
        verdict=verdict,
        clarity=_safe_int(data.get("clarity", 0)),
        feasibility=_safe_int(data.get("feasibility", 0)),
        safety=_safe_int(data.get("safety", 0)),
        market_fit=_safe_int(data.get("market_fit", 0)),
        feedback=data.get("feedback", ""),
    )


def _safe_int(val: Any) -> int:
    try:
        return max(0, min(100, int(float(val))))
    except (TypeError, ValueError):
        return 0
