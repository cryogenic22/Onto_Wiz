"""
API Integration Tests for Onto_Wiz — LENS-001

Tests all 17 endpoints: happy-path + error-path.
Uses FastAPI TestClient — no extra packages.
"""


# =============================================================================
# HEALTH & STATS
# =============================================================================

class TestHealth:
    """GET /health and GET /stats."""

    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "active"
        assert "engine_loaded" in body
        assert body["stores_initialized"] is True

    def test_stats_returns_200(self, client):
        resp = client.get("/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert "deltas" in body
        assert "patterns" in body
        assert "guardrails" in body


# =============================================================================
# DELTA ENDPOINTS
# =============================================================================

class TestDeltaCreate:
    """POST /deltas."""

    def test_create_delta_201(self, client, sample_delta_payload):
        resp = client.post("/deltas", json=sample_delta_payload)
        assert resp.status_code == 200  # FastAPI default for sync POST
        body = resp.json()
        assert "id" in body
        assert body["type"] == "proposed_synonym"
        assert body["confidence"] == 0.85
        assert body["source_type"] == "manual"

    def test_create_delta_auto_approve_level1(self, client):
        """Low blast radius + high confidence synonym = auto-approved."""
        payload = {
            "type": "proposed_synonym",
            "content": {"source": "a", "target": "b"},
            "confidence": 0.95,
            "blast_radius": "low",
            "evidence_pointers": [],
            "source_type": "manual",
        }
        resp = client.post("/deltas", json=payload)
        body = resp.json()
        assert body["auto_approved"] is True
        assert body["status"] == "approved"

    def test_create_delta_missing_type_422(self, client):
        """Missing required 'type' field -> 422."""
        resp = client.post("/deltas", json={"content": {"a": "b"}})
        assert resp.status_code == 422

    def test_create_delta_invalid_confidence_422(self, client):
        """Confidence > 1.0 -> 422."""
        payload = {
            "type": "proposed_synonym",
            "content": {"a": "b"},
            "confidence": 1.5,
        }
        resp = client.post("/deltas", json=payload)
        assert resp.status_code == 422


class TestDeltaList:
    """GET /deltas."""

    def test_list_deltas_empty(self, client):
        resp = client.get("/deltas")
        assert resp.status_code == 200
        body = resp.json()
        assert body["deltas"] == []
        assert body["total"] == 0

    def test_list_deltas_after_create(self, client, sample_delta_payload):
        client.post("/deltas", json=sample_delta_payload)
        resp = client.get("/deltas")
        body = resp.json()
        assert body["total"] >= 1

    def test_list_deltas_filter_by_status(self, client, sample_delta_payload):
        """Filter by status=proposed returns only pending deltas."""
        # Non-auto-approvable delta (medium blast radius)
        payload = {**sample_delta_payload, "blast_radius": "medium", "confidence": 0.5}
        client.post("/deltas", json=payload)
        resp = client.get("/deltas", params={"status": "proposed"})
        body = resp.json()
        assert len(body["deltas"]) >= 1
        for d in body["deltas"]:
            assert d["status"] == "proposed"


class TestDeltaGetById:
    """GET /deltas/{id}."""

    def test_get_delta_by_id(self, client, sample_delta_payload):
        create_resp = client.post("/deltas", json=sample_delta_payload)
        delta_id = create_resp.json()["id"]
        resp = client.get(f"/deltas/{delta_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == delta_id

    def test_get_delta_not_found_404(self, client):
        resp = client.get("/deltas/nonexistent_id")
        assert resp.status_code == 404


class TestDeltaApprove:
    """POST /deltas/{id}/approve."""

    def _create_pending_delta(self, client) -> str:
        """Helper: create a delta that stays in proposed status."""
        payload = {
            "type": "proposed_pattern",
            "content": {"name": "test_pattern"},
            "confidence": 0.5,
            "blast_radius": "medium",
            "evidence_pointers": [],
            "source_type": "manual",
        }
        resp = client.post("/deltas", json=payload)
        body = resp.json()
        assert body["status"] == "proposed"
        return body["id"]

    def test_approve_pending_delta(self, client):
        delta_id = self._create_pending_delta(client)
        resp = client.post(
            f"/deltas/{delta_id}/approve",
            json={"reviewer": "alice"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"

    def test_approve_nonexistent_delta_400(self, client):
        resp = client.post(
            "/deltas/nonexistent/approve",
            json={"reviewer": "alice"},
        )
        assert resp.status_code == 400

    def test_approve_already_approved_400(self, client):
        delta_id = self._create_pending_delta(client)
        client.post(f"/deltas/{delta_id}/approve", json={"reviewer": "alice"})
        resp = client.post(
            f"/deltas/{delta_id}/approve",
            json={"reviewer": "bob"},
        )
        assert resp.status_code == 400


class TestDeltaReject:
    """POST /deltas/{id}/reject."""

    def test_reject_pending_delta(self, client):
        payload = {
            "type": "proposed_edge",
            "content": {"source": "a", "target": "b"},
            "confidence": 0.5,
            "blast_radius": "high",
            "evidence_pointers": [],
            "source_type": "manual",
        }
        resp = client.post("/deltas", json=payload)
        delta_id = resp.json()["id"]

        resp = client.post(
            f"/deltas/{delta_id}/reject",
            json={"reviewer": "bob", "reason": "Too broad"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "rejected"
        assert resp.json()["rejection_reason"] == "Too broad"

    def test_reject_nonexistent_delta_400(self, client):
        resp = client.post(
            "/deltas/nonexistent/reject",
            json={"reviewer": "bob", "reason": "test"},
        )
        assert resp.status_code == 400


class TestDeltaPromote:
    """POST /deltas/promote."""

    def test_promote_returns_result(self, client):
        resp = client.post("/deltas/promote")
        assert resp.status_code == 200
        body = resp.json()
        assert "promoted" in body
        assert "message" in body

    def test_promote_after_approval(self, client, sample_delta_payload):
        # Create and approve a delta
        payload = {**sample_delta_payload, "blast_radius": "medium", "confidence": 0.5}
        create_resp = client.post("/deltas", json=payload)
        delta_id = create_resp.json()["id"]
        client.post(f"/deltas/{delta_id}/approve", json={"reviewer": "alice"})

        resp = client.post("/deltas/promote")
        assert resp.status_code == 200


# =============================================================================
# PATTERN ENDPOINTS
# =============================================================================

class TestPatterns:
    """POST /patterns, GET /patterns, POST /patterns/{id}/approve."""

    def test_create_pattern(self, client, sample_pattern_payload):
        resp = client.post("/patterns", json=sample_pattern_payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "id" in body
        assert body["status"] == "draft"
        assert body["is_active"] is False
        assert body["owner"] == "test_owner"

    def test_list_patterns_empty(self, client):
        resp = client.get("/patterns")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_patterns_after_create(self, client, sample_pattern_payload):
        client.post("/patterns", json=sample_pattern_payload)
        resp = client.get("/patterns")
        assert len(resp.json()) == 1

    def test_approve_pattern(self, client, sample_pattern_payload):
        create_resp = client.post("/patterns", json=sample_pattern_payload)
        pattern_id = create_resp.json()["id"]

        resp = client.post(
            f"/patterns/{pattern_id}/approve",
            params={"approver": "lead_reviewer"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"
        assert resp.json()["is_active"] is True

    def test_approve_pattern_not_found_404(self, client):
        resp = client.post(
            "/patterns/nonexistent/approve",
            params={"approver": "reviewer"},
        )
        assert resp.status_code == 404

    def test_list_active_patterns_only(self, client, sample_pattern_payload):
        create_resp = client.post("/patterns", json=sample_pattern_payload)
        pattern_id = create_resp.json()["id"]
        client.post(
            f"/patterns/{pattern_id}/approve",
            params={"approver": "reviewer"},
        )
        # Create a second pattern but don't approve it
        client.post("/patterns", json=sample_pattern_payload)

        resp = client.get("/patterns", params={"active_only": "true"})
        assert len(resp.json()) == 1


# =============================================================================
# GUARDRAIL ENDPOINTS
# =============================================================================

class TestGuardrails:
    """POST /guardrails, GET /guardrails, POST /guardrails/{id}/approve."""

    def test_create_guardrail(self, client, sample_guardrail_payload):
        resp = client.post("/guardrails", json=sample_guardrail_payload)
        assert resp.status_code == 200
        body = resp.json()
        assert "id" in body
        assert body["status"] == "draft"
        assert body["is_active"] is False
        assert body["owner"] == "compliance_team"

    def test_list_guardrails_empty(self, client):
        resp = client.get("/guardrails")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_guardrails_after_create(self, client, sample_guardrail_payload):
        client.post("/guardrails", json=sample_guardrail_payload)
        resp = client.get("/guardrails")
        assert len(resp.json()) == 1

    def test_approve_guardrail(self, client, sample_guardrail_payload):
        create_resp = client.post("/guardrails", json=sample_guardrail_payload)
        guardrail_id = create_resp.json()["id"]

        resp = client.post(
            f"/guardrails/{guardrail_id}/approve",
            params={"approver": "compliance_lead"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"
        assert resp.json()["is_active"] is True

    def test_approve_guardrail_not_found_404(self, client):
        resp = client.post(
            "/guardrails/nonexistent/approve",
            params={"approver": "reviewer"},
        )
        assert resp.status_code == 404


# =============================================================================
# INTELLIGENCE PACKET
# =============================================================================

class TestIntelligencePacket:
    """POST /intelligence-packet."""

    def test_generate_packet_200(self, client):
        resp = client.post("/intelligence-packet", json={
            "signal": "NBRx decline in Northeast",
            "signal_metric": "NBRx",
            "signal_change": -0.15,
            "context": {"region": "northeast", "brand": "TestBrand"},
            "mission_id": "mission_001",
            "persona": "brand_lead",
        })
        assert resp.status_code == 200
        body = resp.json()
        assert "id" in body
        assert body["signal_metric"] == "NBRx"
        assert "drivers" in body
        assert len(body["drivers"]) >= 1
        assert "implication" in body
        assert "time_to_generate_ms" in body

    def test_generate_packet_missing_signal_422(self, client):
        resp = client.post("/intelligence-packet", json={
            "signal_metric": "NBRx",
            "signal_change": -0.1,
        })
        assert resp.status_code == 422


# =============================================================================
# LEGACY ENDPOINTS
# =============================================================================

class TestLegacy:
    """GET /scenarios and POST /reason."""

    def test_list_scenarios_200(self, client):
        resp = client.get("/scenarios")
        assert resp.status_code == 200
        scenarios = resp.json()
        assert isinstance(scenarios, list)
        assert len(scenarios) >= 1
        assert "id" in scenarios[0]
        assert "name" in scenarios[0]

    def test_reason_without_engine_500(self, client):
        """POST /reason when engine is None returns 500."""
        from src.api import server
        original_engine = server.engine
        server.engine = None
        try:
            resp = client.post("/reason", json={
                "account_id": "acc_001",
                "brand_id": "brand_001",
                "question": "Why did Brand X dip?",
            })
            assert resp.status_code == 500
        finally:
            server.engine = original_engine


# =============================================================================
# VALIDATION EDGE CASES
# =============================================================================

class TestValidation:
    """422 responses for invalid payloads."""

    def test_delta_empty_body_422(self, client):
        resp = client.post("/deltas", json={})
        assert resp.status_code == 422

    def test_delta_invalid_type_422(self, client):
        resp = client.post("/deltas", json={
            "type": "not_a_real_type",
            "content": {"a": "b"},
        })
        assert resp.status_code == 422

    def test_delta_invalid_blast_radius_422(self, client):
        resp = client.post("/deltas", json={
            "type": "proposed_synonym",
            "content": {"a": "b"},
            "blast_radius": "extreme",
        })
        assert resp.status_code == 422

    def test_pattern_missing_signals_422(self, client):
        resp = client.post("/patterns", json={})
        assert resp.status_code == 422

    def test_guardrail_missing_blocks_422(self, client):
        resp = client.post("/guardrails", json={})
        assert resp.status_code == 422

    def test_intelligence_packet_empty_422(self, client):
        resp = client.post("/intelligence-packet", json={})
        assert resp.status_code == 422

    def test_approve_delta_missing_reviewer_422(self, client):
        resp = client.post("/deltas/any_id/approve", json={})
        assert resp.status_code == 422

    def test_reject_delta_missing_reason_422(self, client):
        resp = client.post("/deltas/any_id/reject", json={"reviewer": "bob"})
        assert resp.status_code == 422


# =============================================================================
# SESSION ENDPOINTS
# =============================================================================

class TestSessions:
    """POST /sessions, GET /sessions, GET /sessions/{id}."""

    def _valid_session_payload(self) -> dict:
        """Build a valid game session payload matching frontend GameResponses."""
        return {
            "scenarioId": "university_klinik_bonn",
            "hypothesis": {
                "category": "market_access",
                "specificDriver": "PA edits",
                "confidence": 0.7,
                "reasoning": "Regional pattern suggests access friction"
            },
            "signals": [
                {"signalName": "TRx", "role": "validation", "priorityRank": 1},
                {"signalName": "NBRx", "role": "disconfirming", "priorityRank": 2}
            ],
            "disconfirm": {
                "condition": "If NBRx is flat but TRx drops",
                "wouldSuggest": "Fulfillment issue",
                "wouldRuleOut": "Demand erosion"
            },
            "pattern": {
                "frequency": "often",
                "typicalOutcome": "Localized PA edits",
                "timeToResolution": "4-6 weeks"
            },
            "mistakes": [
                {
                    "wrongConclusion": "Assume demand erosion",
                    "whyWrong": "Need NBRx confirmation first",
                    "unlessEvidence": "NBRx decline confirmed"
                }
            ],
            "actions": [
                {
                    "action": "Pull PA reject data",
                    "actionType": "investigate",
                    "priority": 1,
                    "ownerFunction": "access_team"
                }
            ],
            "confidence": {
                "finalConfidence": 0.75,
                "reasoning": "Strong regional pattern"
            }
        }

    def test_create_session_201(self, client):
        """Happy path: valid session creates deltas."""
        payload = self._valid_session_payload()
        resp = client.post("/sessions", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert "session_id" in body
        assert "reasoning_event_id" in body
        assert body["deltas_generated"] > 0
        assert len(body["delta_ids"]) == body["deltas_generated"]

    def test_create_session_missing_hypothesis_422(self, client):
        """Missing hypothesis field returns 422."""
        payload = {"scenarioId": "test"}
        resp = client.post("/sessions", json=payload)
        assert resp.status_code == 422

    def test_create_session_empty_payload_422(self, client):
        """Empty payload returns 422."""
        resp = client.post("/sessions", json={})
        assert resp.status_code == 422

    def test_create_session_deltas_in_store(self, client):
        """Verify created deltas appear in delta store."""
        payload = self._valid_session_payload()
        resp = client.post("/sessions", json=payload)
        body = resp.json()

        # Check deltas are in the store
        for delta_id in body["delta_ids"]:
            delta_resp = client.get(f"/deltas/{delta_id}")
            assert delta_resp.status_code == 200

    def test_list_sessions_empty(self, client):
        """GET /sessions returns empty list when no sessions exist."""
        resp = client.get("/sessions")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_sessions_after_create(self, client):
        """GET /sessions returns session after creation."""
        payload = self._valid_session_payload()
        client.post("/sessions", json=payload)

        resp = client.get("/sessions")
        assert resp.status_code == 200
        sessions = resp.json()
        assert len(sessions) == 1
        assert sessions[0]["scenario_id"] == "university_klinik_bonn"

    def test_get_session_detail(self, client):
        """GET /sessions/{id} returns full session detail."""
        payload = self._valid_session_payload()
        create_resp = client.post("/sessions", json=payload)
        event_id = create_resp.json()["reasoning_event_id"]

        resp = client.get(f"/sessions/{event_id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["hypothesis_category"] == "market_access"
        assert body["sme_confidence"] == 0.75
        assert body["processed"] is True

    def test_get_session_not_found(self, client):
        """GET /sessions/{id} returns 404 for unknown ID."""
        resp = client.get("/sessions/nonexistent")
        assert resp.status_code == 404

    def test_create_session_minimal(self, client):
        """Minimal valid payload: only hypothesis required beyond scenarioId."""
        payload = {
            "scenarioId": "test_scenario",
            "hypothesis": {
                "category": "too_early",
                "confidence": 0.3
            }
        }
        resp = client.post("/sessions", json=payload)
        assert resp.status_code == 201
        body = resp.json()
        assert body["deltas_generated"] >= 1  # At least the pattern delta


# =============================================================================
# HITL ROUTING ENDPOINTS
# =============================================================================

class TestReviewQueue:
    """GET /review-queue, GET /review-queue/stats, POST /deltas/{id}/escalate."""

    def _create_pending_delta(self, client, blast_radius="medium") -> str:
        """Create a delta that stays in proposed status."""
        payload = {
            "type": "proposed_pattern",
            "content": {"name": "test_pattern"},
            "confidence": 0.5,
            "blast_radius": blast_radius,
            "evidence_pointers": [],
            "source_type": "manual",
        }
        resp = client.post("/deltas", json=payload)
        body = resp.json()
        assert body["status"] == "proposed"
        return body["id"]

    def test_review_queue_empty(self, client):
        """Empty store returns empty review queue."""
        resp = client.get("/review-queue")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_review_queue_with_pending(self, client):
        """Pending delta appears in review queue with routing metadata."""
        self._create_pending_delta(client)
        resp = client.get("/review-queue")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert "queue" in items[0]
        assert "assigned_to" in items[0]
        assert "sla_hours" in items[0]
        assert "judgment_type" in items[0]

    def test_review_queue_filter_by_role(self, client):
        """Role filter returns only deltas assigned to that role."""
        self._create_pending_delta(client, blast_radius="medium")
        resp = client.get("/review-queue", params={"role": "domain_expert"})
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) >= 1
        for item in items:
            assert item["assigned_to"] == "domain_expert"

    def test_review_queue_filter_no_match(self, client):
        """Role filter returns empty when no deltas match."""
        self._create_pending_delta(client, blast_radius="medium")
        resp = client.get("/review-queue", params={"role": "governance_board"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_queue_stats_empty(self, client):
        """Empty store returns all zeros."""
        resp = client.get("/review-queue/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_pending"] == 0
        assert body["auto"] == 0
        assert body["standard"] == 0
        assert body["escalated"] == 0

    def test_queue_stats_after_create(self, client):
        """Stats reflect pending deltas in correct queues."""
        self._create_pending_delta(client, blast_radius="medium")
        resp = client.get("/review-queue/stats")
        body = resp.json()
        assert body["total_pending"] >= 1
        assert body["standard"] >= 1

    def test_escalate_delta(self, client):
        """Escalating a pending delta returns updated delta."""
        delta_id = self._create_pending_delta(client, blast_radius="medium")
        resp = client.post(
            f"/deltas/{delta_id}/escalate",
            json={"reason": "Needs governance review"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == delta_id

    def test_escalate_nonexistent_400(self, client):
        """Escalating unknown delta returns 400."""
        resp = client.post(
            "/deltas/nonexistent/escalate",
            json={"reason": "test"},
        )
        assert resp.status_code == 400

    def test_escalate_missing_reason_422(self, client):
        """Missing reason field returns 422."""
        resp = client.post("/deltas/any_id/escalate", json={})
        assert resp.status_code == 422


# =============================================================================
# AUDIT LOG ENDPOINTS
# =============================================================================

class TestAuditLog:
    """GET /audit-log, GET /audit-log/export."""

    def test_audit_log_empty(self, client):
        """Empty stores return empty audit log."""
        resp = client.get("/audit-log")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_audit_log_after_operations(self, client):
        """Creating a delta generates audit entries."""
        client.post("/deltas", json={
            "type": "proposed_synonym",
            "content": {"source": "a", "target": "b"},
            "confidence": 0.5,
            "blast_radius": "medium",
            "source_type": "manual",
        })
        resp = client.get("/audit-log")
        assert resp.status_code == 200
        entries = resp.json()
        assert len(entries) >= 1
        assert "action" in entries[0]
        assert "timestamp" in entries[0]

    def test_audit_log_filter_deltas_only(self, client):
        """Store filter 'deltas' excludes judgment store entries."""
        client.post("/deltas", json={
            "type": "proposed_synonym",
            "content": {"source": "a", "target": "b"},
            "confidence": 0.5,
            "blast_radius": "medium",
            "source_type": "manual",
        })
        resp = client.get("/audit-log", params={"store": "deltas"})
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_audit_log_export_json(self, client):
        """Export returns JSON array with ISO timestamps."""
        client.post("/deltas", json={
            "type": "proposed_synonym",
            "content": {"source": "a", "target": "b"},
            "confidence": 0.5,
            "blast_radius": "medium",
            "source_type": "manual",
        })
        resp = client.get("/audit-log/export")
        assert resp.status_code == 200
        entries = resp.json()
        assert len(entries) >= 1
        assert "timestamp" in entries[0]
        assert isinstance(entries[0]["timestamp"], str)  # ISO string


# =============================================================================
# CONTRIBUTION / SME IMPACT ENDPOINTS
# =============================================================================

class TestContributions:
    """GET /contributions/stats, /contributors/top, /contributors/{id}/summary, /contributors/{id}/contributions."""

    def _create_session(self, client) -> dict:
        payload = {
            "scenarioId": "university_klinik_bonn",
            "hypothesis": {
                "category": "market_access",
                "specificDriver": "PA edits",
                "confidence": 0.7,
                "reasoning": "Regional pattern suggests access friction",
            },
            "signals": [
                {"signalName": "TRx", "role": "validation", "priorityRank": 1},
            ],
            "mistakes": [],
            "actions": [],
        }
        resp = client.post("/sessions", json=payload)
        assert resp.status_code == 201
        return resp.json()

    def test_contribution_stats_empty(self, client):
        resp = client.get("/contributions/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_contributions"] == 0
        assert body["unique_smes"] == 0
        assert body["total_deltas"] == 0

    def test_contribution_stats_after_session(self, client):
        self._create_session(client)
        resp = client.get("/contributions/stats")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_contributions"] >= 1
        assert body["unique_smes"] >= 1

    def test_top_contributors_empty(self, client):
        resp = client.get("/contributors/top")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_top_contributors_after_sessions(self, client):
        self._create_session(client)
        self._create_session(client)
        resp = client.get("/contributors/top?limit=5")
        assert resp.status_code == 200
        contributors = resp.json()
        assert len(contributors) >= 1
        assert "total_contributions" in contributors[0]
        assert "total_deltas" in contributors[0]

    def test_contributor_summary_unknown(self, client):
        resp = client.get("/contributors/unknown_sme/summary")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total_contributions"] == 0
        assert body["total_deltas"] == 0

    def test_sme_contributions_empty(self, client):
        resp = client.get("/contributors/unknown_sme/contributions")
        assert resp.status_code == 200
        assert resp.json() == []
