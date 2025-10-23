import importlib.util
import inspect
import sys
from pathlib import Path
from types import ModuleType

from ._models import TestResult
from ._stub_parser import generate_test_module_content


def _run_tests_in_module(module: ModuleType) -> TestResult:
    passed, total = 0, 0
    for name, func in inspect.getmembers(module, inspect.isfunction):
        if name.startswith("test_"):
            total += 1
            if func():
                passed += 1
    return TestResult(total=total, passed=passed)


def _load_module_from_file(test_file: Path) -> ModuleType:
    module_name = test_file.stem
    spec = importlib.util.spec_from_file_location(module_name, test_file)
    if not (spec and spec.loader):
        raise ImportError(f"Could not create module spec for {test_file}")

    test_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = test_module
    spec.loader.exec_module(test_module)
    return test_module


def run_pyi_tests(
    pyi_files: list[Path],
    temp_dir: Path,
    verbose: bool,
) -> TestResult:
    all_results: list[TestResult] = []

    for pyi_file in pyi_files:
        module_content = generate_test_module_content(pyi_file)
        if not module_content:
            continue

        test_file = temp_dir / f"{pyi_file.stem}_test.py"
        test_file.write_text(module_content, encoding="utf-8")

        if verbose:
            print(f"Running stub tests for {pyi_file.name}...")

        try:
            test_module = _load_module_from_file(test_file)
            result = _run_tests_in_module(test_module)

            if verbose:
                print(f"  {result.passed}/{result.total} tests passed.")

            if result.failed > 0:
                print(f"  FAILURES in {pyi_file.name} (see log above)")

            all_results.append(result)

        except Exception as e:
            print(f"--- ERROR loading {test_file.name} ---")
            print(f"{e!r}")
            all_results.append(TestResult(total=1, passed=0))

    total = sum(r.total for r in all_results)
    passed = sum(r.passed for r in all_results)
    return TestResult(total=total, passed=passed)
