from __future__ import annotations

import ast
from typing import TYPE_CHECKING, override

import pytest
from _pytest.assertion.rewrite import (  # ruff: ignore[import-private-name]
    rewrite_asserts,
)

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest._code.code import Traceback


class MarkdownCodeItem(pytest.Item):
    """A pytest item that executes a Markdown Python code block via exec()."""

    def __init__(
        self,
        *,
        name: str,
        parent: pytest.Collector,
        source: str,
        lineno: int,
        **kwargs: object,
    ) -> None:
        # pyrefly: ignore [bad-argument-type]
        super().__init__(name=name, parent=parent, **kwargs)  # pyright: ignore[reportUnknownMemberType, reportArgumentType]
        self._source: str = source
        self._lineno: int = lineno

    @override
    def runtest(self) -> None:
        filename = str(self.path)
        tree = ast.parse(self._source, filename, "exec")
        _ = ast.increment_lineno(tree, self._lineno - 1)
        rewrite_asserts(tree, self._source.encode("utf-8"), filename, self.config)
        code = compile(tree, filename, "exec")
        exec(code, {"__name__": "__main__"})  # ruff: ignore[exec-builtin]

    @override
    def reportinfo(self) -> tuple[Path, int, str]:
        return self.path, self._lineno, self.name

    @override
    def _traceback_filter(
        self,
        excinfo: pytest.ExceptionInfo[BaseException],
    ) -> Traceback:
        return excinfo.traceback.cut(path=self.path).filter(excinfo)
