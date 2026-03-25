"""Agent YC CLI — main entrypoint.

Usage:  agent-yc [COMMAND] [OPTIONS]
"""

import click

from core import __version__


@click.group()
@click.version_option(version=__version__, prog_name="agent-yc")
@click.option("--model", default=None, help="Override the default Ollama model.")
@click.pass_context
def cli(ctx: click.Context, model: str | None) -> None:
    """Agent YC — An AI-powered accelerator for AI agents.

    Screen, evaluate, and coach your AI agents locally using Ollama,
    or connect to the cloud for verified scores and pro coaching.
    """
    ctx.ensure_object(dict)
    if model:
        ctx.obj["model"] = model


# ---- Register subcommands ---------------------------------------------------
# ruff: noqa: E402

from cli.commands.init_cmd import init_cmd
from cli.commands.screen import screen
from cli.commands.eval import eval_cmd
from cli.commands.coach import coach
from cli.commands.leaderboard import leaderboard
from cli.commands.publish import publish

cli.add_command(init_cmd, "init")
cli.add_command(screen)
cli.add_command(eval_cmd, "eval")
cli.add_command(coach)
cli.add_command(leaderboard)
cli.add_command(publish)


if __name__ == "__main__":
    cli()
