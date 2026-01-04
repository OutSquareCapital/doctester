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

from ._blocks import BlockTest, MarkdownBlock, Patterns

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
    keep: Annotated[  # noqa: FBT002
        bool,
        typer.Option(
            "--keep",
            help="Keep the temporary test files for debugging purposes",
        ),
    ] = False,
) -> pc.Result[str, str]:
    """Run all doctests in stub files (.pyi).

    This will discover all .pyi stub files and execute their doctests using pytest.

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
    return console.print(
        Panel.fit(
            f"[bold cyan]Doctester[/bold cyan]\n"
            f"Running tests in: [yellow]{path}[/yellow]",
            border_style="cyan",
        )
    )


@contextmanager
def _temp_test_dir(
    *, keep: bool = False
) -> Generator[pc.Result[Path, str], None, None]:
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
        if not keep and TEMP_DIR.exists():
            shutil.rmtree(TEMP_DIR)
            _print_info("Cleaned up temp directory.")
        elif keep:
            _print_info(
                f"[yellow]Debug mode:[/yellow] Kept temp directory at {TEMP_DIR.absolute()}"
            )


def _execute_tests(temp_dir: Path, test_file: Path) -> pc.Result[str, str]:
    return _path_exists(test_file).and_then(
        lambda path: _get_pyi_files(path)
        .filter_map(lambda file: _generate_test_file(file, temp_dir))
        .collect()
        .into(_check_generation)
        .map(lambda _: _run_tests(temp_dir))
        .and_then(_check_status)
        .inspect(console.print)
        .inspect_err(console.print)
    )


def _path_exists(path: Path) -> pc.Result[Path, str]:
    if path.exists():
        return pc.Ok(path)
    return pc.Err(f"[bold red]✗ Error:[/bold red] Path '{path}' not found.")


def _get_pyi_files(path: Path) -> pc.Iter[Path]:
    match path.is_file():
        case True:
            match path.suffix:
                case ".pyi" | ".md":
                    return pc.Iter.once(path)
                case _:
                    return pc.Iter[Path].empty()
        case _:
            return pc.Iter(path.rglob("*.pyi")).chain(pc.Iter(path.rglob("*.md")))


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
    content = file.read_text(encoding="utf-8")
    match file.suffix:
        case ".md":
            return _parse_markdown(content, file.name)
        case ".pyi":
            return _parse_stub(content, file.name)
        case _:
            return ""


def _parse_stub(content: str, filename: str) -> str:
    return (
        pc.Iter(Patterns.BLOCK.finditer(content))
        .map(lambda match: BlockTest.from_match(match, content, filename).to_func())
        .filter(lambda s: s.strip() != "")
        .join("\n")
    )


def _parse_markdown(content: str, filename: str) -> str:
    """Parse markdown file and extract code blocks."""
    headers = pc.Iter(Patterns.MARKDOWN_HEADER.finditer(content)).collect()

    def _find_header_for_block(block_start: int) -> str:
        """Find the closest header before this block."""
        last_header = (
            headers.iter()
            .filter(lambda h: h.start() < block_start)
            .map(lambda h: h.group(2).strip())
            .last()
        )
        return last_header if last_header else "markdown_test"

    return (
        pc.Iter(Patterns.MARKDOWN_BLOCK.finditer(content))
        .enumerate()
        .filter(lambda item: item.value.group(1) in {"py", "python"})
        .map(
            lambda item: MarkdownBlock(
                title=f"{_find_header_for_block(item.value.start())}_{item.idx}",
                code=item.value.group(2),
                line_number=content[: item.value.start()].count("\n") + 1,
                source_file=filename,
            ).to_func()
        )
        .join("\n")
    )


def _check_generation(files: pc.Seq[Path]) -> pc.Result[None, str]:
    if files.length() == 0:
        return pc.Err("[yellow]Warning:[/yellow] No doctests found in stub files.")
    return pc.Ok(None)


def _check_status(exit_code: int) -> pc.Result[str, str]:
    if exit_code != 0:
        return pc.Err(f"[bold red]✗ Tests failed[/bold red] with exit code {exit_code}")
    return pc.Ok("[bold green]✓ All tests passed![/bold green]")


def _replace_pytest_output(
    line_map: pc.Dict[str, pc.Dict[int, tuple[str, int]]], output: str
) -> str:
    """Replace references to generated test files with source file references."""

    def replacer(match: re.Match[str]) -> str:
        line_str = match.group(2)

        return (
            line_map.get_item(match.group(1))
            .and_then(
                lambda file_map: (
                    pc.Option.from_(int(line_str) if line_str else None)
                    .and_then(
                        lambda line_num: file_map.get_item(line_num).map(
                            lambda v: f"tests/examples/{v[0]}:{v[1]}"
                        )
                    )
                    .or_else(
                        lambda: pc.Option.from_(
                            Patterns.TEST_NAME.search(match.group(0))
                        ).map(
                            lambda m: f"tests/examples/{file_map.values_iter().next().unwrap()[0]}::{m.group(1)}"
                        )
                    )
                )
            )
            .unwrap_or(match.group(0))
        )

    return Patterns.TEST_FILE.sub(replacer, output)


def _run_tests(temp_dir: Path) -> int:
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
    processed_output = _build_line_map(temp_dir).into(
        _replace_pytest_output, result.stdout
    )
    console.print(processed_output, end="")
    if result.stderr:
        console.print(result.stderr, style="red", end="")

    return result.returncode


def _build_line_map(
    temp_dir: Path,
) -> pc.Dict[str, pc.Dict[int, tuple[str, int]]]:
    return (
        pc.Iter(temp_dir.glob("*_test.py"))
        .map(
            lambda test_file: (
                test_file.name,
                (
                    pc.Iter(test_file.read_text(encoding="utf-8").splitlines())
                    .enumerate(start=1)
                    .filter_map(
                        lambda item: pc.Option.from_(
                            Patterns.LINE_DIRECTIVE.search(item.value)
                        ).map(lambda m: (item.idx, (m.group(2), int(m.group(1)))))
                    )
                    .collect(pc.Dict)
                ),
            )
        )
        .collect(pc.Dict)
    )


if __name__ == "__main__":
    app()
