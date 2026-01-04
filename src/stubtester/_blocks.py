import re
from typing import NamedTuple, Self


class Patterns:
    """Regex patterns for parsing stub files."""

    BLOCK = re.compile(
        r"(?:def|class)\s+(\w+)(?:\[[^\]]*\])?\s*(?:\([^)]*\))?\s*(?:->[^:]+)?"
        r':\s*[rRbBfFuU]*"""(.*?)"""',
        re.DOTALL,
    )
    MARKDOWN_BLOCK = re.compile(
        r"^```(\w+)\s*$\n(.*?)^```$",
        re.MULTILINE | re.DOTALL,
    )
    MARKDOWN_HEADER = re.compile(r"^(#+)\s+(.+)$", re.MULTILINE)
    PY_CODE = re.compile(r"^\s*```\w*\s*$", flags=re.MULTILINE)
    LINE_DIRECTIVE = re.compile(r'#\s*line\s+(\d+)\s+"([^"]+)"')
    TEST_FILE = re.compile(
        r"(?:[^\s/\\]*[/\\])*doctests_temp[/\\]([^/\\:]+)(?::(\d+)|::[\w.]+)",
    )
    TEST_NAME = re.compile(r"::([^:\s]+)")

    @classmethod
    def clean(cls, docstring: str) -> str:
        return re.sub(cls.PY_CODE, "", docstring)


class BlockTest(NamedTuple):
    """Represents a testable block extracted from a stub file."""

    name: str
    """The name of the function or class."""
    docstring: str
    """The docstring associated with the function or class."""
    line_number: int
    """The line number in the source file where the block starts."""
    source_file: str
    """The name of the source file."""

    @classmethod
    def from_match(cls, match: re.Match[str], content: str, filename: str) -> Self:
        return cls(
            match.group(1),
            match.group(2),
            content[: match.start()].count("\n") + 1,
            filename,
        )

    def to_func(self) -> str:
        """Convert the block into a test function string."""
        escaped_code = (
            Patterns.clean(self.docstring)
            .replace("\\", "\\\\\\\\")
            .replace('"""', '\\"\\"\\"')
        )
        return f'''# line {self.line_number} "{self.source_file}"
def test_{self.name}():
    """{escaped_code}"""
    pass
'''


class MarkdownBlock(NamedTuple):
    """Represents a code block extracted from a markdown file."""

    title: str
    """The section title from the markdown header."""
    code: str
    """The code content."""
    line_number: int
    """The line number in the source file."""
    source_file: str
    """The name of the source file."""

    def to_func(self) -> str:
        """Convert the markdown block into a test function string."""
        safe_title = re.sub(r"[^a-zA-Z0-9_]", "_", self.title).strip("_")
        escaped_code = self.code.replace("\\", "\\\\\\\\").replace('"""', '\\"\\"\\"')
        return f'''# line {self.line_number} "{self.source_file}"
def test_{safe_title}():
    """{escaped_code}"""
    pass
'''
