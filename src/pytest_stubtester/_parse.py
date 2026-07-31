from __future__ import annotations

import ast
import re
from enum import Enum, auto
from typing import TYPE_CHECKING, NamedTuple

from pyochain import Iter, Null, Some, Vec, option

if TYPE_CHECKING:
    from pathlib import Path

    from pyochain.abc import PyoIterator

MARKDOWN_BLOCK = re.compile(r"```(?:python|py)\n(.*?)\n```", re.DOTALL)
"""Pattern to extract Python code blocks from Markdown-formatted docstrings.

Two flavours are supported:
- doctest style (contains `>>>`), compared against expected output
- "standard" style (e.g. `assert x == y`), simply executed for side effects/errors
"""


type HasDoc = ast.FunctionDef | ast.ClassDef | ast.Module


class TestKind(Enum):
    MARKDOWN = auto()
    DOCTEST = auto()
    NONE = auto()


class Parsed(NamedTuple):
    """Parsed doc information as a tuple of: name, docstring, line number, test kind."""

    name: str
    code: str
    lineno: int
    path: Path
    kind: TestKind


def _classify(
    doc: str,
    name: str,
    lineno: int,
    path: Path,
) -> Parsed:
    # Kind must be decided before the fence markers are stripped by extraction,
    # otherwise a fenced `assert`-style block can never match "```py" again.
    match Vec.from_ref(MARKDOWN_BLOCK.findall(doc)).then(lambda m: m.iter().join("\n")):
        case Some(code) if ">>>" in code:
            return Parsed(name, code, lineno, path, TestKind.DOCTEST)
        case Some(code):
            return Parsed(name, code, lineno, path, TestKind.MARKDOWN)
        case Null() if ">>>" in doc:
            return Parsed(name, doc, lineno, path, TestKind.DOCTEST)
        case Null():
            return Parsed(name, doc, lineno, path, TestKind.NONE)


def parse_all(
    node: ast.AST,
    path: Path,
    prefix: str = "",
) -> PyoIterator[Parsed]:

    def _get_doc(node: HasDoc, name: str, lineno: int) -> PyoIterator[Parsed]:
        return (
            option(ast.get_docstring(node))
            .map(lambda doc: _classify(doc, name, lineno, path))
            .iter()
        )

    match node:
        case ast.ClassDef():
            full_name = f"{prefix}{node.name}" if prefix else node.name
            return _get_doc(node, full_name, node.lineno).chain(
                Iter(node.body)
                .map(
                    lambda n: parse_all(n, path, f"{full_name}."),
                )
                .flatten(),
            )
        case ast.FunctionDef():
            full_name = f"{prefix}{node.name}" if prefix else node.name
            return _get_doc(node, full_name, node.lineno)
        case ast.Module():
            return _get_doc(node, path.stem, 1).chain(
                Iter(node.body).map(lambda n: parse_all(n, path, prefix)).flatten(),
            )
        case _:
            return Iter(())
