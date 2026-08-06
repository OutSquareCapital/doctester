"""Pytest plugin for discovering and running doctests from .pyi stub files."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest
from _pytest.doctest import DoctestModule  # ruff: ignore[import-private-name]

from ._definitions import FileKind
from ._parse import collect_all_tests

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

COMMAND = "--external"


class ExtModule(DoctestModule):
    """Custom pytest Module for collecting doctests from non .py files."""

    @override
    # pyrefly: ignore [bad-override]
    def collect(self) -> Iterator[pytest.Item]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return collect_all_tests(self, self.path)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options for the stubtester plugin.

    Args:
        parser (pytest.Parser): Pytest command-line parser.

    """
    parser.addoption(
        COMMAND,
        action="store_true",
        default=False,
        help="Enable automatic non .py file collection and doctest execution",
    )


@pytest.hookimpl(trylast=True)
def pytest_collect_file(
    file_path: Path,
    parent: pytest.Collector,
) -> pytest.Module | None:
    """Collect files for doctest execution.

    Args:
        file_path (Path): Path to the file being collected.
        parent (pytest.Collector): Parent collector node.

    Returns:
        pytest.Module | None

    """
    if not parent.config.getoption(COMMAND) or file_path.suffix not in FileKind:
        return None
    return ExtModule.from_parent(parent=parent, path=file_path)  # pyright: ignore[reportUnknownMemberType]
