"""
Unit Tests for Onto_Wiz Core Models and Stores

Tests the Delta Model, Judgment Artifacts, Governance, and Store operations.
"""

import pytest
from datetime import datetime, timedelta

from src.core import (
    # Models
    Delta, DeltaStatus, DeltaType, BlastRadius, ConflictResult,
    JudgmentPattern, Guardrail, GuardrailResult, ActionTemplate,
    ArtifactStatus, RiskClass, JudgmentType,
    Governance, DecayConfig, Scope,
    DriverAttribution, FunctionAction,
    TraversalPolicy, HardStopResult,
    # Stores
    DeltaStore, JudgmentStore, PromotionPipeline,
)


# =============================================================================
# DELTA MODEL TESTS
# =============================================================================

class TestDelta:
    """Tests for the Delta model (core primitive)."""
    
    def test_delta_creation(self):
        """Delta should be created with sensible defaults."""
        delta = Delta(
            type=DeltaType.PROPOSED_EDGE,
            content={"source": "SignalA", "target": "HypothesisB"}
        )
        
        assert delta.id is not None
        assert delta.status == DeltaStatus.PROPOSED
        assert delta.confidence == 0.5
        assert delta.blast_radius == BlastRadius.MEDIUM
    
    def test_delta_approval(self):
        """Delta can be approved by a reviewer."""
        delta = Delta(type=DeltaType.PROPOSED_PATTERN)
        
        delta.approve("reviewer_alice")
        
        assert delta.status == DeltaStatus.APPROVED
        assert delta.reviewed_by == "reviewer_alice"
        assert delta.reviewed_at is not None
    
    def test_delta_rejection(self):
        """Delta can be rejected with a reason."""
        delta = Delta(type=DeltaType.PROPOSED_GUARDRAIL)
        
        delta.reject("reviewer_bob", "Conflicts with existing guardrail")
        
        assert delta.status == DeltaStatus.REJECTED
        assert delta.rejection_reason == "Conflicts with existing guardrail"
    
    def test_auto_approvable_level1(self):
        """Level 1 deltas (low risk, high confidence) can auto-approve."""
        # Level 1: Low blast radius + high confidence + simple type
        delta = Delta(
            type=DeltaType.PROPOSED_SYNONYM,
            blast_radius=BlastRadius.LOW,
            confidence=0.95
        )
        
        assert delta.is_auto_approvable() is True
    
    def test_not_auto_approvable_high_risk(self):
        """High risk deltas should NOT auto-approve."""
        delta = Delta(
            type=DeltaType.PROPOSED_PATTERN,  # Not a simple type
            blast_radius=BlastRadius.HIGH,
            confidence=0.95
        )
        
        assert delta.is_auto_approvable() is False
    
    def test_not_auto_approvable_low_confidence(self):
        """Low confidence deltas should NOT auto-approve."""
        delta = Delta(
            type=DeltaType.PROPOSED_SYNONYM,
            blast_radius=BlastRadius.LOW,
            confidence=0.7  # Below 0.9 threshold
        )
        
        assert delta.is_auto_approvable() is False


# =============================================================================
# JUDGMENT PATTERN TESTS
# =============================================================================

class TestJudgmentPattern:
    """Tests for JudgmentPattern lifecycle and matching."""
    
    def test_pattern_creation(self):
        """Pattern should be created as draft."""
        pattern = JudgmentPattern(
            applies_when_signals=["TRx_drop", "PA_edit"],
            applies_when_context=["post_launch"]
        )
        
        assert pattern.status == ArtifactStatus.DRAFT
        assert pattern.judgment_type == JudgmentType.CAUSAL_HYPOTHESIS
    
    def test_pattern_not_active_when_draft(self):
        """Draft patterns should not be active."""
        pattern = JudgmentPattern()
        
        assert pattern.is_active() is False
    
    def test_pattern_active_when_approved(self):
        """Approved, non-stale patterns should be active."""
        pattern = JudgmentPattern()
        pattern.status = ArtifactStatus.APPROVED
        pattern.created_at = datetime.utcnow()  # Fresh
        
        assert pattern.is_active() is True
    
    def test_pattern_not_active_when_stale(self):
        """Patterns past their validity period should not be active."""
        pattern = JudgmentPattern(
            decay=DecayConfig(valid_for_days=30)
        )
        pattern.status = ArtifactStatus.APPROVED
        pattern.created_at = datetime.utcnow() - timedelta(days=60)  # Stale
        
        assert pattern.is_active() is False
    
    def test_pattern_matching(self):
        """Pattern should match when signals and scope align."""
        pattern = JudgmentPattern(
            applies_when_signals=["TRx_drop", "PA_edit"],
            scope=Scope(geography=["US"], lifecycle=["launch", "growth"])
        )

        # Matching case
        assert pattern.matches(
            signals=["TRx_drop", "Other"],
            context={"geography": "US", "lifecycle": "launch"}
        ) is True

        # Non-matching signals
        assert pattern.matches(
            signals=["Something_else"],
            context={"geography": "US"}
        ) is False

        # Non-matching scope
        assert pattern.matches(
            signals=["TRx_drop"],
            context={"geography": "EU"}
        ) is False

    def test_match_score_exact_match(self):
        """Full signal + context overlap should score high."""
        pattern = JudgmentPattern(
            applies_when_signals=["TRx_drop", "PA_edit"],
            applies_when_context=["launch"],
            scope=Scope(geography=["US"], lifecycle=["launch"]),
            judgment_type=JudgmentType.EMPIRICAL,
        )
        pattern.created_at = datetime.utcnow()

        score = pattern.match_score(
            signals=["TRx_drop", "PA_edit"],
            context={"geography": "US", "lifecycle": "launch"},
        )
        # signal=1.0, context=1.0, type=1.0, fresh=1.0
        # 0.40*1.0 + 0.25*1.0 + 0.20*1.0 + 0.15*1.0 = 1.0
        assert score == pytest.approx(1.0, abs=0.01)

    def test_match_score_partial_signal(self):
        """Partial signal overlap should reduce score proportionally."""
        pattern = JudgmentPattern(
            applies_when_signals=["TRx_drop", "PA_edit", "NBRx_decline"],
            scope=Scope(geography=["US"]),
        )
        pattern.created_at = datetime.utcnow()

        score = pattern.match_score(
            signals=["TRx_drop"],
            context={"geography": "US"},
        )
        # signal=1/3, context=1.0 (no applies_when_context), type=CAUSAL=0.7, fresh=1.0
        # 0.40*(1/3) + 0.25*1.0 + 0.20*0.7 + 0.15*1.0 ≈ 0.133+0.25+0.14+0.15=0.673
        assert 0.0 < score < 0.75

    def test_match_score_context_mismatch_penalty(self):
        """Scope mismatch should return 0.0."""
        pattern = JudgmentPattern(
            applies_when_signals=["TRx_drop"],
            scope=Scope(geography=["US"]),
        )
        score = pattern.match_score(
            signals=["TRx_drop"],
            context={"geography": "EU"},
        )
        assert score == 0.0

    def test_match_score_decay(self):
        """Stale patterns should score lower than fresh ones."""
        fresh = JudgmentPattern(
            applies_when_signals=["TRx_drop"],
            scope=Scope(geography=["US"]),
            decay=DecayConfig(valid_for_days=180),
        )
        fresh.created_at = datetime.utcnow()

        stale = JudgmentPattern(
            applies_when_signals=["TRx_drop"],
            scope=Scope(geography=["US"]),
            decay=DecayConfig(valid_for_days=180),
        )
        stale.created_at = datetime.utcnow() - timedelta(days=150)

        fresh_score = fresh.match_score(["TRx_drop"], {"geography": "US"})
        stale_score = stale.match_score(["TRx_drop"], {"geography": "US"})
        assert fresh_score > stale_score

    def test_match_score_empty_signals(self):
        """Empty input signals should return 0.0."""
        pattern = JudgmentPattern(
            applies_when_signals=["TRx_drop"],
            scope=Scope(geography=["US"]),
        )
        assert pattern.match_score([], {"geography": "US"}) == 0.0

    def test_match_score_no_pattern_signals(self):
        """Pattern with no signals defined should return 0.0."""
        pattern = JudgmentPattern(
            applies_when_signals=[],
            scope=Scope(geography=["US"]),
        )
        assert pattern.match_score(["TRx_drop"], {"geography": "US"}) == 0.0


