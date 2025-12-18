"""Console utilities for rich output."""

from rich.console import Console

console = Console()


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[cyan]i[/cyan] {message}")
