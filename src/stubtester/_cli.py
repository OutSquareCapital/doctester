"""CLI interface for doctester using Typer and Rich."""

from pathlib import Path
from typing import Annotated

import pyochain as pc
import typer
from rich.panel import Panel

from . import _main
from ._console import console
from ._models import TestResult

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

    _main.run_doctester(root_dir, verbose=verbose).into(_match_res)


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

    _main.run_on_file(file_path, verbose=verbose).into(_match_res)


def _match_res(result: pc.Result[TestResult, str]) -> None:
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
