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

from ._blocks import Patterns, parse_markdown

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
                lambda files: (
                    files.map(lambda p: (p, temp_dir.joinpath(f"{p.stem}_test.py")))
                    .filter_map_star(
                        lambda file, temp_file: _get_blocks(file)
                        .map_star(
                            lambda code, name, offset: (
                                code,
                                (f"{temp_file.stem}.{name}", offset),
                            )
                        )
                        .collect()
                        .then_some()
                        .map(
                            lambda blocks_info: blocks_info.iter()
                            .unzip()
                            .inspect(
                                lambda unzipped: temp_file.write_text(
                                    unzipped.left.join("\n"), encoding="utf-8"
                                )
                            )
                            .right
                        )
                        .map(lambda offsets: ((temp_file, file), offsets))
                    )
                    .collect()
                    .ok_or(
                        Text("Warning:", style="yellow").append(
                            " No doctests found in stub files."
                        )
                    )
                )
            )
        )
        .and_then(
            lambda data: (
                data.iter()
                .unzip()
                .into(
                    lambda unzipped: _run_tests(
                        temp_dir,
                        unzipped.left.collect(),
                        unzipped.right.flatten().collect(pc.Dict),
                    )
                )
                .into(
                    lambda res: pc.Option.if_true(
                        res.unwrap().returncode, predicate=lambda code: code == 0
                    )
                    .ok_or(Text("✗ Tests failed", style="bold red"))
                    .map(lambda _: Text("✓ All tests passed!", style="bold green"))
                )
            )
        )
        .inspect(console.print)
        .inspect_err(console.print)
    )


def _get_test_files(path: Path) -> pc.Result[pc.Iter[Path], Text]:
    """Discover .pyi and .md files, ignoring common directories (venv, .git, etc.)."""
    match path.is_file():
        case True:
            match path.suffix:
                case ".pyi" | ".md":
                    return pc.Ok(pc.Iter.once(path))
                case _:
                    msg = Text("✗ Unsupported file type:", style="bold red").append(
                        f" {path.suffix}. Only .pyi and .md files are supported."
                    )
                    return pc.Err(msg)
        case False:
            return pc.Ok(
                pc.Iter(path.rglob("*.pyi"))
                .chain(path.rglob("*.md"))
                .filter_false(lambda p: _should_ignore(p, path))
            )


def _should_ignore(p: Path, root: Path) -> bool:
    """Check if path should be ignored based on common directories."""
    try:
        return pc.Iter(p.relative_to(root).parts).any(
            lambda part: IGNORED_PATHS.contains(part) or part.endswith(".egg-info")
        )
    except ValueError:
        return False


def _get_blocks(file: Path) -> pc.Iter[tuple[str, str, int]]:
    content = file.read_text(encoding="utf-8")
    match file.suffix:
        case ".md":
            return parse_markdown(content).filter_map_star(
                lambda code, line: pc.Option(Patterns.FUNC_NAME.match(code))
                .map(lambda m: m.group(1))
                .map(lambda name: (code, name, line))
            )
        case ".pyi":
            return pc.Iter.once((content, file.stem, 0))
        case _:
            msg = "Unreachable"
            raise RuntimeError(msg)


def _run_tests(
    temp_dir: Path,
    path_map: pc.Seq[tuple[Path, Path]],
    offset_map: pc.Dict[str, int],
) -> pc.Result[subprocess.CompletedProcess[str], Text]:
    return (
        _run_process(temp_dir)
        .inspect(lambda res: _remap_if_some(res.stdout, path_map, offset_map))
        .inspect(lambda res: _remap_if_some(res.stderr, path_map, offset_map))
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
    out: str, path_map: pc.Seq[tuple[Path, Path]], offset_map: pc.Dict[str, int]
) -> pc.Option[None]:
    """Remap temporary file paths to source file paths in output."""

    def _remap_paths(acc: str, temp: Path, source: Path) -> str:
        source_posix = source.as_posix()
        result = Patterns.doctest_pattern(temp.stem).sub(
            f"<doctest {source.stem}.",
            acc.replace(temp.as_posix(), source_posix).replace(str(temp), str(source)),
        )

        def _adjust_line(match: re.Match[str]) -> str:
            file_path = match.group(1)
            line_num = int(match.group(2))

            return (
                pc.Option(Patterns.func_pattern(source_posix).search(result))
                .map(lambda m: m.group(1))
                .and_then(lambda func_name: offset_map.get_item(func_name))
                .map(lambda offset: f"{file_path}:{line_num + offset}:")
                .unwrap_or(match.group(0))
            )

        return Patterns.line_pattern(source_posix).sub(_adjust_line, result)

    return (
        pc.Option.if_some(out)
        .map(
            lambda text: path_map.iter().fold(
                text, lambda acc, paths: _remap_paths(acc, *paths)
            )
        )
        .map(lambda s: console.print(s))
    )
