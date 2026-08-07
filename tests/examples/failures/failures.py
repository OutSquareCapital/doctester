def function_with_bad_docstring() -> None:
    """This has a markdown fence that breaks the parser.

    Example:
    ```python
    >>> 1 + 1
    2
    >>> ```, "this", "is", "bad"):
    ...
    ```
    """


class Foo:
    def __init__(self, data: object) -> None:
        """Initializes the context with Python data.

        Args:
            data (object): The Python data (e.g., dict, list) to query.

        Example:
        ```python
        >>> 1 + 1
        2
        >>> ```, "this", "is", "bad"):
        ...
        """


def failing_test() -> None:
    """Test qui va échouer.

    Example:
    ```python
    >>> 1 + 1 # Expected to fail.
    3
    ```
    """


def failing_test_md() -> None:
    """Test qui va échouer.

    Example:
    ```python
    assert 1 + 1 == 3  # Expected to fail.
    ```
    """


def error_render[V]() -> None:
    """Check error rendering.

    Example:
        ```python
        >>> from pyochain.collections import StableSet
        >>>
        >>> original = {"Alice": 30, "Bob": 25, "Charlie": 35}
        >>> set_obfdfj = StableSet.from_ref(original)
        >>> set_obj
        StableSet('Alice', 'Bob', 'Charlie')
        >>> original["David"] = 40
        >>> set_obj
        StableSet('Alice', 'Bob', 'Charlie', 'David')

        ```
    """


def test_foo() -> None:
    assert 1 + 1 == 3  # ruff: ignore[magic-value-comparison]
