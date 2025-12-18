from dataclasses import dataclass
from enum import StrEnum
from typing import Self


class Dunders(StrEnum):
    PY_INIT = "__init__.py"
    STUB_INIT = "__init__.pyi"
    PY_PATH = "__path__"


@dataclass(slots=True, frozen=True)
class TestResult:
    total: int
    passed: int

    @property
    def failed(self) -> int:
        return self.total - self.passed

    def show(self) -> Self:
        """Display the test result summary."""
        if self.total > 0:
            print(f"Tests Result: {self.passed}/{self.total} passed.")
        else:
            print("No tests found.")
        return self

    def join_with(self, other: Self) -> Self:
        return self.__class__(
            total=self.total + other.total,
            passed=self.passed + other.passed,
        )
