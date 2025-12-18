import re
import shutil
import subprocess
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

import pyochain as pc
from rich.console import Console

console = Console()


BLOCK_PATTERN = re.compile(
    r"(?:def|class)\s+(\w+)(?:\[[^\]]*\])?\s*(?:\([^)]*\))?\s*(?:->[^:]+)?"
    r':\s*"""(.*?)"""',
    re.DOTALL,
)


def run_tests(path: Path) -> pc.Result[int, str]:
    if not path.exists():
        return pc.Err(f"[bold red]Error:[/bold red] Path '{path}' not found.")

    temp_dir = _get_temp_dir()

    def _clean_up() -> None:
        shutil.rmtree(temp_dir)
        _print_info("Cleaned up temp directory.")

    def _generate_test_file(file: Path) -> pc.Option[Path]:
        def _generate_test_module_content() -> pc.Option[str]:
            header = f"# Generated tests from {file.name}\n\n"
            res = (
                pc.Iter(BLOCK_PATTERN.findall(file.read_text(encoding="utf-8")))
                .map(lambda b: TestBlock(*b).to_func())
                .filter(str.strip)
                .join("\n")
            )
            if not res:
                return pc.NONE
            return pc.Some(header + res)

        test_file = temp_dir.joinpath(f"{file.stem}_test.py")
        return (
            _generate_test_module_content()
            .map(lambda content: test_file.write_text(content, encoding="utf-8"))
            .map(lambda _: test_file)
        )

    def _get_pyi_files() -> pc.Iter[Path]:
        if path.is_file():
            return pc.Iter.from_(path) if path.suffix == ".pyi" else pc.Iter(())
        return pc.Iter(path.glob("**/*.pyi"))

    return (
        _get_pyi_files()
        .filter_map(_generate_test_file)
        .collect()
        .into(_generated_or)
        .and_then(
            lambda _: Step(
                (
                    "pytest",
                    str(temp_dir),
                    "--doctest-modules",
                    "-v",
                    "--tb=short",
                )
            ).run()
        )
        .tap(lambda _: _clean_up())
    )


def _print_info(message: str) -> None:
    console.print(f"[cyan]i[/cyan] {message}")


def _get_temp_dir() -> Path:
    temp_dir = Path("doctests_temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    _print_info(f"Using temp directory: {temp_dir.absolute()}")
    return temp_dir


def _generated_or(files: pc.Seq[Path]) -> pc.Result[None, str]:
    if files.length() == 0:
        return pc.Err("[yellow]Warning:[/yellow] No doctests found in stub files.")
    return pc.Ok(None)


class Step(NamedTuple):
    """A command-line step to execute."""

    args: Sequence[str]

    def run(self) -> pc.Result[int, str]:
        exit_code = subprocess.run(self.args, check=False).returncode
        if exit_code != 0:
            return pc.Err(
                f"[bold red]✗ Tests failed[/bold red] with exit code {exit_code}"
            )  # ty:ignore[invalid-return-type] # ty doesn't seem to handle this well
        return pc.Ok(exit_code)


class TestBlock(NamedTuple):
    name: str
    docstring: str

    def to_func(self) -> str:
        cleaned = re.sub(r"^\s*```\w*\s*$", "", self.docstring, flags=re.MULTILINE)

        return f'''
def test_{self.name}():
    """{cleaned}"""
    pass
'''
