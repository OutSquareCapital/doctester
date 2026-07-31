# pytest-stubtester

A pytest plugin for testing doctests in `.pyi` stub files.

Designed for **Cython/PyO3/Rust extensions** or **stub-only packages**.

Works with both **doctests** (i.e `>>>` lines) and **markup code blocks** (i.e. \`\`\`python ...\`\`\` blocks).

## 📦 Installation

```shell
uv add git+https://github.com/OutSquareCapital/pytest-stubtester.git
```

## 🚀 Quick Start

```shell
uv run pytest <path_to_tests> --stubs
```

### Auto-Enable

**Via `pyproject.toml`:**

```toml
[tool.pytest.ini_options]
addopts = ["--stubs"]
```

**Via `conftest.py`:**

```python
def pytest_configure(config: object) -> None:
    config.option.pyi_enabled = True  # type: ignore[attr-defined]
```

## 📝 Example

Create a `foo.pyi` file with the following content:

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
    assert 1 + 1 == 3
    ```
    """

def failed_docttest(a: int, b: int) -> int:
    """Does not pass.

    >>> 1 + 1
    3
    """

```

Run with pytest

```shell
uv run pytest foo.pyi --stubs
```

Output:

```shell
plugins: stubtester-0.8.0
collected 4 items                                                                                                                                                                                                                                          

foo.pyi ..FF                                                                                                                                                                                                                                         [100%]

======================================================================================================================== FAILURES =========================================================================================================================
_______________________________________________________________________________________________________________________ failed_test _______________________________________________________________________________________________________________________

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
>       assert 1 + 1 == 3
        ```
        """
E       assert (1 + 1) == 3

foo.pyi:23: AssertionError
________________________________________________________________________________________________________________ [doctest] failed_docttest ________________________________________________________________________________________________________________
029 Does not pass.
030 
031 >>> 1 + 1
Expected:
    3
Got:
    2

C:\Users\tibo\python_codes\doctester\foo.pyi:31: DocTestFailure
================================================================================================================= short test summary info =================================================================================================================
FAILED foo.pyi::failed_test - assert (1 + 1) == 3
FAILED foo.pyi::failed_docttest
=============================================================================================================== 2 failed, 2 passed in 0.20s ===============================================================================================================
```

### Dependencies

- Python 3.13>=
- [pyochain](https://github.com/OutSquareCapital/pyochain) for internal implementation
