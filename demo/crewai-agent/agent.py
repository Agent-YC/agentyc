"""CrewAI multi-agent research crew demo.

Shows how to integrate a CrewAI crew with Agent YC.
Uses two agents: a researcher and a writer.

Requirements:
    pip install crewai

Usage with Agent YC:
    agent-yc screen
    agent-yc eval

Usage with the runner directly:
    from core.runner import run_crewai_agent
    result = run_crewai_agent(build_crew("Research AI safety"), "task")
"""

import sys

try:
    from crewai import Agent, Task, Crew, Process

    HAS_CREWAI = True
except ImportError:
    HAS_CREWAI = False


def build_crew(task_description: str):
    """Build and return a CrewAI crew.

    Returns a Crew that can be passed to
    run_crewai_agent() from core.runner.
    """
    if not HAS_CREWAI:
        raise ImportError(
            "CrewAI is required. Install with:\n"
            "  pip install crewai"
        )

    researcher = Agent(
        role="Senior Research Analyst",
        goal="Find comprehensive, accurate information from multiple sources",
        backstory=(
            "You are an expert research analyst with 15 years of experience. "
            "You always verify claims across multiple sources, flag uncertainties, "
            "and detect contradictions. You never fabricate information."
        ),
        verbose=False,
        allow_delegation=False,
    )

    writer = Agent(
        role="Research Writer",
        goal="Produce clear, well-cited research syntheses",
        backstory=(
            "You are a skilled technical writer who specializes in turning "
            "research findings into clear, actionable reports. You always "
            "include citations, confidence levels, and uncertainty flags."
        ),
        verbose=False,
        allow_delegation=False,
    )

    research_task = Task(
        description=f"Research the following topic thoroughly: {task_description}",
        expected_output=(
            "A detailed research brief with findings, sources, "
            "contradictions, and confidence levels."
        ),
        agent=researcher,
    )

    writing_task = Task(
        description=(
            "Based on the research findings, produce a polished synthesis "
            "with citations, confidence levels, and a clear conclusion."
        ),
        expected_output=(
            "A well-structured research synthesis with numbered citations, "
            "confidence indicators, and actionable insights."
        ),
        agent=writer,
    )

    crew = Crew(
        agents=[researcher, writer],
        tasks=[research_task, writing_task],
        process=Process.sequential,
        verbose=False,
    )

    return crew


def run(task: str) -> str:
    """Entry point for Agent YC's Python runner."""
    if not HAS_CREWAI:
        return _fallback_response(task)

    crew = build_crew(task)
    result = crew.kickoff(inputs={"task": task})
    return str(result)


def _fallback_response(task: str) -> str:
    """Fallback when CrewAI is not installed."""
    return (
        "## CrewAI Research Crew Response (fallback mode)\n\n"
        f"**Task**: {task[:200]}\n\n"
        "CrewAI is not installed. Install with:\n"
        "```\npip install crewai\n```\n\n"
        "In production, this crew would:\n"
        "1. **Researcher agent** gathers and verifies information\n"
        "2. **Writer agent** produces a cited synthesis\n"
        "3. Agents run sequentially (researcher → writer)\n\n"
        "This fallback demonstrates the agent interface works correctly."
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(run(sys.argv[1]))
    else:
        print("Usage: python agent.py 'your research task'")
