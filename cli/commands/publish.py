"""agent-yc publish — publish an agent to the marketplace (cloud, Phase 4)."""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel

console = Console()


@click.command()
def publish() -> None:
    """Publish your graduated agent to the marketplace.

    Requires a verified evaluation and Pro subscription.
    Coming in a future release.
    """
    console.print(
        Panel(
            "[bold]The Agent YC Marketplace is coming soon![/bold]\n\n"
            "Once available, you'll be able to publish graduated agents\n"
            "for others to discover, install, and license.\n\n"
            "[dim]Requirements:[/dim]\n"
            "  • Agent must be graduated (score ≥ 75)\n"
            "  • Eval must be verified (cloud)\n"
            "  • Pro subscription required\n\n"
            "[dim]Revenue models:[/dim]\n"
            "  • Free / Open Source\n"
            "  • Subscription (85/15 split)\n"
            "  • Per-use (85/15 split)\n\n"
            "Stay tuned for updates at [cyan]https://agentyc.com[/cyan]",
            title="[bold cyan]📦 Marketplace[/bold cyan]",
            border_style="yellow",
        )
    )
