import re

import pyochain as pc


class Patterns:
    """Regex patterns for parsing stub files."""

    BLOCK = re.compile(
        r"^```(\w+)\s*$\n(.*?)^```$",
        re.MULTILINE | re.DOTALL,
    )
    HEADER = re.compile(r"^(#+)\s+(.+)$", re.MULTILINE)
    TITLE = re.compile(r"[^a-zA-Z0-9_]")
    FUNC_NAME = re.compile(r"def (\w+)\(")

    @staticmethod
    def doctest_pattern(stem: str) -> re.Pattern[str]:
        """Create pattern for matching doctest references."""
        return re.compile(f"<doctest {re.escape(stem)}\\.")

    @staticmethod
    def func_pattern(source_path: str) -> re.Pattern[str]:
        """Create pattern for matching function names in test output."""
        return re.compile(rf"{re.escape(source_path)}::([\w.]+)")

    @staticmethod
    def line_pattern(source_path: str) -> re.Pattern[str]:
        """Create pattern for matching line numbers in test output."""
        return re.compile(rf"({re.escape(source_path)}):" + r"(\d+):")


def parse_markdown(content: str) -> pc.Iter[tuple[str, int]]:
    """Parse markdown file and extract code blocks."""
    headers = pc.Iter(Patterns.HEADER.finditer(content)).collect()

    def _find_header_for_block(block_start: int) -> str:
        """Find the closest header before this block."""
        return (
            headers.iter()
            .filter(lambda h: h.start() < block_start)
            .map(lambda h: h.group(2).strip())
            .into(lambda x: pc.Option.if_some(x.last()))
            .unwrap_or("markdown_test")
        )

    return (
        pc.Iter(Patterns.BLOCK.finditer(content))
        .enumerate()
        .filter_star(lambda _, value: value.group(1) in {"py", "python"})
        .map_star(
            lambda idx, value: (
                Patterns.TITLE.sub(
                    "_", f"{_find_header_for_block(value.start())}_{idx}"
                ).strip("_"),
                value.group(2).replace("\\", "\\\\\\\\").replace('"""', '\\"\\"\\"'),
                content[: value.start()].count("\n") + 2,
            )
        )
        .map_star(lambda title, code, line: _to_func(title, code, line))
    )


def _to_func(title: str, code: str, source_line: int) -> tuple[str, int]:
    # Doctest lines start at line 2 of the function (after "def" and docstring start)
    # We need to offset by (source_line - 2) to map back to source
    line_offset = source_line - 2
    return (
        f'''def {title}():
    """{code}"""
    pass
''',
        line_offset,
    )
