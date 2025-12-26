# Contributing to stubtester

Thank you for your interest in contributing! This guide will help you run and add tests.

## 🧪 Running Tests

This project uses `pytest` for testing. The test suite covers unit tests and integration tests for stubtester.

### Quick Start

```bash
# Run all tests
uv run pytest tests/

# Run specific test files
uv run pytest tests/test_main.py
uv run pytest tests/test_cli.py

# Run with verbose output
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ --cov=stubtester --cov-report=html
```

## 🗂️ Test Structure

- **test_main.py** - Unit tests for core components
- **test_cli.py** - Integration tests for the CLI interface
- **Fixtures (.pyi)** - Stub files used as test fixtures:
  - `clean.pyi` - Tests that pass (nominal case)
  - `foo.pyi` - Tests that fail (error handling validation)
  - `no_tests.pyi` - File without doctests
  - `edge_cases.pyi` - Complex cases (generics, complex signatures)

## 📊 Test Coverage

The test suite covers:

- ✅ Docstring extraction (regex parsing)
- ✅ Test file generation
- ✅ Code fence cleanup
- ✅ Error handling (Result workflow)
- ✅ Edge cases (generics, complex signatures)
- ✅ CLI interface
- ✅ Temporary directory cleanup

## 🧪 Manual Testing

You can also test stubtester manually:

```bash
# On a file that should pass
uv run stubtester tests/clean.pyi

# On a file that should fail
uv run stubtester tests/foo.pyi

# On a directory
uv run stubtester tests/
```

## ✨ Adding New Tests

When adding new functionality:

1. **Add unit tests** in `tests/test_main.py` for core logic
2. **Add CLI tests** in `tests/test_cli.py` for user-facing features
3. **Add fixture files** (.pyi) in `tests/` for integration testing
4. Ensure all tests pass: `uv run pytest tests/`
5. Check code style: `uv run ruff check src/ tests/`

## 🐛 Reporting Issues

If you find a bug:

1. Check if it's already reported in the issues
2. Include a minimal reproducible example
3. Specify your Python version and OS
4. Provide the stubtester version

## 📝 Code Style

This project uses:

- **ruff** for linting and formatting
- **pyochain** for functional error handling
- **Type hints** throughout the codebase

Run the linter before submitting:

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```
