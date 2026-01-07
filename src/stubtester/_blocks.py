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


def parse_markdown(content: str) -> pc.Iter[str]:
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

    def _to_func(title: str, code: str) -> str:
        """Convert the markdown block into a test function string."""
        return f'''def test_{title}():
    """{code}"""
    pass
'''

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
            )
        )
        .map_star(lambda title, code: _to_func(title, code))
    )
