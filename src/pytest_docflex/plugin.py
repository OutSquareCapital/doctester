"""Pytest plugin for flexibly testing code residing in documentation."""

from __future__ import annotations

from typing import TYPE_CHECKING, override

import pytest

from ._definitions import File, FileKind
from ._parse import collect_all_tests

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

COMMAND = "--docflex"


class ExtModule(pytest.Module):
    """Custom pytest Module for collecting tests for the plugin."""

    @override
    def collect(self) -> Iterator[pytest.Item]:

        file = File.new(self.path)
        return collect_all_tests(self, file)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line options for the docflex plugin.

    Args:
        parser (pytest.Parser): Pytest command-line parser.

    """
    parser.addoption(
        COMMAND,
        action="store_true",
        default=False,
        help="Enable automatic execution for docflex plugin.",
    )


@pytest.hookimpl(trylast=True)
def pytest_collect_file(
    file_path: Path,
    parent: pytest.Collector,
) -> pytest.Module | None:
    """Collect files for docflex plugin execution.

    Args:
        file_path (Path): Path to the file being collected.
        parent (pytest.Collector): Parent collector node.

    Returns:
        pytest.Module | None

    """
    if not parent.config.getoption(COMMAND) or file_path.suffix not in FileKind:
        return None
    return ExtModule.from_parent(parent=parent, path=file_path)  # pyright: ignore[reportUnknownMemberType]
