def line_number_regression() -> None:
    """Check that fenced block failures point to the failing line.

    ```python
    def reciprocal(x: int) -> float:
        if x == 0:
            raise RuntimeError("division by zero")
        return 1 / x

    reciprocal(0)
    ```
    """
