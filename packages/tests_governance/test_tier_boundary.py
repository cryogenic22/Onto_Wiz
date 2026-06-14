"""The IP boundary is a tested invariant, not just a script.

Tier A (ontowiz-spec/ctx/runtime/serve) must never import Tier B
(ontowiz-core/factory). This runs the authoritative checker and asserts zero
violations, so the boundary is enforced by the normal test suite + pre-commit.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_CHECKER = Path(__file__).resolve().parents[2] / "tools" / "check_boundaries.py"


def _load_checker():
    spec = importlib.util.spec_from_file_location("check_boundaries", _CHECKER)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_tier_a_imports_no_tier_b():
    checker = _load_checker()
    bad = checker.violations()
    assert bad == [], "Tier A -> Tier B boundary violation(s):\n" + "\n".join(bad)
