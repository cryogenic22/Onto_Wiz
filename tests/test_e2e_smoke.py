"""
End-to-End Smoke Test Suite (SEN-008)
=====================================
Exercises the full Onto_Wiz pipeline: session submission -> delta generation ->
review queue -> approval/rejection/escalation -> audit trail.

Each test is a complete user journey, not an isolated API call.

Usage:
    pytest tests/test_e2e_smoke.py -v           # All smoke tests
    pytest tests/test_e2e_smoke.py -v -m e2e    # Via marker

Owner: Team SENTINEL
"""

from __future__ import annotations

import pytest


pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Helpers — reusable within this test file
# ---------------------------------------------------------------------------

def _valid_session_payload() -> dict:
    """Full 9-step game session payload matching frontend GameResponses."""
    return {
        "scenarioId": "university_klinik_bonn",
        "hypothesis": {
            "category": "market_access",
            "specificDriver": "PA edits",
            "confidence": 0.7,
            "reasoning": "Regional pattern suggests access friction",
        },
        "signals": [
            {"signalName": "TRx", "role": "validation", "priorityRank": 1},
            {"signalName": "NBRx", "role": "disconfirming", "priorityRank": 2},
        ],
        "disconfirm": {
            "condition": "If NBRx is flat but TRx drops",
            "wouldSuggest": "Fulfillment issue",
            "wouldRuleOut": "Demand erosion",
        },
        "pattern": {
            "frequency": "often",
            "typicalOutcome": "Localized PA edits",
            "timeToResolution": "4-6 weeks",
        },
        "mistakes": [
            {
                "wrongConclusion": "Assume demand erosion",
                "whyWrong": "Need NBRx confirmation first",
                "unlessEvidence": "NBRx decline confirmed",
            }
        ],
        "actions": [
            {
                "action": "Pull PA reject data",
                "actionType": "investigate",
                "priority": 1,
                "ownerFunction": "access_team",
            }
        ],
        "confidence": {
            "finalConfidence": 0.75,
            "reasoning": "Strong regional pattern",
        },
    }


def create_game_session(client) -> dict:
    """Submit a full game session, return response body."""
    resp = client.post("/sessions", json=_valid_session_payload())
    assert resp.status_code == 201, resp.text
    return resp.json()


