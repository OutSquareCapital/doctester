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
