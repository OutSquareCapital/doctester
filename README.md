# pytest-external

A pytest plugin for testing doctests in `.pyi` or `.md` files.

Designed for **Cython/PyO3/Rust extensions**, **stub-only packages**, or **documentation testing**.

Works with both **doctests** (i.e `>>>` lines) and **markup code blocks** (i.e. \`\`\`python ...\`\`\` blocks).

## 📦 Installation

```shell
uv add git+https://github.com/OutSquareCapital/pytest-external.git
```

## 🚀 Quick Start

```shell
uv run pytest <path_to_tests> --ext
```

### Auto-Enable

**Via `pyproject.toml`:**

```toml
[tool.pytest.ini_options]
addopts = ["--external"]
```

**Via `conftest.py`:**

```python
def pytest_configure(config: object) -> None:
    config.option.external_enabled = True  # type: ignore[attr-defined]
```

## 📝 Example

The following block can be handled either directly in this file as a markdown test, or copy-pasted in a stub file (e.g. `foo.pyi`) and run with pytest.

```python
def add(a: int, b: int) -> int:
    """Add two numbers.

    >>> 2 + 3
    5

    """

# Also works with markup code blocks:
def multiply(a: int, b: int) -> int:
    """Multiply two numbers.

    ```python
    from operator import mul

    assert mul(3, 4) == 12
    ```
    """

def failed_test(a: int, b: int) -> int:
    """Does not pass.

    ```python
    import pytest
    with pytest.raises(AssertionError):
        assert 1 + 1 == 3
    ```
    """

```

### Dependencies

- Python 3.13>=
- [pyochain](https://github.com/OutSquareCapital/pyochain) for internal implementation
