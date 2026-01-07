# stubtester

A tool that extracts doctests from `.pyi` stub files and `.md` markdown files and runs them with `pytest --doctest-modules`.

## 🎯 Use Cases

This tool is designed for:

- **Documentation validation**: Test code examples in markdown documentation files
- **Stub file testing**: Validate examples in `.pyi` type stub files
- **Non-Python codebases**: Test doctests for Cython/PyO3/Rust extensions where the implementation isn't in Python
- **Third-party stubs**: Verify examples in type stubs for external libraries

> **Note**: For regular Python code, always write doctests directly in your `.py` implementation files, even if you have separate `.pyi` stub files.

## 🎯 How it Works

1. **Discovers** `.pyi` and `.md` files in your project
2. **Extracts** doctests from docstrings (`.pyi`) or code blocks (`.md`)
3. **Generates** temporary test files with proper source mapping
4. **Executes** tests with `pytest --doctest-modules`
5. **Reports** failures with accurate line numbers pointing to source files
6. **Cleans up** temporary files automatically

## 📦 Installation

```bash
uv add git+https://github.com/OutSquareCapital/stubtester.git
```

## 🚀 Usage

### CLI

```bash
# Run on all .pyi and .md files in a directory
uv run stubtester path/to/your/package

# Run on a single file
uv run stubtester path/to/file.pyi
uv run stubtester path/to/docs.md

# Keep temporary files for debugging
uv run stubtester path/to/file.pyi --keep
```

### Programmatic

```python
from pathlib import Path
import stubtester

# Test a directory (discovers all .pyi and .md files)
result = stubtester.run(Path("my_package"))

# Test a single file
result = stubtester.run(Path("my_package/module.pyi"))

# Keep temporary files for debugging
result = stubtester.run(Path("my_package"), keep=True)

# Handle results
match result:
    case stubtester.Ok(message):
        print(f"✓ {message}")
    case stubtester.Err(error):
        print(f"✗ {error}")
```

## 📝 Examples

### Stub Files (`.pyi`)

Your stub file might look like this:

```text
# math_helpers.pyi
def add(a: int, b: int) -> int:
    """Add two numbers.
    
    >>> add(2, 3)
    5
    >>> add(-1, 1)
    0
    """
```

When run with `stubtester`, doctests are extracted and executed.

### Markdown Files (`.md`)

Your documentation might include code blocks like this:

```python
>>> text = "hello"
>>> text.upper()
'HELLO'
```

or this:

```python
>>> # Test basic Python operations
>>> result = 2 + 3
>>> result
5
>>> words = ["hello", "world"]
>>> " ".join(words)
'hello world'
```

Those doctests in code blocks are automatically **discovered** and **tested**.

## 🧪 This README is a real example

The document you are reading is tested itself!

If you clone the repo and run the following command in the root directory:

```bash
uv run stubtester README.md
```

You should see the following output:

```bash
configfile: pyproject.toml
collecting ... collected 2 items

README.md::README_test.Markdown_Files____md___4 PASSED [ 50%]
README.md::README_test.Markdown_Files____md___5 PASSED [100%]

============================== 2 passed in 0.11s ==============================
✓ All tests passed!
i Cleaned up temp directory.
```

## 🔍 Output

When tests fail, errors point directly to the source files:

```text
tests/math_helpers.pyi::math_helpers.add FAILED              [ 50%]
tests/math_helpers.pyi::math_helpers.multiply PASSED         [100%]

================================== FAILURES ===================================
________________________  math_helpers.add _________________________
002 def add(a: int, b: int) -> int:
003     """Add two numbers.
004
005     >>> add(2, 3)
Expected:
    5
Got:
    6

C:\project\tests\math_helpers.pyi:5: DocTestFailure
```

## 🛠️ Options

- `--keep`: Keep temporary test files for debugging (stored in `doctests_temp/`)
- `--help`: Display help information

## 🤝 Contributing

Contributions welcome! Please ensure all tests pass:

```bash
uv run pytest tests/
uv run stubtester/tests/examples/clean/ # This project verifies itself !
```
