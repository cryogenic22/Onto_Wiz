"""Governance persistence (Tier A) — the durable delta lifecycle on the SQLite seam.

F0.2. Proposed deltas, their approvals, the audit trail, and SME contributions
survive a process restart by living in the shared catalog database
(``<root>/catalog.db``) through the ``Database`` wrapper — SQLite for dev/test,
Postgres for production (ADR-016). Mirrors the ``CommentStore``/``UsageStore``
pattern: flat dataclass rows, ``CREATE TABLE IF NOT EXISTS``, ISO timestamps.

Tier note (ADR-012): this is **Tier A**, so ``ontowiz-serve`` (also Tier A) can
consume it — Tier A must not import Tier B. The rows here are deliberately flat
persistence records (DDL §9: "no ORM cleverness"), *not* the Tier B behavioural
``Delta``/``AuditEntry``/``Contribution`` models. This store records the delta
lifecycle; it does **not** promote artifacts to ACTIVE — R1's one pipe (``bridge.py``)
is untouched. Endpoint wiring (``/v1/deltas``) is F0.3.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .db import Database

# Delta lifecycle statuses (mirrors ontowiz_core.DeltaStatus values, by value not import).
STATUS_PROPOSED = "proposed"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


@dataclass
class DeltaRecord:
    """A proposed change and its current lifecycle status."""

    id: str
    type: str
    status: str
    content: dict[str, Any]
    created_by: str
    created_at: str
    updated_at: str
    reviewer: str | None = None
    reason: str | None = None


@dataclass
class DeltaEvent:
    """One append-only entry in a delta's own history."""

    id: str
    delta_id: str
    event: str
    actor: str
    detail: dict[str, Any]
    created_at: str


@dataclass
class ApprovalRecord:
    """A curator's decision on a delta (approve or reject) with its reason."""

    id: str
    delta_id: str
    approver: str
    decision: str
    reason: str
    created_at: str


@dataclass
class AuditRecord:
    """One row of the cross-cutting audit trail."""

    id: str
    actor: str
    action: str
    action_category: str
    store_type: str
    artifact_id: str
    details: dict[str, Any]
    created_at: str


@dataclass
class ContributionRecord:
    """An SME contribution: the deltas that came out of one session."""

    id: str
    sme_id: str
    sme_persona: str
    delta_ids: list[str]
    therapeutic_area: str
    scenario_type: str
    sme_confidence: float
    created_by: str
    created_at: str


