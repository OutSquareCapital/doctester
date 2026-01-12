"""Pytest plugin for discovering and running doctests from .pyi stub files."""

import doctest
from collections.abc import Iterator
from functools import partial
from pathlib import Path

import pyochain as pc
import pytest


class PyiModule(pytest.Module):
    """Custom pytest Module for collecting doctests from .pyi files."""

    @staticmethod
    def _run_doctest(dtest: doctest.DocTest) -> None:
        """Run a single doctest.

        Args:
            dtest: The doctest to run.

        """
        runner = doctest.DocTestRunner(verbose=False)
        runner.run(dtest)
        # Check for failures
        if runner.failures:
            pytest.fail(f"Doctest failed: {runner.failures} failures")

    def collect(self) -> Iterator[pytest.Item]:
        """Collect all doctests from the .pyi file.

        Yields:
            pytest.Item: pytest.Function items for each doctest.

        """
        # Remove triple quotes from docstrings to avoid pollution
        # pytester.makefile adds closing """ which polluates expected output

        text = (
            pc.Iter(self.path.read_text(encoding="utf-8").splitlines())
            .map(lambda line: line if not line.strip().startswith('"""') else "")
            .join("\n")
        )
        fake_module = type(
            self.path.stem,
            (),
            {"__doc__": text, "__file__": str(self.path)},
        )()

        return (
            pc.Iter(doctest.DocTestFinder().find(fake_module, name=self.path.stem))
            .filter(lambda test: bool(test.examples))
            .map(
                lambda test: pytest.Function.from_parent(  # type: ignore[arg-type]
                    name=test.name,
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
