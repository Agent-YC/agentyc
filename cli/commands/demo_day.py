"""agent-yc demo-day — Simulator for YC Demo Day pitches and investments."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

console = Console()


@click.command("demo-day")
@click.option("--spec", default="agent.yml", help="Path to agent spec file.")
@click.pass_context
def demo_day(ctx: click.Context, spec: str) -> None:
    """Pitch your agent at Demo Day to raise simulated capital.

    Generates a pitch based on your agent spec and eval results, then
    presents it to three simulated elite investors (The Visionary,
    The Pragmatist, and The Cynic) to secure a Term Sheet.
    """
    spec_path = Path.cwd() / spec

    if not spec_path.exists():
        console.print(f"[red]✗[/red] Agent spec not found: {spec}")
        raise SystemExit(1)

    # Parse spec
    from core.spec import parse_spec

    try:
        agent_spec = parse_spec(spec_path)
    except ValueError as e:
        console.print(f"[red]✗ Spec validation failed:[/red]\n{e}")
        raise SystemExit(1)

    # Check if agent is graduated or has an eval
    from core.db import get_db

    db = get_db()
    eval_result_dict = db.get_latest_eval(agent_spec.id)
    db.close()

    if not eval_result_dict:
        console.print(
            "[red]✗[/red] You cannot pitch at Demo Day without an evaluation."
        )
        console.print("  Run [bold]agent-yc eval[/bold] first to build traction.")
        raise SystemExit(1)

    # Reconstruct EvalResult structurally
    from core.eval_engine import EvalResult
    from core.scorer import Scorecard

    scores = eval_result_dict.get("score_overall", 0)
    if scores < 75:
        console.print(f"[yellow]⚠[/yellow] Your agent only scored {scores}/100.")
        console.print(
            "  YC Partners recommend a score of 75+ (Graduated) before Demo Day."
        )
        console.print("  [dim]But we'll let you pitch anyway... good luck.[/dim]\n")

    # Connect to Ollama
    from cli.ollama import OllamaClient
    from cli.config import get_config

    config = get_config()
    model = ctx.obj.get("model") or config.default_model
    ollama = OllamaClient(base_url=config.ollama_url, model=model)

    if not ollama.is_available():
        console.print(
            "[red]✗[/red] Ollama is not running.\n"
            "  Start it with: [bold]ollama serve[/bold]"
        )
        raise SystemExit(1)

    from core.demo_day import simulate_demo_day

    eval_mock = EvalResult(
        agent_id=agent_spec.id,
        scorecard=Scorecard(
            reliability=eval_result_dict.get("score_reliability", 0),
            cost=eval_result_dict.get("score_cost", 0),
            safety=eval_result_dict.get("score_safety", 0),
            speed=eval_result_dict.get("score_speed", 0),
        ),
    )

    console.print(
        f"[dim]Stepping onto the stage at Pier 48... Pitching [bold]{agent_spec.name}[/bold].[/dim]"
    )

    with console.status("[bold cyan]Delivering pitch to investors...", spinner="dots"):
        result = simulate_demo_day(agent_spec, eval_mock, ollama)

    console.print()

    # 1. Show the Pitch
    console.print(
        Panel(
            Markdown(result.pitch),
            title=f"[bold cyan]🎤 {agent_spec.name} - Demo Day Pitch[/bold cyan]",
            border_style="cyan",
        )
    )
    console.print()

    # 2. Show the Investors
    console.print("[bold]💼 Investor Feedback:[/bold]")
    console.print(f" [magenta]The Visionary:[/magenta]  {result.visionary_comment}")
    console.print(f" [blue]The Pragmatist:[/blue] {result.pragmatist_comment}")
    console.print(f" [red]The Cynic:[/red]      {result.cynic_comment}")
    console.print()

    # 3. Term Sheet
    def format_money(amount: int) -> str:
        if amount >= 1000000:
            return f"${amount / 1000000:.1f}M"
        return f"${amount:,}"

    cap_str = format_money(result.valuation_cap)
    raised_str = format_money(result.investment_raised)

    table = Table(
        title="📝 YC Term Sheet (Simulated)",
        border_style="gold3",
        title_style="bold gold3",
    )
    table.add_column("Terms", style="bold")
    table.add_column("Value", justify="right", style="green bold")

    table.add_row("Standard Deal", f"{raised_str} on MFN SAFE")
    table.add_row("Seed Valuation Cap", cap_str)
    table.add_row("Hype Factor", f"{result.investment_hype}/10")

    console.print(table)
    console.print(
        "\n[dim italic]Congratulations! Don't spend it all on H100s...[/dim italic]\n"
    )
