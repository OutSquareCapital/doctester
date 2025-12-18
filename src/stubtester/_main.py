import re
import shutil
import subprocess
from pathlib import Path

import pyochain as pc
from rich.console import Console

console = Console()


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[cyan]i[/cyan] {message}")


def run_doctester(root_dir_str: str = "src", *, verbose: bool = False) -> int:
    """Generate test files from .pyi stubs and run pytest.

    Returns:
        int: Exit code from pytest
    """
    root_dir = Path(root_dir_str)
    if not root_dir.is_dir():
        console.print(
            f"[bold red]Error:[/bold red] Root directory '{root_dir_str}' not found."
        )
        return 1

    package_dir_result = _find_package_dir(root_dir)
    if package_dir_result.is_err():
        console.print(f"[bold red]Error:[/bold red] {package_dir_result.unwrap_err()}")
        return 1

    package_dir = package_dir_result.unwrap()
    print_info(f"Searching stubs in: {package_dir}")

    pyi_files = pc.Iter(package_dir.glob("**/*.pyi")).collect()
    if verbose:
        print_info(f"Found {pyi_files.length()} stub files.")

    return _generate_and_run_pytest(pyi_files.iter(), verbose=verbose)


def run_on_file(file_path: Path, *, verbose: bool = False) -> int:
    """Generate test file from a single .pyi stub and run pytest.

    Returns:
        int: Exit code from pytest
    """
    if not file_path.is_file():
        console.print(
            f"[bold red]Error:[/bold red] File '{file_path}' not found or is a directory."
        )
        return 1

    if file_path.suffix != ".pyi":
        console.print(
            f"[bold red]Error:[/bold red] Unsupported file type: {file_path.suffix}. "
            "Only .pyi stub files are supported."
        )
        return 1

    print_info(f"Running doctests for stub file: {file_path.name}")
    return pc.Iter.from_(file_path).into(_generate_and_run_pytest, verbose=verbose)


def _generate_and_run_pytest(pyi_files: pc.Iter[Path], *, verbose: bool) -> int:
    """Generate test files and run pytest directly.

    Returns:
        int: Exit code from pytest
    """
    temp_dir = Path("doctests_temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()

    if verbose:
        print_info(f"Using temp directory: {temp_dir.absolute()}")

    # Generate all test files
    test_files = pyi_files.filter_map(
        lambda pyi: generate_test_file(pyi, temp_dir)
    ).collect()

    if test_files.length() == 0:
        console.print("[yellow]Warning:[/yellow] No doctests found in stub files.")
        shutil.rmtree(temp_dir)
        return 0

    # Run ty check first to validate types
    if verbose:
        print_info("Running ty check on generated files...")

    ty_args = ["ty", "check", str(temp_dir)]
    ty_exit = subprocess.run(ty_args, check=False).returncode

    if ty_exit != 0:
        console.print("[bold red]✗ Type checking failed[/bold red]")
        shutil.rmtree(temp_dir)
        if verbose:
            print_info("Cleaned up temp directory.")
        return ty_exit

    # Run pytest directly - let it handle output and exit code
    args = [
        "pytest",
        str(temp_dir),
        "--doctest-modules",
        "-v" if verbose else "-q",
        "--tb=short",
    ]

    exit_code = subprocess.run(args, check=False).returncode

    # Cleanup
    shutil.rmtree(temp_dir)
    if verbose:
        print_info("Cleaned up temp directory.")

    return exit_code


def _find_package_dir(root_dir: Path) -> pc.Result[Path, RuntimeError]:
    """Find directory containing .pyi stub files."""
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


BLOCK_PATTERN = re.compile(
    r"(?:def|class)\s+(\w+)(?:\[[^\]]*\])?\s*(?:\([^)]*\))?\s*(?:->[^:]+)?"
    r':\s*"""(.*?)"""',
    re.DOTALL,
)


def generate_test_file(pyi_file: Path, temp_dir: Path) -> pc.Option[Path]:
    """Generate a .py test file from a .pyi stub file.

    Returns:
        pc.Option[Path]: Path to generated test file, or NONE if no tests found
    """
    test_file = temp_dir.joinpath(f"{pyi_file.stem}_test.py")
    return (
        _generate_test_module_content(pyi_file)
        .map(lambda content: test_file.write_text(content, encoding="utf-8"))
        .map(lambda _: test_file)
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
