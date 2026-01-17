"""Pytest plugin for discovering and running doctests from .pyi stub files."""

from .plugin import PyiModule, pytest_addoption, pytest_collect_file

__all__ = ["PyiModule", "pytest_addoption", "pytest_collect_file"]
__version__ = "0.4.0"
