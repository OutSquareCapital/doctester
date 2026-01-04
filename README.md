# stubtester

A tool that extracts doctests from `.pyi` stub files and `.md` markdown files and runs them with `pytest --doctest-modules`.

This is aimed for anyone who wants to test and validate code examples in their documentation through markdown files, as well as third-party stubs and cython/Pyo3 extensions where the codebase is not in Python and thus cannot contain doctests.

Otherwise, you should always write your doctests in the actual `.py` implementation files, even if their types are in `.pyi` stub files.

## 🎯 What it does

1. **Extracts** doctests from your `.pyi` stub files and `.md` markdown files
2. **Generates** temporary `.py` test files
3. **Runs** `pytest --doctest-modules` on them
4. **Cleans up** after itself

## 📦 Installation

```bash
uv add git+https://github.com/OutSquareCapital/stubtester.git
```

## 🚀 Usage

with the CLI:

```bash
# Run on all stubs and markdown files in a directory
uv run stubtester path/to/your/package

# Run on a single stub or markdown file
uv run stubtester path/to/file.pyi
uv run stubtester path/to/file.md
```

or programmatically:

```python
from pathlib import Path

import stubtester

# Test both .pyi and .md files
stubtester.run(Path("my_package"))
```
