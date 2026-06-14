#!/usr/bin/env python3
"""
Performance Baseline Benchmark (SEN-005)
========================================
Measures API response times, store operation latency, and memory footprint.
Produces JSON output for comparison in future regression runs (SEN-018).

Usage:
    python tests/perf/benchmark_baseline.py              # Full run
    python tests/perf/benchmark_baseline.py --json        # JSON output
    python tests/perf/benchmark_baseline.py --section api # API only

Owner: Team SENTINEL
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _timeit(fn, *, iterations: int = 100) -> dict[str, float]:
    """Run fn() N times, return timing stats in milliseconds."""
    times: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        fn()
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    return {
        "iterations": iterations,
        "min_ms": round(min(times), 3),
        "max_ms": round(max(times), 3),
        "mean_ms": round(statistics.mean(times), 3),
        "median_ms": round(statistics.median(times), 3),
        "p95_ms": round(sorted(times)[int(len(times) * 0.95)], 3),
        "p99_ms": round(sorted(times)[int(len(times) * 0.99)], 3),
    }


def _mem_snapshot() -> int:
    """Return current traced memory in bytes."""
    current, _ = tracemalloc.get_traced_memory()
    return current


def _mem_kb(b: int) -> float:
    return round(b / 1024, 1)


# ---------------------------------------------------------------------------
# Section 1: API Response Times
# ---------------------------------------------------------------------------

def _bench_api_reads(client: TestClient) -> dict[str, Any]:
    results: dict[str, Any] = {}
    results["GET /health"] = _timeit(lambda: client.get("/health"), iterations=200)
    results["GET /stats"] = _timeit(lambda: client.get("/stats"), iterations=200)
    results["GET /deltas"] = _timeit(lambda: client.get("/deltas"), iterations=100)
    results["GET /patterns"] = _timeit(lambda: client.get("/patterns"), iterations=100)
    results["GET /guardrails"] = _timeit(
        lambda: client.get("/guardrails"), iterations=100
    )
    results["GET /sessions"] = _timeit(
        lambda: client.get("/sessions"), iterations=100
    )
    return results


def _bench_api_mutations(client: TestClient) -> dict[str, Any]:
    results: dict[str, Any] = {}
    delta_payload = {
        "type": "pattern",
        "content": {"signal": "benchmark_test", "hypothesis": "perf_baseline"},
        "confidence": 0.8, "blast_radius": "medium", "evidence_pointers": ["ev-001"],
    }
    results["POST /deltas"] = _timeit(
        lambda: client.post("/deltas", json=delta_payload), iterations=100
    )
    pattern_payload = {
        "applies_when_signals": ["signal_a", "signal_b"],
        "applies_when_context": ["ctx_a"],
        "typical_drivers": [{"driver": "d1", "prior_confidence": 0.7}],
        "judgment_type": "causal_hypothesis",
    }
    results["POST /patterns"] = _timeit(
        lambda: client.post("/patterns", json=pattern_payload), iterations=100
    )
    guardrail_payload = {
        "blocks_action_types": ["aggressive_pricing"],
        "blocks_drivers": ["unverified_source"],
        "unless_evidence": ["clinical_trial"],
    }
    results["POST /guardrails"] = _timeit(
        lambda: client.post("/guardrails", json=guardrail_payload), iterations=100
    )
    packet = {"signal": "competitor_launch", "context": {"brand": "TestBrand", "geography": "US"}}
    results["POST /intelligence-packet"] = _timeit(
        lambda: client.post("/intelligence-packet", json=packet), iterations=50,
    )
    session = {
        "scenarioId": "perf-test",
        "hypothesis": {"category": "competitive_pressure",
                       "specific_driver": "competitor_launch",
                       "confidence": 0.75, "reasoning": "Benchmark test"},
    }
    results["POST /sessions"] = _timeit(
        lambda: client.post("/sessions", json=session), iterations=50
    )
    results["POST /promote"] = _timeit(
        lambda: client.post("/promote"), iterations=50
    )
    return results


def bench_api(client: TestClient) -> dict[str, Any]:
    results = _bench_api_mutations(client)
    results.update(_bench_api_reads(client))
    return results


# ---------------------------------------------------------------------------
# Section 2: Store Operations
# ---------------------------------------------------------------------------

def _bench_delta_store() -> tuple[dict[str, Any], Any, Any]:
    from src.core.models import BlastRadius, Delta, DeltaType
    from src.core.stores import DeltaStore

    results: dict[str, Any] = {}
    ds = DeltaStore()
    delta_fn = lambda: ds.propose(Delta(
        type=DeltaType.PROPOSED_PATTERN,
        content={"signal": "bench"},
        confidence=0.7,
        blast_radius=BlastRadius.LOW,
    ))
    results["DeltaStore.propose()"] = _timeit(delta_fn, iterations=500)
    results["DeltaStore.get_pending_review()"] = _timeit(
        lambda: ds.get_pending_review(), iterations=200
    )
    pending = ds.get_pending_review(limit=10)
    for d in pending:
        ds.approve(d.id, "bench_reviewer")
    results["DeltaStore.approve()"] = _timeit(
        lambda: ds.approve("nonexistent", "r"), iterations=200
    )
    results["DeltaStore.stats()"] = _timeit(lambda: ds.stats(), iterations=200)
    return results, ds


def _bench_judgment_store() -> tuple[dict[str, Any], Any]:
    from src.core.models import DriverAttribution, Guardrail, JudgmentPattern
    from src.core.stores import JudgmentStore

    results: dict[str, Any] = {}
    js = JudgmentStore()
    pat_fn = lambda: js.add_pattern(JudgmentPattern(
        applies_when_signals=["sig_a", "sig_b"],
        typical_drivers=[DriverAttribution(driver="d1", prior_confidence=0.6)],
    ))
    results["JudgmentStore.add_pattern()"] = _timeit(pat_fn, iterations=200)
    results["JudgmentStore.find_matching()"] = _timeit(
        lambda: js.find_matching_patterns(["sig_a", "sig_b"], {}),
        iterations=200,
    )
    guard_fn = lambda: js.add_guardrail(Guardrail(
        blocks_action_types=["price_cut"],
        blocks_drivers=["rumor"],
    ))
    results["JudgmentStore.add_guardrail()"] = _timeit(guard_fn, iterations=200)
    return results, js


def _bench_graph_store() -> dict[str, Any]:
    from src.core.graph_store import (
        EdgeType, GraphEdge, GraphNode, GraphStore, NodeType,
    )

    results: dict[str, Any] = {}
    gs = GraphStore()
    node_counter = [0]

    def add_node():
        node_counter[0] += 1
        gs.add_node(GraphNode(
            type=NodeType.ENTITY,
            label=f"bench_node_{node_counter[0]}",
        ))

    results["GraphStore.add_node()"] = _timeit(add_node, iterations=500)
    nodes = list(gs._nodes.values())[:2] if hasattr(gs, "_nodes") else []
    if len(nodes) >= 2:
        edge_counter = [0]

        def add_edge():
            edge_counter[0] += 1
            gs.add_edge(GraphEdge(
                type=EdgeType.LEADS_TO,
                source_id=nodes[0].id,
                target_id=nodes[1].id,
            ))

        results["GraphStore.add_edge()"] = _timeit(add_edge, iterations=200)
    gs2 = GraphStore()
    results["GraphStore.seed_ontology()"] = _timeit(
        lambda: gs2.seed_commercial_ontology(), iterations=20
    )
    results["GraphStore.stats()"] = _timeit(lambda: gs.stats(), iterations=200)
    return results


def _bench_evidence_store() -> dict[str, Any]:
    from src.core.evidence import EvidenceItem, EvidenceStore
    from src.core.evidence import EvidenceType as EvType

    results: dict[str, Any] = {}
    es = EvidenceStore()
    ev_fn = lambda: es.add(EvidenceItem(
        title="bench evidence",
        content=f"bench content {time.monotonic_ns()}",
        entity_refs=["entity_1"],
    ))
    results["EvidenceStore.add()"] = _timeit(ev_fn, iterations=200)
    results["EvidenceStore.find_by_type()"] = _timeit(
        lambda: es.find_by_type(EvType.DOCUMENT), iterations=200,
    )
    results["EvidenceStore.stats()"] = _timeit(lambda: es.stats(), iterations=200)
    return results


def bench_stores() -> dict[str, Any]:
    from src.core.stores import PromotionPipeline

    delta_results, ds = _bench_delta_store()
    judgment_results, js = _bench_judgment_store()
    results: dict[str, Any] = {}
    results.update(delta_results)
    results.update(judgment_results)
    results.update(_bench_graph_store())
    results.update(_bench_evidence_store())
    pp = PromotionPipeline(ds, js)
    results["PromotionPipeline.promote_all()"] = _timeit(
        lambda: pp.promote_all_approved(), iterations=50
    )
    return results


# ---------------------------------------------------------------------------
# Section 3: Memory Footprint
# ---------------------------------------------------------------------------

def bench_memory() -> dict[str, Any]:
    from src.core.graph_store import GraphStore
    from src.core.models import BlastRadius, Delta, DeltaType
    from src.core.stores import DeltaStore

    results: dict[str, Any] = {}

    tracemalloc.start()

    # Baseline (empty stores)
    baseline = _mem_snapshot()
    results["baseline_empty_kb"] = _mem_kb(baseline)

    # DeltaStore with N deltas
    ds = DeltaStore()
    for count in [100, 500, 1000]:
        for i in range(count - len(ds._deltas)):
            ds.propose(Delta(
                type=DeltaType.PROPOSED_PATTERN,
                content={"i": i},
                confidence=0.5,
                blast_radius=BlastRadius.LOW,
            ))
        mem_after = _mem_snapshot()
        results[f"delta_store_{count}_deltas_kb"] = _mem_kb(mem_after - baseline)

    # GraphStore after ontology seed
    mem_pre_graph = _mem_snapshot()
    gs = GraphStore()
    gs.seed_commercial_ontology()
    mem_post_graph = _mem_snapshot()
    results["graph_store_seeded_kb"] = _mem_kb(mem_post_graph - mem_pre_graph)
    results["graph_store_seeded_nodes"] = len(gs._nodes) if hasattr(gs, "_nodes") else 0
    results["graph_store_seeded_edges"] = len(gs._edges) if hasattr(gs, "_edges") else 0

    tracemalloc.stop()
    return results


# ---------------------------------------------------------------------------
# Section 4: DeltaGenerator
# ---------------------------------------------------------------------------

def bench_delta_generator() -> dict[str, Any]:
    from src.core.delta_generator import process_sme_session
    from src.core.reasoning_event import (
        BrandProfile,
        HypothesisCategory,
        HypothesisRanking,
        ReasoningEvent,
        ScenarioContext,
    )

    event = ReasoningEvent(
        scenario=ScenarioContext(
            brand=BrandProfile(brand_name="BenchBrand"),
            geography="US",
            observation="Sales down 10% in Northeast",
        ),
        scenario_type="regional_performance_dip",
        primary_hypothesis=HypothesisRanking(
            category=HypothesisCategory.COMPETITIVE_PRESSURE,
            specific_driver="competitor_launch",
            confidence=0.75,
            reasoning="Competitor launch impacting share",
        ),
    )

    results: dict[str, Any] = {}
    results["process_sme_session()"] = _timeit(
        lambda: process_sme_session(event), iterations=100
    )
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_all(*, sections: list[str] | None = None) -> dict[str, Any]:
    all_sections = sections or ["api", "stores", "memory", "delta_generator"]
    results: dict[str, Any] = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}

    if "api" in all_sections:
        from src.api.server import app
        client = TestClient(app)
        print("[Benchmark] Running API response time benchmarks...")
        results["api"] = bench_api(client)

    if "stores" in all_sections:
        print("[Benchmark] Running store operation benchmarks...")
        results["stores"] = bench_stores()

    if "memory" in all_sections:
        print("[Benchmark] Running memory footprint benchmarks...")
        results["memory"] = bench_memory()

    if "delta_generator" in all_sections:
        print("[Benchmark] Running DeltaGenerator benchmarks...")
        results["delta_generator"] = bench_delta_generator()

    return results


def _print_section(name: str, data: dict[str, Any], indent: int = 2) -> None:
    prefix = " " * indent
    print(f"\n{'=' * 60}")
    print(f"  {name}")
    print(f"{'=' * 60}")
    for key, val in data.items():
        if isinstance(val, dict) and "mean_ms" in val:
            print(
                f"{prefix}{key:40s}  "
                f"mean={val['mean_ms']:7.3f}ms  "
                f"p95={val['p95_ms']:7.3f}ms  "
                f"p99={val['p99_ms']:7.3f}ms  "
                f"(n={val['iterations']})"
            )
        else:
            print(f"{prefix}{key:40s}  {val}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Performance Baseline Benchmark")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument(
        "--section",
        choices=["api", "stores", "memory", "delta_generator"],
        action="append",
        help="Run specific section(s) only",
    )
    args = parser.parse_args(argv)

    results = run_all(sections=args.section)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for section_name in ["api", "stores", "memory", "delta_generator"]:
            if section_name in results:
                _print_section(section_name.upper(), results[section_name])

    # Save JSON to .quality-reports/
    out_dir = Path(".quality-reports")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / f"perf_baseline_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    if not args.json:
        print(f"\nResults saved to {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
