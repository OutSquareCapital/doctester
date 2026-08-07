from __future__ import annotations

import ast
from doctest import DocTestParser
from typing import TYPE_CHECKING

from _pytest.doctest import (  # ruff: ignore[import-private-name]
    DoctestItem,
    _get_checker,  # pyright: ignore[reportPrivateUsage]
    _get_continue_on_failure,  # pyright: ignore[reportPrivateUsage]
    _get_runner,  # pyright: ignore[reportPrivateUsage]
    get_optionflags,
)
from pyochain import Iter, Null, Option, Some, option

from ._definitions import (
    DOCLINE,
    GLOBS,
    Fence,
    File,
    FileKind,
    HasDoc,
    Parsed,
    TestInfos,
    TestKind,
)
from ._iterators import MdParser, PyParser
from ._md import MarkdownCodeItem

if TYPE_CHECKING:
    from collections.abc import Iterator

    import pytest
    from pyochain.abc import PyoIterator


def collect_all_tests(
    parent: pytest.Module,
    file: File,
) -> Iterator[pytest.Item]:
    txt = file.path.read_text(encoding="utf-8")
    match file.kind:
        case FileKind.PYI | FileKind.PY:
            return _parse_py(ast.parse(txt, file.name), file).filter_map(
                lambda parsed: _to_item(parsed, file, parent)
            )
        case FileKind.MD:
            globs = GLOBS.copy()
            return (
                MdParser(txt)
                .into_iter()
                .map(lambda fence: _fence_to_parsed(fence, file, globs))
                .filter_map(lambda parsed: _to_item(parsed, file, parent))
            )


def _to_item(
    parsed: Parsed,
    file: File,
    parent: pytest.Module,
) -> Option[pytest.Item]:
    match parsed.kind:
        case TestKind.NONE:
            return Null()
        case TestKind.MARKDOWN:
            item = MarkdownCodeItem.from_parent(  # pyright: ignore[reportUnknownMemberType]
                parent,
                name=parsed.infos.name,
                source=parsed.fence.code,
                lineno=parsed.fence.lineno,
                globs=parsed.globs,
            )
            return Some(item)
        case TestKind.DOCTEST:
            if parsed.infos.file.kind is FileKind.PY:
                globs = parent.obj.__dict__  # pyright: ignore[reportAny]
            else:
                globs = parsed.globs

            tst = DocTestParser().get_doctest(
                parsed.fence.code,
                globs,
                parsed.infos.name,
                file.name,
                parsed.fence.lineno,
            )
            if tst.examples:
                config = parent.config
                item = DoctestItem.from_parent(
                    parent,  # pyright: ignore[reportArgumentType]
                    name=parsed.infos.name,
                    runner=_get_runner(
                        verbose=False,
                        optionflags=get_optionflags(config),
                        checker=_get_checker(),
                        continue_on_failure=_get_continue_on_failure(config),
                    ),
                    dtest=tst,
                )
                return Some(item)
            return Null()


def _parse_py(
    node: ast.AST,
    file: File,
    prefix: str = "",
) -> PyoIterator[Parsed]:

    match node:
        case ast.FunctionDef():
            infos = TestInfos(_name_from_node(node, prefix), file)
            return _get_doc(node, infos)
        case ast.ClassDef():
            infos = TestInfos(_name_from_node(node, prefix), file)
            subnodes = _get_subnodes(node.body, infos.name, file)
            return _get_doc(node, infos).chain(subnodes)
        case ast.Module():
            infos = TestInfos(file.path.stem, file)
            subnodes = _get_subnodes(node.body, prefix, file)
            return _get_doc(node, infos).chain(subnodes)
        case _:
            return Iter(())


def _name_from_node(node: ast.FunctionDef | ast.ClassDef, prefix: str) -> str:
    return f"{prefix}.{node.name}" if prefix else node.name


def _get_doc(node: HasDoc, infos: TestInfos) -> PyoIterator[Parsed]:
    return (
        option(ast.get_docstring(node))
        .map(lambda doc: _classify(doc, infos, node.body[0].lineno))
        .iter()
    )


def _get_subnodes(
    nodes: list[ast.stmt],
    prefix: str,
    file: File,
) -> PyoIterator[Parsed]:
    return Iter(nodes).flat_map(lambda node: _parse_py(node, file, prefix))


def _classify(doc: str, infos: TestInfos, doc_lineno: int) -> Parsed:
    # TODO: Once pyochain is updated, use peekable iterator to avoid once + chain
    globs = GLOBS.copy()
    fences = PyParser(doc).into_iter()
    match fences.next():
        case Some(x):
            source = Iter.once(x).chain(fences).map(lambda f: f.code).join("\n\n")
            return Parsed(
                Fence(source, x.lineno + doc_lineno),
                TestKind.DOCTEST if DOCLINE in source else TestKind.MARKDOWN,
                infos,
                globs,
            )
        case Null():
            kind = TestKind.DOCTEST if DOCLINE in doc else TestKind.NONE
            return Parsed(Fence(doc, doc_lineno), kind, infos, globs)


def _fence_to_parsed(fence: Fence, file: File, globs: dict[str, str]) -> Parsed:
    kind = TestKind.DOCTEST if DOCLINE in fence.code else TestKind.MARKDOWN
    return Parsed(
        Fence(fence.code, fence.lineno),
        kind,
        TestInfos(f"{file.path.stem}:{fence.lineno}", file),
        globs,
    )
