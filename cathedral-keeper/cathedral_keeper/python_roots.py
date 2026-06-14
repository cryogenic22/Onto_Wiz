from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple


def discover_python_roots(root: Path) -> List[Tuple[str, Path]]:
    """
    Discover (module_prefix, directory) pairs used to resolve internal imports.

    This must be portable across repos. The heuristic:
    - Consider top-level directories whose names are valid Python identifiers.
    - Exclude common generated/vendor directories.
    - Treat each remaining directory as an importable module prefix (PEP 420 allows namespace packages).
    """
    root = root.resolve()
    out: List[Tuple[str, Path]] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        if _is_excluded_dir(child.name):
            continue
        if not _is_valid_module_prefix(child.name):
            continue
        if not _contains_python_files(child):
            continue
        out.append((child.name, child))
    return sorted(out, key=lambda x: x[0])


_VALID_PREFIX = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _is_valid_module_prefix(name: str) -> bool:
    return bool(_VALID_PREFIX.match(name))


def _is_excluded_dir(name: str) -> bool:
    if name.startswith("."):
        return True
    return name in {
        "__pycache__",
        "frontend",
        "skills",
        "node_modules",
        "dist",
        "build",
        "output",
        "venv",
        ".venv",
        ".pytest_cache",
        ".quality-reports",
        "site-packages",
        "cathedral-keeper",
    }


def _contains_python_files(dir_path: Path) -> bool:
    try:
        for _ in dir_path.rglob("*.py"):
            return True
        return False
    except Exception:
        return False
