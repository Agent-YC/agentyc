"""LangChain research agent demo.

Shows how to integrate a LangChain agent with Agent YC.
This agent uses a simple LLM chain with Ollama.

Requirements:
    pip install langchain langchain-community

Usage with Agent YC:
    agent-yc screen    # Screen the spec
    agent-yc eval      # Evaluate the agent

Usage with the runner directly:
    from core.runner import run_langchain_agent
    result = run_langchain_agent(build_agent(), "Summarize quantum computing")
"""

import sys

try:
    from langchain_community.llms import Ollama
    from langchain.prompts import PromptTemplate
    from langchain.chains import LLMChain

    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False


RESEARCH_PROMPT = PromptTemplate(
    input_variables=["task"],
    template="""You are a research agent. Your job is to analyze the given task
and provide a thorough, well-structured research response.

Rules:
- Always cite your sources (even if simulated)
- Flag any claims with low confidence
- Detect contradictions between sources
- Never fabricate information — say "I don't know" if unsure
- Be concise but comprehensive

Task: {task}

Provide your research response:""",
)


def build_agent():
    """Build and return the LangChain agent.

    Returns a LangChain Chain that can be passed to
    run_langchain_agent() from core.runner.
    """
    if not HAS_LANGCHAIN:
        raise ImportError(
            "LangChain is required. Install with:\n"
            "  pip install langchain langchain-community"
        )

    llm = Ollama(model="llama3.2", temperature=0.3)
    chain = LLMChain(llm=llm, prompt=RESEARCH_PROMPT)
    return chain


def run(task: str) -> str:
    """Entry point for Agent YC's Python runner.

    Agent YC calls this function when the entrypoint is ./agent.py.
    """
    if not HAS_LANGCHAIN:
        # Fallback: run without LangChain for testing
        return _fallback_response(task)

    agent = build_agent()
    result = agent.run(task=task)
    return result


def _fallback_response(task: str) -> str:
    """Fallback when LangChain is not installed."""
    return (
        "## LangChain Agent Response (fallback mode)\n\n"
        f"**Task**: {task[:200]}\n\n"
        "LangChain is not installed. Install with:\n"
        "```\npip install langchain langchain-community\n```\n\n"
        "In production, this agent would:\n"
        "1. Send the task to Ollama via LangChain's LLM interface\n"
        "2. Use a research-focused prompt template\n"
        "3. Return structured, cited research output\n\n"
        "This fallback demonstrates the agent interface works correctly."
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(run(sys.argv[1]))
    else:
        print("Usage: python agent.py 'your research task'")
