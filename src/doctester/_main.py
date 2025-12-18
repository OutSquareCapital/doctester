import contextlib
import doctest
import shutil
import sys
from pathlib import Path
from types import ModuleType

import pyochain as pc

from . import _discovery, _stub_runner
from ._models import TestResult


def _add_root_to_path(root_dir: Path) -> None:
    sys.path.insert(0, str(root_dir.absolute()))


def _remove_root_from_path(root_dir: Path) -> None:
    with contextlib.suppress(ValueError):
        sys.path.remove(str(root_dir.absolute()))


def _run_py_tests(modules: pc.Vec[ModuleType], *, verbose: bool) -> TestResult:
    failures = 0
    total_tests = 0

    for mod in modules:
        result = doctest.testmod(mod, verbose=verbose)
        failures += result.failed
        total_tests += result.attempted

    return TestResult(total=total_tests, passed=total_tests - failures)


def _run_package_tests(root_dir: Path, temp_dir: Path, *, verbose: bool) -> TestResult:
    package_name = (
        _discovery.find_package_name(root_dir)
        .inspect(lambda name: print(f"Found package: {name}"))
        .unwrap()
    )
    package_path = root_dir.joinpath(package_name)

    print("\nRunning .py doctests...")
    py_result = (
        _discovery.get_py_modules(package_name, package_path)
        .tap(
            lambda m: print(f"Found {m.length()} Python modules.") if verbose else None
        )
        .into(_run_py_tests, verbose=verbose)
    )
    py_result.show()
    pyi_files: pc.Seq[Path] = (
        pc.Iter(package_path.glob("**/*.pyi"))
        .collect()
        .tap(lambda pyi: print(f"Found {pyi.length()} Python stub files."))
    )

    pyi_result = TestResult(total=0, passed=0)
    if pyi_files.any():
        print("\nRunning .pyi doctests...")
        pyi_result: TestResult = pyi_files.into(
            lambda pyi: _stub_runner.run_pyi_tests(
                pyi,
                temp_dir,
                verbose=verbose,
            )
        ).show()

    return py_result.join_with(pyi_result)


def _run_file_tests(file_path: Path, temp_dir: Path, *, verbose: bool) -> TestResult:
    print(f"Running doctests for single file: {file_path.name}")

    match file_path.suffix:
        case ".py":
            dt_result = doctest.testfile(
                str(file_path.absolute()),
                module_relative=False,
                verbose=verbose,
            )
            return TestResult(
                total=dt_result.attempted,
                passed=dt_result.attempted - dt_result.failed,
            ).show()

        case ".pyi":
            return _stub_runner.run_pyi_tests(
                [file_path],
                temp_dir,
                verbose=verbose,
            ).show()

        case _:
            print(f"Error: Unsupported file type: {file_path.suffix}")
            print("Only .py and .pyi files are supported.")
            sys.exit(1)


def run_doctester(root_dir_str: str = "src", *, verbose: bool = False) -> None:
    root_dir = Path(root_dir_str)
    if not root_dir.is_dir():
        print(f"Error: Root directory '{root_dir_str}' not found.")
        sys.exit(1)

    _add_root_to_path(root_dir)

    temp_dir = Path("doctests_temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    if verbose:
        print(f"Using temp directory: {temp_dir.absolute()}")

    try:
        result = _run_package_tests(root_dir, temp_dir, verbose=verbose)

        if result.failed > 0:
            print(f"\nTotal Failures: {result.failed} ❌")
            _remove_root_from_path(root_dir)
            sys.exit(1)
        else:
            print("\nAll doctests passed! ✅")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        _remove_root_from_path(root_dir)
        sys.exit(1)
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if verbose:
            print("Cleaned up temp directory.")
        _remove_root_from_path(root_dir)


def run_on_file(file_path: Path, *, verbose: bool = False) -> None:
    if not file_path.is_file():
        print(f"Error: File '{file_path}' not found or is a directory.")
        print("Use run_doctester() for directories.")
        sys.exit(1)

    root_dir = file_path.parent
    _add_root_to_path(root_dir)

    temp_dir = Path("doctests_temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    if verbose:
        print(f"Using temp directory: {temp_dir.absolute()}")
        if root_dir.absolute() != Path.cwd():
            print(f"Added to sys.path: {root_dir.absolute()}")

    try:
        result = _run_file_tests(file_path, temp_dir, verbose=verbose)

        if result.failed > 0:
            print(f"\nTotal Failures: {result.failed} ❌")
            _remove_root_from_path(root_dir)
            sys.exit(1)
        else:
            print("\nAll doctests passed! ✅")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
        _remove_root_from_path(root_dir)
        sys.exit(1)
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if verbose:
            print("Cleaned up temp directory.")
        _remove_root_from_path(root_dir)
