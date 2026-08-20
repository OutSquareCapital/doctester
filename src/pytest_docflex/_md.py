from __future__ import annotations

import ast
from abc import ABC
from typing import TYPE_CHECKING, Self, override

import pytest
from _pytest.assertion.rewrite import (  # ruff: ignore[import-private-name]
    rewrite_asserts,
)

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest._code.code import Traceback

    from ._definitions import Parsed


class MdBlockItem(pytest.Item, ABC):
    def __init__(
        self,
        *,
        name: str,
        parent: pytest.Collector,
        source: str,
        lineno: int,
        globs: dict[str, object],
        **kwargs: object,
    ) -> None:
        # pyrefly: ignore [bad-argument-type]
        super().__init__(name=name, parent=parent, **kwargs)  # pyright: ignore[reportUnknownMemberType, reportArgumentType]
        self._source: str = source
        self._lineno: int = lineno
        self._globs: dict[str, object] = globs
        self._tree: ast.Module = ast.parse(self._source, str(self.path), "exec")

    @classmethod
    def from_parsed(cls, parsed: Parsed, parent: pytest.Collector, pad: int) -> Self:
        padding = "\n" * (parsed.fence.lineno - pad)
        source = padding + "def __docflex_test__():\n"
        for line in parsed.fence.code.splitlines():
            source += "    " + line + "\n"
        return cls.from_parent(  # pyright: ignore[reportUnknownMemberType]
            parent,
            name=parsed.infos.name,
            source=source,
            lineno=parsed.fence.lineno,
            globs=parsed.globs,
        )

    @override
    def runtest(self) -> None:
        filename = str(self.path)
        rewrite_asserts(self._tree, self._source.encode("utf-8"), filename, self.config)
        code = compile(  # pyright: ignore[reportAny]
            self._tree,
            filename,
            "exec",
            flags=annotations.compiler_flag,
            dont_inherit=True,
        )
        exec(code, self._globs)  # pyright: ignore[reportAny]
        _ = self._globs["__docflex_test__"]()  # pyright: ignore[reportCallIssue, reportUnknownVariableType]

    @override
    def reportinfo(self) -> tuple[Path, int, str]:
        return self.path, self._lineno, self.name

    @override
    def _traceback_filter(
        self,
        excinfo: pytest.ExceptionInfo[BaseException],
    ) -> Traceback:
        return excinfo.traceback.cut(path=self.path).filter(excinfo)
