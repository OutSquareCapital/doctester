from __future__ import annotations

import textwrap
from abc import ABC
from typing import final, override

from pyochain import NONE, Iter, Null, Option, Some, Vec
from pyochain.abc import PyoIterator

from ._definitions import FENCE_MARKERS, MD_LIMIT, PY_MARKER, Fence


class ParserIterator(PyoIterator[Fence], ABC):
    __slots__ = ("buf", "fence_len", "inner", "marker", "start_lineno")  # pyright: ignore[reportUnannotatedClassAttribute, reportIncompatibleUnannotatedOverride]

    def __init__(self, text: str) -> None:
        self.marker: Option[str] = NONE
        self.fence_len: int = 0
        self.start_lineno: int = 0
        self.buf: Option[Vec[str]] = NONE
        self.inner: PyoIterator[tuple[int, str]] = Iter(text.splitlines()).enumerate(
            start=1
        )

    def _try_open_fence(self, txt: str, lineno: int) -> None:
        if not txt or txt[0] not in FENCE_MARKERS:
            return
        else:
            ch = txt[0]
            n = len(txt) - len(txt.lstrip(ch))
            if n < MD_LIMIT:
                return
            else:
                self.marker = Some(ch)
                self.fence_len = n
                self.start_lineno = lineno
                info = txt[n:].strip()
                self.buf = Some(Vec[str](())) if info in PY_MARKER else NONE

    def _reset(self) -> None:
        self.marker = NONE
        self.fence_len = 0
        self.buf = NONE


@final
class MdParser(ParserIterator):
    __slots__ = ()  # pyright: ignore[reportIncompatibleUnannotatedOverride]

    @override
    def __next__(self) -> Fence:
        while True:
            lineno, txt = self.inner.__next__()
            indent = len(txt) - len(txt.lstrip(" "))
            txt = txt if indent > MD_LIMIT else txt[indent:]

            match self.marker:
                case Null():
                    self._try_open_fence(txt, lineno)
                    continue
                case Some(marker):
                    n = len(txt) - len(txt.lstrip(marker))
                    if n >= self.fence_len and (txt[n:].isspace() or n == len(txt)):
                        match self.buf:
                            case Some(b):
                                self._reset()
                                return Fence(b.iter().join("\n"), self.start_lineno)
                            case Null():
                                self._reset()
                    else:
                        _ = self.buf.inspect(lambda buf: buf.append(txt))  # ruff: ignore[function-uses-loop-variable]


@final
class PyParser(ParserIterator):
    __slots__ = ()  # pyright: ignore[reportIncompatibleUnannotatedOverride]

    @override
    def __next__(self) -> Fence:
        while True:
            lineno, raw = self.inner.__next__()
            txt = raw.lstrip(" ")

            match self.marker:
                case Null():
                    self._try_open_fence(txt, lineno)
                    continue
                case Some(marker):
                    n = len(txt) - len(txt.lstrip(marker))
                    if n >= self.fence_len and (txt[n:].isspace() or n == len(txt)):
                        match self.buf:
                            case Some(b):
                                self._reset()
                                return Fence(
                                    textwrap.dedent(b.iter().join("\n")),
                                    self.start_lineno,
                                )
                            case Null():
                                self._reset()
                    else:
                        _ = self.buf.inspect(lambda buf: buf.append(raw))  # ruff: ignore[function-uses-loop-variable]
