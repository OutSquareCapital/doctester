"""Tests for the CLI interface."""

from pathlib import Path

import pyochain as pc
import pytest
from typer.testing import CliRunner

import stubtester as st
from stubtester import app

runner = CliRunner()


@pytest.fixture
def test_examples_dir() -> Path:
    """Path to the test examples directory."""
    return Path("tests", "examples")


@pytest.fixture
def failures_dir(test_examples_dir: Path) -> Path:
    """Path to the failures directory."""
    return test_examples_dir.joinpath("failures")


@pytest.fixture
def success_dir(test_examples_dir: Path) -> Path:
    """Path to the success directory."""
    return test_examples_dir.joinpath("success")


def _get_test_files(directory: Path, pattern: str, exclude: set[str]) -> pc.Seq[Path]:
    """Get test files matching pattern, excluding specified stems."""
    return (
        pc.Iter(directory.glob(pattern)).filter(lambda f: f.stem not in exclude).sort()
    )


def test_help_command() -> None:
    """Help command should work."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Run all doctests in stub files" in result.stdout


@pytest.mark.parametrize(
    "test_file",
    _get_test_files(Path("tests", "examples", "success"), "*.pyi", exclude=set()),
    ids=lambda p: p.name,
)
def test_passing_pyi_files(test_file: Path) -> None:
    """All .pyi files in success/ should pass."""
    result = st.run(test_file)

    assert result.is_ok(), f"{test_file.name} failed: {result.unwrap_err()}"


@pytest.mark.parametrize(
    "test_file",
    _get_test_files(Path("tests", "examples", "success"), "*.md", exclude=set()),
    ids=lambda p: p.name,
)
def test_passing_md_files(test_file: Path) -> None:
    """All .md files in success/ should pass."""
    result = st.run(test_file)

    assert result.is_ok(), f"{test_file.name} failed: {result.unwrap_err()}"


def test_success_directory_all_pass(success_dir: Path) -> None:
    """All tests in success/ directory should pass."""
    result = st.run(success_dir)

    assert result.is_ok(), f"Success directory failed: {result.unwrap_err()}"


def test_failures_pyi_should_fail(failures_dir: Path) -> None:
    """failures.pyi contains intentional errors and should fail."""
    failures_pyi = failures_dir.joinpath("failures.pyi")
    result = st.run(failures_pyi)

    assert result.is_err(), "failures.pyi should fail but passed"
    error_msg = result.unwrap_err().plain.lower()
    assert "failed" in error_msg or "error" in error_msg
    assert not st.TEMP_DIR.exists(), "Temp directory should be cleaned up"


def test_failures_md_should_fail(failures_dir: Path) -> None:
    """failures.md contains intentional errors and should fail."""
    failures_md = failures_dir.joinpath("failures.md")
    result = st.run(failures_md)

    assert result.is_err(), "failures.md should fail but passed"
    assert "failed" in result.unwrap_err().plain.lower()


def test_nonexistent_path() -> None:
    """Return error for nonexistent path."""
    nonexistent = Path("nonexistent_xyz_12345")
    result = st.run(nonexistent)

    assert result.is_err(), "Should return error for nonexistent path"
    assert "not found" in result.unwrap_err()


def test_nonexistent_file_with_valid_extension() -> None:
    """Return error for nonexistent file even with valid extension."""
    result = st.run(Path("does_not_exist.pyi"))

    assert result.is_err()
    assert "not found" in result.unwrap_err()


def test_empty_directory(tmp_path: Path) -> None:
    """Return warning when no test files found."""
    empty_dir = tmp_path.joinpath("empty")
    empty_dir.mkdir()

    result = st.run(empty_dir)

    assert result.is_err(), "Empty directory should return error"
    assert "No doctests found" in result.unwrap_err()


def test_directory_with_non_test_files(tmp_path: Path) -> None:
    """Directory with only non-.pyi/.md files should return warning."""
    test_dir = tmp_path.joinpath("no_tests")
    test_dir.mkdir()
    test_dir.joinpath("readme.txt").write_text("Not a test file")
    test_dir.joinpath("script.py").write_text("# Not a stub file")

    result = st.run(test_dir)

    assert result.is_err()
    assert "No doctests found" in result.unwrap_err()


def test_file_with_invalid_extension(tmp_path: Path) -> None:
    """File with invalid extension should return empty."""
    invalid_file = tmp_path.joinpath("test.txt")
    invalid_file.write_text(">>> 1 + 1\n2")

    result = st.run(invalid_file)

    assert result.is_err()
    assert "No doctests found" in result.unwrap_err()


def test_keep_flag_preserves_temp_dir(success_dir: Path) -> None:
    """--keep flag should preserve temporary directory."""
    clean_pyi = success_dir.joinpath("clean.pyi")

    try:
        result = st.run(clean_pyi, keep=True)

        assert result.is_ok()
        assert st.TEMP_DIR.exists(), "Temp directory should be preserved with keep=True"
    finally:
        if st.TEMP_DIR.exists():
            import shutil

            shutil.rmtree(st.TEMP_DIR)
