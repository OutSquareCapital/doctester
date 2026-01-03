"""Tests for the CLI interface."""

from pathlib import Path

import pyochain as pc
import pytest
from typer.testing import CliRunner

import stubtester as st
from stubtester import app

runner = CliRunner()

TEST_DIR = Path("tests", "examples")
FAILURES = TEST_DIR.joinpath("failures.pyi")


def _get_passing_pyi_files() -> pc.Seq[Path]:
    """Get all .pyi files that should pass (all except foo.pyi)."""
    return pc.Iter(TEST_DIR.glob("*.pyi")).filter(lambda f: f.stem != "failures").sort()


def test_help_command() -> None:
    """Help command should work."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Run all doctests in stub files" in result.stdout


@pytest.mark.parametrize("pyi_file", _get_passing_pyi_files(), ids=lambda p: p.name)
def test_pyi_files_should_pass(pyi_file: Path) -> None:
    """All .pyi files except failures.pyi should pass."""
    result = st.run(pyi_file)

    assert result.is_ok(), (
        f"{pyi_file.name} should pass but failed: {result.unwrap_err()}"
    )


def test_failures_pyi_should_fail() -> None:
    """failures.pyi contains intentional errors and should fail."""
    result = st.run(FAILURES)

    assert result.is_err()
    assert "failed" in result.unwrap_err().lower()
    assert not st.TEMP_DIR.exists()


def test_nonexistent_path() -> None:
    """Return error for nonexistent path."""
    result = st.run(Path("nonexistent_xyz"))

    assert result.is_err()
    assert "not found" in result.unwrap_err()


def test_empty_directory(tmp_path: Path) -> None:
    """Return warning when no .pyi files found."""
    empty_dir = tmp_path.joinpath("empty")
    empty_dir.mkdir()

    result = st.run(empty_dir)

    assert result.is_err()
    assert "No doctests found" in result.unwrap_err()
