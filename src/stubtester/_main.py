import contextlib
import shutil
import sys
import traceback
from collections.abc import Callable
from pathlib import Path

import pyochain as pc
from rich.console import Console

from ._models import TestResult
from ._stubs import process_pyi_file

console = Console()


def print_error(message: str) -> None:
    """Print an error message."""
    console.print(f"[bold red]✗[/bold red] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[cyan]i[/cyan] {message}")


def run_doctester(
    root_dir_str: str = "src", *, verbose: bool = False
) -> pc.Result[TestResult, str]:
    root_dir = Path(root_dir_str)
    if not root_dir.is_dir():
        return pc.Err(f"Root directory '{root_dir_str}' not found.")

    return _with_test_context(
        root_dir,
        lambda temp_dir: _run_package_tests(root_dir, temp_dir, verbose=verbose),
        verbose=verbose,
    )


def run_on_file(
    file_path: Path, *, verbose: bool = False
) -> pc.Result[TestResult, str]:
    if not file_path.is_file():
        return pc.Err(
            f"File '{file_path}' not found or is a directory. "
            "Use run_doctester() for directories."
        )

    root_dir = file_path.parent
    if verbose and root_dir.absolute() != Path.cwd():
        print_info(f"Added to sys.path: {root_dir.absolute()}")

    return _with_test_context(
        root_dir,
        lambda temp_dir: _run_file_tests(file_path, temp_dir, verbose=verbose),
        verbose=verbose,
    )


def _with_test_context[T](
    root_path: Path,
    operation: Callable[[Path], pc.Result[T, str]],
    *,
    verbose: bool,
) -> pc.Result[T, str]:
    """Execute operation with temp dir and path setup/cleanup."""
    sys.path.insert(0, str(root_path.absolute()))

    temp_dir = Path("doctests_temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    if verbose:
        print_info(f"Using temp directory: {temp_dir.absolute()}")

    try:
        return operation(temp_dir)
    except Exception:  # noqa: BLE001
        return pc.Err(f"An unexpected error occurred:\n{traceback.format_exc()}")
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if verbose:
            print_info("Cleaned up temp directory.")
        with contextlib.suppress(ValueError):
            sys.path.remove(str(root_path.absolute()))


def _run_file_tests(
    file_path: Path, temp_dir: Path, *, verbose: bool
) -> pc.Result[TestResult, str]:
    print_info(f"Running doctests for stub file: {file_path.name}")

    if file_path.suffix != ".pyi":
        return pc.Err(
            f"Unsupported file type: {file_path.suffix}. "
            "Only .pyi stub files are supported."
        )

    return pc.Ok(
        pc.Iter.from_(file_path).into(
            lambda p: _run_pyi_tests(
                p,
                temp_dir,
                verbose=verbose,
            )
        )
    )


def _run_package_tests(
    root_dir: Path, temp_dir: Path, *, verbose: bool
) -> pc.Result[TestResult, str]:
    package_dir_result = _find_package_dir(root_dir).inspect(
        lambda path: print_info(f"Searching stubs in: {path}")
    )

    if package_dir_result.is_err():
        return pc.Err(str(package_dir_result.unwrap_err()))

    package_dir = package_dir_result.unwrap()

    print_info("Running .pyi doctests...")

    def _show_found(files: pc.Seq[Path]) -> None:
        if verbose:
            print_info(f"Found {files.length()} stub files.")

    result: TestResult = (
        pc.Iter(package_dir.glob("**/*.pyi"))
        .collect()
        .tap(_show_found)
        .iter()
        .into(
            lambda pyi: _run_pyi_tests(
                pyi,
                temp_dir,
                verbose=verbose,
            )
        )
    )

    return pc.Ok(result)


def _find_package_dir(root_dir: Path) -> pc.Result[Path, RuntimeError]:
    if pc.Iter(root_dir.glob("**/*.pyi")).take(1).collect().length() > 0:
        return pc.Ok(root_dir)

    return (
        pc.Iter(root_dir.iterdir())
        .find(
            lambda child: child.is_dir()
            and pc.Iter(child.glob("**/*.pyi")).take(1).collect().length() > 0
        )
        .ok_or(RuntimeError(f"No .pyi stub files found in {root_dir} directory."))
    )


def _run_pyi_tests(
    pyi_files: pc.Iter[Path],
    temp_dir: Path,
    *,
    verbose: bool,
) -> TestResult:
    """Run tests for all .pyi stub files."""
    return (
        pyi_files.filter_map(
            lambda pyi: process_pyi_file(pyi, temp_dir, verbose=verbose).tap(
                lambda _: print_info(f"Running pytest doctests for {pyi.name}...")
            )
        )
        .collect()
        .into(TestResult.from_seq)
    )