# =============================================================================
# GUARDRAIL TESTS
# =============================================================================

class TestGuardrail:
    """Tests for Guardrail enforcement."""
    
    def test_guardrail_creation(self):
        """Guardrail should be normative and restricted by default."""
        guardrail = Guardrail(
            blocks_action_types=["price_recommendation"]
        )
        
        assert guardrail.judgment_type == JudgmentType.NORMATIVE
        assert guardrail.governance.risk_class == RiskClass.RESTRICTED
    
    def test_guardrail_violation_detected(self):
        """Guardrail should detect violations."""
        guardrail = Guardrail(
            blocks_action_types=["price_recommendation"],
            applies_to_personas=["brand_manager"]
        )
        
        is_violated = guardrail.is_violated(
            action_type="price_recommendation",
            evidence=[],
            persona="brand_manager"
        )
        
        assert is_violated is True
    
    def test_guardrail_not_violated_with_evidence(self):
        """Guardrail should allow if required evidence is present."""
        guardrail = Guardrail(
            blocks_action_types=["price_recommendation"],
            unless_evidence=["finance_approval", "legal_review"]
        )
        
        is_violated = guardrail.is_violated(
            action_type="price_recommendation",
            evidence=["finance_approval", "legal_review", "other"],
            persona="brand_manager"
        )
        
        assert is_violated is False
    
    def test_guardrail_not_violated_excluded_persona(self):
        """Guardrail should not apply to excluded personas."""
        guardrail = Guardrail(
            blocks_action_types=["price_recommendation"],
            excludes_personas=["pricing_committee"]
        )
        
        is_violated = guardrail.is_violated(
            action_type="price_recommendation",
            evidence=[],
            persona="pricing_committee"
        )
        
        assert is_violated is False

    def test_evaluate_drivers_no_hit(self):
        """No overlap between proposed drivers and blocks_drivers."""
        guardrail = Guardrail(
            blocks_drivers=["Price_Erosion"],
            unless_evidence=["finance_approval"],
        )
        result = guardrail.evaluate_drivers(
            proposed_drivers=["Access_Friction", "Competitive_Pressure"],
            available_evidence=[],
        )
        assert result.is_blocked is False
        assert result.blocked_drivers == []

    def test_evaluate_drivers_blocked(self):
        """Driver in blocks_drivers with no escape evidence should block."""
        guardrail = Guardrail(
            blocks_drivers=["Price_Erosion", "Off_Label_Use"],
            unless_evidence=["finance_approval"],
        )
        result = guardrail.evaluate_drivers(
            proposed_drivers=["Price_Erosion", "Access_Friction"],
            available_evidence=[],
        )
        assert result.is_blocked is True
        assert "Price_Erosion" in result.blocked_drivers
        assert "Access_Friction" not in result.blocked_drivers
        assert result.escape_conditions_unmet == ["finance_approval"]

    def test_evaluate_drivers_unblocked_by_evidence(self):
        """Blocked driver should be unblocked when all escape evidence present."""
        guardrail = Guardrail(
            blocks_drivers=["Price_Erosion"],
            unless_evidence=["finance_approval", "legal_review"],
        )
        result = guardrail.evaluate_drivers(
            proposed_drivers=["Price_Erosion"],
            available_evidence=["finance_approval", "legal_review"],
        )
        assert result.is_blocked is False
        assert result.blocked_drivers == ["Price_Erosion"]
        assert result.escape_conditions_met == ["finance_approval", "legal_review"]
        assert result.escape_conditions_unmet == []

    def test_evaluate_drivers_partial_evidence(self):
        """Partial escape evidence should still block."""
        guardrail = Guardrail(
            blocks_drivers=["Price_Erosion"],
            unless_evidence=["finance_approval", "legal_review"],
        )
        result = guardrail.evaluate_drivers(
            proposed_drivers=["Price_Erosion"],
            available_evidence=["finance_approval"],
        )
        assert result.is_blocked is True
        assert result.escape_conditions_met == ["finance_approval"]
        assert result.escape_conditions_unmet == ["legal_review"]

    def test_evaluate_drivers_no_blocks_drivers(self):
        """Guardrail with empty blocks_drivers should never block drivers."""
        guardrail = Guardrail(
            blocks_action_types=["price_recommendation"],
            blocks_drivers=[],
        )
        result = guardrail.evaluate_drivers(
            proposed_drivers=["Price_Erosion"],
            available_evidence=[],
        )
        assert result.is_blocked is False


# =============================================================================
# GUARDRAIL STORE TESTS (blocks_drivers)
# =============================================================================

class TestGuardrailDriverStore:
    """Tests for JudgmentStore.check_driver_guardrails()."""

    def test_check_driver_guardrails_blocked(self):
        """Active guardrail blocking a driver should appear in results."""
        store = JudgmentStore()
        g = Guardrail(
            blocks_drivers=["Price_Erosion"],
            unless_evidence=["finance_approval"],
        )
        store.add_guardrail(g)
        store.approve_guardrail(g.id, "compliance")

        results = store.check_driver_guardrails(
            drivers=["Price_Erosion"],
            evidence=[],
        )
        assert len(results) == 1
        assert results[0].is_blocked is True
        assert results[0].guardrail_id == g.id

    def test_check_driver_guardrails_inactive_ignored(self):
        """Draft guardrails should be ignored."""
        store = JudgmentStore()
        g = Guardrail(blocks_drivers=["Price_Erosion"])
        store.add_guardrail(g)  # stays DRAFT

        results = store.check_driver_guardrails(
            drivers=["Price_Erosion"],
            evidence=[],
        )
        assert len(results) == 0

    def test_check_driver_guardrails_multiple(self):
        """Multiple active guardrails can each contribute results."""
        store = JudgmentStore()
        g1 = Guardrail(blocks_drivers=["Price_Erosion"])
        g2 = Guardrail(blocks_drivers=["Off_Label_Use"])
        store.add_guardrail(g1)
        store.approve_guardrail(g1.id, "compliance")
        store.add_guardrail(g2)
        store.approve_guardrail(g2.id, "compliance")

        results = store.check_driver_guardrails(
            drivers=["Price_Erosion", "Off_Label_Use"],
            evidence=[],
        )
        assert len(results) == 2


# =============================================================================
# TRAVERSAL POLICY TESTS
# =============================================================================

class TestTraversalPolicy:
    """Tests for bounded agent traversal."""
    
    def test_hard_stop_low_confidence(self):
        """Should halt when confidence is too low."""
        policy = TraversalPolicy(min_confidence=0.55)
        
        result = policy.check_hard_stops(
            confidence=0.4,
            evidence_count=5,
            required_evidence=3,
            conflicting_ratio=0.1,
            guardrail_violations=[]
        )
        
        assert result.triggered is True
        assert "Confidence" in result.reason
        assert result.action == "halt"
    
    def test_hard_stop_missing_evidence(self):
        """Should halt when evidence is insufficient."""
        policy = TraversalPolicy()
        
        result = policy.check_hard_stops(
            confidence=0.8,
            evidence_count=1,
            required_evidence=3,
            conflicting_ratio=0.1,
            guardrail_violations=[]
        )
        
        assert result.triggered is True
        assert "evidence" in result.reason.lower()
    
    def test_hard_stop_conflicting_drivers(self):
        """Should halt when driver conflict is too high."""
        policy = TraversalPolicy(max_conflicting_driver_ratio=0.4)
        
        result = policy.check_hard_stops(
            confidence=0.8,
            evidence_count=5,
            required_evidence=3,
            conflicting_ratio=0.6,
            guardrail_violations=[]
        )
        
        assert result.triggered is True
        assert "Conflicting" in result.reason
    
    def test_hard_stop_guardrail_violation(self):
        """Should halt and escalate on guardrail violation."""
        policy = TraversalPolicy()
        
        result = policy.check_hard_stops(
            confidence=0.8,
            evidence_count=5,
            required_evidence=3,
            conflicting_ratio=0.1,
            guardrail_violations=["GR_NO_PRICE_SPECULATION"]
        )
        
        assert result.triggered is True
        assert result.action == "halt_and_escalate"
    
    def test_no_hard_stop_when_all_good(self):
        """Should continue when all checks pass."""
        policy = TraversalPolicy()
        
        result = policy.check_hard_stops(
            confidence=0.8,
            evidence_count=5,
            required_evidence=3,
            conflicting_ratio=0.1,
            guardrail_violations=[]
        )
        
        assert result.triggered is False
        assert result.action == "continue"


