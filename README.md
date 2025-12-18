# stubtester

A minimal tool that extracts doctests from `.pyi` stub files and runs them with `pytest --doctest-modules`.

This is primarily aimed for third-party stubs and cython/Pyo3 extensions, where the codebase is not in Python and thus cannot contain doctests.

Otherwise, you should always write your doctests in the actual `.py` implementation files, even if their types are in `.pyi` stub files.

## 🎯 What it does

1. **Extracts** doctests from your `.pyi` stub files
2. **Generates** temporary `.py` test files
3. **Type checks** them with `ty`
4. **Runs** `pytest --doctest-modules` on them
5. **Cleans up** after itself

## 📦 Installation

```bash
uv add git+https://github.com/OutSquareCapital/stubtester.git
```

## 🚀 Usage

```bash
# Run on all stubs in a directory
uv run stubtester path/to/your/package

# Run on a single stub file
uv run stubtester path/to/file.pyi
```
