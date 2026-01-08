import shutil
import subprocess
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Annotated

import pyochain as pc
import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from ._blocks import parse_markdown

console = Console()


app = typer.Typer(
    name="doctester",
    help="Run doctests from stub files (.pyi) using pytest --doctest-modules",
)
TEMP_DIR = Path("doctests_temp")
IGNORED_PATHS: set[str] = {
    ".venv",
    "venv",
    ".env",
    "env",
    ".git",
    ".github",
    ".hg",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".coverage",
    "build",
    "dist",
    ".eggs",
    ".egg-info",
    ".idea",
    ".vscode",
    ".DS_Store",
}
"""Common directory and file names to ignore when searching for stub files."""


@app.command()
def run(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to a file or directory containing files to test",
            parser=Path,
        ),
    ],
    keep: Annotated[  # noqa: FBT002
        bool,
        typer.Option(
            "--keep",
            help="Keep the temporary test files for debugging purposes",
        ),
    ] = False,
) -> pc.Result[Text, Text]:
    """Run all doctests in stub files (.pyi) or markdown files (.md).

    This will discover and execute their doctests using pytest with dynamically generated .py files.

    Args:
        path (Path): Path to a file or directory containing stub files to test.
        keep (bool): If True, keep the temporary test files for debugging.

    Returns:
        pc.Result[str, str]: Ok with success message, or Err with error message.

    """
    _header(path)
    with _temp_test_dir(keep=keep) as temp_dir_result:
        return temp_dir_result.and_then(lambda temp_dir: _execute_tests(temp_dir, path))


def _header(path: Path) -> None:
    content = (
        Text()
        .append(Text("Doctester", style="bold cyan"))
        .append("\nRunning tests in: ")
        .append(path.absolute().as_posix(), style="yellow")
    )
    return console.print(
        Panel.fit(
            content,
            border_style="cyan",
        )
    )


@contextmanager
def _temp_test_dir(
    *, keep: bool = False
) -> Generator[pc.Result[Path, Text], None, None]:
    def _print_info(message: Text) -> None:
        text = Text("i ", style="cyan").append(message)
        console.print(text)

    try:
        if TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)
        TEMP_DIR.mkdir()
        _print_info(Text(f"Using temp directory: {TEMP_DIR.absolute()}", style="cyan"))
        yield pc.Ok(TEMP_DIR)
    except (OSError, PermissionError) as e:
        txt = Text("✗ Failed to create temp directory:\n", style="bold red").append(
            f" {e}"
        )
        yield pc.Err(txt)
    finally:
        if not keep and TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)
            _print_info(Text("Cleaned up temp directory.", style="cyan"))
        elif keep:
            text = Text("Debug mode:", style="yellow").append(
                f" Kept temp directory at {TEMP_DIR.absolute()}"
            )
            _print_info(text)


def _execute_tests(temp_dir: Path, test_file: Path) -> pc.Result[Text, Text]:
    return (
        pc.Option.if_true(test_file, predicate=test_file.exists)
        .ok_or(
            Text()
            .append(Text("\u2717 Error:", style="bold red"))
            .append(f" Path '{test_file}' not found.")
        )
        .inspect_err(console.print)
        .and_then(
            lambda path: _get_test_files(path)
            .filter_map(lambda file: _generate_test_file(file, temp_dir))
            .collect()
            .ok_or(
                Text("Warning:", style="yellow").append(
                    " No doctests found in stub files."
                )
            )
            .and_then(lambda path_map: _run_tests(temp_dir, path_map))
            .inspect(console.print)
            .inspect_err(console.print)
        )
    )


def _should_ignore(p: Path, root: Path) -> bool:
    """Check if path should be ignored based on common directories."""
    try:
        return pc.Iter(p.relative_to(root).parts).any(
            lambda part: part in IGNORED_PATHS or part.endswith(".egg-info")
        )
    except ValueError:
        return False


def _get_test_files(path: Path) -> pc.Iter[Path]:
    """Discover .pyi and .md files, ignoring common directories (venv, .git, etc.)."""
    match path.is_file():
        case True:
            match path.suffix:
                case ".pyi" | ".md":
                    return pc.Iter.once(path)
                case _:
                    return pc.Iter[Path].empty()
        case False:
            return (
                pc.Iter(path.rglob("*.pyi"))
                .chain(path.rglob("*.md"))
                .filter_false(lambda p: _should_ignore(p, path))
            )


def _generate_test_file(file: Path, temp_dir: Path) -> pc.Option[tuple[Path, Path]]:
    test_file = temp_dir.joinpath(f"{file.stem}_test.py")
    return (
        _get_blocks(file)
        .collect()
        .then_some()
        .map(lambda blocks: test_file.write_text(blocks.join("\n"), encoding="utf-8"))
        .map(lambda _: (test_file, file))
    )


def _get_blocks(file: Path) -> pc.Iter[str]:
    content = file.read_text(encoding="utf-8")
    match file.suffix:
        case ".md":
            return parse_markdown(content)
        case ".pyi":
            return pc.Iter.once(content)
        case _:
            return pc.Iter[str].empty()


def _run_tests(
    temp_dir: Path, path_map: pc.Seq[tuple[Path, Path]]
) -> pc.Result[Text, Text]:
    def _remap_if_some(out: str) -> pc.Option[None]:
        return (
            pc.Option.if_some(out)
            .map(
                lambda text: path_map.iter()
                .fold(
                    text,
                    lambda acc, paths: acc.replace(
                        paths[0].as_posix(), paths[1].as_posix()
                    ),
                )
                .replace(temp_dir.as_posix(), "")
            )
            .map(lambda s: console.print(s))
        )

    result = subprocess.run(
        args=(
            "pytest",
            temp_dir.as_posix(),
            "--doctest-modules",
            "-v",
        ),
        check=False,
        capture_output=True,
        text=True,
    )
    _remap_if_some(result.stdout)
    _remap_if_some(result.stderr)

    return _check_status(result.returncode)


def _check_status(exit_code: int) -> pc.Result[Text, Text]:
    match exit_code:
        case 0:
            msg = Text("✓ All tests passed!", style="bold green")
            return pc.Ok(msg)
        case _:
            msg = Text("✗ Tests failed", style="bold red").append(
                f" with exit code {exit_code}"
            )
            return pc.Err(msg)


if __name__ == "__main__":
    app()
