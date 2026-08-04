from __future__ import annotations

import ast
import textwrap
from doctest import DocTestParser
from typing import TYPE_CHECKING

from _pytest.doctest import (  # ruff: ignore[import-private-name]
    DoctestItem,
    _get_runner,  # pyright: ignore[reportPrivateUsage]
)
from pyochain import Iter, Null, Option, Some, Vec, option

from ._definitions import MARKDOWN_BLOCK, HasDoc, Parsed, TestInfos, TestKind
from ._md import MarkdownCodeItem

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    import pytest
    from _pytest.doctest import DoctestModule
    from pyochain.abc import PyoIterator


def collect_all_tests(
    parent: DoctestModule,
    path: Path,
) -> Iterator[pytest.Item]:
    txt = path.read_text(encoding="utf-8")
    filename = str(path)
    return _parse_all(ast.parse(txt, filename), path).filter_map(
        lambda parsed: _to_item(parsed, filename, parent),
    )


def _to_item(
    parsed: Parsed,
    filename: str,
    parent: DoctestModule,
) -> Option[pytest.Item]:
    match parsed.kind:
        case TestKind.NONE:
            return Null()
        case TestKind.MARKDOWN:
            item = MarkdownCodeItem.from_parent(  # pyright: ignore[reportUnknownMemberType]
                parent,
                name=parsed.infos.name,
                source=parsed.code,
                lineno=parsed.lineno,
            )
            return Some(item)
        case TestKind.DOCTEST:
            tst = DocTestParser().get_doctest(
                parsed.code,
                {},
                parsed.infos.name,
                filename,
                parsed.lineno,
            )
            if tst.examples:
                item = DoctestItem.from_parent(
                    parent,
                    name=parsed.infos.name,
                    runner=_get_runner(verbose=False),
                    dtest=tst,
                )
                return Some(item)
            return Null()


def _parse_all(
    node: ast.AST,
    path: Path,
    prefix: str = "",
) -> PyoIterator[Parsed]:

    match node:
        case ast.FunctionDef():
            infos = TestInfos(_name_from_node(node, prefix), path)
            return _get_doc(node, infos)
        case ast.ClassDef():
            infos = TestInfos(_name_from_node(node, prefix), path)
            return _get_doc(node, infos).chain(
                _get_subnodes(node.body, infos.name, path),
            )
        case ast.Module():
            infos = TestInfos(path.stem, path)
            return _get_doc(node, infos).chain(
                _get_subnodes(node.body, prefix, path),
            )
        case _:
            return Iter(())


def _name_from_node(node: ast.FunctionDef | ast.ClassDef, prefix: str) -> str:
    return f"{prefix}.{node.name}" if prefix else node.name


def _get_subnodes(
    nodes: list[ast.stmt],
    prefix: str,
    path: Path,
) -> PyoIterator[Parsed]:
    return Iter(nodes).flat_map(lambda node: _parse_all(node, path, prefix))


def _get_doc(node: HasDoc, infos: TestInfos) -> PyoIterator[Parsed]:
    return (
        option(ast.get_docstring(node))
        .map(lambda doc: _classify(doc, infos, node.body[0].lineno))
        .iter()
    )


def _classify(
    doc: str,
    infos: TestInfos,
    doc_lineno: int,
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
            return Parsed(code, lineno, kind, infos)
        case Null():
            kind = TestKind.DOCTEST if ">>>" in doc else TestKind.NONE
            return Parsed(doc, doc_lineno, kind, infos)
