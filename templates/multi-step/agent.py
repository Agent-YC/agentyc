"""Multi-step reasoning agent entrypoint for {{AGENT_NAME}}.

This agent breaks complex problems into sub-tasks and synthesizes results.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class Step:
    """A single step in the agent's reasoning chain."""
    number: int
    description: str
    result: str = ""
    confidence: float = 1.0


class ReasoningAgent:
    """Agent that decomposes tasks into explicit reasoning steps."""

    def __init__(self) -> None:
        self.steps: list[Step] = []

    def plan(self, task: str) -> list[str]:
        """Break a task into sub-steps.

        Args:
            task: The high-level task description.

        Returns:
            List of sub-step descriptions.
        """
        # TODO: Use your LLM to decompose the task
        return [
            f"Analyze the task: {task}",
            "Gather relevant information",
            "Synthesize findings",
            "Validate conclusions",
            "Produce final output",
        ]

    def execute_step(self, step_desc: str) -> Step:
        """Execute a single reasoning step.

        Args:
            step_desc: Description of the step to execute.

        Returns:
            The completed Step with results.
        """
        # TODO: Implement step execution with your LLM
        step = Step(
            number=len(self.steps) + 1,
            description=step_desc,
            result=f"[Result for: {step_desc}]",
        )
        self.steps.append(step)
        return step

    def synthesize(self) -> str:
        """Synthesize all step results into a final response."""
        parts = [f"Step {s.number}: {s.description}\n  → {s.result}" for s in self.steps]
        return "\n".join(parts)


def run(task: str) -> str:
    """Execute the agent's main task using multi-step reasoning.

    Args:
        task: The task description / prompt.

    Returns:
        The agent's synthesized response.
    """
    agent = ReasoningAgent()
    sub_steps = agent.plan(task)

    for step_desc in sub_steps:
        agent.execute_step(step_desc)

    return agent.synthesize()


if __name__ == "__main__":
    import sys
    task = " ".join(sys.argv[1:]) or "Hello, world!"
    print(run(task))
