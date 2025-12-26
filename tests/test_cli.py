"""Tests for the CLI interface."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from stubtester._cli import app

runner = CliRunner()


class TestCLI:
    """Test the CLI application."""

    def test_help_command(self) -> None:
        """Help command should work."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Run all doctests in stub files" in result.stdout

    def test_clean_file(self) -> None:
        """Running on clean.pyi should succeed."""
        test_file = Path("tests").joinpath("clean.pyi")
        if not test_file.exists():
            pytest.skip("clean.pyi not found")

        result = runner.invoke(app, [test_file.as_posix()])

        assert "All tests passed" in result.stdout

    def test_failing_file(self) -> None:
        """Running on foo.pyi should fail."""
        test_file = Path("tests").joinpath("foo.pyi")
        if not test_file.exists():
            pytest.skip("foo.pyi not found")

        result = runner.invoke(app, [test_file.as_posix()])

        assert "failed" in result.stdout.lower()

    def test_nonexistent_path(self) -> None:
        """Nonexistent path should show error."""
        result = runner.invoke(app, ["nonexistent_xyz"])

        assert "not found" in result.stdout.lower()
