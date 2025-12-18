# Doctester

A modern tool to automatically run and verify doctests in Python packages, with support for both `.py` files and `.pyi` stub files.

## Features

- 🔍 **Auto-discovery**: Find and run doctests in all Python files within a package
- 📝 **Stub support**: Generate and run tests from `.pyi` stub files

## 📦 Installation

```bash
uv add git+https://github.com/OutSquareCapital/doctester.git
```

## 🚀 Usage

### CLI (Recommended)

Doctester provides a modern CLI built with Typer:

```bash
# Test all files in src/ directory
doctester run

# Test a specific directory
doctester run path/to/package

# Test a single file
doctester file mymodule.py
doctester file stubs/mymodule.pyi

# Test with verbose output
doctester run --verbose
doctester file myfile.py -v

# Get help
doctester --help
doctester run --help
```

### Programmatic API

You can also use doctester as a library (returns `Result[TestResult, str]`):

```python
from doctester import run_doctester, run_on_file
from pathlib import Path
import pyochain as pc

# Test entire package - returns Result
result = run_doctester(root_dir="src", verbose=True)

match result:
    case pc.Ok(test_result):
        print(f"✓ {test_result.passed}/{test_result.total} passed")
    case pc.Err(error):
        print(f"✗ Error: {error}")

# Test single file
result = run_on_file(Path("myfile.pyi"), verbose=True)
```

## 🎯 Features in Detail

### Stub File Testing

Doctester can parse docstrings from `.pyi` stub files and generate executable tests:

```python
# mymodule.pyi
def add(x: int, y: int) -> int:
    """Add two numbers.
    
    Example:
    ```python
    >>> add(2, 3)
    5
    >>> add(10, -5)
    5
    ```
    """
```

### Rich Console Output

Beautiful, colorful output with:

- 📦 Bordered panels for sections
- ℹ️ Info messages with icons
- ✓ Success indicators
- ✗ Error highlighting
