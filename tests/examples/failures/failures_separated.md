# This is an example of a markdown file with doctest failures

## First failure

```python
def function_with_bad_docstring() -> None:
    """This has a markdown fence that breaks the parser.

    Example:
    >>> 1 + 1
    2
    >>> # ```, "this", "is", "bad"):
    >>> # ...
    """
```

## Second failure

```python
class Foo:
    def __init__(self, data: object) -> None:
        """Initializes the context with Python data.

        Args:
            data (object): The Python data (e.g., dict, list) to query.

        Example:
        >>> 1 + 1
        2
        """
```

## Third failure

```python
def failing_test() -> None:
    """Test qui va échouer.

    Example:
    >>> 1 + 1  # Expected to fail.
    3
    """
```
