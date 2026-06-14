#!/usr/bin/env python
"""Run the live agent-lift benchmark on the real commercial_analytics pack.

This is the operator entrypoint for the deferred 'live-LLM agent_lift' item: it
loads the pack, drives a live Anthropic agent through the faithful CTX router
loop (with-pack) and blind (without-pack), prints the per-case ledger, and —
unless ``--dry-run`` — writes the verdict into the pack's manifest.

    python scripts/run_agent_lift_benchmark.py [--model M] [--dry-run]

The API key is read from the environment or a local .env (ANTHROPIC_API_KEY).
The benchmark code lives in ontowiz_factory.benchmark (Tier B); this is only the
operator shell, so it carries no test obligation of its own.
"""

from __future__ import annotations

import argparse
import datetime
import os
from pathlib import Path

from ontowiz_factory.benchmark import (
    DEFAULT_MODEL,
    AnthropicChatAgent,
    run_lift_benchmark,
    write_results_to_manifest,
)
from ontowiz_factory.commercial_eval_suite import COMMERCIAL_EVAL_CASES
from ontowiz_runtime.registry import load_pack

REPO = Path(__file__).resolve().parents[1]
PACK_DIR = REPO / "packs" / "commercial_analytics" / "0.1.0"


def _load_dotenv(path: Path) -> None:
    """Minimal .env loader — set keys that aren't already in the environment."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def _print_ledger(report) -> None:  # noqa: ANN001 - operator script
    by_id = {r.case_id: r for r in report.without_pack.results}
    print(f"\nPack:  {report.pack}    Model: {report.model}    Cases: {report.n_cases}")
    print(f"{'case':28} {'blind':>6} {'+pack':>6} {'delta':>6}")
    print("-" * 52)
    for w in report.with_pack.results:
        wo = by_id[w.case_id].score
        print(f"{w.case_id:28} {wo:6.2f} {w.score:6.2f} {w.score - wo:+6.2f}")
    print("-" * 50)
    print(f"blind pass-rate : {report.without_pack.pass_rate:.3f}")
    print(f"+pack pass-rate : {report.with_pack.pass_rate:.3f}")
    print(f"AGENT LIFT      : {report.agent_lift:+.3f}")
    print(f"gate passed     : {report.gate_passed}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Live agent-lift benchmark")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--dry-run", action="store_true", help="do not write pack.yaml")
    args = parser.parse_args()

    _load_dotenv(REPO / ".env")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY not set (env or .env).")
        return 2

    pack = load_pack(PACK_DIR)
    agent = AnthropicChatAgent(model=args.model)
    print(f"Running {len(COMMERCIAL_EVAL_CASES)} cases live against {args.model} ...")
    report = run_lift_benchmark(pack, agent, COMMERCIAL_EVAL_CASES, model=args.model)
    _print_ledger(report)

    if args.dry_run:
        print("\n(dry-run: manifest not written)")
        return 0

    run_at = datetime.datetime.now(datetime.UTC).isoformat()
    write_results_to_manifest(PACK_DIR, report, run_at=run_at)
    print(f"\nWrote evals -> {PACK_DIR / 'pack.yaml'} (last_run_at={run_at})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
