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


def _run_py_tests(modules: list[ModuleType], verbose: bool) -> TestResult:
    failures = 0
    total_tests = 0

    for mod in modules:
        result = doctest.testmod(mod, verbose=verbose)
        failures += result.failed
        total_tests += result.attempted

    return TestResult(total=total_tests, passed=total_tests - failures)


def _run_package_tests(
    root_dir: Path,
    temp_dir: Path,
    verbose: bool,
) -> TestResult:
    package_name = _discovery.find_package_name(root_dir)
    package_path = root_dir.joinpath(package_name)
    print(f"Found package: {package_name}")

    py_modules = _discovery.get_py_modules(package_name, package_path)
    pyi_files = _discovery.get_pyi_files(package_path)

    if verbose:
        print(f"Found {len(py_modules)} Python modules.")
        print(f"Found {len(pyi_files)} Python stub files.")

    print("\nRunning .py doctests...")
    py_result = _run_py_tests(py_modules, verbose)

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
            print(f".pyi Tests Result: {pyi_result.passed}/{pyi_result.total} passed.")
        else:
            print("No .pyi doctests found.")

    return TestResult(
        total=py_result.total + pyi_result.total,
        passed=py_result.passed + pyi_result.passed,
    )


def _run_file_tests(
    file_path: Path,
    temp_dir: Path,
    verbose: bool,
) -> TestResult:
    print(f"Running doctests for single file: {file_path.name}")
    result = TestResult(total=0, passed=0)

    match file_path.suffix:
        case ".py":
            dt_result = doctest.testfile(
                str(file_path.absolute()),
                module_relative=False,
                verbose=verbose,
            )
            result = TestResult(
                total=dt_result.attempted,
                passed=dt_result.attempted - dt_result.failed,
            )
            if result.total > 0:
                print(f".py Tests Result: {result.passed}/{result.total} passed.")
            else:
                print("No .py doctests found.")

        case ".pyi":
            result = _stub_runner.run_pyi_tests(
                [file_path],
                temp_dir,
                verbose,
            )
            if result.total > 0:
                print(f".pyi Tests Result: {result.passed}/{result.total} passed.")
            else:
                print("No .pyi doctests found.")

        case _:
            print(f"Error: Unsupported file type: {file_path.suffix}")
            print("Only .py and .pyi files are supported.")
            sys.exit(1)

    return result


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
        result = _run_package_tests(root_dir, temp_dir, verbose)

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


def run_on_file(file_path_str: str, verbose: bool = False) -> None:
    file_path = Path(file_path_str)
    if not file_path.is_file():
        print(f"Error: File '{file_path_str}' not found or is a directory.")
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
        result = _run_file_tests(file_path, temp_dir, verbose)

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
