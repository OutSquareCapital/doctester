from __future__ import annotations

import importlib.util
import inspect
import sys
from importlib.machinery import ModuleSpec
from pathlib import Path
from types import ModuleType
from typing import NamedTuple

import pyochain as pc

from . import _console
from ._models import TestResult
from ._stub_parser import generate_test_module_content


def process_pyi_file(
    pyi_file: Path, temp_dir: Path, *, verbose: bool
) -> pc.Option[TestResult]:
    """Process a single .pyi file and return test results if any."""
    module_content = generate_test_module_content(pyi_file)
    if module_content.is_none():
        return pc.NONE

    test_file = temp_dir.joinpath(f"{pyi_file.stem}_test.py")
    test_file.write_text(module_content.unwrap(), encoding="utf-8")

    if verbose:
        _console.print_info(f"Running stub tests for {pyi_file.name}...")

    def _logs(result: TestResult) -> None:
        if verbose:
            _console.print_info(f"  {result.passed}/{result.total} tests passed.")

        if result.failed > 0:
            _console.print_error(f"  FAILURES in {pyi_file.name} (see log above)")

    def _on_err(e: ImportError) -> None:
        _console.print_error(f"--- ERROR loading {test_file.name} ---")
        _console.print_error(f"{e!r}")

    return pc.Some(
        ModuleLoader.from_file(test_file)
        .map(load)
        .map(_run_tests_in_module)
        .inspect(_logs)
        .map_err(_on_err)
        .ok()
        .unwrap_or(TestResult(total=1, passed=0))
    )


class ModuleLoader(NamedTuple):
    spec: ModuleSpec
    loader: importlib.abc.Loader

    @staticmethod
    def from_file(test_file: Path) -> pc.Result[ModuleLoader, ImportError]:
        def _on_err() -> ImportError:
            msg = f"Could not create module spec for {test_file}"
            return ImportError(msg)

        def _get_loader(spec: ModuleSpec) -> pc.Option[importlib.abc.Loader]:
            return pc.Option.from_(spec.loader)

        spec = pc.Option.from_(
            importlib.util.spec_from_file_location(test_file.stem, test_file)
        ).ok_or_else(_on_err)
        loader = spec.ok().and_then(_get_loader)
        if spec.is_ok and loader.is_some():
            return pc.Ok(ModuleLoader(spec.unwrap(), loader.unwrap()))
        return pc.Err(spec.unwrap_err())


def load(loader: ModuleLoader) -> ModuleType:
    test_module = importlib.util.module_from_spec(loader.spec)
    sys.modules[loader.spec.name] = test_module
    loader.loader.exec_module(test_module)
    return test_module


def _run_tests_in_module(module: ModuleType) -> TestResult:
    return (
        pc.Iter(inspect.getmembers(module, inspect.isfunction))
        .filter(lambda item: item[0].startswith("test_"))
        .map(lambda item: item[1])
        .collect()
        .into(
            lambda x: TestResult(
                total=x.length(),
                passed=x.iter().filter(lambda fn: fn()).length(),
            )
        )
    )