# =============================================================================
# DELTA STORE TESTS
# =============================================================================

class TestDeltaStore:
    """Tests for delta persistence and review workflow."""
    
    def test_propose_delta(self):
        """Should add delta to store."""
        store = DeltaStore()
        delta = Delta(type=DeltaType.PROPOSED_EDGE)
        
        result = store.propose(delta)
        
        assert result.id in [d.id for d in store.get_pending_review()]
    
    def test_auto_approve_level1(self):
        """Level 1 deltas should auto-approve."""
        store = DeltaStore()
        delta = Delta(
            type=DeltaType.PROPOSED_SYNONYM,
            blast_radius=BlastRadius.LOW,
            confidence=0.95
        )
        
        result = store.propose(delta)
        
        assert result.status == DeltaStatus.APPROVED
        assert result.reviewed_by == "system_auto"
    
    def test_approve_delta(self):
        """Should approve pending delta."""
        store = DeltaStore()
        delta = Delta(type=DeltaType.PROPOSED_PATTERN)
        store.propose(delta)
        
        result = store.approve(delta.id, "alice")
        
        assert result.status == DeltaStatus.APPROVED
        assert delta.id not in [d.id for d in store.get_pending_review()]
    
    def test_reject_delta(self):
        """Should reject pending delta with reason."""
        store = DeltaStore()
        delta = Delta(type=DeltaType.PROPOSED_GUARDRAIL)
        store.propose(delta)
        
        result = store.reject(delta.id, "bob", "Not needed")
        
        assert result.status == DeltaStatus.REJECTED
        assert result.rejection_reason == "Not needed"
    
    def test_pending_sorted_by_blast_radius(self):
        """Pending review should be sorted by blast radius."""
        store = DeltaStore()
        
        low = Delta(type=DeltaType.PROPOSED_EDGE, blast_radius=BlastRadius.LOW)
        high = Delta(type=DeltaType.PROPOSED_EDGE, blast_radius=BlastRadius.HIGH)
        medium = Delta(type=DeltaType.PROPOSED_EDGE, blast_radius=BlastRadius.MEDIUM)
        
        store.propose(low)
        store.propose(high)
        store.propose(medium)
        
        pending = store.get_pending_review()
        
        assert pending[0].blast_radius == BlastRadius.HIGH
        assert pending[1].blast_radius == BlastRadius.MEDIUM
        assert pending[2].blast_radius == BlastRadius.LOW
    
    def test_stats(self):
        """Should return accurate stats."""
        store = DeltaStore()
        store.propose(Delta(type=DeltaType.PROPOSED_EDGE))
        store.propose(Delta(type=DeltaType.PROPOSED_EDGE))
        
        stats = store.stats()
        
        assert stats["total"] == 2
        assert stats["proposed"] == 2


# =============================================================================
# CLASSIFICATION TESTS (CTX-005)
# =============================================================================

class TestClassification:
    """Tests for classify_delta() and get_required_approver()."""

    def test_classify_synonym_as_empirical(self):
        """PROPOSED_SYNONYM should always classify as EMPIRICAL."""
        delta = Delta(type=DeltaType.PROPOSED_SYNONYM, content={"source": "a", "target": "b"})
        from src.core.stores import classify_delta
        assert classify_delta(delta) == JudgmentType.EMPIRICAL

    def test_classify_mapping_as_empirical(self):
        """PROPOSED_MAPPING should always classify as EMPIRICAL."""
        delta = Delta(type=DeltaType.PROPOSED_MAPPING, content={"source": "a", "target": "b"})
        from src.core.stores import classify_delta
        assert classify_delta(delta) == JudgmentType.EMPIRICAL

    def test_classify_pattern_as_causal(self):
        """PROPOSED_PATTERN should classify as CAUSAL_HYPOTHESIS."""
        delta = Delta(type=DeltaType.PROPOSED_PATTERN, content={"name": "test"})
        from src.core.stores import classify_delta
        assert classify_delta(delta) == JudgmentType.CAUSAL_HYPOTHESIS

    def test_classify_action_as_normative(self):
        """PROPOSED_ACTION should classify as NORMATIVE."""
        delta = Delta(type=DeltaType.PROPOSED_ACTION, content={"action": "test"})
        from src.core.stores import classify_delta
        assert classify_delta(delta) == JudgmentType.NORMATIVE

    def test_classify_edge_by_blast_radius(self):
        """PROPOSED_EDGE classification depends on blast_radius."""
        from src.core.stores import classify_delta
        low = Delta(type=DeltaType.PROPOSED_EDGE, blast_radius=BlastRadius.LOW)
        med = Delta(type=DeltaType.PROPOSED_EDGE, blast_radius=BlastRadius.MEDIUM)
        high = Delta(type=DeltaType.PROPOSED_EDGE, blast_radius=BlastRadius.HIGH)
        assert classify_delta(low) == JudgmentType.EMPIRICAL
        assert classify_delta(med) == JudgmentType.CAUSAL_HYPOTHESIS
        assert classify_delta(high) == JudgmentType.NORMATIVE

    def test_classify_entity_by_blast_radius(self):
        """PROPOSED_ENTITY classification depends on blast_radius."""
        from src.core.stores import classify_delta
        low = Delta(type=DeltaType.PROPOSED_ENTITY, blast_radius=BlastRadius.LOW)
        high = Delta(type=DeltaType.PROPOSED_ENTITY, blast_radius=BlastRadius.HIGH)
        assert classify_delta(low) == JudgmentType.EMPIRICAL
        assert classify_delta(high) == JudgmentType.NORMATIVE

    def test_propose_auto_classifies(self):
        """DeltaStore.propose() should auto-set judgment_type."""
        store = DeltaStore()
        delta = Delta(type=DeltaType.PROPOSED_ACTION, content={"action": "test"})
        result = store.propose(delta)
        assert result.judgment_type == JudgmentType.NORMATIVE

    def test_get_required_approver_empirical(self):
        """EMPIRICAL deltas should route to system_auto."""
        from src.core.stores import get_required_approver
        delta = Delta(type=DeltaType.PROPOSED_SYNONYM, judgment_type=JudgmentType.EMPIRICAL)
        assert get_required_approver(delta) == "system_auto"

    def test_get_required_approver_causal(self):
        """CAUSAL_HYPOTHESIS deltas should route to domain_expert."""
        from src.core.stores import get_required_approver
        delta = Delta(type=DeltaType.PROPOSED_PATTERN, judgment_type=JudgmentType.CAUSAL_HYPOTHESIS)
        assert get_required_approver(delta) == "domain_expert"

    def test_get_required_approver_normative(self):
        """NORMATIVE deltas should route to governance_board."""
        from src.core.stores import get_required_approver
        delta = Delta(type=DeltaType.PROPOSED_ACTION, judgment_type=JudgmentType.NORMATIVE)
        assert get_required_approver(delta) == "governance_board"


# =============================================================================
# CONFLICT DETECTION TESTS (US-025)
# =============================================================================

