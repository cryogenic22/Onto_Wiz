from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List

from cathedral_keeper.integrations.types import IntegrationContext
from cathedral_keeper.models import Evidence, Finding, clamp_snippet


def run_quality_gate(ctx: IntegrationContext, cfg: Dict[str, Any]) -> List[Finding]:
    """
    Optional integration that ingests quality-gate results without making CK depend on it.

    If quality-gate is missing or errors, this returns no findings.
    """
    qg_path = str((cfg.get("qg_path") or "quality-gate/quality_gate.py")).strip()
    qg = (ctx.root / qg_path).resolve()
    if not qg.exists():
        return []

    payload = _run_quality_gate_json(root=ctx.root, qg=qg, paths_file=ctx.target_paths_file)
    if not payload:
        return []

    prs = dict(payload.get("prs", {}) or {})
    stats = _collect_issue_stats(list(payload.get("issues", []) or []))
    return _findings_from_prs(prs=prs, qg_path=qg_path, stats=stats)


def _run_quality_gate_json(*, root: Path, qg: Path, paths_file: Path) -> Dict[str, Any]:
    args = [sys.executable, str(qg), "--root", str(root), "--mode", "audit", "--json", "--paths-from", str(paths_file)]
    try:
        proc = subprocess.run(args, capture_output=True)
        raw = proc.stdout.decode("utf-8", errors="ignore") if proc.stdout else ""
        if not raw.strip():
            return {}
        return dict(json.loads(raw))
    except Exception:
        return {}


def _collect_issue_stats(issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    per_file_msgs: dict[str, list[str]] = defaultdict(list)
    per_file_rules: dict[str, Counter[str]] = defaultdict(Counter)
    per_file_first_line: dict[str, int] = {}
    for issue in issues[:5000]:
        file = str(issue.get("file") or "")
        if not file:
            continue
        per_file_first_line.setdefault(file, int(issue.get("line") or 1))
        rule = str(issue.get("rule") or "quality_gate")
        if rule:
            per_file_rules[file][rule] += 1
        msg = str(issue.get("message") or "").strip()
        if msg:
            per_file_msgs[file].append(msg)
    return {"msgs": per_file_msgs, "rules": per_file_rules, "first_line": per_file_first_line}


def _findings_from_prs(*, prs: Dict[str, Any], qg_path: str, stats: Dict[str, Any]) -> List[Finding]:
    per_file_msgs = stats.get("msgs") or {}
    per_file_rules = stats.get("rules") or {}
    per_file_first_line = stats.get("first_line") or {}
    findings: List[Finding] = []
    for file, prs_entry in prs.items():
        entry = dict(prs_entry or {})
        score = float(entry.get("score", 100.0))
        errors = int(entry.get("errors", 0))
        warnings = int(entry.get("warnings", 0))
        if errors <= 0 and score >= 85:
            continue
        top_rules = _top_rules(per_file_rules.get(file))
        fix_msgs = [clamp_snippet(m) for m in (per_file_msgs.get(file) or [])[:5] if m]
        line = int(per_file_first_line.get(file, 1))
        findings.append(
            _prs_finding(
                file=file,
                line=line,
                qg_path=qg_path,
                score=score,
                errors=errors,
                warnings=warnings,
                top_rules=top_rules,
                fix_msgs=fix_msgs,
            )
        )
    return sorted(findings, key=lambda f: float(f.metadata.get("prs", 100.0)))


def _prs_finding(
    *, file: str, line: int, qg_path: str, score: float, errors: int, warnings: int, top_rules: str, fix_msgs: List[str]
) -> Finding:
    why = f"PRS={score:.1f} (errors={errors}, warnings={warnings}). Deterministic gate issues block safe change velocity."
    return Finding(
        policy_id="CK-INTEGRATION::quality_gate",
        title=f"Quality Gate PRS below threshold ({score:.1f})",
        severity="high" if errors > 0 or score < 85 else "medium",
        confidence="high",
        why_it_matters=why,
        evidence=[Evidence(file=file, line=line, snippet=clamp_snippet(top_rules or "quality-gate issues"), note="quality-gate summary")],
        fix_options=fix_msgs or (["Run quality gate on the file and fix blocking rules."] if errors else []),
        verification=[f"python {qg_path} --root . {file}"],
        metadata={
            "source": "quality-gate",
            "prs": score,
            "errors": errors,
            "warnings": warnings,
            "top_rules": top_rules,
        },
    )


def _top_rules(counter: Counter[str] | None) -> str:
    if not counter:
        return ""
    return ", ".join([r for r, _ in counter.most_common(3)])

