# Performance Baseline Report (SEN-005)

> **Owner:** Team SENTINEL
> **Date:** 2026-02-01
> **Benchmark Script:** `tests/perf/benchmark_baseline.py`
> **Raw JSON:** `.quality-reports/perf_baseline_20260201_160923.json`
> **Environment:** Python 3.13.3, Windows, in-memory stores, single-process TestClient

---

## Executive Summary

All API endpoints respond under 5ms mean latency. All store operations complete under 1ms mean. Memory footprint scales linearly (~1.15 KB per delta). The DeltaGenerator pipeline (`process_sme_session`) completes in 0.016ms mean. No performance concerns at current scale.

---

## 1. API Response Times

| Endpoint | Mean (ms) | Median (ms) | P95 (ms) | P99 (ms) | Iterations |
|---|---|---|---|---|---|
| GET /health | 2.170 | 2.046 | 3.209 | 3.873 | 200 |
| GET /stats | 2.038 | 1.892 | 2.795 | 3.599 | 200 |
| POST /deltas | 1.821 | 1.699 | 2.382 | 6.897 | 100 |
| GET /deltas | 3.159 | 2.980 | 4.546 | 5.934 | 100 |
| POST /patterns | 2.250 | 1.953 | 3.932 | 10.465 | 100 |
| GET /patterns | 3.601 | 3.047 | 6.516 | 6.861 | 100 |
| POST /guardrails | 2.015 | 1.947 | 2.682 | 3.076 | 100 |
| GET /guardrails | 4.666 | 4.940 | 5.869 | 7.202 | 100 |
| POST /intelligence-packet | 1.668 | 1.531 | 2.499 | 2.745 | 50 |
| POST /sessions | 2.311 | 2.136 | 3.291 | 5.519 | 50 |
| GET /sessions | 4.390 | 3.911 | 6.460 | 54.567 | 100 |
| POST /promote | 1.912 | 1.811 | 2.995 | 3.349 | 50 |

### Observations

- All endpoints mean < 5ms. Fastest: POST /intelligence-packet (1.67ms), POST /deltas (1.82ms).
- GET /sessions P99 outlier at 54.6ms — likely GC pause or list serialization cost as session count grows (50 sessions created during writes benchmark).
- GET /guardrails shows median > mean, indicating a left-skewed distribution (many fast responses with occasional slower ones during initial runs).
- Write endpoints are generally faster than their corresponding read endpoints because reads must serialize growing collections.

### Recommended Thresholds for Regression Detection (SEN-018)

| Endpoint | Threshold P95 (ms) |
|---|---|
| GET /health | 10 |
| GET /stats | 10 |
| POST /deltas | 10 |
| GET /deltas | 15 |
| POST /patterns | 10 |
| GET /patterns | 15 |
| POST /guardrails | 10 |
| GET /guardrails | 15 |
| POST /intelligence-packet | 10 |
| POST /sessions | 10 |
| GET /sessions | 15 |
| POST /promote | 10 |

---

## 2. Store Operation Latency

| Operation | Mean (ms) | Median (ms) | P95 (ms) | P99 (ms) | Iterations |
|---|---|---|---|---|---|
| DeltaStore.propose() | 0.010 | 0.008 | 0.013 | 0.071 | 500 |
| DeltaStore.get_pending_review() | 0.051 | 0.049 | 0.056 | 0.109 | 200 |
| DeltaStore.approve() | 0.000 | 0.000 | 0.000 | 0.000 | 200 |
| DeltaStore.stats() | 0.000 | 0.000 | 0.000 | 0.001 | 200 |
| JudgmentStore.add_pattern() | 0.007 | 0.006 | 0.012 | 0.055 | 200 |
| JudgmentStore.find_matching() | 0.010 | 0.009 | 0.014 | 0.034 | 200 |
| JudgmentStore.add_guardrail() | 0.007 | 0.005 | 0.009 | 0.046 | 200 |
| GraphStore.add_node() | 0.005 | 0.004 | 0.008 | 0.018 | 500 |
| GraphStore.add_edge() | 0.005 | 0.004 | 0.006 | 0.016 | 200 |
| GraphStore.seed_ontology() | 0.148 | 0.141 | 0.199 | 0.199 | 20 |
| GraphStore.stats() | 0.145 | 0.121 | 0.281 | 0.627 | 200 |
| EvidenceStore.add() | 0.005 | 0.005 | 0.007 | 0.016 | 200 |
| EvidenceStore.find_by_type() | 0.004 | 0.004 | 0.005 | 0.007 | 200 |
| EvidenceStore.stats() | 0.002 | 0.002 | 0.002 | 0.007 | 200 |
| PromotionPipeline.promote_all() | 0.004 | 0.000 | 0.001 | 0.185 | 50 |

