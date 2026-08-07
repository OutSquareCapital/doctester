"""Clean test file for doctester."""


def add(x: int, y: int) -> int:
    """Add two numbers.

    Example:
    ```python
    >>> 2 + 3
    5
    >>> 10 + (-5)
    5

    ```
    """  # ruff: ignore[docstring-missing-returns]
    return x + y


def multiply(x: int, y: int) -> int:
    """Multiply two numbers.

    ```python
    >>> 3 * 4
    12
    >>> 0 * 100
    0

    ```
    """  # ruff: ignore[docstring-missing-returns]
    return x * y


def multiply_no_doctest(x: int, y: int) -> int:
    """Multiply two numbers.

    ```python
    assert 3 * 4 == 12
    assert 0 * 100 == 0
    ```
    """  # ruff: ignore[docstring-missing-returns]
    return x * y


"""Stub file with no doctests to test empty file handling."""


def no_docstring() -> None: ...
def empty_docstring() -> None:
    """"""  # ruff: ignore[empty-docstring]


def no_examples() -> None:
    """Function without examples.

    Args:
        None
    """


class EdgeCases:
    """Class with complex signature.

    ```python
    >>> # Testing complex class instantiation patterns
    >>> class Example:
    ...     pass
    >>> obj = Example()
    >>> type(obj).__name__
    'Example'

    ```
    """

    def generic_method[T](self, value: T) -> T:  # ruff: ignore[no-self-use]
        """Method with generic type parameter.

        ```python
        >>> def identity[T](x: T) -> T:
        ...     return x
        >>> identity(42)
        42
        >>> identity("hello")
        'hello'
        >>> identity([1, 2, 3])
        [1, 2, 3]

        ```
        """  # ruff: ignore[docstring-missing-returns]
        return value


def function_with_default(x: int = 10, y: str = "default") -> str:
    """Function with default parameters.

    ```python
    >>> def greet(name: str = "World", prefix: str = "Hello") -> str:
    ...     return f"{prefix}, {name}!"
    >>> greet()
    'Hello, World!'
    >>> greet("Alice")
    'Hello, Alice!'
    >>> greet("Bob", "Hi")
    'Hi, Bob!'
    >>> greet(prefix="Hey", name="Charlie")
    'Hey, Charlie!'

    ```
    """  # ruff: ignore[docstring-missing-returns]
    return f"{y}, {x}!"


def function_with_complex_return() -> dict[str, list[int | None]]:
    r"""Function with complex return type annotation.

    ```python
    >>> # Complex nested types with union
    >>> result: dict[str, list[int | None]] = {
    ...     "values": [1, 2, None, 3],
    ...     "empty": [],
    ...     "mixed": [None, 42, None]
    ... }
    >>> result["values"]
    [1, 2, None, 3]
    >>> len(result)
    3
    >>> None in result["mixed"]
    True

    ```
    """  # ruff: ignore[docstring-missing-returns]
    return {}


def unfenced_doctest() -> None:
    """Function with un-fenced doctest.

    >>> 5 - 3
    2
    """


def intersection() -> None:
    """Exracted from pyochain.

    Check complex docstring.

    Args:
        other (AbstractSet[Any]): The set to intersect with.

    Returns:
        AbstractSet[T]: A new `Set` containing shared elements only.

    Example:
        ```python
        from pyochain import Set, Dict, Vec

        from_set = Set((1, 2))
        assert from_set.intersection({2, 3}) == Set((2,))
        assert from_set.intersection({3, 4}) == Set(())
        dct = Dict.from_ref({"a": 1, "b": 2, "c": 3})
        from_keys = dct.keys().intersection({"b", "c", "d"}).iter().sort()
        assert from_keys == Vec(("b", "c"))
        from_items = (
            dct.items().intersection({("b", 2), ("c", 3), ("d", 4)}).iter().sort()
        )
        assert from_items == Vec((("b", 2), ("c", 3)))
        ```
    """
