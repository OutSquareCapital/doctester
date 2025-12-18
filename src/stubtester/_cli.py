"""CLI interface for doctester using Typer and Rich."""

from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel

from ._main import console, run_doctester, run_on_file

app = typer.Typer(
    name="doctester",
    help="Run doctests from stub files (.pyi) using pytest --doctest-modules",
    add_completion=False,
)
VerboseArg = Annotated[
    bool,
    typer.Option("--verbose", "-v", help="Enable verbose output"),
]


@app.command()
def run(
    root_dir: Annotated[
        str,
        typer.Argument(help="Root directory containing stub files to test"),
    ] = "src",
    *,
    verbose: VerboseArg = False,
) -> None:
    """Run all doctests in stub files (.pyi).

    This will discover all .pyi stub files and execute their doctests using pytest.
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Doctester[/bold cyan]\n"
            f"Running tests in: [yellow]{root_dir}[/yellow]",
            border_style="cyan",
        )
    )

    exit_code = run_doctester(root_dir, verbose=verbose)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


@app.command()
def file(
    file_path: Annotated[
        Path,
        typer.Argument(help="Path to a single .pyi stub file to test"),
    ],
    *,
    verbose: VerboseArg = False,
) -> None:
    """Run doctests in a single stub file.

    Only .pyi stub files are supported.
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Doctester[/bold cyan]\n"
            f"Testing file: [yellow]{file_path}[/yellow]",
            border_style="cyan",
        )
    )

    exit_code = run_on_file(file_path, verbose=verbose)
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


if __name__ == "__main__":
    app()
