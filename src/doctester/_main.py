import contextlib
import doctest
import shutil
import sys
import traceback
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pyochain as pc

from . import _console, _discovery
from ._models import TestResult
from ._stubs import process_pyi_file


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
        _console.print_info(f"Added to sys.path: {root_dir.absolute()}")

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
        _console.print_info(f"Using temp directory: {temp_dir.absolute()}")

    try:
        return operation(temp_dir)
    except Exception:
        tb = traceback.format_exc()
        return pc.Err(f"An unexpected error occurred:\n{tb}")
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if verbose:
            _console.print_info("Cleaned up temp directory.")
        with contextlib.suppress(ValueError):
            sys.path.remove(str(root_path.absolute()))


def _run_file_tests(
    file_path: Path, temp_dir: Path, *, verbose: bool
) -> pc.Result[TestResult, str]:
    _console.print_info(f"Running doctests for single file: {file_path.name}")

    match file_path.suffix:
        case ".py":
            dt_result = doctest.testfile(
                str(file_path.absolute()),
                module_relative=False,
                verbose=verbose,
            )
            return pc.Ok(
                TestResult(
                    total=dt_result.attempted,
                    passed=dt_result.attempted - dt_result.failed,
                )
            )

        case ".pyi":
            return pc.Ok(
                pc.Iter.from_(file_path).into(
                    lambda p: _run_pyi_tests(
                        p,
                        temp_dir,
                        verbose=verbose,
                    )
                )
            )

        case _:
            return pc.Err(
                f"Unsupported file type: {file_path.suffix}. "
                "Only .py and .pyi files are supported."
            )


def _run_package_tests(
    root_dir: Path, temp_dir: Path, *, verbose: bool
) -> pc.Result[TestResult, str]:
    package_name_result = _discovery.find_package_name(root_dir).inspect(
        lambda name: _console.print_info(f"Found package: {name}")
    )

    if package_name_result.is_err():
        return pc.Err(str(package_name_result.unwrap_err()))

    package_name = package_name_result.unwrap()
    package_path = root_dir.joinpath(package_name)

    _console.print_info("Running .py doctests...")

    def _show_founds(m: pc.Vec[ModuleType]) -> None:
        if verbose:
            _console.print_info(f"Found {m.length()} Python modules.")

    py_result: TestResult = (
        _discovery.get_py_modules(package_name, package_path)
        .unwrap()
        .tap(_show_founds)
        .iter()
        .map(lambda mod: doctest.testmod(mod, verbose=verbose))
        .map(lambda r: TestResult(total=r.attempted, passed=r.attempted - r.failed))
        .collect()
        .into(TestResult.from_seq)
    )

    pyi_files: pc.Seq[Path] = (
        pc.Iter(package_path.glob("**/*.pyi"))
        .collect()
        .tap(
            lambda pyi: _console.print_info(f"Found {pyi.length()} Python stub files.")
        )
    )
    pyi_result: TestResult = TestResult(total=0, passed=0)
    if pyi_files.any():
        _console.print_info("Running .pyi doctests...")
        pyi_result = pyi_files.iter().into(
            lambda pyi: _run_pyi_tests(
                pyi,
                temp_dir,
                verbose=verbose,
            )
        )

    _console.print_test_summary(py_result, pyi_result)

    return pc.Ok(py_result.join_with(pyi_result))


def _run_pyi_tests(
    pyi_files: pc.Iter[Path],
    temp_dir: Path,
    *,
    verbose: bool,
) -> TestResult:
    """Run tests for all .pyi stub files."""
    return (
        pyi_files.filter_map(
            lambda pyi: process_pyi_file(pyi, temp_dir, verbose=verbose)
        )
        .collect()
        .into(TestResult.from_seq)
    )