class TestConflictDetection:
    """Tests for DeltaStore.find_conflicts() — US-025."""

    def test_canonical_id_collision(self):
        """Two synonym deltas targeting same canonical_id should conflict."""
        store = DeltaStore()
        d1 = Delta(
            type=DeltaType.PROPOSED_SYNONYM,
            content={"canonical_id": "TERM_001", "alias": "PA"},
        )
        d2 = Delta(
            type=DeltaType.PROPOSED_SYNONYM,
            content={"canonical_id": "TERM_001", "alias": "Prior Auth"},
        )
        store.propose(d1)
        store.propose(d2)

        conflicts = store.find_conflicts(d1)
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "canonical_id_collision"
        assert conflicts[0].severity == "blocker"
        assert conflicts[0].delta_id == d2.id

    def test_scope_overlap_pattern_deltas(self):
        """Pattern deltas with overlapping signals should conflict."""
        store = DeltaStore()
        d1 = Delta(
            type=DeltaType.PROPOSED_PATTERN,
            content={"applies_when_signals": ["TRx_drop", "PA_edit"]},
        )
        d2 = Delta(
            type=DeltaType.PROPOSED_PATTERN,
            content={"applies_when_signals": ["TRx_drop", "NBRx_decline"]},
        )
        store.propose(d1)
        store.propose(d2)

        conflicts = store.find_conflicts(d1)
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "scope_overlap"
        assert "TRx_drop" in conflicts[0].description

    def test_edge_contradiction_different_relationship(self):
        """Same source+target with different relationships should be blocker."""
        store = DeltaStore()
        d1 = Delta(
            type=DeltaType.PROPOSED_EDGE,
            content={"source": "A", "target": "B", "relationship": "causes"},
        )
        d2 = Delta(
            type=DeltaType.PROPOSED_EDGE,
            content={"source": "A", "target": "B", "relationship": "correlates"},
        )
        store.propose(d1)
        store.propose(d2)

        conflicts = store.find_conflicts(d1)
        assert len(conflicts) == 1
        assert conflicts[0].conflict_type == "edge_contradiction"
        assert conflicts[0].severity == "blocker"

    def test_edge_duplicate_warning(self):
        """Same source+target+relationship should be warning (duplicate)."""
        store = DeltaStore()
        d1 = Delta(
            type=DeltaType.PROPOSED_EDGE,
            content={"source": "A", "target": "B", "relationship": "causes"},
        )
        d2 = Delta(
            type=DeltaType.PROPOSED_EDGE,
            content={"source": "A", "target": "B", "relationship": "causes"},
        )
        store.propose(d1)
        store.propose(d2)

        conflicts = store.find_conflicts(d1)
        assert len(conflicts) == 1
        assert conflicts[0].severity == "warning"

    def test_no_conflict_different_types(self):
        """Deltas of different types should not conflict."""
        store = DeltaStore()
        d1 = Delta(
            type=DeltaType.PROPOSED_EDGE,
            content={"source": "A", "target": "B"},
        )
        d2 = Delta(
            type=DeltaType.PROPOSED_PATTERN,
            content={"applies_when_signals": ["TRx_drop"]},
        )
        store.propose(d1)
        store.propose(d2)

        assert store.find_conflicts(d1) == []

    def test_rejected_deltas_ignored(self):
        """Rejected deltas should not appear as conflicts."""
        store = DeltaStore()
        d1 = Delta(
            type=DeltaType.PROPOSED_SYNONYM,
            content={"canonical_id": "TERM_001"},
        )
        d2 = Delta(
            type=DeltaType.PROPOSED_SYNONYM,
            content={"canonical_id": "TERM_001"},
        )
        store.propose(d1)
        store.propose(d2)
        store.reject(d2.id, "bob", "stale")

        assert store.find_conflicts(d1) == []

    def test_no_conflict_disjoint_signals(self):
        """Pattern deltas with no signal overlap should not conflict."""
        store = DeltaStore()
        d1 = Delta(
            type=DeltaType.PROPOSED_PATTERN,
            content={"applies_when_signals": ["TRx_drop"]},
        )
        d2 = Delta(
            type=DeltaType.PROPOSED_PATTERN,
            content={"applies_when_signals": ["NBRx_decline"]},
        )
        store.propose(d1)
        store.propose(d2)

        assert store.find_conflicts(d1) == []


# =============================================================================
# JUDGMENT STORE TESTS
# =============================================================================

class TestJudgmentStore:
    """Tests for judgment artifact persistence."""
    
    def test_add_pattern_as_draft(self):
        """Patterns should start as draft."""
        store = JudgmentStore()
        pattern = JudgmentPattern(applies_when_signals=["TRx_drop"])
        
        result = store.add_pattern(pattern)
        
        assert result.status == ArtifactStatus.DRAFT
    
    def test_approve_pattern(self):
        """Should approve pattern."""
        store = JudgmentStore()
        pattern = store.add_pattern(JudgmentPattern())
        
        result = store.approve_pattern(pattern.id, "alice")
        
        assert result.status == ArtifactStatus.APPROVED
        assert result.governance.approver == "alice"
    
    def test_get_active_patterns(self):
        """Should only return approved, non-stale patterns."""
        store = JudgmentStore()
        
        # Draft pattern
        store.add_pattern(JudgmentPattern())
        
        # Approved pattern
        approved = store.add_pattern(JudgmentPattern())
        store.approve_pattern(approved.id, "alice")
        
        active = store.get_active_patterns()
        
        assert len(active) == 1
        assert active[0].id == approved.id
    
    def test_find_matching_patterns_ranked(self):
        """Patterns should be returned ranked by match_score."""
        store = JudgmentStore()

        # High-match pattern: all signals match
        high = JudgmentPattern(
            applies_when_signals=["TRx_drop"],
            scope=Scope(geography=["US"]),
            judgment_type=JudgmentType.EMPIRICAL,
        )
        store.add_pattern(high)
        store.approve_pattern(high.id, "alice")

        # Lower-match pattern: partial signal overlap
        low = JudgmentPattern(
            applies_when_signals=["TRx_drop", "PA_edit", "NBRx_decline"],
            scope=Scope(geography=["US"]),
            judgment_type=JudgmentType.NORMATIVE,
        )
        store.add_pattern(low)
        store.approve_pattern(low.id, "alice")

        results = store.find_matching_patterns(
            signals=["TRx_drop"],
            context={"geography": "US"},
        )

        assert len(results) >= 2
        # First result should have higher score
        assert results[0][1] >= results[1][1]
        assert results[0][0].id == high.id

    def test_find_matching_patterns_min_score_filter(self):
        """Patterns below min_score should be excluded."""
        store = JudgmentStore()
        pattern = JudgmentPattern(
            applies_when_signals=["TRx_drop", "PA_edit", "NBRx_decline"],
            scope=Scope(geography=["US"]),
        )
        store.add_pattern(pattern)
        store.approve_pattern(pattern.id, "alice")

        # High min_score should filter out partial matches
        results = store.find_matching_patterns(
            signals=["TRx_drop"],
            context={"geography": "US"},
            min_score=0.95,
        )
        assert len(results) == 0

    def test_check_guardrail_violations(self):
        """Should find violating guardrails."""
        store = JudgmentStore()
        
        guardrail = Guardrail(
            blocks_action_types=["price_recommendation"],
            applies_to_personas=["brand_manager"]
        )
        store.add_guardrail(guardrail)
        store.approve_guardrail(guardrail.id, "compliance")
        
        violations = store.check_violations(
            action_type="price_recommendation",
            evidence=[],
            persona="brand_manager"
        )
        
        assert len(violations) == 1


# =============================================================================
# PROMOTION PIPELINE TESTS
# =============================================================================

class TestPromotionPipeline:
    """Tests for delta promotion to graph."""
    
    def test_promote_pattern_delta(self):
        """Should promote approved pattern delta to judgment store."""
        delta_store = DeltaStore()
        judgment_store = JudgmentStore()
        pipeline = PromotionPipeline(delta_store, judgment_store)
        
        # Create and approve a pattern delta
        delta = Delta(
            type=DeltaType.PROPOSED_PATTERN,
            content={
                "applies_when_signals": ["TRx_drop", "PA_edit"],
                "typical_drivers": [
                    {"driver": "Access_Friction", "prior_confidence": 0.7}
                ],
                "trained_from_scenarios": ["S001", "S002"]
            }
        )
        delta_store.propose(delta)
        delta_store.approve(delta.id, "alice")
        
        # Promote
        result = pipeline.promote_all_approved()
        
        assert result.get("proposed_pattern", 0) == 1
        assert len(judgment_store.get_active_patterns()) == 1
        
        # Delta should be marked merged
        assert delta_store.get(delta.id).status == DeltaStatus.MERGED


# =============================================================================
# HITL ROUTING TESTS (CTX-006)
# =============================================================================