### Observations

- All store operations are sub-millisecond. In-memory dict/list stores are extremely fast.
- `DeltaStore.get_pending_review()` is the slowest DeltaStore op at 0.051ms mean — it filters by status across all deltas. At 500+ deltas this is still negligible.
- `GraphStore.stats()` at 0.145ms mean is the slowest individual store op — it iterates all nodes and edges for counts. Will need monitoring when graph exceeds 10K nodes (Phase 6).
- `GraphStore.seed_ontology()` at 0.148ms mean creates 18 nodes + 13 edges. Predictable O(n) scaling.
- `DeltaStore.approve()` on nonexistent IDs returns in ~0ms (no-op fast path).

### Recommended Thresholds for Regression Detection

| Operation | Threshold P95 (ms) |
|---|---|
| DeltaStore.propose() | 1.0 |
| DeltaStore.get_pending_review() | 1.0 |
| GraphStore.add_node() | 1.0 |
| GraphStore.stats() | 5.0 |
| JudgmentStore.find_matching() | 1.0 |
| EvidenceStore.add() | 1.0 |

---

## 3. Memory Footprint

| Measurement | Value |
|---|---|
| Baseline (empty stores) | 0.0 KB |
| DeltaStore (100 deltas) | 109.2 KB |
| DeltaStore (500 deltas) | 575.6 KB |
| DeltaStore (1000 deltas) | 1,180.3 KB |
| GraphStore (seeded ontology) | 32.6 KB |
| GraphStore seeded nodes | 18 |
| GraphStore seeded edges | 13 |

### Observations

- Delta memory scales linearly: ~1.15 KB per delta (1,180 KB / 1,000 deltas).
- At 10,000 deltas: projected ~11.5 MB. At 100,000: ~115 MB. In-memory stores remain viable up to ~100K deltas on a 512MB server.
- Seeded graph is compact at 32.6 KB (18 nodes + 13 edges). The commercial ontology will grow significantly in Phase 3+ but memory is not a near-term concern.
- No memory leaks detected — each measurement is cumulative from a clean `tracemalloc.start()`.

### Recommended Thresholds

| Measurement | Threshold |
|---|---|
| 1,000 deltas | < 5 MB |
| Seeded graph | < 1 MB |

---

## 4. DeltaGenerator

| Operation | Mean (ms) | Median (ms) | P95 (ms) | P99 (ms) | Iterations |
|---|---|---|---|---|---|
| process_sme_session() | 0.016 | 0.015 | 0.018 | 0.095 | 100 |

### Observations

- `process_sme_session()` is extremely fast at 0.016ms mean. This converts a full `ReasoningEvent` into Delta proposals.
- The P99 outlier at 0.095ms is likely first-call initialization overhead.
- This operation is not a bottleneck and will not be for foreseeable scale.

### Recommended Threshold

| Operation | Threshold P95 (ms) |
|---|---|
| process_sme_session() | 5.0 |

---

## 5. Summary and Recommendations

### Verdict: PASS — No Performance Concerns

All measured latencies are well within acceptable ranges for the current in-memory architecture. The system can handle interactive use (SME game sessions) without perceptible delay.

### Recommendations for Future Tickets

1. **SEN-018 (Regression Detection):** Use the thresholds defined above in a CI benchmark step. Fail the build if any P95 exceeds its threshold by more than 2x.
2. **Phase 6 (Database Migration):** Re-run this benchmark after Postgres/Neo4j migration. Expected API latencies will increase 10-50x. Store operation thresholds must be recalibrated.
3. **GET /sessions P99 outlier:** Monitor `GET /sessions` latency as session count grows. Consider pagination if P95 exceeds 15ms at 500+ sessions.
4. **GraphStore.stats() scaling:** At 10K+ nodes, `stats()` may need indexing or cached counters. Current O(n) iteration is fine up to ~5K nodes.
5. **SEN-009 (Load Testing):** This baseline measures single-request latency. Concurrent load testing is out of scope but recommended for Phase 5.

---

_End of Performance Baseline Report_