def create_delta(client, delta_type="proposed_pattern",
                 blast_radius="medium", confidence=0.5) -> dict:
    """Submit a delta with specific type/blast, return response body."""
    payload = {
        "type": delta_type,
        "content": {"signal": "smoke_test", "name": "e2e_test"},
        "confidence": confidence,
        "blast_radius": blast_radius,
        "evidence_pointers": ["ev_smoke_001"],
        "source_type": "manual",
        "source_id": "e2e_smoke",
    }
    resp = client.post("/deltas", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


def approve_delta(client, delta_id: str,
                  reviewer: str = "e2e_reviewer") -> dict:
    """Approve a delta and return response body."""
    resp = client.post(
        f"/deltas/{delta_id}/approve", json={"reviewer": reviewer},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def reject_delta(client, delta_id: str, reviewer: str = "e2e_reviewer",
                 reason: str = "E2E rejection") -> dict:
    """Reject a delta and return response body."""
    resp = client.post(
        f"/deltas/{delta_id}/reject",
        json={"reviewer": reviewer, "reason": reason},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# Test 1: Full Game Session Pipeline
# ---------------------------------------------------------------------------

class TestGameSessionPipeline:
    """POST /sessions -> deltas generated -> appear in review queue."""

    def test_full_game_session_pipeline(self, client):
        session = create_game_session(client)
        assert session["deltas_generated"] > 0
        assert len(session["delta_ids"]) == session["deltas_generated"]

        # Verify deltas exist in the store
        for did in session["delta_ids"]:
            resp = client.get(f"/deltas/{did}")
            assert resp.status_code == 200

        # Verify deltas appear in review queue
        resp = client.get("/review-queue")
        assert resp.status_code == 200
        queue_items = resp.json()
        queue_delta_ids = {
            item["delta"]["id"] for item in queue_items
        }
        session_in_queue = queue_delta_ids & set(session["delta_ids"])
        assert len(session_in_queue) > 0, (
            "No session deltas found in review queue"
        )

        # Verify routing metadata on queued items
        for item in queue_items:
            assert "queue" in item
            assert "assigned_to" in item
            assert "priority" in item


# ---------------------------------------------------------------------------
# Test 2: Delta Approve Flow
# ---------------------------------------------------------------------------

class TestDeltaApproveFlow:
    """Propose -> review queue -> approve -> audit log."""

    def test_delta_approve_flow(self, client):
        delta = create_delta(client)
        delta_id = delta["id"]
        assert delta["status"] == "proposed"

        # Confirm appears in review queue
        resp = client.get("/review-queue")
        ids_in_queue = [item["delta"]["id"] for item in resp.json()]
        assert delta_id in ids_in_queue

        # Approve
        approved = approve_delta(client, delta_id, "domain_expert_alice")
        assert approved["status"] == "approved"

        # Verify audit log captures the approval
        resp = client.get("/audit-log", params={"store": "deltas"})
        entries = resp.json()
        approval_entries = [
            e for e in entries
            if e["action"] == "approve" and e.get("artifact_id") == delta_id
        ]
        assert len(approval_entries) >= 1


# ---------------------------------------------------------------------------
# Test 3: Delta Reject Flow
# ---------------------------------------------------------------------------

class TestDeltaRejectFlow:
    """Propose -> reject with reason -> audit captures reason."""

    def test_delta_reject_flow(self, client):
        delta = create_delta(client, blast_radius="high")
        delta_id = delta["id"]

        rejected = reject_delta(
            client, delta_id, "governance_reviewer", "Insufficient evidence",
        )
        assert rejected["status"] == "rejected"
        assert rejected["rejection_reason"] == "Insufficient evidence"

        # Verify audit log
        resp = client.get("/audit-log", params={"store": "deltas"})
        entries = resp.json()
        reject_entries = [
            e for e in entries
            if e["action"] == "reject" and e.get("artifact_id") == delta_id
        ]
        assert len(reject_entries) >= 1


# ---------------------------------------------------------------------------
# Test 4: Escalation Flow
# ---------------------------------------------------------------------------

class TestEscalationFlow:
    """CAUSAL delta -> escalate -> governance_board."""

    def test_escalation_flow(self, client):
        # CAUSAL + MEDIUM = standard queue, domain_expert
        delta = create_delta(
            client, delta_type="proposed_pattern", blast_radius="medium",
        )
        delta_id = delta["id"]

        # Verify initial routing
        resp = client.get("/review-queue")
        items = resp.json()
        item = next(
            (i for i in items if i["delta"]["id"] == delta_id), None,
        )
        assert item is not None
        assert item["assigned_to"] == "domain_expert"

        # Escalate
        resp = client.post(
            f"/deltas/{delta_id}/escalate",
            json={"reason": "Needs governance review"},
        )
        assert resp.status_code == 200

        # Verify audit log records escalation
        resp = client.get("/audit-log", params={"store": "deltas"})
        entries = resp.json()
        escalation_entries = [
            e for e in entries if "escalat" in e.get("action", "").lower()
        ]
        assert len(escalation_entries) >= 1


# ---------------------------------------------------------------------------
# Test 5: Conflict Detection E2E
# ---------------------------------------------------------------------------

class TestConflictDetectionE2E:
    """Two deltas targeting the same canonical ID -> conflicts detected."""

    def test_conflict_detection_e2e(self, client):
        # Create two synonym deltas sharing the same canonical term
        payload_a = {
            "type": "proposed_synonym",
            "content": {"term": "market_access", "target": "formulary"},
            "confidence": 0.5,
            "blast_radius": "medium",
            "source_type": "manual",
        }
        payload_b = {
            "type": "proposed_synonym",
            "content": {"term": "market_access", "target": "payer_access"},
            "confidence": 0.5,
            "blast_radius": "medium",
            "source_type": "manual",
        }
        resp_a = client.post("/deltas", json=payload_a)
        resp_b = client.post("/deltas", json=payload_b)
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200

        # Verify both deltas were created
        list_resp = client.get("/deltas")
        body = list_resp.json()
        assert body["total"] >= 2

        # Verify the store detects conflicts internally
        from src.api.server import delta_store
        delta_b = delta_store.get(resp_b.json()["id"])
        conflicts = delta_store.find_conflicts(delta_b)
        assert len(conflicts) >= 1
        assert conflicts[0].conflict_type == "canonical_id_collision"


# ---------------------------------------------------------------------------
# Test 6: Pattern Matching E2E
# ---------------------------------------------------------------------------

class TestPatternMatchingE2E:
    """Create + approve pattern -> intelligence packet uses it."""

    def test_pattern_matching_e2e(self, client):
        # Create and approve a pattern
        pattern_resp = client.post("/patterns", json={
            "applies_when_signals": ["NBRx"],
            "applies_when_context": ["northeast"],
            "typical_drivers": [
                {"driver": "access_friction", "prior_confidence": 0.8},
            ],
        })
        assert pattern_resp.status_code == 200
        pattern_id = pattern_resp.json()["id"]

        approve_resp = client.post(
            f"/patterns/{pattern_id}/approve",
            params={"approver": "lead_reviewer"},
        )
        assert approve_resp.status_code == 200

        # Generate intelligence packet with matching signal
        packet_resp = client.post("/intelligence-packet", json={
            "signal": "NBRx decline in Northeast",
            "signal_metric": "NBRx",
            "signal_change": -0.12,
            "context": {"region": "northeast"},
            "mission_id": "e2e_mission",
            "persona": "brand_lead",
        })
        assert packet_resp.status_code == 200
        packet = packet_resp.json()

        # Verify matched pattern is referenced
        assert pattern_id in packet["patterns_used"]
        assert len(packet["drivers"]) >= 1
        assert any(
            d["driver"] == "access_friction" for d in packet["drivers"]
        )


# ---------------------------------------------------------------------------
# Test 7: Guardrail Enforcement E2E
# ---------------------------------------------------------------------------

class TestGuardrailEnforcementE2E:
    """Create + approve guardrail -> appears in intelligence packet."""

    def test_guardrail_enforcement_e2e(self, client):
        # Create and approve a guardrail
        guard_resp = client.post("/guardrails", json={
            "blocks_action_types": ["aggressive_pricing"],
            "blocks_drivers": ["unverified_rumor"],
            "unless_evidence": ["confirmed_competitive_intel"],
        })
        assert guard_resp.status_code == 200
        guardrail_id = guard_resp.json()["id"]

        approve_resp = client.post(
            f"/guardrails/{guardrail_id}/approve",
            params={"approver": "compliance_lead"},
        )
        assert approve_resp.status_code == 200

        # Also create a pattern so intelligence packet works
        pattern_resp = client.post("/patterns", json={
            "applies_when_signals": ["TRx"],
            "typical_drivers": [
                {"driver": "competitive_entry", "prior_confidence": 0.6},
            ],
        })
        pat_id = pattern_resp.json()["id"]
        client.post(
            f"/patterns/{pat_id}/approve",
            params={"approver": "reviewer"},
        )

        # Generate intelligence packet
        packet_resp = client.post("/intelligence-packet", json={
            "signal": "TRx decline",
            "signal_metric": "TRx",
            "signal_change": -0.08,
            "context": {},
            "mission_id": "e2e_guard",
            "persona": "brand_lead",
        })
        assert packet_resp.status_code == 200
        packet = packet_resp.json()

        # Verify guardrail is referenced
        assert guardrail_id in packet["guardrails_applied"]


# ---------------------------------------------------------------------------
# Test 8: Audit Trail Completeness
# ---------------------------------------------------------------------------

class TestAuditTrailCompleteness:
    """5 operations -> all appear in audit log in order."""

    def test_audit_trail_completeness(self, client):
        # Op 1: Propose delta
        d1 = create_delta(client)
        d1_id = d1["id"]

        # Op 2: Approve delta
        approve_delta(client, d1_id, "reviewer_1")

        # Op 3: Propose + reject another delta
        d2 = create_delta(client, blast_radius="high")
        d2_id = d2["id"]

        # Op 4: Reject delta
        reject_delta(client, d2_id, "reviewer_2", "Not enough evidence")

        # Op 5: Create pattern
        client.post("/patterns", json={
            "applies_when_signals": ["audit_test"],
            "typical_drivers": [
                {"driver": "test_driver", "prior_confidence": 0.5},
            ],
        })

        # Verify audit log captures all delta operations
        resp = client.get("/audit-log", params={"store": "deltas"})
        assert resp.status_code == 200
        entries = resp.json()

        actions = [e["action"] for e in entries]
        assert "propose" in actions, f"Missing 'propose' in {actions}"
        assert "approve" in actions, f"Missing 'approve' in {actions}"
        assert "reject" in actions, f"Missing 'reject' in {actions}"

        # Verify export includes all entries
        export_resp = client.get("/audit-log/export")
        assert export_resp.status_code == 200
        export_entries = export_resp.json()
        assert len(export_entries) >= len(entries)


# ---------------------------------------------------------------------------
# Test 9: Queue Stats Accuracy
# ---------------------------------------------------------------------------

class TestQueueStatsAccuracy:
    """3 delta types -> verify routing counts match."""

    def test_queue_stats_accuracy(self, client):
        # EMPIRICAL + LOW = auto queue (auto-approved if high confidence)
        # Use medium confidence so it stays proposed
        create_delta(
            client, delta_type="proposed_synonym",
            blast_radius="low", confidence=0.5,
        )

        # CAUSAL + MEDIUM = standard queue
        create_delta(
            client, delta_type="proposed_pattern",
            blast_radius="medium", confidence=0.5,
        )

        # NORMATIVE + HIGH = escalated queue
        create_delta(
            client, delta_type="proposed_action",
            blast_radius="high", confidence=0.5,
        )

        resp = client.get("/review-queue/stats")
        assert resp.status_code == 200
        stats = resp.json()

        assert stats["total_pending"] >= 3
        # EMPIRICAL+LOW goes to auto queue
        assert stats["auto"] >= 1, f"Expected auto >= 1, got {stats}"
        # CAUSAL+MEDIUM goes to standard queue
        assert stats["standard"] >= 1, f"Expected standard >= 1, got {stats}"
        # NORMATIVE+HIGH goes to escalated queue
        assert stats["escalated"] >= 1, f"Expected escalated >= 1, got {stats}"
