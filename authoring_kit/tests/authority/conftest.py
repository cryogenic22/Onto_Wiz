from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType


def _install_adapters_namespace() -> None:
    """Expose ``adapters._support`` (and the repo adapters) as one namespace.

    Mirrors ``tests/adapters/conftest.py`` so the authority tests can reuse the shared
    ``ExternalTestProvider`` harness without duplicating it.
    """

    tests_adapters = Path(__file__).parents[1] / "adapters"
    repo_adapters = Path(__file__).parents[2] / "adapters"
    package = ModuleType("adapters")
    package.__path__ = [str(tests_adapters), str(repo_adapters)]
    sys.modules["adapters"] = package


_install_adapters_namespace()
