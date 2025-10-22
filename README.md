# Doctester

A simple tool to automatically run and verify doctests in Python packages.

## Features

- Discover and run doctests in all Python files within a package.
- Generate and run tests for `.pyi` stub files.
- Provide detailed output on test results, including failures.

## Usage

To use Doctester, simply call the `run_doctester` function from your Python code:

```python
from doctester import run_doctester

run_doctester(verbose=True)
```

This will discover all modules in the `src` directory, run their doctests, and generate tests for any associated `.pyi` files.

## Installation

```bash
uv add your installation instructions here
```
