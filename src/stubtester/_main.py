import re
import shutil
import subprocess
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated, NamedTuple

import pyochain as pc
import typer
from rich.console import Console
from rich.panel import Panel

console = Console()


app = typer.Typer(
    name="doctester",
    help="Run doctests from stub files (.pyi) using pytest --doctest-modules",
)
TEMP_DIR = Path("doctests_temp")


@app.command()
def run(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to a file or directory containing stub files to test",
            parser=Path,
        ),
    ],
) -> pc.Result[str, str]:
    """Run all doctests in stub files (.pyi).

    This will discover all .pyi stub files and execute their doctests using pytest.

    Args:
        path (Path): Path to a file or directory containing stub files to test.

    Returns:
        pc.Result[str, str]: Ok with success message, or Err with error message.

    """
    _header(path)
    with _temp_test_dir() as temp_dir_result:
        return (
            temp_dir_result.and_then(
                lambda temp_dir: _path_exists(path).and_then(
                    lambda path: _get_pyi_files(path)
                    .filter_map(lambda file: _generate_test_file(file, temp_dir))
                    .collect()
                    .into(_check_generation)
                    .map(lambda _: _run_tests(temp_dir))
                    .and_then(_check_status)
                )
            )
            .inspect(console.print)
            .inspect_err(console.print)
        )


def _header(path: Path) -> None:
    return console.print(
        Panel.fit(
            f"[bold cyan]Doctester[/bold cyan]\n"
            f"Running tests in: [yellow]{path}[/yellow]",
            border_style="cyan",
        )
    )


def _path_exists(path: Path) -> pc.Result[Path, str]:
    if path.exists():
        return pc.Ok(path)
    return pc.Err(f"[bold red]✗ Error:[/bold red] Path '{path}' not found.")


@contextmanager
def _temp_test_dir() -> Generator[pc.Result[Path, str], None, None]:
    def _print_info(message: str) -> None:
        console.print(f"[cyan]i[/cyan] {message}")

    try:
        if TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)
        TEMP_DIR.mkdir()
        _print_info(f"Using temp directory: {TEMP_DIR.absolute()}")
        yield pc.Ok(TEMP_DIR)
    except (OSError, PermissionError) as e:
        yield pc.Err(f"Failed to create temp directory: {e}")
    finally:
        if TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)
            _print_info("Cleaned up temp directory.")


def _generate_test_file(file: Path, temp_dir: Path) -> pc.Option[Path]:
    test_file = temp_dir.joinpath(f"{file.stem}_test.py")
    return (
        _generate_test_module_content(file)
        .map(lambda content: test_file.write_text(content, encoding="utf-8"))
        .map(lambda _: test_file)
    )


def _generate_test_module_content(file: Path) -> pc.Option[str]:
    res = _get_blocks(file)
    if not res:
        return pc.NONE
    return pc.Some(f"# Generated tests from {file.name}\n\n" + res)


def _get_blocks(file: Path) -> str:
    return (
        pc.Iter(Patterns.BLOCK.findall(file.read_text(encoding="utf-8")))
        .map(lambda b: BlockTest(*b).to_func())
        .filter(lambda s: s.strip() != "")
        .join("\n")
    )


def _get_pyi_files(path: Path) -> pc.Iter[Path]:
    match path.is_file():
        case True:
            match path.suffix:
                case ".pyi":
                    return pc.Iter.once(path)
                case _:
                    return pc.Iter[Path].empty()
        case _:
            return pc.Iter(path.glob("**/*.pyi"))


def _check_generation(files: pc.Seq[Path]) -> pc.Result[None, str]:
    if files.length() == 0:
        return pc.Err("[yellow]Warning:[/yellow] No doctests found in stub files.")
    return pc.Ok(None)


def _check_status(exit_code: int) -> pc.Result[str, str]:
    if exit_code != 0:
        return pc.Err(f"[bold red]✗ Tests failed[/bold red] with exit code {exit_code}")
    return pc.Ok("[bold green]✓ All tests passed![/bold green]")


def _run_tests(temp_dir: Path) -> int:
    return subprocess.run(
        args=(
            "pytest",
            temp_dir.as_posix(),
            "--doctest-modules",
            "-v",
        ),
        check=False,
    ).returncode


class Patterns:
    """Regex patterns for parsing stub files."""

    BLOCK = re.compile(
        r"(?:def|class)\s+(\w+)(?:\[[^\]]*\])?\s*(?:\([^)]*\))?\s*(?:->[^:]+)?"
        r':\s*[rRbBfFuU]*"""(.*?)"""',
        re.DOTALL,
    )
    PY_CODE = re.compile(r"^\s*```\w*\s*$", flags=re.MULTILINE)

    @classmethod
    def clean(cls, docstring: str) -> str:
        return re.sub(cls.PY_CODE, "", docstring)


class BlockTest(NamedTuple):
    """Represents a testable block extracted from a stub file."""

    name: str
    """The name of the function or class."""
    docstring: str
    """The docstring associated with the function or class."""

    def to_func(self) -> str:
        """Convert the block into a test function string."""
        return f'''
def test_{self.name}():
    """{Patterns.clean(self.docstring)}"""
    pass
'''


if __name__ == "__main__":
    app()