class TestHITLRouting:
    """Tests for route_delta(), queue filtering, escalation, and stats."""

    def test_route_empirical_low_auto(self):
        """EMPIRICAL+LOW should auto-route with 0h SLA."""
        from src.core.stores import route_delta
        delta = Delta(
            type=DeltaType.PROPOSED_SYNONYM,
            blast_radius=BlastRadius.LOW,
            judgment_type=JudgmentType.EMPIRICAL,
        )
        decision = route_delta(delta)
        assert decision.queue == "auto"
        assert decision.assigned_to == "system_auto"
        assert decision.priority == "low"
        assert decision.sla_hours == 0

    def test_route_empirical_high_standard(self):
        """EMPIRICAL+HIGH should route to domain_expert/standard/high/24h."""
        from src.core.stores import route_delta
        delta = Delta(
            type=DeltaType.PROPOSED_SYNONYM,
            blast_radius=BlastRadius.HIGH,
            judgment_type=JudgmentType.EMPIRICAL,
        )
        decision = route_delta(delta)
        assert decision.queue == "standard"
        assert decision.assigned_to == "domain_expert"
        assert decision.priority == "high"
        assert decision.sla_hours == 24

    def test_route_causal_medium_standard(self):
        """CAUSAL+MEDIUM should route to domain_expert/standard/high/24h."""
        from src.core.stores import route_delta
        delta = Delta(
            type=DeltaType.PROPOSED_PATTERN,
            blast_radius=BlastRadius.MEDIUM,
            judgment_type=JudgmentType.CAUSAL_HYPOTHESIS,
        )
        decision = route_delta(delta)
        assert decision.queue == "standard"
        assert decision.assigned_to == "domain_expert"
        assert decision.priority == "high"
        assert decision.sla_hours == 24

    def test_route_normative_high_escalated(self):
        """NORMATIVE+HIGH should escalate to governance_board/critical/5h."""
        from src.core.stores import route_delta
        delta = Delta(
            type=DeltaType.PROPOSED_ACTION,
            blast_radius=BlastRadius.HIGH,
            judgment_type=JudgmentType.NORMATIVE,
        )
        decision = route_delta(delta)
        assert decision.queue == "escalated"
        assert decision.assigned_to == "governance_board"
        assert decision.priority == "critical"
        assert decision.sla_hours == 5

    def test_propose_auto_routes(self):
        """DeltaStore.propose() should set assigned_to from routing."""
        store = DeltaStore()
        delta = Delta(
            type=DeltaType.PROPOSED_ACTION,
            content={"action": "test"},
            blast_radius=BlastRadius.HIGH,
        )
        result = store.propose(delta)
        assert result.assigned_to == "governance_board"

    def test_get_pending_for_role(self):
        """get_pending_for_role() should filter by assigned role."""
        store = DeltaStore()
        # NORMATIVE+HIGH → governance_board
        d1 = Delta(
            type=DeltaType.PROPOSED_ACTION,
            content={"action": "a"},
            blast_radius=BlastRadius.HIGH,
        )
        # PROPOSED_EDGE+MEDIUM → CAUSAL → domain_expert
        d2 = Delta(
            type=DeltaType.PROPOSED_EDGE,
            content={"source": "A", "target": "B"},
            blast_radius=BlastRadius.MEDIUM,
        )
        store.propose(d1)
        store.propose(d2)

        gov = store.get_pending_for_role("governance_board")
        expert = store.get_pending_for_role("domain_expert")
        assert len(gov) == 1
        assert gov[0].id == d1.id
        assert len(expert) == 1
        assert expert[0].id == d2.id

    def test_escalate_delta(self):
        """escalate() should move delta to next review level."""
        store = DeltaStore()
        delta = Delta(
            type=DeltaType.PROPOSED_EDGE,
            content={"source": "A", "target": "B"},
            blast_radius=BlastRadius.MEDIUM,
        )
        store.propose(delta)
        assert delta.assigned_to == "domain_expert"

        result = store.escalate(delta.id, "needs higher review")
        assert result is not None
        assert result.assigned_to == "governance_board"

    def test_escalate_nonexistent_returns_none(self):
        """escalate() on missing delta should return None."""
        store = DeltaStore()
        assert store.escalate("nonexistent_id", "reason") is None

    def test_escalate_top_level_returns_none(self):
        """escalate() from governance_board (top) should return None."""
        store = DeltaStore()
        delta = Delta(
            type=DeltaType.PROPOSED_ACTION,
            content={"action": "a"},
            blast_radius=BlastRadius.HIGH,
        )
        store.propose(delta)
        assert delta.assigned_to == "governance_board"
        assert store.escalate(delta.id, "already top") is None

    def test_get_queue_stats(self):
        """get_queue_stats() should count pending per queue."""
        store = DeltaStore()
        # EMPIRICAL+LOW → auto (but auto-approved, so not pending)
        store.propose(Delta(
            type=DeltaType.PROPOSED_SYNONYM,
            blast_radius=BlastRadius.LOW,
            confidence=0.95,
        ))
        # CAUSAL+MEDIUM → standard
        store.propose(Delta(
            type=DeltaType.PROPOSED_EDGE,
            content={"source": "A", "target": "B"},
            blast_radius=BlastRadius.MEDIUM,
        ))
        # NORMATIVE+HIGH → escalated
        store.propose(Delta(
            type=DeltaType.PROPOSED_ACTION,
            content={"action": "a"},
            blast_radius=BlastRadius.HIGH,
        ))

        stats = store.get_queue_stats()
        assert stats["standard"] >= 1
        assert stats["escalated"] >= 1


# =============================================================================
# CONTRIBUTION TRACKING TESTS (CTX-018)
# =============================================================================

