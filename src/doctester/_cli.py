"""CLI interface for doctester using Typer and Rich."""

from pathlib import Path
from typing import Annotated

import pyochain as pc
import typer
from rich.console import Console
from rich.panel import Panel

from . import _main

app = typer.Typer(
    name="doctester",
    help="Run doctests from Python files (.py) and stub files (.pyi)",
    add_completion=False,
)
console = Console()

VerboseArg = Annotated[
    bool,
    typer.Option("--verbose", "-v", help="Enable verbose output"),
]


@app.command()
def run(
    root_dir: Annotated[
        str,
        typer.Argument(help="Root directory containing the package to test"),
    ] = "src",
    *,
    verbose: VerboseArg = False,
) -> None:
    """Run all doctests in a package directory.

    This will discover all Python modules and stub files, then execute their doctests.
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Doctester[/bold cyan]\n"
            f"Running tests in: [yellow]{root_dir}[/yellow]",
            border_style="cyan",
        )
    )

    result = _main.run_doctester(root_dir, verbose=verbose)

    match result:
        case pc.Ok(test_result):
            if test_result.failed > 0:
                console.print(
                    f"\n[bold red]✗ {test_result.failed} test(s) failed[/bold red]"
                )
                raise typer.Exit(code=1)
            console.print("\n[bold green]✓ All tests passed![/bold green]")
        case pc.Err(error):
            console.print(f"\n[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1)


@app.command()
def file(
    file_path: Annotated[
        Path,
        typer.Argument(help="Path to a single .py or .pyi file to test"),
    ],
    *,
    verbose: VerboseArg = False,
) -> None:
    """Run doctests in a single Python file.

    Supports both .py and .pyi files.
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Doctester[/bold cyan]\n"
            f"Testing file: [yellow]{file_path}[/yellow]",
            border_style="cyan",
        )
    )

    result = _main.run_on_file(file_path, verbose=verbose)

    match result:
        case pc.Ok(test_result):
            if test_result.failed > 0:
                console.print(
                    f"\n[bold red]✗ {test_result.failed} test(s) failed[/bold red]"
                )
                raise typer.Exit(code=1)
            console.print("\n[bold green]✓ All tests passed![/bold green]")
        case pc.Err(error):
            console.print(f"\n[bold red]Error:[/bold red] {error}")
            raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
