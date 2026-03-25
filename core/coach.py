"""Coach agent — provides actionable feedback on agent eval results.

The local coach uses Ollama to analyze eval traces and give YC-partner-style
feedback: sharp, specific, and prioritized.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cli.ollama import OllamaClient
    from core.eval_engine import EvalResult
    from core.spec import AgentSpec

COACH_PROMPT_FILE = (
    Path(__file__).resolve().parent.parent / "prompts" / "coach_local.txt"
)


_DEFAULT_COACH_PROMPT = """\
You are the Coach Agent for Agent YC. You give sharp, specific,
actionable feedback — like a YC partner in office hours.

You have access to:
- The agent's spec (name, description, tools, constraints)
- The agent's eval scorecard (scores across all dimensions)
- The agent's challenge results (pass/fail + details)

Your feedback must:
1. Reference specific scores and failures
2. Identify root causes, not just symptoms
3. Suggest concrete code/prompt changes
4. Prioritize — what's the ONE thing to fix first?
5. Be under 200 words
"""


def _load_coach_prompt() -> str:
    """Load the coach system prompt from disk."""
    if COACH_PROMPT_FILE.exists():
        return COACH_PROMPT_FILE.read_text(encoding="utf-8")
    return _DEFAULT_COACH_PROMPT


def get_coaching(
    spec: AgentSpec,
    eval_result: EvalResult | None,
    question: str,
    ollama: OllamaClient,
) -> str:
    """Get coaching feedback from the local LLM.

    Args:
        spec: The agent's spec.
        eval_result: The latest eval result (may be None if no eval yet).
        question: The developer's question or "general feedback".
        ollama: An OllamaClient instance.

    Returns:
        The coach's response text.
    """

    system = _load_coach_prompt()
    context = _build_context(spec, eval_result)

    prompt = f"""\
{context}

---

Developer's question: {question}

Give your coaching feedback:"""

    return ollama.generate(prompt, system=system, temperature=0.5)


def get_coaching_chat(
    spec: AgentSpec,
    eval_result: EvalResult | None,
    messages: list[dict[str, str]],
    ollama: OllamaClient,
) -> str:
    """Multi-turn coaching chat session.

    Args:
        spec: The agent's spec.
        eval_result: The latest eval result (may be None).
        messages: Chat history (list of role/content dicts).
        ollama: An OllamaClient instance.

    Returns:
        The coach's reply.
    """
    system = _load_coach_prompt()
    context = _build_context(spec, eval_result)

    # Prepend context as the first user message if not already present
    enriched_messages = [
        {"role": "user", "content": f"Here is my agent's context:\n\n{context}"},
        {
            "role": "assistant",
            "content": "Got it. I've reviewed your agent's spec and eval results. What would you like to work on?",
        },
        *messages,
    ]

    return ollama.chat(enriched_messages, system=system, temperature=0.5)


def _build_context(spec: AgentSpec, eval_result: EvalResult | None) -> str:
    """Build the context block for the coach prompt."""
    from core.spec import spec_to_yaml

    parts = [
        "## Agent Spec\n",
        f"```yaml\n{spec._raw_yaml or spec_to_yaml(spec)}\n```\n",
    ]

    if eval_result:
        scores = eval_result.scorecard.to_dict()
        parts.append("## Eval Scorecard\n")
        parts.append(f"- Reliability: {scores['reliability']}/100\n")
        parts.append(f"- Cost: {scores['cost']}/100\n")
        parts.append(f"- Safety: {scores['safety']}/100\n")
        parts.append(f"- Speed: {scores['speed']}/100\n")
        parts.append(f"- **Overall: {scores['overall']}/100**\n\n")

        parts.append("## Challenge Results\n")
        for cr in eval_result.challenges:
            status = "✅ PASS" if cr.passed else "❌ FAIL"
            parts.append(f"- {cr.name}: {status} (score: {cr.score})\n")
            if cr.details:
                parts.append(f"  Details: {cr.details}\n")
    else:
        parts.append("\n*No eval results yet — coaching is based on spec only.*\n")

    return "".join(parts)
