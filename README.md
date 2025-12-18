# Doctester

A tool to automatically run and verify doctests in `.pyi` stub files using `pytest --doctest-modules`.

## 📦 Installation

```bash
uv add git+https://github.com/OutSquareCapital/stubtester.git
```

## 🚀 Usage

After installation, you can run doctests on your stub files using the command line interface:

```bash
uv run stubtester run path/to/your/package
uv run stubtester file path/to/file.pyi
uv run stubtester --help
```
