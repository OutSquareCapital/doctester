from dataclasses import dataclass
from enum import StrEnum


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
