import doctest
import shutil
import sys
from pathlib import Path
from types import ModuleType

from . import _discovery, _stub_runner
from ._models import TestResult


def _add_root_to_path(root_dir: Path) -> None:
    sys.path.insert(0, str(root_dir.absolute()))


def _remove_root_from_path(root_dir: Path) -> None:
    try:
        sys.path.remove(str(root_dir.absolute()))
    except ValueError:
        pass


def run_py_tests(modules: list[ModuleType], verbose: bool) -> TestResult:
    failures = 0
    total_tests = 0

    for mod in modules:
        result = doctest.testmod(mod, verbose=verbose)
        failures += result.failed
        total_tests += result.attempted

    return TestResult(total=total_tests, passed=total_tests - failures)


def run_doctester(root_dir_str: str = "src", verbose: bool = False) -> None:
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
        package_name = _discovery.find_package_name(root_dir)
        package_path = root_dir.joinpath(package_name)
        print(f"Found package: {package_name}")

        py_modules = _discovery.get_py_modules(package_name, package_path)
        pyi_files = _discovery.get_pyi_files(package_path)

        if verbose:
            print(f"Found {len(py_modules)} Python modules.")
            print(f"Found {len(pyi_files)} Python stub files.")

        print("\nRunning .py doctests...")
        py_result = run_py_tests(py_modules, verbose)

        if py_result.total > 0:
            print(f".py Tests Result: {py_result.passed}/{py_result.total} passed.")
        else:
            print("No .py doctests found.")

        pyi_result = TestResult(total=0, passed=0)
        if pyi_files:
            print("\nRunning .pyi doctests...")
            pyi_result = _stub_runner.run_pyi_tests(
                pyi_files,
                temp_dir,
                verbose,
            )
            if pyi_result.total > 0:
                print(
                    f".pyi Tests Result: {pyi_result.passed}/{pyi_result.total} passed."
                )
            else:
                print("No .pyi doctests found.")

        total_failed = py_result.failed + pyi_result.failed

        if total_failed > 0:
            print(f"\nTotal Failures: {total_failed} ❌")
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
