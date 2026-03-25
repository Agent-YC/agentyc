"""agent-yc eval — run the evaluation suite against an agent."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.command("eval")
@click.option("--spec", default="agent.yml", help="Path to agent spec file.")
@click.option("--challenge", "-c", default=None, help="Run a specific challenge by ID.")
@click.option("--ci", is_flag=True, help="CI mode — exit code 1 if score below threshold.")
@click.option("--min-score", default=75, type=int, help="Minimum overall score for CI mode.")
@click.option("--verify", is_flag=True, help="Submit for verified cloud evaluation (requires login).")
@click.pass_context
def eval_cmd(
    ctx: click.Context,
    spec: str,
    challenge: str | None,
    ci: bool,
    min_score: int,
    verify: bool,
) -> None:
    """Run the evaluation suite against your agent.

    Executes challenges across reliability, cost, safety, and speed dimensions.
    Produces a scorecard with an overall composite score.
    """
    if verify:
        console.print(
            "[yellow]⚠[/yellow]  Verified evaluations are coming in a future release.\n"
            "  Use [bold]agent-yc eval[/bold] for local evaluation."
        )
        raise SystemExit(0)

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

    # Load challenges
    from core.eval_engine import load_challenges, run_eval, run_challenge
    from core.scorer import is_graduated, grade_label

    if challenge:
        all_challenges = load_challenges()
        matches = [c for c in all_challenges if c.id == challenge]
        if not matches:
            console.print(f"[red]✗[/red] Challenge not found: {challenge}")
            console.print("[dim]Available challenges:[/dim]")
            for c in all_challenges:
                console.print(f"  - {c.id}")
            raise SystemExit(1)
        challenges = matches
    else:
        challenges = load_challenges()

    if not challenges:
        console.print("[yellow]⚠[/yellow]  No challenges found in registry.")
        raise SystemExit(1)

    # Run eval
    console.print(
        f"[bold cyan]Evaluating[/bold cyan] [bold]{agent_spec.name}[/bold] "
        f"[dim]({len(challenges)} challenges, model: {model})[/dim]"
    )
    console.print()

    with console.status("[bold cyan]Running evaluation...", spinner="dots"):
        result = run_eval(agent_spec, challenges=challenges, ollama=ollama)

    # Display challenge results
    ch_table = Table(title="Challenge Results", border_style="dim")
    ch_table.add_column("Challenge", style="bold")
    ch_table.add_column("Category", style="dim")
    ch_table.add_column("Status", justify="center")
    ch_table.add_column("Score", justify="right")
    ch_table.add_column("Time", justify="right", style="dim")

    for cr in result.challenges:
        status = "[green]✓ PASS[/green]" if cr.passed else "[red]✗ FAIL[/red]"
        ch_table.add_row(
            cr.name,
            cr.challenge_id.split("/")[0] if "/" in cr.challenge_id else "",
            status,
            f"{cr.score}/100",
            f"{cr.duration_seconds:.1f}s",
        )

    console.print(ch_table)
    console.print()

    # Display scorecard
    scores = result.scorecard
    graduated = is_graduated(scores)
    grade = grade_label(scores)

    score_table = Table(title="Scorecard", border_style="dim")
    score_table.add_column("Dimension", style="bold")
    score_table.add_column("Score", justify="right")
    score_table.add_column("Weight", justify="right", style="dim")
    score_table.add_column("Bar", min_width=20)

    def _bar(score: int) -> str:
        filled = score // 5
        color = "green" if score >= 75 else "yellow" if score >= 50 else "red"
        return f"[{color}]{'█' * filled}[/{color}][dim]{'░' * (20 - filled)}[/dim]"

    score_table.add_row("Reliability", f"{scores.reliability}", "30%", _bar(scores.reliability))
    score_table.add_row("Safety", f"{scores.safety}", "25%", _bar(scores.safety))
    score_table.add_row("Cost", f"{scores.cost}", "25%", _bar(scores.cost))
    score_table.add_row("Speed", f"{scores.speed}", "20%", _bar(scores.speed))
    score_table.add_row("─" * 12, "─" * 5, "─" * 6, "─" * 20)
    score_table.add_row(
        "[bold]Overall[/bold]",
        f"[bold]{scores.overall}[/bold]",
        "",
        _bar(scores.overall),
    )

    console.print(score_table)
    console.print()

    # Graduation status
    grad_color = "green" if graduated else "red"
    console.print(
        Panel(
            f"Grade: [bold]{grade}[/bold]  |  "
            f"Overall: [bold]{scores.overall}/100[/bold]  |  "
            f"Status: [{grad_color} bold]"
            f"{'GRADUATED ✓' if graduated else 'NOT GRADUATED ✗'}"
            f"[/{grad_color} bold]",
            title=f"[bold]{agent_spec.name}[/bold]",
            border_style=grad_color,
        )
    )

    # Save eval result
    agentyc_dir = Path.cwd() / ".agentyc" / "evals"
    agentyc_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    result_file = agentyc_dir / f"{agent_spec.id}_{ts}.json"
    result_file.write_text(
        json.dumps(result.to_dict(), indent=2),
        encoding="utf-8",
    )
    console.print(f"\n[dim]Result saved to {result_file}[/dim]")

    # Also save to local DB
    from core.db import get_db

    db = get_db()
    db.save_agent(
        agent_spec.id,
        agent_spec.name,
        agent_spec._raw_yaml,
        description=agent_spec.description,
        author=agent_spec.author,
        status="graduated" if graduated else "evaluated",
    )
    db.save_eval(
        agent_spec.id,
        scores=scores.to_dict(),
        challenges=[
            {"id": c.challenge_id, "name": c.name, "passed": c.passed, "score": c.score}
            for c in result.challenges
        ],
        meta=result.meta,
    )
    db.close()

    # CI mode exit code
    if ci and scores.overall < min_score:
        console.print(
            f"\n[red bold]CI FAIL:[/red bold] Overall score {scores.overall} "
            f"< required {min_score}"
        )
        raise SystemExit(1)
