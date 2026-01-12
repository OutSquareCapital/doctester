# pytest-stubtester

A pytest plugin that discovers and runs doctests from `.pyi` stub files.

## 🎯 Use Cases

This plugin is designed for:

- **Stub file testing**: Validate examples in `.pyi` type stub files
- **Non-Python codebases**: Test doctests for Cython/PyO3/Rust extensions where the implementation isn't in Python
- **Third-party stubs**: Verify examples in type stubs for external libraries

> **Note**: For regular Python code, always write doctests directly in your `.py` implementation files.

## 🎯 How it Works

1. **Integrates** with pytest's collection phase
2. **Discovers** `.pyi` files automatically
3. **Parses** doctests from docstrings using Python's doctest module
4. **Creates** DoctestItem instances for pytest execution
5. **Reports** failures with standard pytest output

## 📦 Installation

```bash
uv add pytest-stubtester
# Or with pip
pip install pytest-stubtester
```

## 🚀 Usage

### Basic Usage

```bash
# Enable the plugin with --pyi-enabled flag
pytest tests/ --pyi-enabled -v

# Test specific .pyi files
pytest tests/my_stubs.pyi --pyi-enabled -v
```

### Auto-enable in conftest.py

Add to your `conftest.py` to enable automatically:

```python
def pytest_configure(config: object) -> None:
    """Enable pytest-stubtester plugin automatically."""
    config.option.pyi_enabled = True  # type: ignore[attr-defined]
```

### Configure in pytest.ini / pyproject.toml

**pytest.ini:**

```ini
[pytest]
addopts = --pyi-enabled
```

**pyproject.toml:**

```toml
[tool.pytest.ini_options]
addopts = ["--pyi-enabled"]
```

## 📝 Example

### Stub File (`.pyi`)

```python
# math_helpers.pyi
def add(a: int, b: int) -> int:
    """Add two numbers.
    
    ```python
    >>> add(2, 3)
    5
    >>> add(-1, 1)
    0
    
    ```
    """
```

Run pytest:

```bash
pytest math_helpers.pyi --pyi-enabled -v
```

## 🤝 Contributing

Contributions welcome! Please ensure all tests pass:

```bash
uv run pytest tests/ --pyi-enabled -v
```
