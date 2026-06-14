"""Eval loop (Loop 4 of the 5) — eval gate + agent-lift.

Run an EvalCase suite against agent answers (a deterministic must-contain /
must-not-contain judge — an LLM judge can slot in later behind the same API),
compute pass-rate, and the headline number: with-pack vs without-pack agent lift.
The gate is what blocks a pack from promotion if it doesn't actually help.

Tier B (factory).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field

from ontowiz_spec import EvalCase


def _contains(haystack: str, needle: str) -> bool:
    """Word-boundary, case-insensitive containment — 'access' ≠ 'accessory'."""
    return re.search(rf"(?<!\w){re.escape(needle.lower())}(?!\w)", haystack) is not None


@dataclass
class EvalResult:
    case_id: str
    passed: bool
    score: float  # [0, 1]
    missing: list[str] = field(default_factory=list)
    forbidden_hits: list[str] = field(default_factory=list)


@dataclass
class EvalSummary:
    total: int
    passed: int
    pass_rate: float
    mean_score: float
    results: list[EvalResult] = field(default_factory=list)


def score_answer(case: EvalCase, answer: str) -> EvalResult:
    """Deterministic judge: required phrases present, forbidden phrases absent.

    Matching is word-boundary (so 'access' does not match 'accessory'). A case
    with neither must_contain nor must_not_contain proves nothing and scores 0 —
    it never vacuously certifies an answer.
    """
    al = answer.lower()
    missing = [s for s in case.must_contain if not _contains(al, s)]
    forbidden = [s for s in case.must_not_contain if _contains(al, s)]
    required = case.must_contain
    if required:
        score = (len(required) - len(missing)) / len(required)
    elif case.must_not_contain:
        score = 1.0 if not forbidden else 0.0
    else:
        # nothing asserted → non-scorable; do not pass vacuously
        return EvalResult(case.id, False, 0.0, missing, forbidden)
    return EvalResult(case.id, not missing and not forbidden, round(score, 3), missing, forbidden)


def run_suite(cases: list[EvalCase], answer_fn: Callable[[EvalCase], str]) -> EvalSummary:
    """Score every case using answer_fn to produce the candidate answer."""
    results = [score_answer(c, answer_fn(c)) for c in cases]
    if not results:
        return EvalSummary(0, 0, 0.0, 0.0, [])
    passed = sum(1 for r in results if r.passed)
    return EvalSummary(
        len(results),
        passed,
        round(passed / len(results), 3),
        round(sum(r.score for r in results) / len(results), 3),
        results,
    )


def agent_lift(
    cases: list[EvalCase],
    with_pack_fn: Callable[[EvalCase], str],
    without_pack_fn: Callable[[EvalCase], str],
) -> float:
    """Mean per-case score delta (with-pack minus without-pack), in [-1, 1]."""
    if not cases:
        return 0.0
    deltas = [
        score_answer(c, with_pack_fn(c)).score - score_answer(c, without_pack_fn(c)).score
        for c in cases
    ]
    return round(sum(deltas) / len(deltas), 3)


def gate(
    summary: EvalSummary,
    *,
    min_pass_rate: float = 0.8,
    lift: float | None = None,
    min_lift: float = 0.0,
) -> bool:
    """The promotion gate — a pack ships only if its evals clear the bar.

    When ``lift`` (from :func:`agent_lift`) is supplied, the pack must ALSO beat
    baseline by ``min_lift`` — so a pack that passes its evals but adds no agent
    lift is blocked. Omitting ``lift`` keeps the pass-rate-only behaviour.
    """
    return summary.pass_rate >= min_pass_rate and (lift is None or lift >= min_lift)
