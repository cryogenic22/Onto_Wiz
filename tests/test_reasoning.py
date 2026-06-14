import pytest
import yaml
from pathlib import Path
from src.reasoning.engine import ReasoningEngine, ScenarioContext
from src.core.models import (
    JudgmentPattern, DriverAttribution, ArtifactStatus, Governance,
)
from src.core.stores import JudgmentStore

# Load Synthetic Data
DATA_PATH = Path("ontology/synthetic_data/compellium_pharma.yaml")
ONTOLOGY_PATH = Path("ontology/commercial.yaml")

@pytest.fixture
def engine():
    # Initialize Engine with Ontology and Data
    with open(ONTOLOGY_PATH, "r") as f:
        ontology = yaml.safe_load(f)
    with open(DATA_PATH, "r") as f:
        data = yaml.safe_load(f)
    return ReasoningEngine(ontology, data)


# ---------------------------------------------------------------------------
# Minimal ontology + data helpers for CTX-041 unit tests
# ---------------------------------------------------------------------------

def _minimal_ontology(rules=None):
    """Return a bare ontology dict with optional inference_rules."""
    return {"ontology": {"inference_rules": rules or []}}


def _minimal_data(account_id="acct_1", tags=None, confidence=0.7):
    """Return data with a single signal for the given account."""
    return {
        "market_context": {
            "dark_data_signals": [
                {
                    "account_id": account_id,
                    "tags": tags or [],
                    "confidence": confidence,
                }
            ]
        }
    }


def _make_pattern(signals, drivers=None, status=ArtifactStatus.APPROVED):
    """Create an approved JudgmentPattern with given signals and drivers."""
    pattern = JudgmentPattern(
        applies_when_signals=signals,
        typical_drivers=drivers or [],
    )
    pattern.status = status
    return pattern


def _store_with_patterns(patterns):
    """Create a JudgmentStore pre-loaded with approved patterns."""
    store = JudgmentStore()
    for p in patterns:
        store.add_pattern(p)       # sets status -> DRAFT
        store.approve_pattern(p.id, "test_approver")  # sets status -> APPROVED
    return store

def test_scenario_competitor_lockout(engine):
    """
    Golden Scenario 1: Competitor Lock-out Detection.
    """
    question = "Is the budget objection at University Hospital Bonn real?"
    context = ScenarioContext(account_id="university_klinik_bonn", brand_id="brand_oncovance")
    
    response = engine.reason(question, context)
    
    assert "Risk:Lockout" in response.identified_risks
    assert "Lock-out" in response.verdict

def test_scenario_budget_diagnosis(engine):
    """
    Golden Scenario 2: Budget Objection Diagnosis.
    """
    question = "Is the budget objection at St. Mary's real?"
    context = ScenarioContext(account_id="st_mary_hospital", brand_id="brand_oncovance")
    
    response = engine.reason(question, context)
    
    assert "Constraint:Financial" in response.identified_risks
    assert "Genuine Budget Crisis" in response.verdict

def test_scenario_safety_signal(engine):
    """
    Golden Scenario 3: The Clinical Trojan Horse.
    Situation: Volume drop masked as "Preference", but linked to "Medical Inquiry".
    """
    question = "Why is volume dropping at Metro General?"
    context = ScenarioContext(account_id="metro_general_hospital", brand_id="brand_oncovance")
    
    response = engine.reason(question, context)
    
    assert response.confidence_score > 0.8
    assert "Risk:Safety" in response.identified_risks
    assert "Emerging Safety Signal" in response.verdict


# =============================================================================
# CTX-041 — Unified reasoning tests
# =============================================================================

class TestCTX041EngineWithoutStore:
    """Backward compatibility: engine without judgment_store behaves identically."""

    def test_engine_without_store_unchanged(self):
        ontology = _minimal_ontology([{
            "id": "rule_static",
            "priority": 60,
            "conditions": [{"name": "c1", "pattern": "tag_match", "args": ["tag_a"]}],
            "logic": "c1",
            "consequence": {"risk": "Risk:Static", "verdict": "Static wins", "confidence_modifier": "average"},
        }])
        data = _minimal_data(tags=["tag_a"])
        engine = ReasoningEngine(ontology, data)  # no judgment_store
        resp = engine.reason("test?", ScenarioContext(account_id="acct_1", brand_id="b"))
        assert resp.identified_risks == ["Risk:Static"]
        assert resp.verdict == "Static wins"

    def test_engine_with_empty_store(self):
        ontology = _minimal_ontology([{
            "id": "rule_static",
            "priority": 60,
            "conditions": [{"name": "c1", "pattern": "tag_match", "args": ["tag_a"]}],
            "logic": "c1",
            "consequence": {"risk": "Risk:Static", "verdict": "Static wins", "confidence_modifier": "average"},
        }])
        data = _minimal_data(tags=["tag_a"])
        store = JudgmentStore()  # empty
        engine = ReasoningEngine(ontology, data, judgment_store=store)
        resp = engine.reason("test?", ScenarioContext(account_id="acct_1", brand_id="b"))
        assert resp.identified_risks == ["Risk:Static"]
        assert resp.verdict == "Static wins"


class TestCTX041PatternToRule:
    """Unit tests for the _pattern_to_rule adapter."""

    def test_pattern_to_rule_conversion(self):
        pattern = _make_pattern(
            signals=["sig_x", "sig_y"],
            drivers=[DriverAttribution(driver="Driver:Budget", prior_confidence=0.8)],
        )
        engine = ReasoningEngine(_minimal_ontology(), {})
        rule = engine._pattern_to_rule(pattern, score=0.9)
        assert rule["_source"] == "judgment_store"
        assert rule["priority"] == 0.9 * ReasoningEngine.LEARNED_PRIORITY_BASE
        assert rule["conditions"][0]["args"] == ["sig_x", "sig_y"]
        assert rule["consequence"]["risk"] == "Driver:Budget"

    def test_pattern_to_rule_no_drivers(self):
        pattern = _make_pattern(signals=["sig_z"], drivers=[])
        engine = ReasoningEngine(_minimal_ontology(), {})
        rule = engine._pattern_to_rule(pattern, score=0.5)
        assert rule["consequence"]["risk"] == "Risk:Learned"


