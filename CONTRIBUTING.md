# Contributing to stubtester

Thank you for your interest in contributing! This guide will help you run and add tests.

## 🧪 Running Tests

This project uses `pytest` for testing. The test suite covers unit tests and integration tests for stubtester.

### Quick Start

```bash
# Run all tests with pytest
uv run pytest tests/main.py
# Run stubtester on his own tests
uv run stubtester tests/clean.pyi
```

## 📝 Code Style

This project uses:

- **ruff** for linting and formatting
- **pyochain** for functional error handling

Run the linter before submitting:

```bash
uv run ruff check src/ tests/
uv run ruff format src/ tests/
```