class GovernanceStore:
    """Durable governance records (deltas / events / approvals / audit / contributions)."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self._db = Database(self.root / "catalog.db")
        self._create_tables()

    def _create_tables(self) -> None:
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS deltas ("
            "id TEXT PRIMARY KEY, type TEXT NOT NULL, status TEXT NOT NULL, "
            "content TEXT NOT NULL, created_by TEXT NOT NULL, "
            "created_at TEXT NOT NULL, updated_at TEXT NOT NULL, "
            "reviewer TEXT, reason TEXT)"
        )
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS delta_events ("
            "id TEXT PRIMARY KEY, delta_id TEXT NOT NULL, event TEXT NOT NULL, "
            "actor TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS approvals ("
            "id TEXT PRIMARY KEY, delta_id TEXT NOT NULL, approver TEXT NOT NULL, "
            "decision TEXT NOT NULL, reason TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS audit_log ("
            "id TEXT PRIMARY KEY, actor TEXT NOT NULL, action TEXT NOT NULL, "
            "action_category TEXT NOT NULL, store_type TEXT NOT NULL, "
            "artifact_id TEXT NOT NULL, details TEXT NOT NULL, created_at TEXT NOT NULL)"
        )
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS contributions ("
            "id TEXT PRIMARY KEY, sme_id TEXT NOT NULL, sme_persona TEXT NOT NULL, "
            "delta_ids TEXT NOT NULL, therapeutic_area TEXT NOT NULL, "
            "scenario_type TEXT NOT NULL, sme_confidence REAL NOT NULL, "
            "created_by TEXT NOT NULL, created_at TEXT NOT NULL)"
        )

    # ---- internal append helpers -------------------------------------------

    def _record_event(
        self, delta_id: str, event: str, actor: str, detail: dict[str, Any], at: str
    ) -> None:
        self._db.execute(
            "INSERT INTO delta_events (id, delta_id, event, actor, detail, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (_new_id(), delta_id, event, actor, json.dumps(detail), at),
        )

    def _record_audit(
        self,
        *,
        actor: str,
        action: str,
        action_category: str,
        artifact_id: str,
        details: dict[str, Any],
        at: str,
        store_type: str = "delta",
    ) -> None:
        self._db.execute(
            "INSERT INTO audit_log "
            "(id, actor, action, action_category, store_type, artifact_id, details, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (_new_id(), actor, action, action_category, store_type, artifact_id,
             json.dumps(details), at),
        )

    def _require_delta(self, delta_id: str) -> DeltaRecord:
        delta = self.get_delta(delta_id)
        if delta is None:
            raise ValueError(f"unknown delta: {delta_id!r}")
        return delta

    # ---- writes ------------------------------------------------------------

    def propose_delta(
        self,
        delta_id: str,
        *,
        delta_type: str,
        content: dict[str, Any],
        created_by: str,
        at: str | None = None,
    ) -> DeltaRecord:
        """Persist a new PROPOSED delta + its opening event + an audit row."""
        ts = at or _now()
        with self._db.transaction():
            self._db.execute(
                "INSERT INTO deltas "
                "(id, type, status, content, created_by, created_at, updated_at, reviewer, reason) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL)",
                (delta_id, delta_type, STATUS_PROPOSED, json.dumps(content),
                 created_by, ts, ts),
            )
            self._record_event(delta_id, "proposed", created_by, {"type": delta_type}, ts)
            self._record_audit(
                actor=created_by, action="propose", action_category="create",
                artifact_id=delta_id, details={"type": delta_type}, at=ts,
            )
        return self._require_delta(delta_id)

    def approve_delta(
        self, delta_id: str, *, approver: str, reason: str = "", at: str | None = None
    ) -> DeltaRecord:
        """Approve a delta: status → approved, + approval + event + audit rows."""
        return self._decide(delta_id, "approve", STATUS_APPROVED, approver, reason, at)

    def reject_delta(
        self, delta_id: str, *, approver: str, reason: str, at: str | None = None
    ) -> DeltaRecord:
        """Reject a delta: status → rejected, + approval + event + audit rows."""
        return self._decide(delta_id, "reject", STATUS_REJECTED, approver, reason, at)

    def _decide(
        self, delta_id: str, action: str, new_status: str, approver: str, reason: str,
        at: str | None,
    ) -> DeltaRecord:
        self._require_delta(delta_id)
        ts = at or _now()
        event = STATUS_APPROVED if action == "approve" else STATUS_REJECTED
        with self._db.transaction():
            self._db.execute(
                "UPDATE deltas SET status = ?, reviewer = ?, reason = ?, updated_at = ? "
                "WHERE id = ?",
                (new_status, approver, reason, ts, delta_id),
            )
            self._db.execute(
                "INSERT INTO approvals (id, delta_id, approver, decision, reason, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (_new_id(), delta_id, approver, action, reason, ts),
            )
            self._record_event(delta_id, event, approver, {"reason": reason}, ts)
            self._record_audit(
                actor=approver, action=action, action_category=action,
                artifact_id=delta_id, details={"reason": reason}, at=ts,
            )
        return self._require_delta(delta_id)

    def escalate_delta(
        self, delta_id: str, *, actor: str, reason: str, at: str | None = None
    ) -> DeltaRecord:
        """Escalate a delta: a routing signal — status is unchanged; event + audit logged."""
        self._require_delta(delta_id)
        ts = at or _now()
        with self._db.transaction():
            self._db.execute("UPDATE deltas SET updated_at = ? WHERE id = ?", (ts, delta_id))
            self._record_event(delta_id, "escalated", actor, {"reason": reason}, ts)
            self._record_audit(
                actor=actor, action="escalate", action_category="escalate",
                artifact_id=delta_id, details={"reason": reason}, at=ts,
            )
        return self._require_delta(delta_id)

    def record_contribution(
        self,
        *,
        sme_id: str,
        delta_ids: list[str],
        created_by: str,
        sme_persona: str = "",
        therapeutic_area: str = "",
        scenario_type: str = "",
        sme_confidence: float = 0.5,
        contribution_id: str | None = None,
        at: str | None = None,
    ) -> ContributionRecord:
        """Persist an SME contribution (the deltas from one session) + an audit row."""
        cid = contribution_id or _new_id()
        ts = at or _now()
        with self._db.transaction():
            self._db.execute(
                "INSERT INTO contributions "
                "(id, sme_id, sme_persona, delta_ids, therapeutic_area, scenario_type, "
                "sme_confidence, created_by, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (cid, sme_id, sme_persona, json.dumps(delta_ids), therapeutic_area,
                 scenario_type, sme_confidence, created_by, ts),
            )
            self._record_audit(
                actor=created_by, action="record", action_category="record",
                artifact_id=cid, details={"sme_id": sme_id, "deltas": len(delta_ids)},
                at=ts, store_type="contribution",
            )
        return ContributionRecord(
            id=cid, sme_id=sme_id, sme_persona=sme_persona, delta_ids=list(delta_ids),
            therapeutic_area=therapeutic_area, scenario_type=scenario_type,
            sme_confidence=sme_confidence, created_by=created_by, created_at=ts,
        )

    # ---- reads -------------------------------------------------------------

    def get_delta(self, delta_id: str) -> DeltaRecord | None:
        row = self._db.fetch_one("SELECT * FROM deltas WHERE id = ?", (delta_id,))
        return self._delta_from_row(row) if row is not None else None

    def list_deltas(self, status: str | None = None) -> list[DeltaRecord]:
        if status is None:
            rows = self._db.fetch_all("SELECT * FROM deltas ORDER BY rowid")
        else:
            rows = self._db.fetch_all(
                "SELECT * FROM deltas WHERE status = ? ORDER BY rowid", (status,)
            )
        return [self._delta_from_row(r) for r in rows]

    def list_delta_events(self, delta_id: str) -> list[DeltaEvent]:
        rows = self._db.fetch_all(
            "SELECT * FROM delta_events WHERE delta_id = ? ORDER BY rowid", (delta_id,)
        )
        return [
            DeltaEvent(
                id=r["id"], delta_id=r["delta_id"], event=r["event"], actor=r["actor"],
                detail=json.loads(r["detail"]), created_at=r["created_at"],
            )
            for r in rows
        ]

    def list_approvals(self, delta_id: str) -> list[ApprovalRecord]:
        rows = self._db.fetch_all(
            "SELECT * FROM approvals WHERE delta_id = ? ORDER BY rowid", (delta_id,)
        )
        return [
            ApprovalRecord(
                id=r["id"], delta_id=r["delta_id"], approver=r["approver"],
                decision=r["decision"], reason=r["reason"], created_at=r["created_at"],
            )
            for r in rows
        ]

    def get_audit_log(self, limit: int = 100, action: str | None = None) -> list[AuditRecord]:
        """Most-recent-first audit rows, optionally filtered by action."""
        if action is None:
            rows = self._db.fetch_all(
                "SELECT * FROM audit_log ORDER BY rowid DESC LIMIT ?", (limit,)
            )
        else:
            rows = self._db.fetch_all(
                "SELECT * FROM audit_log WHERE action = ? ORDER BY rowid DESC LIMIT ?",
                (action, limit),
            )
        return [
            AuditRecord(
                id=r["id"], actor=r["actor"], action=r["action"],
                action_category=r["action_category"], store_type=r["store_type"],
                artifact_id=r["artifact_id"], details=json.loads(r["details"]),
                created_at=r["created_at"],
            )
            for r in rows
        ]

    def list_contributions(self, sme_id: str) -> list[ContributionRecord]:
        rows = self._db.fetch_all(
            "SELECT * FROM contributions WHERE sme_id = ? ORDER BY rowid", (sme_id,)
        )
        return [
            ContributionRecord(
                id=r["id"], sme_id=r["sme_id"], sme_persona=r["sme_persona"],
                delta_ids=json.loads(r["delta_ids"]), therapeutic_area=r["therapeutic_area"],
                scenario_type=r["scenario_type"], sme_confidence=r["sme_confidence"],
                created_by=r["created_by"], created_at=r["created_at"],
            )
            for r in rows
        ]

    def close(self) -> None:
        """Close the underlying connection (used to simulate a process restart)."""
        self._db.close()

    @staticmethod
    def _delta_from_row(row: dict[str, Any]) -> DeltaRecord:
        return DeltaRecord(
            id=row["id"], type=row["type"], status=row["status"],
            content=json.loads(row["content"]), created_by=row["created_by"],
            created_at=row["created_at"], updated_at=row["updated_at"],
            reviewer=row["reviewer"], reason=row["reason"],
        )
