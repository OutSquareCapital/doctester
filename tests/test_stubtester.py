"""Tests for the pytest-stubtester plugin."""

from __future__ import annotations

from pathlib import Path
from shutil import copyfile

import pytest

import pytest_docflex as pst

ROOT = Path(__file__).resolve().parent
CASES = ROOT.joinpath("cases")
EXAMPLES = ROOT.joinpath("examples")


def test_plugin_is_registered(pytestconfig: pytest.Config) -> None:
    """Plugin should be registered with pytest."""
    plugin = pytestconfig.pluginmanager.get_plugin("docflex")
    assert plugin is not None


def test_pyi_enabled_option_exists(pytestconfig: pytest.Config) -> None:
    """--pyi-enabled option should be available."""
    assert hasattr(pytestconfig.option, "docflex")


def test_pyi_module_class_exists() -> None:
    """PyiModule class should exist and inherit from pytest.Module."""
    assert issubclass(pst.ExtModule, pytest.Module)


def test_plugin_disabled_by_default(pytester: pytest.Pytester) -> None:
    """Plugin should not collect .pyi files when disabled."""
    # Should not collect the .pyi file when plugin disabled
    pytester.runpytest("-v", _case("test_sample.pyi")).stdout.no_fnmatch_line(
        "*test_sample.pyi*"
    )


def test_plugin_enabled_collects_pyi(pytester: pytest.Pytester) -> None:
    """Plugin should collect .pyi files when enabled."""
    result = pytester.runpytest(pst.COMMAND, "-v", _case("test_sample.pyi"))
    # Should collect and pass the doctest
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*test_sample.pyi*PASSED*"])


def test_passing_doctests(pytester: pytest.Pytester) -> None:
    """Valid doctests should pass."""
    result = pytester.runpytest(pst.COMMAND, "-v", _case("passing.pyi"))
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*passing.pyi*PASSED*"])


def test_syntax_errors_are_reported_during_collection(
    pytester: pytest.Pytester,
) -> None:
    """Invalid fenced Python should fail collection with a syntax error."""
    result = pytester.runpytest(pst.COMMAND, "-v", _case("syntax_error.pyi"))
    assert result.ret != 0
    result.stdout.fnmatch_lines([
        "*ERROR collecting*syntax_error.pyi*",
        "*SyntaxError: invalid syntax*",
    ])


def test_failing_doctests(pytester: pytest.Pytester) -> None:
    """Invalid doctests should fail."""
    result = pytester.runpytest(pst.COMMAND, "-v", _case("failing.pyi"))
    assert result.ret != 0
    result.stdout.fnmatch_lines(["*failing.pyi*FAILED*"])


def test_fenced_block_failure_points_to_failing_line(pytester: pytest.Pytester) -> None:
    """Fenced block failures should report the failing source line."""
    result = pytester.runpytest(pst.COMMAND, "-v", _case("line_numbers.pyi"))
    assert result.ret != 0
    result.stdout.fnmatch_lines(['*raise RuntimeError("division by zero")*'])


def test_multiple_fences_preserve_traceback_line(pytester: pytest.Pytester) -> None:
    """Multiple fences should preserve the line of a later failure."""
    result = pytester.runpytest(pst.COMMAND, "-v", _case("two_blocks.pyi"))
    assert result.ret != 0
    result.stdout.fnmatch_lines(["*assert run(10) == Ok(0.1)*"])


def test_multiple_doctests_in_file(pytester: pytest.Pytester) -> None:
    """Multiple doctests in one file should all be collected."""
    result = pytester.runpytest(pst.COMMAND, "-v", _case("multi.pyi"))
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*multi.pyi::add*PASSED*"])
    result.stdout.fnmatch_lines(["*multi.pyi::sub*PASSED*"])


def test_non_pyi_files_ignored(pytester: pytest.Pytester) -> None:
    """Non-.pyi files should be ignored even with plugin enabled."""
    _ = copyfile(_case("readme.txt"), pytester.path.joinpath("readme.txt"))
    result = pytester.runpytest(pst.COMMAND, "-v")
    # Should not collect .txt file
    result.stdout.no_fnmatch_line("*readme.txt*")


def test_empty_pyi_file(pytester: pytest.Pytester) -> None:
    """Empty .pyi file should not cause errors."""
    result = pytester.runpytest(pst.COMMAND, "-v", _case("empty.pyi"))
    # Should complete without errors, just no tests collected from this file
    assert "error" not in result.stdout.str().lower()


def test_pyi_file_without_doctests(pytester: pytest.Pytester) -> None:
    """.pyi file without doctests should not collect any tests."""
    result = pytester.runpytest(
        pst.COMMAND, "-v", "--collect-only", _case("no_doctests.pyi")
    )
    # File with no doctests returns exit code 5 (NO_TESTS_COLLECTED)
    no_tests_collected = 5
    assert result.ret == no_tests_collected


def test_success_examples_all_pass(pytester: pytest.Pytester) -> None:
    """All .pyi files in tests/examples/success should pass."""
    result = pytester.runpytest(pst.COMMAND, "-v", str(EXAMPLES.joinpath("success")))
    assert result.ret == 0


def test_failure_examples_have_failures(pytester: pytest.Pytester) -> None:
    """tests/examples/failures should contain failing doctests."""
    result = pytester.runpytest(pst.COMMAND, "-v", str(EXAMPLES.joinpath("failures")))
    assert result.ret != 0


def test_class_doctest(pytester: pytest.Pytester) -> None:
    """Class-level docstring with doctests should be collected and run."""
    result = pytester.runpytest(pst.COMMAND, "-v", _case("cls_test.pyi"))
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*cls_test.pyi::MyClass*PASSED*"])


def test_class_method_doctest(pytester: pytest.Pytester) -> None:
    """Method inside a class should be collected as ClassName.method_name."""
    result = pytester.runpytest(pst.COMMAND, "-v", _case("cls_method.pyi"))
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*cls_method.pyi::MyClass.my_method*PASSED*"])


def test_markdown_fence_doctest(pytester: pytest.Pytester) -> None:
    """Doctests inside markdown code fences should be extracted and run."""
    result = pytester.runpytest(pst.COMMAND, "-v", _case("markdown.pyi"))
    assert result.ret == 0
    result.stdout.fnmatch_lines(["*markdown.pyi::foo*PASSED*"])


def _case(name: str) -> str:
    return str(CASES.joinpath(name))
