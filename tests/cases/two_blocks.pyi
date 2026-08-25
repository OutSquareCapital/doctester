def result_type_and_then() -> None:
    """ResultType.and_then.

    ```python
    from pyochain import Ok, Err, Result

    def try_mul_to_str(x: int) -> Result[str, str]:
        if x < 100_000:
            return Ok(str(x * x))
        else:
            return Err("overflow")

    assert True
    assert True
    assert True
    ```

    Often used to chain fallible operations that may return [`Err`].

    ```python
    from pyochain import Option, NONE
    from pathlib import Path

    CONFIG = Path("pyproject")

    def run(path: Path, value: int) -> Result[float, str]:
        return (
            check_toml(path)
            .map(lambda _: value)
            .and_then(parse_int)
            .and_then(reciprocal)
        )

    def check_toml(path: Option[Path] = NONE) -> Result[None, str]:
        p = path.unwrap_or(CONFIG).with_suffix(".toml")
        if p.exists():
            return Ok(None)
        else:
            return Err(f"File {p} does not exist")

    def parse_int(s: str) -> Result[int, str]:
        try:
            return Ok(int(s))
        except ValueError:
            return Err(f"'{s}' is not a valid int")

    def reciprocal(x: int) -> Result[float, str]:
        if x == 0:
            return Err("division by zero")
        else:
            return Ok(1 / x)

    assert run(10) == Ok(0.1)
    assert run(Some(Path("ruff")), 10) == Ok(0.1)
    assert run(Path("bad"), 10) == Err("File bad.toml does not exist")
    assert run(0) == Err("division by zero")
    assert run("hi") == Err("'hi' is not a valid int")
    ```
    """