class TestCTX041PriorityCompetition:
    """Learned patterns and static rules compete in one priority-ranked loop."""

    def test_learned_pattern_wins_over_low_priority_rule(self):
        """A learned pattern with score 0.8 (priority 40) beats a static rule at priority 30."""
        ontology = _minimal_ontology([{
            "id": "rule_low",
            "priority": 30,
            "conditions": [{"name": "c1", "pattern": "tag_match", "args": ["tag_a"]}],
            "logic": "c1",
            "consequence": {"risk": "Risk:Low", "verdict": "Low static", "confidence_modifier": "average"},
        }])
        data = _minimal_data(tags=["tag_a"])
        pattern = _make_pattern(
            signals=["tag_a"],
            drivers=[DriverAttribution(driver="Driver:Learned", prior_confidence=0.7)],
        )
        store = _store_with_patterns([pattern])
        engine = ReasoningEngine(ontology, data, judgment_store=store)
        resp = engine.reason("test?", ScenarioContext(account_id="acct_1", brand_id="b"))
        # Learned pattern priority = score * 50; score should be > 0.6 => priority > 30
        assert "Driver:Learned" in resp.identified_risks
        assert resp.verdict.startswith("Learned:")

    def test_static_safety_rule_wins_over_learned(self):
        """A static safety rule at priority 90 always beats a learned pattern."""
        ontology = _minimal_ontology([{
            "id": "rule_safety",
            "priority": 90,
            "conditions": [{"name": "c1", "pattern": "tag_match", "args": ["tag_a"]}],
            "logic": "c1",
            "consequence": {"risk": "Risk:Safety", "verdict": "Safety first", "confidence_modifier": "max"},
        }])
        data = _minimal_data(tags=["tag_a"], confidence=0.95)
        pattern = _make_pattern(
            signals=["tag_a"],
            drivers=[DriverAttribution(driver="Driver:Learned", prior_confidence=0.9)],
        )
        store = _store_with_patterns([pattern])
        engine = ReasoningEngine(ontology, data, judgment_store=store)
        resp = engine.reason("test?", ScenarioContext(account_id="acct_1", brand_id="b"))
        assert resp.identified_risks == ["Risk:Safety"]
        assert resp.verdict == "Safety first"

    def test_multiple_learned_patterns_highest_score_wins(self):
        """When no static rules match, the pattern with more signal overlap wins."""
        data = _minimal_data(tags=["sig_alpha", "sig_beta", "sig_gamma"])
        p1 = _make_pattern(
            signals=["sig_alpha", "sig_missing"],  # only 50% overlap → lower score
            drivers=[DriverAttribution(driver="Driver:Partial", prior_confidence=0.6)],
        )
        p2 = _make_pattern(
            signals=["sig_alpha", "sig_beta"],  # 100% overlap → higher score
            drivers=[DriverAttribution(driver="Driver:Full", prior_confidence=0.8)],
        )
        store = _store_with_patterns([p1, p2])
        engine = ReasoningEngine(_minimal_ontology(), data, judgment_store=store)
        resp = engine.reason("test?", ScenarioContext(account_id="acct_1", brand_id="b"))
        # p2 has 100% signal overlap vs p1's 50% → higher match_score → wins
        assert "Driver:Full" in resp.identified_risks

    def test_mixed_rules_and_patterns_priority_order(self):
        """Static rule at priority 55 beats learned pattern at score 0.8 (priority 40)
        but loses to a pattern that somehow gets score 1.0+ (priority 50+)."""
        ontology = _minimal_ontology([{
            "id": "rule_mid",
            "priority": 55,
            "conditions": [{"name": "c1", "pattern": "tag_match", "args": ["tag_a"]}],
            "logic": "c1",
            "consequence": {"risk": "Risk:Mid", "verdict": "Mid static", "confidence_modifier": "average"},
        }])
        data = _minimal_data(tags=["tag_a"])
        pattern = _make_pattern(
            signals=["tag_a"],
            drivers=[DriverAttribution(driver="Driver:Learned", prior_confidence=0.7)],
        )
        store = _store_with_patterns([pattern])
        engine = ReasoningEngine(ontology, data, judgment_store=store)
        resp = engine.reason("test?", ScenarioContext(account_id="acct_1", brand_id="b"))
        # Static priority 55 > learned max priority ~50 → static wins
        assert resp.identified_risks == ["Risk:Mid"]


class TestCTX041LearnedResponse:
    """Learned rules produce enriched responses with driver data."""

    def test_learned_pattern_builds_driver_response(self):
        data = _minimal_data(tags=["sig_1", "sig_2"], confidence=0.8)
        pattern = _make_pattern(
            signals=["sig_1", "sig_2"],
            drivers=[
                DriverAttribution(driver="Driver:Payer", prior_confidence=0.7),
                DriverAttribution(driver="Driver:Access", prior_confidence=0.6),
            ],
        )
        store = _store_with_patterns([pattern])
        engine = ReasoningEngine(_minimal_ontology(), data, judgment_store=store)
        resp = engine.reason("test?", ScenarioContext(account_id="acct_1", brand_id="b"))
        assert "Driver:Payer" in resp.identified_risks
        assert "Driver:Access" in resp.identified_risks
        assert resp.confidence_score > 0.0
        assert len(resp.supporting_evidence_tags) > 0
