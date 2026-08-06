from __future__ import annotations

import ast
import textwrap
from doctest import DocTestParser
from typing import TYPE_CHECKING, Final

from _pytest.doctest import (  # ruff: ignore[import-private-name]
    DoctestItem,
    _get_checker,  # pyright: ignore[reportPrivateUsage]
    _get_continue_on_failure,  # pyright: ignore[reportPrivateUsage]
    _get_runner,  # pyright: ignore[reportPrivateUsage]
    get_optionflags,
)
from pyochain import Iter, Null, Option, Some, Vec, option

from ._definitions import (
    DOCLINE,
    MARKDOWN_BLOCK,
    PYFENCE,
    Fence,
    FileKind,
    HasDoc,
    Parsed,
    TestInfos,
    TestKind,
)
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
    return _get_iterator(txt, path, filename).filter_map(
        lambda parsed: _to_item(parsed, filename, parent),
    )


def _get_iterator(txt: str, path: Path, filename: str) -> PyoIterator[Parsed]:
    match path.suffix:
        case FileKind.PYI | FileKind.PY:
            return _parse_pyi(
                ast.parse(txt, filename),
                path,
            )
        case FileKind.MD:
            return Iter(_parse_md(txt)).map(
                lambda fence: Parsed(
                    fence,
                    TestKind.DOCTEST if DOCLINE in fence.code else TestKind.MARKDOWN,
                    TestInfos(f"{path.stem}:{fence.lineno}", path),
                ),
            )
        case _:
            return Iter(())


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
                source=parsed.fence.code,
                lineno=parsed.fence.lineno,
            )
            return Some(item)
        case TestKind.DOCTEST:
            if parsed.infos.path.suffix == FileKind.PY:
                globs = parent.obj.__dict__.copy()  # pyright: ignore[reportAny]
            else:
                globs = {"__name__": "__main__"}

            tst = DocTestParser().get_doctest(
                parsed.fence.code,
                globs,
                parsed.infos.name,
                filename,
                parsed.fence.lineno,
            )
            if tst.examples:
                config = parent.config
                item = DoctestItem.from_parent(
                    parent,
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


def _parse_md(text: str) -> Iterator[Fence]:
    marker: str | None = None
    fence_len = 0
    start_lineno = 0
    limit: Final = 3
    buf: Vec[str] | None = None

    for lineno, line in Vec.from_ref(text.splitlines()).iter().enumerate(start=1):
        indent = len(line) - len(line.lstrip(" "))
        stripped = line if indent > limit else line[indent:]

        if marker is None:
            if not stripped:
                continue

            ch = stripped[0]
            if ch not in {"`", "~"}:
                continue

            n = len(stripped) - len(stripped.lstrip(ch))
            if n < limit:
                continue

            marker = ch
            fence_len = n
            start_lineno = lineno + 1

            info = stripped[n:].strip()

            buf = Vec[str](()) if info in PYFENCE else None
            continue

        # fermeture du fence
        if stripped.startswith(marker):
            n = len(stripped) - len(stripped.lstrip(marker))

            if n >= fence_len and not stripped[n:].strip():
                if buf is not None:
                    yield Fence(
                        buf.iter().join("\n"),
                        start_lineno,
                    )

                marker = None
                fence_len = 0
                buf = None
                continue

        # contenu du fence Python uniquement
        if buf is not None:
            buf.append(line)


def _parse_pyi(
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
    return Iter(nodes).flat_map(lambda node: _parse_pyi(node, path, prefix))


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
            fence = Fence(code, lineno)
            kind = TestKind.DOCTEST if DOCLINE in code else TestKind.MARKDOWN
            return Parsed(fence, kind, infos)
        case Null():
            kind = TestKind.DOCTEST if DOCLINE in doc else TestKind.NONE
            fence = Fence(doc, doc_lineno)
            return Parsed(fence, kind, infos)
