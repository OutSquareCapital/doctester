from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, override

import pytest
from pyochain import Iter, Vec, option

if TYPE_CHECKING:
    from pathlib import Path


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
        globs: dict[str, object] = {"__name__": "__main__"}
        padding = "\n" * (self._lineno - 1)
        code = compile(padding + self._source, str(self.path), "exec")
        exec(code, globs)  # ruff: ignore[exec-builtin]

    @override
    def reportinfo(self) -> tuple[Path, int, str]:
        return self.path, self._lineno, self.name

    @override
    def repr_failure(
        self,
        excinfo: pytest.ExceptionInfo[BaseException],
        style: object | None = None,
    ) -> str:
        stack_summary = traceback.StackSummary.extract(traceback.walk_tb(excinfo.tb))
        rawlines = Vec.from_ref(self._source.rstrip("\n").split("\n"))
        maxdigits = len(str(rawlines.len()))
        code_margin = "   "
        pt = _traceback(stack_summary, str(self.path), excinfo)
        numbered_code = _numbered_code(rawlines, self._lineno, maxdigits, code_margin)
        return _full_msg(maxdigits, code_margin, numbered_code, pt)


def _full_msg(maxdigits: int, code_margin: str, numbered_code: str, pt: str) -> str:
    return f"""Error in code block:
{maxdigits * " "}{code_margin}```
{numbered_code}
{maxdigits * " "}{code_margin}```
{pt}
"""


def _traceback(
    stack_summary: traceback.StackSummary,
    test_path: str,
    excinfo: pytest.ExceptionInfo[BaseException],
) -> str:
    return f"""Traceback (most recent call last):
{_pretty_traceback(stack_summary, test_path)}
{excinfo.exconly()}"""


def _numbered_code(
    rawlines: Vec[str],
    start_line: int,
    maxdigits: int,
    code_margin: str,
) -> str:

    return (
        rawlines
        .iter()
        .take(start_line)
        .enumerate(start_line + 1)
        .map_star(lambda i, line: f"{i:>{maxdigits}}{code_margin}{line}")
        .join("\n")
    )


def _pretty_traceback(stack_summary: traceback.StackSummary, test_path: str) -> str:
    return (
        Iter(stack_summary)
        .filter(
            lambda frame_summary: frame_summary.filename == test_path,
        )
        .flat_map(
            _format_summary,
        )
        .join("\n")
    )


def _format_summary(fs: traceback.FrameSummary) -> tuple[str, str]:
    location = f"File {fs.filename}, line {fs.lineno}, in {fs.name}"
    line = option(fs.line).unwrap_or("").lstrip()
    return (
        f"""  {location}""",
        f"    {line}",
    )
