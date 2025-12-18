from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
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
    def from_process(
        cls, result: subprocess.CompletedProcess, *, verbose: bool
    ) -> Self:
        # Parser la sortie pytest: "X failed, Y passed in Z.ZZs"
        passed = failed = 0

        if match := re.search(r"(\d+) passed", result.stdout):
            passed = int(match.group(1))
        if match := re.search(r"(\d+) failed", result.stdout):
            failed = int(match.group(1))

        # Afficher l'output de pytest si verbose ou si échecs
        if verbose or failed > 0:
            print(result.stdout)
            if result.stderr:
                print(result.stderr)

        return cls(total=passed + failed, passed=passed)

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
