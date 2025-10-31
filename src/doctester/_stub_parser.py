import doctest
import re
from pathlib import Path

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


def _extract_blocks(content: str) -> list[tuple[str, str]]:
    return BLOCK_PATTERN.findall(content)


def _test_block(source: str, expected: str, block_name: str) -> str:
    source_literal = repr(source)
    return f"""
    res = {source}
    if not _assert_test(res, {expected}, "{block_name}", {source_literal}):
        return False"""


def _is_setup_code(source: str) -> bool:
    return source.startswith(("import ", "from ", "def ", "class ")) or (
        "=" in source and not any(op in source for op in ["==", ">=", "<=", "!="])
    )


def _test_generator(
    block_name: str, test_blocks: list[str], setup_code: list[str]
) -> str:
    setup_str = "\n".join(f"    {line}" for line in "\n".join(setup_code).split("\n"))
    tests_str = "\n".join(test_blocks)
    return f"""
def test_{block_name}() -> bool:
{setup_str}
{tests_str}
    return True
"""


def _module_content(pyi_file: Path) -> list[str]:
    return [
        f"# Generated tests from {pyi_file.name}\n",
        ASSERTION_HELPER,
    ]


def _convert_doctest(
    block_name: str,
    docstring: str,
) -> str:
    doctest_parser = doctest.DocTestParser()
    examples = doctest_parser.parse(docstring)

    setup_code: list[str] = []
    test_blocks: list[str] = []

    for example in examples:
        if not isinstance(example, doctest.Example):
            continue

        if doctest.SKIP in example.options:
            continue

        source = example.source.strip()

        if source.startswith("```"):
            continue

        if _is_setup_code(source):
            setup_code.append(source)
        else:
            raw_expected = example.want.strip()
            if not raw_expected or raw_expected == "...":
                continue

            expected = raw_expected.strip()
            test_blocks.append(_test_block(source, expected, block_name))

    if not test_blocks:
        return ""
    return _test_generator(block_name, test_blocks, setup_code)


def generate_test_module_content(pyi_file: Path) -> str | None:
    content = pyi_file.read_text(encoding="utf-8")
    blocks = _extract_blocks(content)
    if not blocks:
        return None

    module_content = _module_content(pyi_file)
    has_tests = False

    for block_name, docstring in blocks:
        test_function = _convert_doctest(block_name, docstring)
        if test_function.strip():
            module_content.append(test_function)
            has_tests = True

    if not has_tests:
        return None

    return "\n".join(module_content)
