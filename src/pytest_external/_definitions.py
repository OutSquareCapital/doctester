from __future__ import annotations

import ast
import re
from enum import Enum, auto
from typing import TYPE_CHECKING, Literal, NamedTuple

if TYPE_CHECKING:
    from pathlib import Path

MARKDOWN_BLOCK = re.compile(
    r"^[ \t]*```(?:python|py)\n(.*?)\n[ \t]*```",
    re.DOTALL | re.MULTILINE,
)
"""Pattern to extract Python code blocks from Markdown-formatted docstrings.

Two flavours are supported:
- doctest style (contains `>>>`), compared against expected output
- "standard" style (e.g. `assert x == y`).

Fence markers may be indented (e.g. nested under an "Example:" line).

The captured code is dedented in `_classify` before being returned.
"""


type HasDoc = ast.FunctionDef | ast.ClassDef | ast.Module
"""Any AST node susceptible to have testable docstrings."""
FileKind = Literal[".pyi", ".md", ".py"]
"""All possible file kinds that can be collected by the plugin."""


class Parsed(NamedTuple):
    """Parsed doc data."""

    fence: Fence
    kind: TestKind
    """The kind of test extracted from the docstring (doctest, markdown, or none)."""
    infos: TestInfos
    """Basic, static information about the test (name and path)."""


class Fence(NamedTuple):
    code: str
    lineno: int


class TestInfos(NamedTuple):
    """Basic, static informations about a test extracted from a docstring."""

    name: str
    path: Path


class TestKind(Enum):
    """Possible kinds of tests extracted from docstrings."""

    MARKDOWN = auto()
    """A fenced Python code block in a docstring, e.g. `assert x == y`."""
    DOCTEST = auto()
    """A fenced Python code block in a docstring containing `>>>` prompts."""
    NONE = auto()
    """Absence of both code block kinds."""