class TestContributionStore:
    """Tests for ContributionStore — SME contribution tracking."""

    def _make_event(self, sme_id="sme_001", sme_persona="commercial_lead",
                    ta="oncology", scenario_type="regional_dip", confidence=0.7):
        """Create a minimal ReasoningEvent for testing."""
        from src.core.reasoning_event import (
            ReasoningEvent, ScenarioContext, BrandProfile,
            TherapeuticArea, BrandLifecycle, AssetClass,
            ChannelType, MarketArchetype,
        )
        ta_enum = TherapeuticArea(ta) if ta in [e.value for e in TherapeuticArea] else TherapeuticArea.OTHER
        brand = BrandProfile(
            brand_name="TestBrand",
            therapeutic_area=ta_enum,
            lifecycle=BrandLifecycle.GROWTH,
            asset_class=AssetClass.SMALL_MOLECULE,
            channel=ChannelType.SPECIALTY,
            market_archetype=MarketArchetype.FRAGMENTED,
        )
        scenario = ScenarioContext(brand=brand)
        return ReasoningEvent(
            sme_id=sme_id,
            sme_persona=sme_persona,
            scenario=scenario,
            scenario_type=scenario_type,
            sme_confidence=confidence,
        )

    def test_record_contribution(self):
        """record() should create a Contribution from a ReasoningEvent."""
        from src.core.stores import ContributionStore
        store = ContributionStore()
        event = self._make_event()
        delta_ids = ["d1", "d2", "d3"]

        result = store.record(event, delta_ids)

        assert result.reasoning_event_id == event.id
        assert result.sme_id == "sme_001"
        assert result.sme_persona == "commercial_lead"
        assert result.delta_ids == ["d1", "d2", "d3"]
        assert result.therapeutic_area == "oncology"
        assert result.sme_confidence == 0.7

    def test_get_by_sme(self):
        """get_by_sme() should return contributions newest first."""
        from src.core.stores import ContributionStore
        store = ContributionStore()
        e1 = self._make_event(sme_id="sme_A", scenario_type="scenario_1")
        e2 = self._make_event(sme_id="sme_A", scenario_type="scenario_2")
        e3 = self._make_event(sme_id="sme_B", scenario_type="scenario_3")

        store.record(e1, ["d1"])
        store.record(e2, ["d2", "d3"])
        store.record(e3, ["d4"])

        results = store.get_by_sme("sme_A")
        assert len(results) == 2
        # Both should be sme_A
        assert all(c.sme_id == "sme_A" for c in results)

    def test_get_by_sme_empty(self):
        """get_by_sme() for unknown SME should return empty list."""
        from src.core.stores import ContributionStore
        store = ContributionStore()
        assert store.get_by_sme("unknown") == []

    def test_contributor_summary(self):
        """get_contributor_summary() should aggregate stats correctly."""
        from src.core.stores import ContributionStore
        store = ContributionStore()
        e1 = self._make_event(sme_id="sme_X", ta="oncology", confidence=0.8)
        e2 = self._make_event(sme_id="sme_X", ta="immunology", confidence=0.6)

        store.record(e1, ["d1", "d2"])
        store.record(e2, ["d3"])

        summary = store.get_contributor_summary("sme_X")
        assert summary["total_contributions"] == 2
        assert summary["total_deltas"] == 3
        assert summary["domains"]["oncology"] == 1
        assert summary["domains"]["immunology"] == 1
        assert summary["avg_confidence"] == 0.7
        assert summary["last_contributed"] is not None

    def test_contributor_summary_unknown(self):
        """get_contributor_summary() for unknown SME returns zeroed stats."""
        from src.core.stores import ContributionStore
        store = ContributionStore()
        summary = store.get_contributor_summary("nobody")
        assert summary["total_contributions"] == 0
        assert summary["total_deltas"] == 0
        assert summary["avg_confidence"] == 0.0

    def test_top_contributors(self):
        """get_top_contributors() should rank by total deltas."""
        from src.core.stores import ContributionStore
        store = ContributionStore()
        # sme_A: 5 deltas across 2 sessions
        store.record(self._make_event(sme_id="sme_A"), ["d1", "d2", "d3"])
        store.record(self._make_event(sme_id="sme_A"), ["d4", "d5"])
        # sme_B: 1 delta
        store.record(self._make_event(sme_id="sme_B"), ["d6"])

        top = store.get_top_contributors(limit=10)
        assert len(top) == 2
        assert top[0]["sme_id"] == "sme_A"
        assert top[0]["total_deltas"] == 5
        assert top[1]["sme_id"] == "sme_B"
        assert top[1]["total_deltas"] == 1

    def test_stats(self):
        """stats() should return store-level totals."""
        from src.core.stores import ContributionStore
        store = ContributionStore()
        store.record(self._make_event(sme_id="sme_A"), ["d1", "d2"])
        store.record(self._make_event(sme_id="sme_B"), ["d3"])

        s = store.stats()
        assert s["total_contributions"] == 2
        assert s["unique_smes"] == 2
        assert s["total_deltas"] == 3

    def test_process_sme_session_records_contribution(self):
        """process_sme_session() with store should record contribution."""
        from src.core.stores import ContributionStore
        from src.core.delta_generator import process_sme_session
        from src.core.reasoning_event import (
            ReasoningEvent, ScenarioContext, BrandProfile,
            TherapeuticArea, BrandLifecycle, AssetClass,
            ChannelType, MarketArchetype, HypothesisRanking,
            HypothesisCategory, SignalPriority,
        )
        brand = BrandProfile(
            brand_name="OncoVance",
            therapeutic_area=TherapeuticArea.ONCOLOGY,
            lifecycle=BrandLifecycle.GROWTH,
            asset_class=AssetClass.SMALL_MOLECULE,
            channel=ChannelType.SPECIALTY,
            market_archetype=MarketArchetype.FRAGMENTED,
        )
        event = ReasoningEvent(
            sme_id="sme_test",
            sme_persona="access_strategist",
            scenario=ScenarioContext(brand=brand),
            scenario_type="regional_performance_dip",
            sme_confidence=0.75,
            primary_hypothesis=HypothesisRanking(
                category=HypothesisCategory.MARKET_ACCESS,
                confidence=0.75,
            ),
            signal_priorities=[
                SignalPriority(signal_name="TRx_drop", priority_rank=1, role="validation"),
            ],
        )

        contrib_store = ContributionStore()
        deltas = process_sme_session(event, contribution_store=contrib_store)

        assert len(deltas) > 0
        contribs = contrib_store.get_by_sme("sme_test")
        assert len(contribs) == 1
        assert contribs[0].delta_ids == [d.id for d in deltas]
        assert contribs[0].therapeutic_area == "oncology"


# =============================================================================
# ENHANCED AUDIT TRAIL TESTS (CTX-008)
# =============================================================================

class TestEnhancedAuditTrail:
    """Tests for enhanced AuditEntry fields and unified audit query."""

    def test_audit_entry_store_type(self):
        """DeltaStore entries should have store_type='delta'."""
        store = DeltaStore()
        store.propose(Delta(type=DeltaType.PROPOSED_EDGE))
        entries = store.get_audit_log()
        assert len(entries) >= 1
        assert entries[-1].store_type == "delta"

    def test_audit_entry_actor_on_approve(self):
        """Approve should capture reviewer as actor."""
        store = DeltaStore()
        delta = Delta(type=DeltaType.PROPOSED_PATTERN)
        store.propose(delta)
        store.approve(delta.id, "alice")
        entries = store.get_audit_log(action="approve")
        assert len(entries) == 1
        assert entries[0].actor == "alice"

    def test_audit_entry_action_category(self):
        """Entries should have correct action_category."""
        store = DeltaStore()
        delta = Delta(type=DeltaType.PROPOSED_EDGE)
        store.propose(delta)
        store.approve(delta.id, "bob")
        entries = store.get_audit_log()
        categories = [e.action_category for e in entries]
        assert "create" in categories
        assert "approve" in categories

    def test_audit_before_after_snapshot(self):
        """Approve should capture before=PROPOSED, after=APPROVED."""
        store = DeltaStore()
        delta = Delta(type=DeltaType.PROPOSED_PATTERN)
        store.propose(delta)
        store.approve(delta.id, "carol")
        entries = store.get_audit_log(action="approve")
        assert len(entries) == 1
        assert entries[0].before_snapshot == {"status": "proposed"}
        assert entries[0].after_snapshot == {"status": "approved"}

    def test_audit_reject_snapshot(self):
        """Reject should capture status transition in snapshots."""
        store = DeltaStore()
        delta = Delta(type=DeltaType.PROPOSED_GUARDRAIL)
        store.propose(delta)
        store.reject(delta.id, "dave", "Not needed")
        entries = store.get_audit_log(action="reject")
        assert len(entries) == 1
        assert entries[0].before_snapshot == {"status": "proposed"}
        assert entries[0].after_snapshot == {"status": "rejected"}
        assert entries[0].actor == "dave"

    def test_judgment_store_audit_actor(self):
        """JudgmentStore entries should capture approver as actor."""
        store = JudgmentStore()
        pattern = JudgmentPattern()
        store.add_pattern(pattern)
        store.approve_pattern(pattern.id, "expert_1")
        entries = store.get_audit_log(action="approve_pattern")
        assert len(entries) == 1
        assert entries[0].actor == "expert_1"
        assert entries[0].store_type == "judgment"
        assert entries[0].action_category == "approve"

    def test_contribution_store_audit_sme(self):
        """ContributionStore entries should capture sme_id as actor."""
        from src.core.stores import ContributionStore
        from src.core.reasoning_event import (
            ReasoningEvent, ScenarioContext, BrandProfile,
            TherapeuticArea, BrandLifecycle, AssetClass,
            ChannelType, MarketArchetype,
        )
        brand = BrandProfile(
            brand_name="TestBrand",
            therapeutic_area=TherapeuticArea.ONCOLOGY,
            lifecycle=BrandLifecycle.GROWTH,
            asset_class=AssetClass.SMALL_MOLECULE,
            channel=ChannelType.SPECIALTY,
            market_archetype=MarketArchetype.FRAGMENTED,
        )
        event = ReasoningEvent(
            sme_id="sme_audit_test",
            sme_persona="commercial_lead",
            scenario=ScenarioContext(brand=brand),
            scenario_type="test",
            sme_confidence=0.8,
        )
        store = ContributionStore()
        store.record(event, ["d1", "d2"])
        entries = store.get_audit_log()
        assert len(entries) == 1
        assert entries[0].actor == "sme_audit_test"
        assert entries[0].store_type == "contribution"
        assert entries[0].action_category == "record"

    def test_combined_audit_log(self):
        """get_combined_audit_log merges from multiple stores."""
        from src.core.stores import get_combined_audit_log
        ds = DeltaStore()
        js = JudgmentStore()
        ds.propose(Delta(type=DeltaType.PROPOSED_EDGE))
        pattern = JudgmentPattern()
        js.add_pattern(pattern)
        js.approve_pattern(pattern.id, "approver")

        combined = get_combined_audit_log([ds, js])
        store_types = {e.store_type for e in combined}
        assert "delta" in store_types
        assert "judgment" in store_types
        assert len(combined) >= 3

    def test_combined_audit_log_filter_action(self):
        """get_combined_audit_log filters by action."""
        from src.core.stores import get_combined_audit_log
        ds = DeltaStore()
        delta = Delta(type=DeltaType.PROPOSED_PATTERN)
        ds.propose(delta)
        ds.approve(delta.id, "reviewer")

        filtered = get_combined_audit_log([ds], action="approve")
        assert len(filtered) == 1
        assert filtered[0].action == "approve"

    def test_combined_audit_log_filter_store_type(self):
        """get_combined_audit_log filters by store_type."""
        from src.core.stores import get_combined_audit_log
        ds = DeltaStore()
        js = JudgmentStore()
        ds.propose(Delta(type=DeltaType.PROPOSED_EDGE))
        js.add_pattern(JudgmentPattern())

        delta_only = get_combined_audit_log([ds, js], store_type="delta")
        assert all(e.store_type == "delta" for e in delta_only)
        judgment_only = get_combined_audit_log([ds, js], store_type="judgment")
        assert all(e.store_type == "judgment" for e in judgment_only)

    def test_store_level_action_filter(self):
        """Store-level get_audit_log() filters by action."""
        store = DeltaStore()
        delta = Delta(type=DeltaType.PROPOSED_EDGE)
        store.propose(delta)
        store.approve(delta.id, "test")

        propose_only = store.get_audit_log(action="propose")
        assert len(propose_only) == 1
        assert propose_only[0].action == "propose"


