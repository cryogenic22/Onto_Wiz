"""F0.2 — governance persistence + restart-survival (Tier A runtime).

Anchors: BUILD_INSTRUCTION_SET_2026-07 §F0.2 + §9 (DDL) + §11 (restart-survival).
The store persists the delta lifecycle onto the db.py SQLite seam; it does NOT
promote artifacts to ACTIVE (R1's pipe, bridge.py, is untouched).
"""
from __future__ import annotations

import pytest
from ontowiz_runtime.governance import GovernanceStore


def _store(tmp_path) -> GovernanceStore:
    return GovernanceStore(tmp_path)


def test_propose_delta_persists_row_event_and_audit(tmp_path) -> None:
    store = _store(tmp_path)
    d = store.propose_delta(
        "D-1",
        delta_type="proposed_edge",
        content={"subject": "R-110", "change": "add anti-pattern"},
        created_by="sme:alice",
    )
    assert d.id == "D-1"
    assert d.status == "proposed"
    assert d.content["subject"] == "R-110"
    assert d.created_by == "sme:alice"

    got = store.get_delta("D-1")
    assert got is not None and got.status == "proposed"

    events = store.list_delta_events("D-1")
    assert [e.event for e in events] == ["proposed"]
    assert events[0].actor == "sme:alice"

    audit = store.get_audit_log()
    assert any(a.action == "propose" and a.artifact_id == "D-1" for a in audit)


def test_approve_records_approval_event_audit_and_status(tmp_path) -> None:
    store = _store(tmp_path)
    store.propose_delta("D-2", delta_type="proposed_entity", content={}, created_by="sme:bob")
    d = store.approve_delta("D-2", approver="curator:carol", reason="grounded")
    assert d.status == "approved"
    assert d.reviewer == "curator:carol"

    approvals = store.list_approvals("D-2")
    assert len(approvals) == 1
    assert approvals[0].approver == "curator:carol"
    assert approvals[0].decision == "approve"
    assert approvals[0].reason == "grounded"

    assert [e.event for e in store.list_delta_events("D-2")] == ["proposed", "approved"]
    assert "approve" in [a.action for a in store.get_audit_log()]


def test_reject_records_reason_and_status(tmp_path) -> None:
    store = _store(tmp_path)
    store.propose_delta("D-3", delta_type="proposed_edge", content={}, created_by="sme:bob")
    d = store.reject_delta("D-3", approver="curator:carol", reason="unsupported")
    assert d.status == "rejected"
    approvals = store.list_approvals("D-3")
    assert approvals[0].decision == "reject"
    assert approvals[0].reason == "unsupported"
    assert [e.event for e in store.list_delta_events("D-3")] == ["proposed", "rejected"]


def test_escalate_logs_without_changing_status(tmp_path) -> None:
    store = _store(tmp_path)
    store.propose_delta("D-4", delta_type="proposed_edge", content={}, created_by="sme:bob")
    d = store.escalate_delta("D-4", actor="curator:carol", reason="needs medical review")
    assert d.status == "proposed"  # escalation is a routing signal, not a decision
    assert [e.event for e in store.list_delta_events("D-4")] == ["proposed", "escalated"]
    assert "escalate" in [a.action for a in store.get_audit_log()]


def test_record_contribution_persists(tmp_path) -> None:
    store = _store(tmp_path)
    c = store.record_contribution(
        sme_id="sme:alice",
        delta_ids=["D-1", "D-2"],
        created_by="sme:alice",
        sme_persona="oncology-msl",
        therapeutic_area="oncology",
        scenario_type="qbr",
        sme_confidence=0.8,
    )
    assert c.sme_id == "sme:alice"
    assert c.delta_ids == ["D-1", "D-2"]
    got = store.list_contributions("sme:alice")
    assert len(got) == 1 and got[0].delta_ids == ["D-1", "D-2"]
    assert "record" in [a.action for a in store.get_audit_log()]


def test_write_on_unknown_delta_raises(tmp_path) -> None:
    store = _store(tmp_path)
    with pytest.raises(ValueError):
        store.approve_delta("nope", approver="curator:carol")
    with pytest.raises(ValueError):
        store.reject_delta("nope", approver="curator:carol", reason="x")
    with pytest.raises(ValueError):
        store.escalate_delta("nope", actor="curator:carol", reason="x")


def test_get_audit_log_filter_and_limit(tmp_path) -> None:
    store = _store(tmp_path)
    store.propose_delta("D-5", delta_type="proposed_edge", content={}, created_by="sme:bob")
    store.approve_delta("D-5", approver="curator:carol", reason="ok")
    only_approve = store.get_audit_log(action="approve")
    assert only_approve and all(a.action == "approve" for a in only_approve)
    assert len(store.get_audit_log(limit=1)) == 1


def test_list_deltas_by_status(tmp_path) -> None:
    store = _store(tmp_path)
    store.propose_delta("D-6", delta_type="proposed_edge", content={}, created_by="sme:bob")
    store.propose_delta("D-7", delta_type="proposed_edge", content={}, created_by="sme:bob")
    store.approve_delta("D-7", approver="curator:carol", reason="ok")
    assert {d.id for d in store.list_deltas(status="proposed")} == {"D-6"}
    assert {d.id for d in store.list_deltas(status="approved")} == {"D-7"}
    assert {d.id for d in store.list_deltas()} == {"D-6", "D-7"}


def test_approval_and_audit_survive_restart(tmp_path) -> None:
    # Approve on the first "process".
    store = GovernanceStore(tmp_path)
    store.propose_delta(
        "D-42", delta_type="proposed_edge", content={"rule": "R-110"}, created_by="sme:alice"
    )
    store.approve_delta("D-42", approver="curator:carol", reason="grounded in QBR")
    store.close()

    # Restart: a brand-new store instance over the same directory.
    restarted = GovernanceStore(tmp_path)
    d = restarted.get_delta("D-42")
    assert d is not None
    assert d.status == "approved"
    assert d.reviewer == "curator:carol"

    approvals = restarted.list_approvals("D-42")
    assert approvals and approvals[0].approver == "curator:carol"

    actions = [a.action for a in restarted.get_audit_log()]
    assert "propose" in actions and "approve" in actions

    # R4: attribution is a real principal, never the literal 'curator'.
    assert all(a.actor != "curator" for a in restarted.get_audit_log())
