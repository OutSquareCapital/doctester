"""Pytest plugin for discovering and running doctests from .pyi stub files."""

from .plugin import COMMAND, ExtModule, pytest_addoption, pytest_collect_file

__all__ = ["COMMAND", "ExtModule", "pytest_addoption", "pytest_collect_file"]
__version__ = "0.7.2"
