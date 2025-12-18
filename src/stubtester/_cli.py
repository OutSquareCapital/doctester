"""CLI interface for doctester using Typer and Rich."""

from pathlib import Path
from typing import Annotated

import typer
from rich.panel import Panel

from ._main import console, run_tests

app = typer.Typer(
    name="doctester",
    help="Run doctests from stub files (.pyi) using pytest --doctest-modules",
    add_completion=False,
)
PathArg = Annotated[
    Path,
    typer.Argument(
        help="Path to a file or directory containing stub files to test", parser=Path
    ),
]


@app.command()
def run(path: PathArg) -> None:
    """Run all doctests in stub files (.pyi).

    This will discover all .pyi stub files and execute their doctests using pytest.
    """
    console.print(
        Panel.fit(
            f"[bold cyan]Doctester[/bold cyan]\n"
            f"Running tests in: [yellow]{path}[/yellow]",
            border_style="cyan",
        )
    )

    def _handle_err(msg: str) -> None:
        console.print(msg)
        raise typer.Exit(1)

    run_tests(path).map_or_else(
        ok=lambda _: console.print("[bold green]✓ All tests passed![/bold green]"),
        err=_handle_err,
    )


if __name__ == "__main__":
    app()
