"""Console utilities for rich output."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from ._models import TestResult

console = Console()


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[cyan]i[/cyan] {message}")


def create_results_table(py_result: TestResult, pyi_result: TestResult) -> Table:
    """Create a formatted results table."""
    table = Table(title="Test Results", show_header=True, header_style="bold cyan")
    table.add_column("File Type", style="cyan")
    table.add_column("Total", justify="right")
    table.add_column("Passed", justify="right", style="green")
    table.add_column("Failed", justify="right", style="red")

    table.add_row(
        ".py", str(py_result.total), str(py_result.passed), str(py_result.failed)
    )
    table.add_row(
        ".pyi", str(pyi_result.total), str(pyi_result.passed), str(pyi_result.failed)
    )
    table.add_row(
        "[bold]Total[/bold]",
        f"[bold]{py_result.total + pyi_result.total}[/bold]",
        f"[bold green]{py_result.passed + pyi_result.passed}[/bold green]",
        f"[bold red]{py_result.failed + pyi_result.failed}[/bold red]",
    )

    return table


def print_test_summary(py_result: TestResult, pyi_result: TestResult) -> None:
    """Print a formatted summary table of test results."""
    if py_result.total > 0 or pyi_result.total > 0:
        console.print("")
        console.print(create_results_table(py_result, pyi_result))