# =============================================================================
# CTX-007: REVIEW CYCLE ENFORCEMENT TESTS
# =============================================================================

class TestReviewCycleEnforcement:
    """Tests for governance review cycle enforcement (CTX-007)."""

    def test_review_cycle_days_mapping(self):
        """Categorical review_cycle converts to correct numeric days."""
        assert Governance(owner="x", review_cycle="monthly").get_review_cycle_days() == 30
        assert Governance(owner="x", review_cycle="quarterly").get_review_cycle_days() == 90
        assert Governance(owner="x", review_cycle="annual").get_review_cycle_days() == 365
        # Unknown defaults to 90
        assert Governance(owner="x", review_cycle="biweekly").get_review_cycle_days() == 90

    def test_is_review_due_not_approved(self):
        """Unapproved artifact is never due for review."""
        gov = Governance(owner="x")
        assert gov.is_review_due() is False

    def test_is_review_due_fresh(self):
        """Recently approved artifact is not due for review."""
        gov = Governance(owner="x", approved_on=datetime.utcnow(), review_cycle="quarterly")
        assert gov.is_review_due() is False

    def test_is_review_due_overdue(self):
        """Artifact past review cycle deadline is due."""
        old = datetime.utcnow() - timedelta(days=100)
        gov = Governance(owner="x", approved_on=old, review_cycle="quarterly")
        assert gov.is_review_due() is True

    def test_days_until_review(self):
        """days_until_review returns correct remaining days."""
        gov_none = Governance(owner="x")
        assert gov_none.days_until_review() is None

        gov_fresh = Governance(owner="x", approved_on=datetime.utcnow(), review_cycle="quarterly")
        assert gov_fresh.days_until_review() == 90

        old = datetime.utcnow() - timedelta(days=100)
        gov_overdue = Governance(owner="x", approved_on=old, review_cycle="quarterly")
        assert gov_overdue.days_until_review() == -10

    def test_get_patterns_due_for_review(self):
        """Store returns overdue patterns."""
        store = JudgmentStore()
        old = datetime.utcnow() - timedelta(days=100)
        fresh = datetime.utcnow()

        p_overdue = JudgmentPattern(
            applies_when_signals=["overdue_signal"],
            governance=Governance(owner="x", approved_on=old, review_cycle="quarterly"),
        )
        p_fresh = JudgmentPattern(
            applies_when_signals=["fresh_signal"],
            governance=Governance(owner="x", approved_on=fresh, review_cycle="quarterly"),
        )
        store.add_pattern(p_overdue)
        store.approve_pattern(p_overdue.id, "tester")
        store.add_pattern(p_fresh)
        store.approve_pattern(p_fresh.id, "tester")

        # Force approved_on timestamps (approve_pattern sets its own)
        p_overdue.governance.approved_on = old
        p_fresh.governance.approved_on = fresh

        due = store.get_patterns_due_for_review()
        assert len(due) == 1
        assert due[0].id == p_overdue.id

    def test_get_guardrails_due_for_review(self):
        """Store returns overdue guardrails."""
        store = JudgmentStore()
        old = datetime.utcnow() - timedelta(days=40)

        g = Guardrail(
            blocks_action_types=["test"],
            governance=Governance(owner="x", approved_on=old, review_cycle="monthly"),
        )
        store.add_guardrail(g)
        store.approve_guardrail(g.id, "tester")
        g.governance.approved_on = old  # Force timestamp

        due = store.get_guardrails_due_for_review()
        assert len(due) == 1
        assert due[0].id == g.id

    def test_get_review_summary(self):
        """Review summary returns correct counts."""
        store = JudgmentStore()
        old = datetime.utcnow() - timedelta(days=100)

        p = JudgmentPattern(
            applies_when_signals=["overdue_signal"],
            governance=Governance(owner="x", approved_on=old, review_cycle="quarterly"),
        )
        store.add_pattern(p)
        store.approve_pattern(p.id, "tester")
        p.governance.approved_on = old

        summary = store.get_review_summary()
        assert summary["patterns_overdue"] == 1
        assert p.id in summary["pattern_ids"]
        assert summary["guardrails_overdue"] == 0
        assert summary["action_templates_overdue"] == 0

    def test_include_upcoming_days(self):
        """include_upcoming_days surfaces patterns that are almost due."""
        store = JudgmentStore()
        almost_due = datetime.utcnow() - timedelta(days=85)  # 5 days left on quarterly

        p = JudgmentPattern(
            applies_when_signals=["almost_due_signal"],
            governance=Governance(owner="x", approved_on=almost_due, review_cycle="quarterly"),
        )
        store.add_pattern(p)
        store.approve_pattern(p.id, "tester")
        p.governance.approved_on = almost_due

        # Not yet overdue (0 upcoming days)
        assert len(store.get_patterns_due_for_review(include_upcoming_days=0)) == 0
        # But within 7-day lookahead
        assert len(store.get_patterns_due_for_review(include_upcoming_days=7)) == 1


# =============================================================================
# CTX-009: PATTERN CONSOLIDATION TESTS
# =============================================================================

