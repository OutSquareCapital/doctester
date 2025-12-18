from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Self

import pyochain as pc


class Dunders(StrEnum):
    PY_INIT = "__init__.py"
    STUB_INIT = "__init__.pyi"
    PY_PATH = "__path__"


@dataclass(slots=True, frozen=True)
class TestResult:
    total: int
    passed: int

    @classmethod
    def from_seq(cls, results: pc.Seq[TestResult]) -> Self:
        """Aggregate multiple test results into one."""
        return cls(
            total=results.iter().map(lambda r: r.total).sum(),
            passed=results.iter().map(lambda r: r.passed).sum(),
        )

    @property
    def failed(self) -> int:
        return self.total - self.passed

    def join_with(self, other: Self) -> Self:
        return self.__class__(
            total=self.total + other.total,
            passed=self.passed + other.passed,
        )
