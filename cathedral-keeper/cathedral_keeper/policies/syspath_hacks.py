from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from cathedral_keeper.models import Evidence, Finding, clamp_snippet, normalize_path
from cathedral_keeper.python_imports import read_text_best_effort


SYSPATH_RE = re.compile(r"\bsys\.path\.(insert|append)\s*\(")


def check_syspath_hacks(*, root: Path, cfg: Dict[str, Any], files: List[Path]) -> List[Finding]:
    findings: List[Finding] = []
    for path in files:
        text = read_text_best_effort(path)
        if "sys.path" not in text:
            continue
        rel = normalize_path(str(path.resolve().relative_to(root.resolve())))
        for line_no, line in _lines(text):
            if not SYSPATH_RE.search(line):
                continue
            findings.append(
                Finding(
                    policy_id="CK-PY-SYSPATH",
                    title="sys.path manipulation detected",
                    severity=_severity(cfg, default="medium"),
                    confidence="high",
                    why_it_matters="sys.path manipulation increases import ambiguity and can cause environment-specific bugs.",
                    evidence=[
                        Evidence(
                            file=rel,
                            line=line_no,
                            snippet=clamp_snippet(line),
                            note="prefer packaging or explicit entrypoints",
                        )
                    ],
                    fix_options=[
                        "Prefer installing the package, using a proper module layout, or moving the integration behind a stable API boundary."
                    ],
                    verification=[f"python -m compileall -q {rel}"],
                    metadata={},
                )
            )
    return findings


def _lines(text: str) -> List[tuple[int, str]]:
    return [(i + 1, line) for i, line in enumerate(text.splitlines())]


def _severity(cfg: Dict[str, Any], *, default: str) -> str:
    return str(cfg.get("severity") or default).strip().lower()

