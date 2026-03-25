"""agent-yc leaderboard — view the public leaderboard (cloud, Phase 3)."""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.command()
def leaderboard() -> None:
    """View the public agent leaderboard.

    Shows top-performing verified agents across all batches.
    Requires a cloud account (coming in a future release).
    """
    console.print(
        Panel(
            "[bold]The Agent YC Leaderboard is coming soon![/bold]\n\n"
            "The public leaderboard will show verified agents ranked by\n"
            "overall score across batches.\n\n"
            "[dim]Features planned:[/dim]\n"
            "  • Verified agent rankings\n"
            "  • Batch-specific views\n"
            "  • Percentile comparisons\n"
            "  • Score breakdowns by dimension\n\n"
            "Stay tuned for updates at [cyan]https://agentyc.com[/cyan]",
            title="[bold cyan]🏆 Leaderboard[/bold cyan]",
            border_style="yellow",
        )
    )
