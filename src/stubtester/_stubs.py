from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pyochain as pc

from . import _console
from ._models import TestResult

BLOCK_PATTERN = re.compile(
    r"(?:def|class)\s+(\w+)(?:\[[^\]]*\])?\s*(?:\([^)]*\))?\s*(?:->[^:]+)?"
    r':\s*"""(.*?)"""',
    re.DOTALL,
)


def process_pyi_file(
    pyi_file: Path, temp_dir: Path, *, verbose: bool
) -> pc.Option[TestResult]:
    """Process a single .pyi file and run tests with pytest."""
    test_file = temp_dir.joinpath(f"{pyi_file.stem}_test.py")
    if (
        _generate_test_module_content(pyi_file)
        .map(lambda content: test_file.write_text(content, encoding="utf-8"))
        .is_none()
    ):
        return pc.NONE
    if verbose:
        _console.print_info(f"Running pytest doctests for {pyi_file.name}...")

    return pc.Some(_run_pytest(test_file, verbose=verbose))


def _run_pytest(test_file: Path, *, verbose: bool) -> TestResult:
    """Run pytest with doctest support on the generated test file."""
    args = [
        "pytest",
        str(test_file),
        "--doctest-modules",
        "-v" if verbose else "-q",
        "--tb=short",
    ]

    return TestResult.from_process(
        subprocess.run(args, capture_output=True, text=True, check=False),
        verbose=verbose,
    )


def _generate_test_module_content(pyi_file: Path) -> pc.Option[str]:
    """Generate Python module with doctests in docstrings for pytest."""
    header = f"# Generated tests from {pyi_file.name}\n\n"
    res = (
        pc.Iter(BLOCK_PATTERN.findall(pyi_file.read_text(encoding="utf-8")))
        .map(_block_to_test_function)
        .filter(str.strip)
        .join("\n")
    )
    if not res:
        return pc.NONE
    return pc.Some(header + res)


def _block_to_test_function(block: tuple[str, str]) -> str:
    """Convert a (name, docstring) block to a pytest-compatible test function."""
    name, docstring = block
    # Nettoyer les lignes markdown fences complètes (```python et ```)
    cleaned = re.sub(r"^\s*```\w*\s*$", "", docstring, flags=re.MULTILINE)

    return f'''
def test_{name}():
    """{cleaned}"""
    pass
'''
