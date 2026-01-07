# Contributing to stubtester

Thank you for your interest in contributing! This guide will help you run and add tests.

## 🧪 Running Tests

This project uses `pytest` for testing. The test suite covers unit tests and integration tests for stubtester.

### Quick Start

```bash
# Run all tests with pytest
uv run pytest tests/ -v
# Run stubtester on his own tests
uv run stubtester tests/success/
```

#### Auto-testing stubteser

When running with stubtester itself, take note of the following structure:

- [`examples`](tests/examples) contains the files to test.

- [`examples/success`](tests\examples\success) contains files that should pass without errors.
- [`examples/failures`](tests\examples\failures) contains files that should produce errors.

## 📝 Code Style

This project uses:

- **ruff** for linting and formatting
- **pyochain** for functional error handling

Run the linter before submitting:

```bash
uv run ruff check . --fix
uv run ruff format .
```
