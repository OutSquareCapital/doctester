import doctest
import importlib
import importlib.util
import inspect
import re
import shutil
import sys
from enum import StrEnum
from pathlib import Path
from types import ModuleType
from typing import TypedDict


class Files(StrEnum):
    SOURCE = "src"
    PYSRC = "__init__.py"
    PYISRC = "__init__.pyi"


class TestCounts(TypedDict):
    total: int
    passed: int
    failed: int


def _extract_block_with_docstring(content: str) -> list[tuple[str, str]]:
    pattern = (
        r"(?:def|class)\s+(\w+)(?:\[[^\]]*\])?\s*(?:\([^)]*\))?\s*(?:->[^:]+)?"
        r':\s*"""(.*?)"""'
    )
    return re.findall(pattern, content, re.DOTALL)


def _convert_doctests_to_assertions(block_name: str, docstring: str) -> str:
    doctest_parser = doctest.DocTestParser()
    examples = doctest_parser.parse(docstring)

    setup_code: list[str] = []
    test_blocks: list[str] = []

    for example in examples:
        if not isinstance(example, doctest.Example):
            continue

        if doctest.SKIP in example.options:
            continue

        source = example.source.strip()
        is_setup = source.startswith(("import ", "from ", "def ", "class ")) or (
            "=" in source and not any(op in source for op in ["==", ">=", "<=", "!="])
        )

        if is_setup:
            setup_code.append(source)
        else:
            raw_expected = example.want.strip()
            if not raw_expected or raw_expected == "...":
                continue

            expected = raw_expected.strip()
            source_literal = repr(source)
            test_blocks.append(
                f"""
    res = {source}
    if not _assert_test(res, {expected}, "{block_name}", {source_literal}):
        return False"""
            )

    if not test_blocks:
        return ""

    setup_str = "\n".join(f"    {line}" for line in "\n".join(setup_code).split("\n"))
    tests_str = "\n".join(test_blocks)

    return f"""
def test_{block_name}() -> bool:
{setup_str}
{tests_str}
    return True
"""


def _run_tests_in_module(module: ModuleType) -> tuple[int, int]:
    passed, total = 0, 0
    for name, func in inspect.getmembers(module, inspect.isfunction):
        if name.startswith("test_"):
            total += 1
            if func():
                passed += 1
    return passed, total


def test_pyi_files(package_name: str, verbose: bool) -> None:
    package_path = Path(Files.SOURCE).joinpath(package_name)

    temp_dir = Path("doctests_temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    print(f"Test files will be saved to: {temp_dir.absolute()}")

    all_tests_passed = True
    test_counts = TestCounts({"total": 0, "passed": 0, "failed": 0})

    assertion_helper = """
from typing import Any
def _assert_test(got: Any, expected: Any, name: str, source: str) -> bool:
    if got != expected:
        print(f'--- ERROR IN: {name} ---')
        print(f'Source  : {source}')
        print(f'Got     : {got!r}')
        print(f'Expected: {expected!r}')
        return False
    return True
"""

    for pyi_file in package_path.glob("**/*.pyi"):
        module_name = pyi_file.stem
        test_file = temp_dir / f"{module_name}_test.py"

        with open(pyi_file, "r", encoding="utf-8") as f:
            content = f.read()

        blocks = _extract_block_with_docstring(content)
        if not blocks:
            continue

        module_content = [f"# Generated tests from {pyi_file}\n", assertion_helper]
        has_tests = False

        for block_name, docstring in blocks:
            test_function = _convert_doctests_to_assertions(block_name, docstring)
            if test_function.strip():
                module_content.append(test_function)
                has_tests = True

        if not has_tests:
            continue

        with open(test_file, "w", encoding="utf-8") as f:
            f.write("\n".join(module_content))

        print(f"Running tests for {module_name}...")
        spec = importlib.util.spec_from_file_location(f"{module_name}_test", test_file)
        if spec and spec.loader:
            test_module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = test_module
            spec.loader.exec_module(test_module)

            passed, total = _run_tests_in_module(test_module)
            print(f"  {passed}/{total} tests passed for {module_name}")

            test_counts["total"] += total
            test_counts["passed"] += passed
            failed = total - passed
            test_counts["failed"] += failed

            if failed > 0:
                all_tests_passed = False

    print(
        f"\nTotal Results: {test_counts['passed']}/{test_counts['total']} tests passed"
    )
    if test_counts["failed"] > 0:
        print(f"{test_counts['failed']} tests failed")

    if not all_tests_passed:
        print("\nSome tests failed")
        sys.exit(1)
