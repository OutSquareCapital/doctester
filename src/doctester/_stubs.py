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


def generate_test_module_content(pyi_file: Path) -> pc.Option[str]:
    """Generate Python module with doctests in docstrings for pytest."""
    blocks: pc.Seq[tuple[str, str]] = pc.Iter(
        BLOCK_PATTERN.findall(pyi_file.read_text(encoding="utf-8"))
    ).collect()
    if not blocks.any():
        return pc.NONE

    header = f"# Generated tests from {pyi_file.name}\n\n"

    functions = blocks.iter().map(_block_to_test_function).filter(str.strip).join("\n")

    return pc.Some(header + functions)


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


def process_pyi_file(
    pyi_file: Path, temp_dir: Path, *, verbose: bool
) -> pc.Option[TestResult]:
    """Process a single .pyi file and run tests with pytest."""
    module_content = generate_test_module_content(pyi_file)
    if module_content.is_none():
        return pc.NONE

    test_file = temp_dir.joinpath(f"{pyi_file.stem}_test.py")
    test_file.write_text(module_content.unwrap(), encoding="utf-8")

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

    result = subprocess.run(args, capture_output=True, text=True, check=False)

    # Parser la sortie pytest: "X failed, Y passed in Z.ZZs"
    passed = failed = 0

    if match := re.search(r"(\d+) passed", result.stdout):
        passed = int(match.group(1))
    if match := re.search(r"(\d+) failed", result.stdout):
        failed = int(match.group(1))

    total = passed + failed

    # Afficher l'output de pytest si verbose ou si échecs
    if verbose or failed > 0:
        print(result.stdout)
        if result.stderr:
            print(result.stderr)

    return TestResult(total=total, passed=passed)
