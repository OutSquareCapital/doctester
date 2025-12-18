import doctest
import re
from pathlib import Path
from typing import NamedTuple

import pyochain as pc

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
        cleaned_docstring = re.sub(
            r"^\s*```.*$", "", self.docstring, flags=re.MULTILINE
        )

        setup_code = pc.Vec[str].new()
        test_blocks = pc.Vec[str].new()

        for example in doctest.DocTestParser().parse(cleaned_docstring):
            if not isinstance(example, doctest.Example):
                continue

            if doctest.SKIP in example.options:
                continue

            source = example.source.strip()
            if _is_setup_code(source):
                setup_code.append(source)
            else:
                raw_expected = example.want.strip()
                if not raw_expected or raw_expected == "...":
                    continue

                expected = raw_expected.strip()
                test_blocks.append(_test_block(source, expected, self.name))

        if not test_blocks.any():
            return ""
        return test_blocks.into(lambda t: _test_generator(self.name, t, setup_code))


def _extract_blocks(content: str) -> list[Block]:
    return BLOCK_PATTERN.findall(content)


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
    setup_str = "\n".join(f"    {line}" for line in "\n".join(setup_code).split("\n"))
    return f"""
def test_{block_name}() -> bool:
{setup_str}
{test_blocks.join("\n")}
    return True
"""


def _module_content(pyi_file: Path) -> pc.Vec[str]:
    return pc.Vec(
        [
            f"# Generated tests from {pyi_file.name}\n",
            ASSERTION_HELPER,
        ]
    )


def generate_test_module_content(pyi_file: Path) -> pc.Option[str]:
    content = pyi_file.read_text(encoding="utf-8")
    blocks = _extract_blocks(content)
    if not blocks:
        return pc.NONE

    module_content = _module_content(pyi_file)
    has_tests = False

    for block in blocks:
        test_function = block.convert()
        if test_function.strip():
            module_content.append(test_function)
            has_tests = True

    if not has_tests:
        return pc.NONE

    return pc.Some(module_content.iter().join("\n"))
