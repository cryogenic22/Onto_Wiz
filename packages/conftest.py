"""Test-time import setup for the packages monorepo.

Puts each package's source root on sys.path so `import ontowiz_spec` etc. resolve
during `pytest packages/` without requiring editable installs. This is test
infrastructure only — production code never manipulates sys.path (CK-PY-SYSPATH
governs that, and applies to src/ and the package modules, not this conftest).

For an interactive dev environment, prefer `make install-packages` (editable
installs); this conftest keeps the test run self-sufficient in CI/pre-commit.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PKGS = Path(__file__).resolve().parent
for _name in (
    "ontowiz-spec", "ontowiz-ctx", "ontowiz-runtime", "ontowiz-serve",
    "ontowiz-core", "ontowiz-factory",
):
    _root = _PKGS / _name
    if _root.is_dir():
        sys.path.insert(0, str(_root))
