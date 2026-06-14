from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, Dict, List, Tuple

from cathedral_keeper.models import Evidence, Finding, clamp_snippet, normalize_path
from cathedral_keeper.python_imports import read_text_best_effort


BLOCKING_CALLEES = ("requests.", "subprocess.", "time.sleep", "Path.read_text", "Path.write_text", "open(")


def check_async_blocking(*, root: Path, cfg: Dict[str, Any], files: List[Path]) -> List[Finding]:
    findings: List[Finding] = []
    for path in files:
        text = read_text_best_effort(path)
        if "async def " not in text:
            continue
        rel = normalize_path(str(path.resolve().relative_to(root.resolve())))
        for line, snippet in _blocking_calls_in_async(text):
            findings.append(
                Finding(
                    policy_id="CK-PY-ASYNC-BLOCKING",
                    title="Potential blocking call inside async function",
                    severity=_severity(cfg, default="high"),
                    confidence="medium",
                    why_it_matters="Blocking I/O inside async endpoints can stall the event loop and degrade throughput/latency.",
                    evidence=[Evidence(file=rel, line=line, snippet=clamp_snippet(snippet), note="heuristic")],
                    fix_options=[
                        "Use async equivalents (httpx AsyncClient, asyncio.to_thread) or move blocking work off the event loop."
                    ],
                    verification=[f"python -m compileall -q {rel}"],
                    metadata={"callee": snippet},
                )
            )
    return findings


def _blocking_calls_in_async(source: str) -> List[Tuple[int, str]]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    out: List[Tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.AsyncFunctionDef):
            body_src = _node_source_segment(source, node) or ""
            for callee in BLOCKING_CALLEES:
                if callee in body_src:
                    out.append((int(node.lineno or 1), f"{callee} ..."))
    return out


def _node_source_segment(source: str, node: ast.AST) -> str:
    try:
        return ast.get_source_segment(source, node) or ""
    except Exception:
        return ""


def _severity(cfg: Dict[str, Any], *, default: str) -> str:
    return str(cfg.get("severity") or default).strip().lower()

