#!/usr/bin/env python3
"""Enforce the A -> B never rule (the IP boundary).

Tier A packages ship to clients; Tier B packages are the secret sauce and must
never be importable from a client artifact. This scans every Tier A package for
any import of a Tier B package and fails loudly if it finds one.

Run in CI (mirrors the spirit of ADR-007 / cathedral-keeper):

    python tools/check_boundaries.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TIER_A = {"ontowiz_spec", "ontowiz_ctx", "ontowiz_runtime", "ontowiz_serve"}
TIER_B = {"ontowiz_core", "ontowiz_factory"}

PKG_ROOT = Path(__file__).resolve().parent.parent / "packages"
IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+(ontowiz_[a-z_]+)", re.MULTILINE)


def package_dir(pkg: str) -> Path:
    # ontowiz_spec -> packages/ontowiz-spec/ontowiz_spec
    return PKG_ROOT / pkg.replace("_", "-") / pkg


def violations() -> list[str]:
    out: list[str] = []
    for a_pkg in TIER_A:
        root = package_dir(a_pkg)
        if not root.exists():
            continue
        for py in root.rglob("*.py"):
            text = py.read_text(encoding="utf-8", errors="ignore")
            for m in IMPORT_RE.finditer(text):
                imported = m.group(1)
                # match top-level package (ontowiz_core.x -> ontowiz_core)
                base = imported.split(".")[0]
                if base in TIER_B:
                    line = text[: m.start()].count("\n") + 1
                    out.append(f"{py}:{line}  Tier A '{a_pkg}' imports Tier B '{base}'")
    return out


def main() -> int:
    bad = violations()
    if bad:
        print("IP BOUNDARY VIOLATION — Tier A must never import Tier B:\n", file=sys.stderr)
        for v in bad:
            print("  " + v, file=sys.stderr)
        print(f"\n{len(bad)} violation(s).", file=sys.stderr)
        return 1
    print("OK — A->B boundary clean. Tier A packages import no secret sauce.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
