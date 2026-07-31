from __future__ import annotations

import ast
import doctest
from typing import TYPE_CHECKING

from _pytest.doctest import (  # ruff: ignore[import-private-name]
    DoctestItem,
    _get_runner,  # pyright: ignore[reportPrivateUsage]
)
from pyochain import Null, Option, Some

from ._md import MarkdownCodeItem
from ._parse import Parsed, TestKind, parse_all

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    import pytest
    from _pytest.doctest import DoctestModule


def collect_all_tests(
    parent: DoctestModule,
    path: Path,
) -> Iterator[pytest.Item]:
    txt = path.read_text(encoding="utf-8")
    filename = str(path)
    tree = ast.parse(txt, filename)
    return parse_all(tree, path).filter_map(
        lambda parsed: from_parsed(parsed, filename, parent),
    )


def from_parsed(
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
                name=parsed.name,
                source=parsed.code,
                lineno=parsed.lineno,
            )
            return Some(item)
        case TestKind.DOCTEST:
            tst = doctest.DocTestParser().get_doctest(
                parsed.code,
                {},
                parsed.name,
                filename,
                parsed.lineno,
            )
            if tst.examples:
                item = DoctestItem.from_parent(
                    parent,
                    name=parsed.name,
                    runner=_get_runner(verbose=False),
                    dtest=tst,
                )
                return Some(item)
            return Null()
