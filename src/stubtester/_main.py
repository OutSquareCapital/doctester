import re
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

console = Console()


app = typer.Typer(
    name="doctester",
    help="Run doctests from stub files (.pyi) using pytest --doctest-modules",
)
TEMP_DIR = Path("doctests_temp")
IGNORED_PATHS = pc.Set[str](
    (
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
    )
)
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
    """Run all doctests in stub files (.pyi).

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

    result: pc.Result[Path, Text] = pc.Ok(Path())
    try:
        if TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)
        TEMP_DIR.mkdir()
        _print_info(Text(f"Using temp directory: {TEMP_DIR.absolute()}", style="cyan"))
        result = pc.Ok(TEMP_DIR)
    except (OSError, PermissionError) as e:
        txt = Text("✗ Failed to create temp directory:\n", style="bold red").append(
            f" {e}"
        )
        result = pc.Err(txt)
    finally:
        yield result
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
        pc.Option.if_true(test_file, predicate=Path.exists)
        .ok_or(
            Text("\u2717 Error:", style="bold red").append(
                f" Path '{test_file}' not found."
            )
        )
        .and_then(
            lambda path: _get_test_files(path)
            .inspect_err(console.print)
            .and_then(
                lambda files: files.map(
                    lambda p: (p, temp_dir.joinpath(f"{p.stem}_test.py"))
                )
                .map_star(_write_files)
                .collect()
                .ok_or(
                    Text("Warning:", style="yellow").append(
                        " No doctests found in stub files."
                    )
                )
            )
        )
        .and_then(
            lambda path_map: _run_tests(temp_dir, path_map).and_then(
                lambda res: pc.Option.if_true(
                    res.returncode, predicate=lambda code: code == 0
                )
                .ok_or(Text("\u2717 Tests failed", style="bold red"))
                .map(lambda _: Text("\u2713 All tests passed!", style="bold green"))
            )
        )
        .inspect(console.print)
        .inspect_err(console.print)
    )


def _get_test_files(path: Path) -> pc.Result[pc.Iter[Path], Text]:
    """Discover .pyi files, ignoring common directories (venv, .git, etc.)."""
    match path.is_file():
        case True:
            match path.suffix:
                case ".pyi":
                    return pc.Ok(pc.Iter.once(path))
                case _:
                    msg = Text("✗ Unsupported file type:", style="bold red").append(
                        f" {path.suffix}. Only .pyi files are supported."
                    )
                    return pc.Err(msg)
        case False:
            return pc.Ok(
                pc.Iter(path.rglob("*.pyi")).filter_false(
                    lambda p: _should_ignore(p, path)
                )
            )


def _should_ignore(p: Path, root: Path) -> bool:
    """Check if path should be ignored based on common directories."""
    try:
        return pc.Iter(p.relative_to(root).parts).any(
            lambda part: IGNORED_PATHS.contains(part) or part.endswith(".egg-info")
        )
    except ValueError:
        return False


def _write_files(file: Path, temp_file: Path) -> tuple[Path, Path]:
    temp_file.write_text(file.read_text(encoding="utf-8"), encoding="utf-8")
    return temp_file, file


def _run_tests(
    temp_dir: Path,
    path_map: pc.Seq[tuple[Path, Path]],
) -> pc.Result[subprocess.CompletedProcess[str], Text]:
    return (
        _run_process(temp_dir)
        .inspect(lambda res: _remap_if_some(res.stdout, path_map))
        .inspect(lambda res: _remap_if_some(res.stderr, path_map))
    )


def _run_process(path: Path) -> pc.Result[subprocess.CompletedProcess[str], Text]:
    try:
        return pc.Ok(
            subprocess.run(
                args=(
                    "pytest",
                    path.as_posix(),
                    "--doctest-modules",
                    "-v",
                ),
                check=False,
                capture_output=True,
                text=True,
            )
        )
    except Exception as e:  # noqa: BLE001
        msg = Text("✗ Unexpected error:\n", style="bold red").append(f" {e}")
        return pc.Err(msg)


def _remap_if_some(
    out: str,
    path_map: pc.Seq[tuple[Path, Path]],
) -> pc.Option[None]:
    """Remap temporary file paths to source file paths in output."""

    def _remap_paths(acc: str, temp: Path, source: Path) -> str:
        return re.compile(f"<doctest {re.escape(temp.stem)}\\.").sub(
            f"<doctest {source.stem}.",
            acc.replace(str(temp), str(source)),
        )

    return (
        pc.Option.if_some(out)
        .map(
            lambda text: path_map.iter().fold(
                text, lambda acc, paths: _remap_paths(acc, *paths)
            )
        )
        .map(console.print)
    )
