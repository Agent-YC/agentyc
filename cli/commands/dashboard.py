"""Dashboard command."""

import click
import uvicorn
from rich.console import Console

console = Console()

@click.command()
@click.option("--port", default=8000, help="Port to run the dashboard on.")
@click.option("--host", default="127.0.0.1", help="Host interface to bind to.")
def dashboard(port: int, host: str) -> None:
    """Launch the Agent YC Dashboard locally."""
    console.print(f"[bold green]Starting Agent YC Dashboard on http://{host}:{port}[/]")
    console.print("[dim]Press Ctrl+C to stop.[/]")
    
    # We run uvicorn programmatically
    uvicorn.run("api.server:app", host=host, port=port, log_level="info")
