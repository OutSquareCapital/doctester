from __future__ import annotations

import ast
import re
import textwrap
from enum import Enum, auto
from typing import TYPE_CHECKING, NamedTuple

from pyochain import Iter, Null, Some, Vec, option

if TYPE_CHECKING:
    from pathlib import Path

    from pyochain.abc import PyoIterator

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
    doc_lineno: int,
    path: Path,
) -> Parsed:
    # Kind must be decided before the fence markers are stripped by extraction,
    # otherwise a fenced `assert`-style block can never match "```py" again.
    match option(MARKDOWN_BLOCK.search(doc)):
        case Some(fence):
            code = (
                Vec
                .from_ref(MARKDOWN_BLOCK.findall(doc))
                .iter()
                .map(textwrap.dedent)
                .join("\n")
            )
            # +1 skips past the fence marker line itself, down to the code.
            lineno = doc_lineno + doc[: fence.start()].count("\n") + 1
            kind = TestKind.DOCTEST if ">>>" in code else TestKind.MARKDOWN
            return Parsed(name, code, lineno, path, kind)
        case Null():
            kind = TestKind.DOCTEST if ">>>" in doc else TestKind.NONE
            return Parsed(name, doc, doc_lineno, path, kind)


def parse_all(
    node: ast.AST,
    path: Path,
    prefix: str = "",
) -> PyoIterator[Parsed]:

    def _get_doc(node: HasDoc, name: str) -> PyoIterator[Parsed]:
        return (
            option(ast.get_docstring(node))
            .map(lambda doc: _classify(doc, name, node.body[0].lineno, path))
            .iter()
        )

    match node:
        case ast.ClassDef():
            full_name = f"{prefix}{node.name}" if prefix else node.name
            return _get_doc(node, full_name).chain(
                Iter(node.body)
                .map(
                    lambda n: parse_all(n, path, f"{full_name}."),
                )
                .flatten(),
            )
        case ast.FunctionDef():
            full_name = f"{prefix}{node.name}" if prefix else node.name
            return _get_doc(node, full_name)
        case ast.Module():
            return _get_doc(node, path.stem).chain(
                Iter(node.body).map(lambda n: parse_all(n, path, prefix)).flatten(),
            )
        case _:
            return Iter(())
