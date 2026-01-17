# Contributing to stubtester

Thank you for your interest in contributing! This guide will help you run and add tests.

## 🧪 Running Tests

This project uses `pytest` for testing. The test suite covers unit tests and integration tests for the pytest-stubtester plugin.

### Quick Start

Install development dependencies:

```bash
uv sync --dev
```

Then run the tests with:

```bash
uv run pytest tests/test_stubtester.py --pyi-enabled -v
uv run pytest tests/examples/success/ --pyi-enabled -v
```

#### Test structure

- [`tests/examples`](tests/examples) contains example `.pyi` files used for testing.
  - [`tests/examples/success`](tests/examples/success) contains files with valid doctests that should pass.
  - [`tests/examples/failures`](tests/examples/failures) contains files with intentional errors that should fail.

- [`tests/test_stubtester.py`](tests/test_stubtester.py) contains unit tests for the plugin itself.

**Note:** The `failures.pyi` file is **expected to fail** - it contains intentional errors to verify the plugin correctly detects failures.

## 📝 Code Style

This project uses:

- **ruff** for linting and formatting
- **pyochain** for functional error handling

Run the linter before submitting:

```bash
uv run ruff check . --fix
uv run ruff format .
```
