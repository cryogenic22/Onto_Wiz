"""C10 — catalog telemetry: persist consult events, aggregate per-pack stats."""

from __future__ import annotations

from ontowiz_runtime import UsageStore, catalog_stats


def test_record_and_aggregate(tmp_path):
    s = UsageStore(tmp_path)
    s.record("commercial_analytics", "0.3.0", function="market_access", hit=True)
    s.record("commercial_analytics", "0.3.0", function="forecasting", hit=True)
    s.record("commercial_analytics", "0.3.0", function="forecasting", hit=False)

    stats = {p.pack: p for p in catalog_stats(s)}
    ca = stats["commercial_analytics"]
    assert ca.consults == 3
    assert ca.hits == 2
    assert ca.hit_rate == round(2 / 3, 3)
    assert ca.by_function == {"forecasting": 2, "market_access": 1}


def test_usage_persists_across_instances(tmp_path):
    UsageStore(tmp_path).record("p", "0.1.0", hit=True)
    again = UsageStore(tmp_path)
    again.record("p", "0.1.0", hit=False)
    stats = {p.pack: p for p in catalog_stats(again)}
    assert stats["p"].consults == 2  # the first instance's event survived


def test_usage_is_backed_by_sqlite_catalog_db(tmp_path):
    # ADR-016: DB-backed, not JSON; shares the catalog.db with CommentStore
    UsageStore(tmp_path).record("p", "0.1.0", hit=True)
    assert (tmp_path / "catalog.db").is_file()
    assert not (tmp_path / "usage.json").exists()
