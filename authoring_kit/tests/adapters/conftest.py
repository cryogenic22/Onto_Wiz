from __future__ import annotations

import sys
from pathlib import Path
from types import ModuleType


def _prefer_repository_adapter_namespace() -> None:
    adapter_root = Path(__file__).parents[2] / "adapters"
    package = ModuleType("adapters")
    package.__path__ = [str(Path(__file__).parent), str(adapter_root)]
    sys.modules["adapters"] = package


_prefer_repository_adapter_namespace()