class TestPatternConsolidation:
    """Tests for pattern consolidation / reconciler (CTX-009)."""

    def _make_approved_pattern(self, store, signals, context=None, drivers=None):
        """Helper to create and approve a pattern."""
        p = JudgmentPattern(
            applies_when_signals=signals,
            applies_when_context=context or [],
            typical_drivers=drivers or [],
        )
        store.add_pattern(p)
        store.approve_pattern(p.id, "tester")
        return p

    def test_superseded_by_default_none(self):
        """JudgmentPattern.superseded_by should default to None."""
        p = JudgmentPattern()
        assert p.superseded_by is None

    def test_compute_similarity_full_overlap(self):
        """Identical signals should yield similarity 1.0."""
        store = JudgmentStore()
        a = self._make_approved_pattern(store, ["sig_a", "sig_b"])
        b = self._make_approved_pattern(store, ["sig_a", "sig_b"])
        assert store.compute_pattern_similarity(a.id, b.id) == 1.0

    def test_compute_similarity_no_overlap(self):
        """Disjoint signals should yield similarity 0.0."""
        store = JudgmentStore()
        a = self._make_approved_pattern(store, ["sig_a"])
        b = self._make_approved_pattern(store, ["sig_x"])
        assert store.compute_pattern_similarity(a.id, b.id) == 0.0

    def test_compute_similarity_partial(self):
        """Partial overlap should yield correct Jaccard coefficient."""
        store = JudgmentStore()
        a = self._make_approved_pattern(store, ["sig_a", "sig_b", "sig_c"])
        b = self._make_approved_pattern(store, ["sig_b", "sig_c", "sig_d"])
        # Intersection={b,c}=2, Union={a,b,c,d}=4 → 0.5
        assert store.compute_pattern_similarity(a.id, b.id) == pytest.approx(0.5)

    def test_compute_similarity_not_found(self):
        """Missing pattern IDs should return 0.0."""
        store = JudgmentStore()
        assert store.compute_pattern_similarity("nonexistent", "also_missing") == 0.0

    def test_find_overlapping_patterns(self):
        """Should return pairs of active patterns above similarity threshold."""
        store = JudgmentStore()
        a = self._make_approved_pattern(store, ["sig_a", "sig_b"])
        b = self._make_approved_pattern(store, ["sig_a", "sig_b", "sig_c"])
        c = self._make_approved_pattern(store, ["sig_x", "sig_y"])

        results = store.find_overlapping_patterns(min_similarity=0.5)
        pair_ids = [(r[0], r[1]) for r in results]
        # a and b overlap (2/3 ≈ 0.67), c is disjoint from both
        assert (a.id, b.id) in pair_ids
        assert all(c.id not in (r[0], r[1]) for r in results)

    def test_consolidate_merges_signals(self):
        """Consolidation should union signals, context, scenarios."""
        store = JudgmentStore()
        a = self._make_approved_pattern(
            store, ["sig_a", "sig_b"],
            context=["ctx_1"], drivers=[DriverAttribution(driver="d1", prior_confidence=0.6)],
        )
        a.trained_from_scenarios = ["S001"]
        b = self._make_approved_pattern(
            store, ["sig_b", "sig_c"],
            context=["ctx_2"], drivers=[DriverAttribution(driver="d2", prior_confidence=0.7)],
        )
        b.trained_from_scenarios = ["S002"]

        result = store.consolidate_patterns(a.id, b.id, actor="curator")
        assert result is not None
        assert sorted(result.applies_when_signals) == ["sig_a", "sig_b", "sig_c"]
        assert sorted(result.applies_when_context) == ["ctx_1", "ctx_2"]
        assert sorted(result.trained_from_scenarios) == ["S001", "S002"]
        driver_names = {d.driver for d in result.typical_drivers}
        assert driver_names == {"d1", "d2"}

    def test_consolidate_deprecates_source(self):
        """Merge_id should be deprecated with superseded_by pointing to keep_id."""
        store = JudgmentStore()
        a = self._make_approved_pattern(store, ["sig_a"])
        b = self._make_approved_pattern(store, ["sig_a", "sig_b"])

        store.consolidate_patterns(a.id, b.id, actor="curator")
        assert b.status == ArtifactStatus.DEPRECATED
        assert b.superseded_by == a.id

    def test_consolidate_version_bump(self):
        """Consolidation should increment the keep pattern's minor version."""
        store = JudgmentStore()
        a = self._make_approved_pattern(store, ["sig_a"])
        b = self._make_approved_pattern(store, ["sig_a"])

        assert a.version == "1.0.0"
        store.consolidate_patterns(a.id, b.id, actor="curator")
        assert a.version == "1.1.0"

    def test_consolidate_audit_logged(self):
        """Consolidation should create audit entries."""
        store = JudgmentStore()
        a = self._make_approved_pattern(store, ["sig_a"])
        b = self._make_approved_pattern(store, ["sig_a"])

        store.consolidate_patterns(a.id, b.id, actor="curator")
        entries = store.get_audit_log(action="consolidate_patterns")
        assert len(entries) == 1
        assert entries[0].actor == "curator"
        assert entries[0].details["merged_from"] == b.id

    def test_consolidate_not_approved_returns_none(self):
        """Cannot consolidate draft or deprecated patterns."""
        store = JudgmentStore()
        a = self._make_approved_pattern(store, ["sig_a"])
        b = JudgmentPattern(applies_when_signals=["sig_b"])
        store.add_pattern(b)  # stays DRAFT

        assert store.consolidate_patterns(a.id, b.id, actor="curator") is None

    def test_consolidate_merges_drivers_by_confidence(self):
        """When both patterns have same driver, keep higher prior_confidence."""
        store = JudgmentStore()
        a = self._make_approved_pattern(
            store, ["sig_a"],
            drivers=[DriverAttribution(driver="d1", prior_confidence=0.6)],
        )
        b = self._make_approved_pattern(
            store, ["sig_a"],
            drivers=[DriverAttribution(driver="d1", prior_confidence=0.9)],
        )
        result = store.consolidate_patterns(a.id, b.id, actor="curator")
        assert len(result.typical_drivers) == 1
        assert result.typical_drivers[0].prior_confidence == 0.9

    def test_get_consolidation_candidates(self):
        """Candidates report should include similarity and shared signals."""
        store = JudgmentStore()
        a = self._make_approved_pattern(store, ["sig_a", "sig_b"])
        b = self._make_approved_pattern(store, ["sig_a", "sig_b", "sig_c"])

        candidates = store.get_consolidation_candidates(min_similarity=0.5)
        assert len(candidates) >= 1
        entry = candidates[0]
        assert "pattern_a_id" in entry
        assert "similarity" in entry
        assert "shared_signals" in entry
        assert "sig_a" in entry["shared_signals"]
        assert "sig_b" in entry["shared_signals"]


# =============================================================================
# CTX-019: SEMANTIC SEARCH TESTS (JudgmentStore)
# =============================================================================

class TestSemanticSearch:
    """Tests for semantic search over patterns (CTX-019)."""

    def _seeded_semantic_store(self):
        """Create a SemanticStore with a few synonyms for testing."""
        from src.core.semantic_store import SemanticStore, CanonicalTerm, FunctionalDomain
        ss = SemanticStore()
        pa = ss.add_canonical_term(CanonicalTerm(
            term="Prior_Authorization",
            domains=[FunctionalDomain.COMMERCIAL],
        ))
        ss.add_synonym("PA", pa.id)
        ss.add_synonym("Prior Auth", pa.id)
        trx = ss.add_canonical_term(CanonicalTerm(
            term="Total_Rx",
            domains=[FunctionalDomain.COMMERCIAL],
        ))
        ss.add_alias("TRx", trx.id)
        return ss

    def test_expand_signals_with_synonyms(self):
        """'PA' should expand to include 'Prior_Authorization' and variants."""
        ss = self._seeded_semantic_store()
        expanded = JudgmentStore.expand_signals(["PA"], ss)
        assert "Prior_Authorization" in expanded
        assert "PA" in expanded
        assert "Prior Auth" in expanded

    def test_expand_signals_unknown_term(self):
        """Unknown terms should pass through unchanged."""
        ss = self._seeded_semantic_store()
        expanded = JudgmentStore.expand_signals(["unknown_signal"], ss)
        assert expanded == ["unknown_signal"]

    def test_expand_includes_canonical_and_variants(self):
        """Expansion from canonical term should include all variants."""
        ss = self._seeded_semantic_store()
        expanded = JudgmentStore.expand_signals(["Prior_Authorization"], ss)
        assert "PA" in expanded
        assert "Prior Auth" in expanded
        assert "Prior_Authorization" in expanded

    def test_semantic_find_patterns(self):
        """Semantic search should find patterns via expanded signals."""
        ss = self._seeded_semantic_store()
        store = JudgmentStore()
        # Pattern uses canonical signal name
        p = JudgmentPattern(
            applies_when_signals=["Prior_Authorization"],
            scope=Scope(geography=["US"]),
        )
        store.add_pattern(p)
        store.approve_pattern(p.id, "tester")

        # Search with alias — should find pattern via expansion
        results = store.semantic_find_patterns(
            query_terms=["PA"], context={"geography": "US"},
            semantic_store=ss, min_score=0.1,
        )
        assert len(results) >= 1
        assert results[0][0].id == p.id

    def test_semantic_find_patterns_no_match(self):
        """Unrelated terms should not match after expansion."""
        ss = self._seeded_semantic_store()
        store = JudgmentStore()
        p = JudgmentPattern(
            applies_when_signals=["Prior_Authorization"],
            scope=Scope(geography=["US"]),
        )
        store.add_pattern(p)
        store.approve_pattern(p.id, "tester")

        results = store.semantic_find_patterns(
            query_terms=["Competitor_Launch"], context={"geography": "US"},
            semantic_store=ss, min_score=0.1,
        )
        assert len(results) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
