from __future__ import annotations

import ast
from enum import Enum, StrEnum, auto
from typing import TYPE_CHECKING, Final, NamedTuple

if TYPE_CHECKING:
    from pathlib import Path

type HasDoc = ast.FunctionDef | ast.ClassDef | ast.Module
"""Any AST node susceptible to have testable docstrings."""


PY_MARKER: Final[frozenset[str]] = frozenset({"py", "python"})
"""All possible fence markers for Python code blocks in Markdown docstrings."""
DOCLINE = ">>>"
"""The marker for doctest-style code blocks in Markdown docstrings."""
FENCE_MARKERS: Final[frozenset[str]] = frozenset({"`", "~"})
"""All possible fence markers for fenced code blocks in Markdown docstrings."""
MD_LIMIT: Final = 3
"""Max number of spaces allowed before a fenced code block in Markdown docstrings."""
GLOBS: Final[dict[str, str]] = {"__name__": "__main__"}
"""Globals for executing code blocks via `exec()`."""


class Parsed(NamedTuple):
    """Parsed doc data."""

    fence: Fence
    kind: TestKind
    """The kind of test extracted from the docstring (doctest, markdown, or none)."""
    infos: TestInfos
    """Basic, static information about the test (name and path)."""
    globs: dict[str, str]


class Fence(NamedTuple):
    code: str
    lineno: int


class TestInfos(NamedTuple):
    """Basic, static informations about a test extracted from a docstring."""

    name: str
    file: File


class File(NamedTuple):
    kind: FileKind
    name: str
    path: Path

    @classmethod
    def new(cls, path: Path) -> File:
        return cls(FileKind(path.suffix), name=str(path.stem), path=path)


class FileKind(StrEnum):
    """All possible file kinds that can be collected by the plugin."""

    PY = ".py"
    PYI = ".pyi"
    MD = ".md"


class TestKind(Enum):
    """Possible kinds of tests extracted from docstrings."""

    MARKDOWN = auto()
    """A fenced Python code block in a docstring, e.g. `assert x == y`."""
    DOCTEST = auto()
    """A fenced Python code block in a docstring containing `>>>` prompts."""
    NONE = auto()
    """Absence of both code block kinds."""
