"""
Shared test fixtures for Onto_Wiz API integration tests.

Provides a fresh TestClient and sample payloads for each test function.
"""

import pytest
from fastapi.testclient import TestClient

from src.api.server import app, delta_store, judgment_store, reasoning_event_store, contribution_store


@pytest.fixture(autouse=True)
def _reset_stores():
    """Clear all in-memory stores before each test to prevent state leakage."""
    delta_store._deltas.clear()
    delta_store._pending_queue.clear() if hasattr(delta_store, "_pending_queue") else None
    if hasattr(delta_store, "_by_status"):
        delta_store._by_status.clear()
    if hasattr(delta_store, "_by_type"):
        delta_store._by_type.clear()
    judgment_store._patterns.clear()
    judgment_store._guardrails.clear()
    judgment_store._action_templates.clear()
    reasoning_event_store._events.clear()
    delta_store._audit_log.clear()
    judgment_store._audit_log.clear()
    contribution_store._contributions.clear()
    if hasattr(contribution_store, "_by_sme_id"):
        contribution_store._by_sme_id.clear()
    if hasattr(contribution_store, "_by_therapeutic_area"):
        contribution_store._by_therapeutic_area.clear()
    if hasattr(contribution_store, "_audit_log"):
        contribution_store._audit_log.clear()
    yield


@pytest.fixture()
def client():
    """FastAPI TestClient wrapping the Onto_Wiz app."""
    return TestClient(app)


@pytest.fixture()
def sample_delta_payload() -> dict:
    """Valid payload for POST /deltas."""
    return {
        "type": "proposed_synonym",
        "content": {"source": "market_access", "target": "formulary_access"},
        "confidence": 0.85,
        "blast_radius": "low",
        "evidence_pointers": ["ev_001"],
        "source_type": "manual",
        "source_id": "test_session_1",
    }


@pytest.fixture()
def sample_pattern_payload() -> dict:
    """Valid payload for POST /patterns."""
    return {
        "applies_when_signals": ["TRx_dip", "NBRx_decline"],
        "applies_when_context": ["regional_performance_dip"],
        "typical_drivers": [
            {"driver": "access_friction", "prior_confidence": 0.7},
            {"driver": "competitive_entry", "prior_confidence": 0.4},
        ],
        "disallowed_drivers": ["pricing_error"],
        "owner": "test_owner",
    }


@pytest.fixture()
def sample_guardrail_payload() -> dict:
    """Valid payload for POST /guardrails."""
    return {
        "blocks_action_types": ["escalate_safety"],
        "blocks_drivers": ["unverified_safety_signal"],
        "unless_evidence": ["confirmed_adr_report"],
        "applies_to_personas": ["field_rep"],
        "excludes_personas": [],
        "owner": "compliance_team",
    }
