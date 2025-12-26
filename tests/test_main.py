"""Tests for the main stubtester functionality."""

from pathlib import Path
from textwrap import dedent

import pyochain as pc
import pytest

from stubtester._main import (
    TestBlock,
    _generated_or,  # pyright: ignore[reportPrivateUsage]
    _get_temp_dir,  # pyright: ignore[reportPrivateUsage]
    run_tests,
)


class TestTestBlock:
    """Test the TestBlock NamedTuple and its methods."""

    def test_to_func_basic(self) -> None:
        """Generate a test function from a basic docstring."""
        block = TestBlock(
            name="add",
            docstring=dedent("""
                Add two numbers.
                Example:
                ```python
                >>> 2 + 3
                5
                ```
            """).strip(),
        )
        result = block.to_func()

        assert "def test_add():" in result
        assert "2 + 3" in result
        assert "5" in result
        assert "```python" not in result  # Code fence should be removed

    def test_to_func_multiple_examples(self) -> None:
        """Handle multiple examples in a docstring."""
        block = TestBlock(
            name="multiply",
            docstring=dedent("""
                Multiply numbers.
                Examples:
                ```python
                >>> 3 * 4
                12
                >>> 0 * 100
                0
                ```
            """).strip(),
        )
        result = block.to_func()

        assert "def test_multiply():" in result
        assert "3 * 4" in result
        assert "0 * 100" in result

    def test_to_func_removes_code_fences(self) -> None:
        """Code fences should be stripped from the docstring."""
        block = TestBlock(
            name="example",
            docstring=dedent("""
                ```python
                >>> 1 + 1
                2
                ```
            """).strip(),
        )
        result = block.to_func()

        assert "```python" not in result
        assert "```" not in result
        assert ">>> 1 + 1" in result


class TestGeneratedOr:
    """Test the _generated_or helper function."""

    def test_with_files(self) -> None:
        """Return Ok when files are present."""
        files = pc.Seq((Path("a.py"), Path("b.py")))
        result = _generated_or(files)

        assert result.is_ok()

    def test_without_files(self) -> None:
        """Return Err when no files are generated."""
        result = pc.Seq[Path]([]).into(_generated_or)

        assert result.is_err()
        assert "No doctests found" in result.unwrap_err()


class TestGetTempDir:
    """Test temp directory creation and cleanup."""

    def test_creates_temp_dir(self) -> None:
        """Temp directory should be created."""
        temp_dir = _get_temp_dir()

        assert temp_dir.exists()
        assert temp_dir.is_dir()
        assert temp_dir.name == "doctests_temp"

        # Cleanup
        temp_dir.rmdir()

    def test_removes_existing_temp_dir(self) -> None:
        """Existing temp directory should be removed and recreated."""
        temp_dir = Path("doctests_temp")
        temp_dir.mkdir(exist_ok=True)
        test_file = temp_dir.joinpath("old.txt")
        test_file.write_text("old content")

        result = _get_temp_dir()

        assert result.exists()
        assert not test_file.exists()

        # Cleanup
        result.rmdir()


class TestRunTests:
    """Integration tests for the run_tests function."""

    def test_nonexistent_path(self) -> None:
        """Return error for nonexistent path."""
        result = run_tests(Path("nonexistent_path_xyz"))

        assert result.is_err()
        assert "not found" in result.unwrap_err()

    def test_clean_pyi_file(self) -> None:
        """Run tests on clean.pyi which should pass."""
        test_file = Path("tests").joinpath("clean.pyi")
        if not test_file.exists():
            pytest.skip("clean.pyi not found")

        result = run_tests(test_file)

        assert result.is_ok()

    def test_failing_pyi_file(self) -> None:
        """Run tests on foo.pyi which contains failing tests."""
        test_file = Path("tests").joinpath("foo.pyi")
        if not test_file.exists():
            pytest.skip("foo.pyi not found")

        result = run_tests(test_file)

        assert result.is_err()
        assert "failed" in result.unwrap_err().lower()

    def test_directory_with_pyi_files(self) -> None:
        """Run tests on a directory containing .pyi files."""
        test_dir = Path("tests")
        if not test_dir.exists():
            pytest.skip("tests directory not found")

        result = run_tests(test_dir)

        # Will fail because foo.pyi has failing tests
        assert result.is_err()

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Return warning when no .pyi files found."""
        empty_dir = tmp_path.joinpath("empty")
        empty_dir.mkdir()

        result = run_tests(empty_dir)

        assert result.is_err()
        assert "No doctests found" in result.unwrap_err()

    def test_cleans_up_temp_dir(self) -> None:
        """Temp directory should be cleaned up after tests."""
        test_file = Path("tests").joinpath("clean.pyi")
        if not test_file.exists():
            pytest.skip("clean.pyi not found")

        temp_dir = Path("doctests_temp")
        run_tests(test_file)

        assert not temp_dir.exists()
