"""Docker agent entrypoint.

This script is packaged inside a Docker container.
It reads a task from stdin and prints the result to stdout.

Build:   docker build -t demo-agent .
Run:     echo "Research AI safety" | docker run -i --rm demo-agent
"""

import sys
import json


def process(task: str) -> str:
    """Process a task and return structured output."""
    return json.dumps({
        "output": (
            f"## Docker Agent Response\n\n"
            f"**Task**: {task[:200]}\n\n"
            f"Processed inside a sandboxed Docker container with:\n"
            f"- No network access (--network none)\n"
            f"- 512MB memory limit\n"
            f"- 1 CPU core\n\n"
            f"In production, this container would run your full agent stack "
            f"(LangChain, CrewAI, custom code) in complete isolation."
        ),
        "success": True,
        "metadata": {"runtime": "docker", "sandbox": True},
    })


if __name__ == "__main__":
    task = sys.stdin.read().strip()
    if task:
        print(process(task))
    else:
        print(json.dumps({"error": "No task provided via stdin"}))
