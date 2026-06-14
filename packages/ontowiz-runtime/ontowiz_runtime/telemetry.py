"""Catalog telemetry (Tier A) — persist consult events, aggregate usage stats.

The serving-side counterpart to the factory's in-process UsageEvent: a JSON-backed
store of consult records (which pack/version/function was served, and whether it
was a hit) plus a per-pack aggregation for the catalog's Manager lens — where is
the catalog being used, and where is it missing? MVP persistence (a JSON file,
not a database) — honest and self-contained.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class UsageRecord:
    """One consult against a pack."""

    pack: str
    version: str
    function: str | None
    hit: bool
    at: str


@dataclass
class PackUsage:
    """Aggregated usage for one pack across all its consults."""

    pack: str
    consults: int
    hits: int
    hit_rate: float
    by_function: dict[str, int] = field(default_factory=dict)


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


class UsageStore:
    """Append-only consult records, JSON-backed under ``root``."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._file = self.root / "usage.json"

    def _load(self) -> list[dict]:
        if not self._file.is_file():
            return []
        data = json.loads(self._file.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []

    def record(
        self, pack: str, version: str, *,
        function: str | None = None, hit: bool = True, at: str | None = None,
    ) -> UsageRecord:
        """Append a consult record and persist it."""
        rec = UsageRecord(pack=pack, version=version, function=function, hit=hit, at=at or _now())
        rows = self._load()
        rows.append(asdict(rec))
        self._file.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        return rec

    def all(self) -> list[UsageRecord]:
        return [UsageRecord(**row) for row in self._load()]


def catalog_stats(store: UsageStore) -> list[PackUsage]:
    """Aggregate the store's records into per-pack usage, busiest pack first."""
    by_pack: dict[str, list[UsageRecord]] = {}
    for rec in store.all():
        by_pack.setdefault(rec.pack, []).append(rec)

    out: list[PackUsage] = []
    for pack, recs in by_pack.items():
        hits = sum(1 for r in recs if r.hit)
        by_function: dict[str, int] = {}
        for r in recs:
            if r.function:
                by_function[r.function] = by_function.get(r.function, 0) + 1
        out.append(
            PackUsage(
                pack=pack,
                consults=len(recs),
                hits=hits,
                hit_rate=round(hits / len(recs), 3) if recs else 0.0,
                by_function=dict(sorted(by_function.items())),
            )
        )
    return sorted(out, key=lambda p: (-p.consults, p.pack))
