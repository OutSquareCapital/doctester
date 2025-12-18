import contextlib
import importlib
import pkgutil
from pathlib import Path
from types import ModuleType

import pyochain as pc

from ._models import Dunders


def find_package_name(root_dir: Path) -> pc.Result[str, RuntimeError]:
    if root_dir.joinpath(Dunders.PY_INIT).exists():
        return pc.Ok(root_dir.name)

    return (
        pc.Iter(root_dir.iterdir())
        .find(
            lambda child: child.is_dir()
            and (
                child.joinpath(Dunders.PY_INIT).exists()
                or child.joinpath(Dunders.STUB_INIT).exists()
            )
        )
        .map(lambda child: child.name)
        .ok_or(RuntimeError(f"No package found in {root_dir} directory."))
    )


def get_py_modules(
    package_name: str, package_path: Path
) -> pc.Result[pc.Vec[ModuleType], RuntimeError]:
    modules = pc.Vec[ModuleType].new()

    try:
        pkg: ModuleType = importlib.import_module(package_name)
    except ImportError:
        msg = (
            f"Could not import package '{package_name}'. "
            f"Is '{package_path.parent}' in PYTHONPATH?"
        )
        return pc.Err(RuntimeError(msg))

    if not hasattr(pkg, Dunders.PY_PATH):
        msg = (
            f"Package '{package_name}' has no {Dunders.PY_PATH}. "
            "Is it correctly installed or in PYTHONPATH?"
        )
        return pc.Err(RuntimeError(msg))

    for _, modname, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        if not ispkg:
            with contextlib.suppress(Exception):
                modules.append(importlib.import_module(modname))
    return pc.Ok(modules)
