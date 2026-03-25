"""agent-yc screen — run the screening agent on an agent spec."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.command()
@click.option("--spec", default="agent.yml", help="Path to agent spec file.")
@click.pass_context
def screen(ctx: click.Context, spec: str) -> None:
    """Screen your agent spec for batch admission.

    Runs a local screening agent via Ollama that evaluates your agent's
    spec for clarity, feasibility, safety, and market fit.
    """
    spec_path = Path.cwd() / spec

    if not spec_path.exists():
        console.print(f"[red]✗[/red] Agent spec not found: {spec}")
        console.print("  Run [bold]agent-yc init[/bold] to create a new agent project.")
        raise SystemExit(1)

    # Parse spec
    from core.spec import parse_spec

    console.print("[dim]Parsing agent spec...[/dim]")
    try:
        agent_spec = parse_spec(spec_path)
    except ValueError as e:
        console.print(f"[red]✗ Spec validation failed:[/red]\n{e}")
        raise SystemExit(1)

    # Connect to Ollama
    from cli.ollama import OllamaClient
    from cli.config import get_config

    config = get_config()
    model = ctx.obj.get("model") or config.default_model
    ollama = OllamaClient(base_url=config.ollama_url, model=model)

    if not ollama.is_available():
        console.print(
            "[red]✗[/red] Ollama is not running.\n"
            "  Start it with: [bold]ollama serve[/bold]\n"
            "  Pull a model with: [bold]ollama pull llama3.2[/bold]"
        )
        raise SystemExit(1)

    # Run screening
    console.print(
        f"[dim]Screening [bold]{agent_spec.name}[/bold] with {model}...[/dim]"
    )
    with console.status("[bold cyan]Screening agent...", spinner="dots"):
        from core.screener import screen_agent

        result = screen_agent(agent_spec, ollama)

    # Display result
    verdict_colors = {
        "ADMIT": "green",
        "CONDITIONAL": "yellow",
        "REJECT": "red",
    }
    color = verdict_colors.get(result.verdict, "white")

    console.print()

    # Scores table
    table = Table(title="Screening Scores", border_style="dim")
    table.add_column("Criterion", style="bold")
    table.add_column("Score", justify="right")
    table.add_column("Weight", justify="right", style="dim")

    table.add_row("Clarity", f"{result.clarity}/100", "25%")
    table.add_row("Feasibility", f"{result.feasibility}/100", "25%")
    table.add_row("Safety", f"{result.safety}/100", "30%")
    table.add_row("Market Fit", f"{result.market_fit}/100", "20%")
    table.add_row("─" * 12, "─" * 7, "─" * 6)
    table.add_row("[bold]Overall[/bold]", f"[bold]{result.overall}/100[/bold]", "")

    console.print(table)
    console.print()

    # Verdict
    console.print(
        Panel(
            f"[{color} bold]{result.verdict}[/{color} bold]\n\n{result.feedback}",
            title=f"[bold]Verdict: {agent_spec.name}[/bold]",
            border_style=color,
        )
    )

    # Save result
    agentyc_dir = Path.cwd() / ".agentyc" / "screenings"
    agentyc_dir.mkdir(parents=True, exist_ok=True)

    import json
    from datetime import datetime, timezone

    result_file = agentyc_dir / f"{agent_spec.id}.json"
    result_file.write_text(
        json.dumps(
            {**result.to_dict(), "timestamp": datetime.now(timezone.utc).isoformat()},
            indent=2,
        ),
        encoding="utf-8",
    )
    console.print(f"\n[dim]Result saved to {result_file}[/dim]")
