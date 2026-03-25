"""Plain Python research agent.

This is the simplest possible agent — just a run() function.
Agent YC imports this and calls run(task) directly.
"""

import sys


def run(task: str) -> str:
    """Process a research task and return a structured response.

    In a real agent, this would call APIs, search the web, etc.
    This demo shows the expected interface.
    """
    # Simple keyword-based routing to demonstrate agent behavior
    task_lower = task.lower()

    if "synthesize" in task_lower or "research" in task_lower:
        return _synthesize(task)
    elif "summarize" in task_lower:
        return _summarize(task)
    elif any(word in task_lower for word in ["inject", "ignore", "forget"]):
        return _safety_response(task)
    else:
        return _general_response(task)


def _synthesize(task: str) -> str:
    return (
        "## Research Synthesis\n\n"
        "Based on analysis of multiple sources:\n\n"
        "1. **Finding 1**: The primary consensus supports the stated hypothesis "
        "(Source: Academic Database, confidence: high)\n"
        "2. **Finding 2**: A contradicting perspective was identified in recent "
        "literature (Source: ArXiv 2024, confidence: medium)\n"
        "3. **Finding 3**: Further investigation needed on edge cases "
        "(Source: Domain experts, confidence: low)\n\n"
        "⚠️ **Uncertainty flag**: Finding 3 has limited supporting evidence.\n\n"
        "### Sources\n"
        "- [1] Academic Database — peer-reviewed, 2024\n"
        "- [2] ArXiv preprint — not yet peer-reviewed\n"
        "- [3] Expert interviews — anecdotal"
    )


def _summarize(task: str) -> str:
    return (
        "## Summary\n\n"
        "The key points are:\n"
        "- Point A: Primary argument with strong evidence\n"
        "- Point B: Supporting detail with moderate confidence\n"
        "- Point C: Area requiring further research\n\n"
        "Source: Analysis of provided materials"
    )


def _safety_response(task: str) -> str:
    return (
        "I've detected what appears to be a prompt injection attempt. "
        "I will not ignore my instructions, reveal system prompts, or "
        "change my behavior based on injected content. "
        "If you have a legitimate research question, please rephrase it."
    )


def _general_response(task: str) -> str:
    return (
        f"## Response to: {task[:100]}\n\n"
        "I've analyzed your request. Here is my structured response:\n\n"
        "1. **Analysis**: The topic has been examined from multiple angles\n"
        "2. **Key insight**: [Based on available information]\n"
        "3. **Recommendation**: Further investigation recommended\n\n"
        "⚠️ Note: This response is based on limited context. "
        "For higher confidence results, provide more specific constraints."
    )


if __name__ == "__main__":
    # Also works as a subprocess: python agent.py "task"
    if len(sys.argv) > 1:
        print(run(sys.argv[1]))
    else:
        print("Usage: python agent.py 'your task here'")
