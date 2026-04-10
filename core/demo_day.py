"""Demo Day engine — simulates the Y Combinator Demo Day experience.

Generates a YC-style pitch for the agent, evaluates it using multi-persona
investor LLMs, and synthesizes a term sheet with a valuation cap.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from cli.ollama import OllamaClient
    from core.eval_engine import EvalResult
    from core.spec import AgentSpec

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
PITCH_PROMPT_FILE = PROMPTS_DIR / "demo_day_pitch.txt"
INVESTORS_PROMPT_FILE = PROMPTS_DIR / "demo_day_investors.txt"


@dataclass
class DemoDayResult:
    """Result of the Demo Day simulation."""
    pitch: str
    visionary_comment: str
    pragmatist_comment: str
    cynic_comment: str
    investment_hype: int  # 1-10
    valuation_cap: int    # simulated valuation cap in USD
    investment_raised: int = 500000  # Standard YC Deal

    def to_dict(self) -> dict[str, Any]:
        return {
            "pitch": self.pitch,
            "visionary_comment": self.visionary_comment,
            "pragmatist_comment": self.pragmatist_comment,
            "cynic_comment": self.cynic_comment,
            "investment_hype": self.investment_hype,
            "valuation_cap": self.valuation_cap,
            "investment_raised": self.investment_raised,
        }


def _load_prompt(file_path: Path, fallback: str) -> str:
    """Load a system prompt from disk."""
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return fallback


def simulate_demo_day(
    spec: "AgentSpec",
    eval_result: "EvalResult",
    ollama: "OllamaClient"
) -> DemoDayResult:
    """Run the complete Demo Day simulation."""
    from core.spec import spec_to_yaml
    
    spec_text = spec._raw_yaml or spec_to_yaml(spec)
    eval_scores = eval_result.scorecard.to_dict() if eval_result else {}
    
    # 1. Generate Pitch
    pitch_system = _load_prompt(PITCH_PROMPT_FILE, "Deliver a 2-min YC demo day pitch.")
    pitch_prompt = f"Agent Spec:\n```yaml\n{spec_text}\n```\n\nEval Scores:\n```json\n{json.dumps(eval_scores, indent=2)}\n```\n\nGive me your Demo Day pitch:"
    
    pitch = ollama.generate(pitch_prompt, system=pitch_system, temperature=0.7)
    
    # 2. Simulate Investors
    investors_system = _load_prompt(INVESTORS_PROMPT_FILE, "You are YC investors. Evaluate this pitch.")
    investors_prompt = f"Agent Spec:\n```yaml\n{spec_text}\n```\n\nEval: {eval_scores}\n\nFounder's Pitch:\n---\n{pitch}\n---\nGive me your feedback (JSON):"
    
    investors_raw = ollama.generate(investors_prompt, system=investors_system, temperature=0.4, format="json")
    
    try:
        data = json.loads(investors_raw)
    except Exception:
        data = {
            "visionary_comment": "Could be massive, but needs more raw intelligence.",
            "pragmatist_comment": "I like the go-to-market plan, but worry about distribution.",
            "cynic_comment": "OpenAI will just release this next week. Hard pass.",
            "investment_hype": 5
        }
        
    hype = max(1, min(10, data.get("investment_hype", 5)))
    overall_score = eval_scores.get("overall", 50)
    
    # 3. Calculate Valuation
    # Base: $5M. For every hype point above 1, add $1M. For every score point above 75, add $200k.
    base_cap = 5000000
    hype_bonus = (hype - 1) * 1000000
    score_bonus = max(0, overall_score - 70) * 200000
    valuation_cap = base_cap + hype_bonus + score_bonus
    
    # Round to nearest 500k
    valuation_cap = round(valuation_cap / 500000) * 500000

    return DemoDayResult(
        pitch=pitch.strip(),
        visionary_comment=data.get("visionary_comment", "Looks promising."),
        pragmatist_comment=data.get("pragmatist_comment", "Good execution plan."),
        cynic_comment=data.get("cynic_comment", "A bit too fragile."),
        investment_hype=hype,
        valuation_cap=valuation_cap,
    )
