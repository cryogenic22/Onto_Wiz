from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List

from cathedral_keeper.models import Evidence, Finding, clamp_snippet, normalize_path
from cathedral_keeper.python_imports import read_text_best_effort


REQUESTS_CALL_RE = re.compile(r"\brequests\.(get|post|put|patch|delete)\s*\(")


def check_requests_timeouts(*, root: Path, cfg: Dict[str, Any], files: List[Path]) -> List[Finding]:
    findings: List[Finding] = []
    for path in files:
        text = read_text_best_effort(path)
        if "requests." not in text:
            continue
        rel = normalize_path(str(path.resolve().relative_to(root.resolve())))
        for line_no, line in _lines(text):
            if "requests." not in line:
                continue
            if not REQUESTS_CALL_RE.search(line):
                continue
            if "timeout=" in line:
                continue
            findings.append(
                Finding(
                    policy_id="CK-PY-REQUESTS-TIMEOUT",
                    title="requests.* call missing timeout",
                    severity=_severity(cfg, default="high"),
                    confidence="high",
                    why_it_matters="Network calls without timeouts can hang workers indefinitely and cause cascading failures.",
                    evidence=[Evidence(file=rel, line=line_no, snippet=clamp_snippet(line), note="add timeout=")],
                    fix_options=["Add an explicit `timeout=` (and consider retries/backoff for transient failures)."],
                    verification=[f"python -m compileall -q {rel}"],
                    metadata={},
                )
            )
    return findings


def _lines(text: str) -> List[tuple[int, str]]:
    return [(i + 1, line) for i, line in enumerate(text.splitlines())]


def _severity(cfg: Dict[str, Any], *, default: str) -> str:
    return str(cfg.get("severity") or default).strip().lower()

