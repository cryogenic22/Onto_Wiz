"""Governance test — F0.1: the CI blocking path must equal the R3 gate set.

Machine-checks `.github/workflows/ci.yml` so the gate set is enforced structurally,
not eyeballed. Anchors: BUILD_INSTRUCTION_SET_2026-07 §F0.1 + §R3.

R3 blocking path: ruff, mypy, pytest >=85% coverage, check_boundaries.py, and the
frontend Vitest suite. slop_checker + quality-gate are advisory (removed from the
blocking path). This test owns the last three facts (the Python gates are enforced
directly by scripts/verify-audit.sh).

Lives in tests/ so verify-audit gate 6 (`pytest tests/`) collects it.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _load_ci() -> dict:
    return yaml.safe_load(CI_WORKFLOW.read_text(encoding="utf-8"))


def _all_steps():
    """Yield (job_name, job, step) for every step across every job in ci.yml."""
    wf = _load_ci()
    for job_name, job in (wf.get("jobs") or {}).items():
        for step in (job.get("steps") or []):
            yield job_name, job, step


def _run_text(step: dict) -> str:
    return step.get("run") or ""


def _is_advisory(step: dict) -> bool:
    # continue-on-error may be a bool or the string "true" in YAML.
    val = step.get("continue-on-error")
    return val is True or (isinstance(val, str) and val.strip().lower() == "true")


def _find_step(pattern: str):
    rx = re.compile(pattern)
    return [
        (job_name, job, step)
        for job_name, job, step in _all_steps()
        if rx.search(_run_text(step))
    ]


def test_ci_workflow_exists() -> None:
    assert CI_WORKFLOW.is_file(), f"missing CI workflow: {CI_WORKFLOW}"


def test_frontend_vitest_is_a_blocking_ci_step() -> None:
    """R3: the frontend Vitest suite is wired into CI as a BLOCKING job/step."""
    hits = _find_step(r"vitest|npm (run )?test")
    assert hits, (
        "no CI step runs the frontend Vitest suite "
        "(expected `npm run test:cov` / `npm run test` / `vitest`)"
    )
    blocking = [(j, s) for (j, _job, s) in hits if not _is_advisory(s)]
    assert blocking, (
        "the frontend Vitest step(s) exist but are all advisory "
        "(continue-on-error); R3 requires it to BLOCK CI"
    )


def test_quality_gate_is_advisory() -> None:
    """R3: quality-gate is removed from the blocking path (advisory only)."""
    hits = _find_step(r"quality[-_]gate|quality_gate\.py")
    assert hits, "expected a Quality Gate step in ci.yml to demote to advisory"
    offenders = [
        j for (j, _job, s) in hits if not _is_advisory(s)
    ]
    assert not offenders, (
        f"Quality Gate step is still BLOCKING in job(s) {offenders}; "
        "R3 requires continue-on-error: true (advisory)"
    )


def test_slop_checker_is_advisory() -> None:
    """R3: slop_checker is advisory (pre-commit still blocks new slop on staged files)."""
    hits = _find_step(r"slop[_-]?checker")
    assert hits, "expected a Slop Checker step in ci.yml"
    offenders = [j for (j, _job, s) in hits if not _is_advisory(s)]
    assert not offenders, (
        f"Slop Checker step is BLOCKING in job(s) {offenders}; "
        "R3 requires continue-on-error: true (advisory)"
    )
