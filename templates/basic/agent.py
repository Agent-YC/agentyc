"""Basic agent entrypoint for {{AGENT_NAME}}."""


def run(task: str) -> str:
    """Execute the agent's main task.

    Args:
        task: The task description / prompt.

    Returns:
        The agent's response.
    """
    # TODO: Implement your agent logic here
    # This is where you connect to your LLM, use tools, and produce output.
    return f"Agent received task: {task}"


if __name__ == "__main__":
    import sys

    task = " ".join(sys.argv[1:]) or "Hello, world!"
    print(run(task))
