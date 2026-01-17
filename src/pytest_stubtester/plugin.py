"""Pytest plugin for discovering and running doctests from .pyi stub files."""

import ast
import doctest
from collections.abc import Iterator
from functools import partial
from pathlib import Path
from typing import TypeIs

import pyochain as pc
import pytest

type IsDef = ast.FunctionDef | ast.ClassDef


class PyiModule(pytest.Module):
    """Custom pytest Module for collecting doctests from .pyi files."""

    @staticmethod
    def _run_doctest(dtest: doctest.DocTest) -> None:
        runner = doctest.DocTestRunner(verbose=False)
        runner.run(dtest)
        if runner.failures:
            failure_msgs = (
                pc.Iter(dtest.examples)
                .enumerate()
                .filter_star(lambda _, ex: ex.exc_msg is not None)
                .map_star(lambda _, ex: f"Line {ex.lineno}: {ex.source.strip()}")
                .join("\n")
            )
            pytest.fail(
                f"Doctest failed: {runner.failures} failures\n{failure_msgs}",
                pytrace=False,
            )

    def collect(self) -> Iterator[pytest.Item]:
        """Collect all doctests from the .pyi file.

        Yields:
            pytest.Item: pytest.Function items for each doctest.

        """
        return (
            _extract_doctests_from_ast(self.path)
            .map_star(
                lambda name, doc, lineno: (
                    name,
                    doctest.DocTestParser().get_doctest(
                        doc,
                        globs={},
                        name=name,
                        filename=str(self.path),
                        lineno=lineno,
                    ),
                )
            )
            .filter_star(lambda _, test: bool(test.examples))
            .map_star(
                lambda name, test: pytest.Function.from_parent(  # type: ignore[arg-type]
                    name=name,
                    parent=self,
                    callobj=partial(self._run_doctest, test),
                )
            )
        )


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options for the stubtester plugin.

    Args:
        parser (pytest.Parser): Pytest command-line parser.

    """
    parser.addoption(
        "--pyi-enabled",
        action="store_true",
        default=False,
        help="Enable automatic .pyi file collection and doctest execution",
    )


@pytest.hookimpl(trylast=True)
def pytest_collect_file(
    file_path: Path,
    parent: pytest.Collector,
) -> PyiModule | None:
    """Collect .pyi files for doctest execution.

    Args:
        file_path (Path): Path to the file being collected.
        parent (pytest.Collector): Parent collector node.

    Returns:
        PyiModule | None: PyiModule instance if .pyi file and enabled, None otherwise.

    """
    if not parent.config.getoption("--pyi-enabled"):
        return None

    if file_path.suffix.lower() != ".pyi":
        return None

    return PyiModule.from_parent(parent=parent, path=file_path)  # type: ignore[arg-type]


def _extract_doctests_from_ast(file_path: Path) -> pc.Iter[tuple[str, str, int]]:
    tree = _get_tree(file_path)
    if tree.is_err():
        return pc.Iter[tuple[str, str, int]].new()

    module_docstring = ast.get_docstring(tree.unwrap())
    if module_docstring and ">>>" in module_docstring:
        return pc.Iter([(file_path.stem, module_docstring, 1)])

    return (
        pc.Iter(tree.unwrap().body)
        .filter(_is_def)
        .flat_map(lambda node: _recurse_extract(node))
    )


def _get_tree(file_path: Path) -> pc.Result[ast.Module, None]:
    try:
        return pc.Ok(
            ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        )
    except SyntaxError:
        return pc.Err(None)


def _recurse_extract(node: IsDef, prefix: str = "") -> Iterator[tuple[str, str, int]]:
    docstring = ast.get_docstring(node)
    full_name = f"{prefix}{node.name}" if prefix else node.name

    if docstring and ">>>" in docstring:
        yield (full_name, docstring, node.lineno)
    if isinstance(node, ast.ClassDef):
        return (
            pc.Iter(node.body)
            .filter(_is_def)
            .flat_map(lambda n: _recurse_extract(n, f"{full_name}."))
        )


def _is_def(n: object) -> TypeIs[IsDef]:
    return isinstance(n, ast.FunctionDef | ast.ClassDef)
