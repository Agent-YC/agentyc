"""agent-yc coach — get coaching feedback on your agent."""

from __future__ import annotations

from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

console = Console()


@click.command()
@click.argument("question", required=False, default=None)
@click.option("--spec", default="agent.yml", help="Path to agent spec file.")
@click.option(
    "--pro", is_flag=True, help="Use Pro Coach (requires cloud subscription)."
)
@click.pass_context
def coach(ctx: click.Context, question: str | None, spec: str, pro: bool) -> None:
    """Get coaching feedback — like a YC partner in office hours.

    Without a question, enters an interactive coaching session.
    With a question, gives a single-shot answer.
    """
    if pro:
        console.print(
            "[yellow]⚠[/yellow]  Pro coaching is coming in a future release.\n"
            "  Using local coach via Ollama."
        )

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

    # Load latest eval result if available
    from core.db import get_db

    db = get_db()
    eval_result = None
    latest_eval = db.get_latest_eval(agent_spec.id)
    if latest_eval:
        from core.eval_engine import EvalResult, ChallengeResult
        from core.scorer import Scorecard

        eval_result = EvalResult(
            agent_id=agent_spec.id,
            scorecard=Scorecard.from_dict(
                {
                    "reliability": latest_eval["score_reliability"],
                    "cost": latest_eval["score_cost"],
                    "safety": latest_eval["score_safety"],
                    "speed": latest_eval["score_speed"],
                    "overall": latest_eval["score_overall"],
                }
            ),
            challenges=[
                ChallengeResult(
                    challenge_id=c.get("id", ""),
                    name=c.get("name", ""),
                    passed=c.get("passed", False),
                    score=c.get("score", 0),
                )
                for c in latest_eval.get("challenges", [])
            ],
        )
    db.close()

    from core.coach import get_coaching, get_coaching_chat

    if question:
        # Single-shot mode
        console.print(f"[bold cyan]Coach[/bold cyan] [dim](model: {model})[/dim]\n")
        with console.status("[bold cyan]Thinking...", spinner="dots"):
            response = get_coaching(agent_spec, eval_result, question, ollama)

        console.print(
            Panel(
                Markdown(response),
                title="[bold cyan]🎯 Coach Feedback[/bold cyan]",
                border_style="cyan",
            )
        )
    else:
        # Interactive mode
        console.print(
            Panel(
                "[bold]Welcome to Coach Mode[/bold]\n\n"
                f"Agent: [cyan]{agent_spec.name}[/cyan]\n"
                f"Model: [dim]{model}[/dim]\n\n"
                "Ask questions about your agent. Type [bold]quit[/bold] to exit.",
                title="[bold cyan]🎯 Agent YC Coach[/bold cyan]",
                border_style="cyan",
            )
        )

        messages: list[dict[str, str]] = []

        while True:
            console.print()
            try:
                user_input = click.prompt(
                    click.style("You", fg="green", bold=True),
                    prompt_suffix=" › ",
                )
            except (click.Abort, EOFError):
                break

            if user_input.lower() in ("quit", "exit", "q"):
                break

            messages.append({"role": "user", "content": user_input})

            with console.status("[bold cyan]Thinking...", spinner="dots"):
                response = get_coaching_chat(agent_spec, eval_result, messages, ollama)

            messages.append({"role": "assistant", "content": response})

            console.print()
            console.print(
                Panel(
                    Markdown(response),
                    title="[bold cyan]Coach[/bold cyan]",
                    border_style="cyan",
                )
            )

        # Save session
        if messages:
            db = get_db()
            db.save_coach_session(agent_spec.id, messages, mode="local")
            db.close()
            console.print("\n[dim]Session saved.[/dim]")

        console.print("[dim]Goodbye![/dim]")
