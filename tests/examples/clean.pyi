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
    """

def multiply(x: int, y: int) -> int:
    """Multiply two numbers.

    ```python
    >>> 3 * 4
    12
    >>> 0 * 100
    0

    ```
    """

"""Stub file with no doctests to test empty file handling."""

def no_docstring() -> None: ...
def empty_docstring() -> None:
    """"""  # noqa: D419

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

    def generic_method[T](self, value: T) -> T:
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
        """

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
    """

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
    """
