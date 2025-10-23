import importlib
import pkgutil
from pathlib import Path
from types import ModuleType

from ._models import Dunders


def find_package_name(root_dir: Path) -> str:
    for child in root_dir.iterdir():
        if child.is_dir() and (
            child.joinpath(Dunders.PY_INIT).exists()
            or child.joinpath(Dunders.STUB_INIT).exists()
        ):
            return child.name
    raise RuntimeError(f"No package found in {root_dir} directory.")


def get_py_modules(package_name: str, package_path: Path) -> list[ModuleType]:
    modules: list[ModuleType] = []

    try:
        pkg: ModuleType = importlib.import_module(package_name)
    except ImportError:
        raise RuntimeError(
            f"Could not import package '{package_name}'. "
            f"Is '{package_path.parent}' in PYTHONPATH?"
        )

    if not hasattr(pkg, Dunders.PY_PATH):
        raise RuntimeError(
            f"Package '{package_name}' has no {Dunders.PY_PATH}. "
            "Is it correctly installed or in PYTHONPATH?"
        )

    for _, modname, ispkg in pkgutil.walk_packages(pkg.__path__, pkg.__name__ + "."):
        if not ispkg:
            try:
                modules.append(importlib.import_module(modname))
            except Exception:
                pass
    return modules


def get_pyi_files(package_path: Path) -> list[Path]:
    return list(package_path.glob("**/*.pyi"))
