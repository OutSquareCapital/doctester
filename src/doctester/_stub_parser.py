import doctest
import re
from pathlib import Path
from typing import NamedTuple

import pyochain as pc
from typing_extensions import TypeIs

BLOCK_PATTERN = re.compile(
    r"(?:def|class)\s+(\w+)(?:\[[^\]]*\])?\s*(?:\([^)]*\))?\s*(?:->[^:]+)?"
    r':\s*"""(.*?)"""',
    re.DOTALL,
)

ASSERTION_HELPER = """
from typing import Any
def _assert_test(got: Any, expected: Any, name: str, source: str) -> bool:
    if got != expected:
        print(f'--- ERROR IN: {name} ---')
        print(f'Source  : {source}')
        print(f'Got     : {got!r}')
        print(f'Expected: {expected!r}')
        return False
    return True
"""

PY_KWORDS: tuple[str, ...] = ("import ", "from ", "def ", "class ")
PY_OP = ("==", ">=", "<=", "!=")


class Block(NamedTuple):
    name: str
    docstring: str

    def convert(self) -> str:
        """Convert docstring examples to executable test function."""
        cleaned_docstring = re.sub(
            r"^\s*```.*$", "", self.docstring, flags=re.MULTILINE
        )

        setup_code = pc.Vec[str].new()
        test_blocks = pc.Vec[str].new()

        def _is_example(obj: object) -> TypeIs[doctest.Example]:
            return isinstance(obj, doctest.Example)

        def _process_example(example: doctest.Example) -> None:
            source = example.source.strip()
            if _is_setup_code(source):
                setup_code.append(source)
            else:
                raw_expected = example.want.strip()
                if raw_expected and raw_expected != "...":
                    test_blocks.append(_test_block(source, raw_expected, self.name))

        (
            pc.Iter(doctest.DocTestParser().parse(cleaned_docstring))
            .filter(_is_example)
            .filter(lambda ex: doctest.SKIP not in ex.options)
            .for_each(_process_example)
        )

        if not test_blocks.any():
            return ""
        return test_blocks.into(lambda t: _test_generator(self.name, t, setup_code))


def _test_block(source: str, expected: str, block_name: str) -> str:
    return f"""
    res = {source}
    if not _assert_test(res, {expected}, "{block_name}", {source!r}):
        return False"""


def _is_setup_code(source: str) -> bool:
    return source.startswith(PY_KWORDS) or (
        "=" in source and not any(op in source for op in PY_OP)
    )


def _test_generator(
    block_name: str, test_blocks: pc.Vec[str], setup_code: pc.Vec[str]
) -> str:
    """Generate test function from setup code and test blocks."""

    def _format(x: pc.Iter[str]) -> pc.Iter[str]:
        return pc.Iter(x.join("\n").split("\n"))

    setup_str = (
        setup_code.iter().into(_format).map(lambda line: f"    {line}").join("\n")
    )
    return f"""
def test_{block_name}() -> bool:
{setup_str}
{test_blocks.join("\n")}
    return True
"""


def generate_test_module_content(pyi_file: Path) -> pc.Option[str]:
    blocks: pc.Seq[tuple[str, str]] = pc.Iter(
        BLOCK_PATTERN.findall(pyi_file.read_text(encoding="utf-8"))
    ).collect()
    if not blocks.any():
        return pc.NONE

    return pc.Some(
        pc.Iter(
            [
                f"# Generated tests from {pyi_file.name}\n",
                ASSERTION_HELPER,
            ]
        )
        .chain(blocks.iter().map(lambda t: Block(*t).convert()).filter(str.strip))
        .join("\n")
    )
