"""agent-yc init — scaffold a new agent project."""

from __future__ import annotations

import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel

console = Console()

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"


@click.command("init")
@click.argument("name", default="my-agent")
@click.option(
    "--template",
    "-t",
    type=click.Choice(["basic", "tool-heavy", "multi-step", "langchain", "crewai", "docker"]),
    default="basic",
    help="Agent template to use.",
)
def init_cmd(name: str, template: str) -> None:
    """Scaffold a new agent project.

    Creates a directory with agent.yml, agent.py, and .agentyc/ directory.
    """
    target = Path.cwd() / name

    if target.exists():
        console.print(f"[red]✗[/red] Directory '{name}' already exists.")
        raise SystemExit(1)

    # Create project structure
    target.mkdir(parents=True)
    (target / ".agentyc").mkdir()

    # Copy template files
    template_dir = TEMPLATES_DIR / template
    if template_dir.exists():
        for src in template_dir.iterdir():
            if src.is_file():
                content = src.read_text(encoding="utf-8")
                # Replace template placeholder with project name
                content = content.replace("{{AGENT_NAME}}", name)
                content = content.replace("{{agent_name}}", name.lower().replace("-", "_"))
                (target / src.name).write_text(content, encoding="utf-8")
    else:
        # Inline basic template as fallback
        _write_basic_template(target, name)

    console.print()
    console.print(
        Panel(
            f"[green bold]✓ Agent project created:[/green bold] {name}/\n\n"
            f"  [dim]├──[/dim] agent.yml    [dim]  # Agent spec — edit this[/dim]\n"
            f"  [dim]├──[/dim] agent.py     [dim]  # Agent entrypoint[/dim]\n"
            f"  [dim]└──[/dim] .agentyc/    [dim]  # Local data[/dim]\n\n"
            f"[bold]Next steps:[/bold]\n"
            f"  cd {name}\n"
            f"  agent-yc screen      [dim]# Check if your spec is ready[/dim]\n"
            f"  agent-yc eval        [dim]# Run evaluation suite[/dim]\n"
            f"  agent-yc coach       [dim]# Get coaching feedback[/dim]",
            title="[bold cyan]Agent YC[/bold cyan]",
            border_style="cyan",
        )
    )


def _write_basic_template(target: Path, name: str) -> None:
    """Write a basic agent template directly."""
    agent_yml = f"""\
name: {name}
version: 0.1.0
author: ""
description: >
  Describe what your agent does. Be specific about its capabilities,
  the problems it solves, and how it uses its tools.
tools:
  - web_search
constraints:
  max_cost_per_task: 0.05
  max_latency: 30s
  safety_level: standard
expected_behaviors:
  - "Always cite sources"
  - "Stay within token budget"
entrypoint: ./agent.py
"""
    (target / "agent.yml").write_text(agent_yml, encoding="utf-8")

    agent_py = f'''\
"""Agent entrypoint for {name}."""


def run(task: str) -> str:
    """Execute the agent's main task.

    Args:
        task: The task description / prompt.

    Returns:
        The agent's response.
    """
    # TODO: Implement your agent logic here
    return f"Agent {{task=}} is not yet implemented."


if __name__ == "__main__":
    import sys
    task = " ".join(sys.argv[1:]) or "Hello, world!"
    print(run(task))
'''
    (target / "agent.py").write_text(agent_py, encoding="utf-8")
