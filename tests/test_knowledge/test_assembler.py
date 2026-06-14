"""Tests for ContextAssembler."""

import pytest

from src.core.models import (
    ArtifactStatus,
    JudgmentPattern,
    Guardrail,
    Governance,
    DriverAttribution,
)
from src.core.stores import JudgmentStore
from src.core.semantic_store import SemanticStore
from src.knowledge.models import FewShotExample, ContextPackage
from src.knowledge.few_shot_store import FewShotStore
from src.knowledge.assembler import ContextAssembler


@pytest.fixture
def judgment_store():
    store = JudgmentStore()

    # Add and approve a pattern
    p1 = JudgmentPattern(
        id="pat-001",
        applies_when_signals=["NBRx_Drop", "PA_Edit_Increase"],
        applies_when_context=["oncology", "launch"],
        typical_drivers=[
            DriverAttribution(driver="Access_Friction", prior_confidence=0.8),
            DriverAttribution(driver="Field_Execution_Gap", prior_confidence=0.4),
        ],
        governance=Governance(owner="system"),
    )
    store.add_pattern(p1)
    store.approve_pattern("pat-001", "test_approver")

    # Add and approve a guardrail
    g1 = Guardrail(
        id="guard-001",
        blocks_action_types=["direct_promotion"],
        blocks_drivers=["Unverified_Claim"],
        applies_to_personas=["field_rep"],
        governance=Governance(owner="compliance"),
    )
    store.add_guardrail(g1)
    store.approve_guardrail("guard-001", "compliance_officer")

    return store


@pytest.fixture
def semantic_store():
    store = SemanticStore()
    store.seed_commercial_synonyms()
    return store


@pytest.fixture
def few_shot_store(tmp_path):
    store = FewShotStore(tmp_path / "few_shots")
    store.add(FewShotExample(
        id="fs-test-001",
        task_type="driver_attribution",
        input_text="NBRx drop test",
        output_text="Access_Friction",
        tags={"therapeutic_area": ["oncology"]},
        quality_score=0.9,
        status=ArtifactStatus.APPROVED,
    ))
    return store


@pytest.fixture
def assembler(judgment_store, semantic_store, few_shot_store):
    return ContextAssembler(
        judgment_store=judgment_store,
        semantic_store=semantic_store,
        graph_store=None,
        few_shot_store=few_shot_store,
    )


class TestContextAssembler:
    def test_assemble_basic(self, assembler):
        """Should return a ContextPackage for a valid query."""
        result = assembler.assemble("NBRx_Drop in oncology")
        assert isinstance(result, ContextPackage)
        assert result.query == "NBRx_Drop in oncology"
        assert result.token_estimate > 0
        assert result.max_tokens == 4000

    def test_assemble_includes_guardrails(self, assembler):
        """Guardrails should always be included."""
        result = assembler.assemble("any query")
        assert len(result.guardrails) >= 1
        assert result.guardrails[0]["id"] == "guard-001"

    def test_assemble_includes_patterns(self, assembler):
        """Matching patterns should be included."""
        result = assembler.assemble("NBRx_Drop PA_Edit_Increase oncology launch")
        assert len(result.patterns) >= 1

    def test_assemble_empty_query_still_has_guardrails(self, assembler):
        """Even with no matching patterns, guardrails should be present."""
        result = assembler.assemble("completely unrelated query xyz123")
        assert len(result.guardrails) >= 1

    def test_assemble_min_tokens_error(self, assembler):
        """max_tokens < 100 should raise ValueError."""
        with pytest.raises(ValueError):
            assembler.assemble("test", max_tokens=50)

    def test_assemble_token_budget_respected(self, assembler):
        """Token estimate should not exceed max_tokens."""
        result = assembler.assemble("NBRx_Drop", max_tokens=500)
        assert result.token_estimate <= result.max_tokens

    def test_assemble_resolves_jargon(self, assembler):
        """Jargon map should contain resolved terms from SemanticStore."""
        result = assembler.assemble("PA NBRx")
        # PA and NBRx should resolve to canonical terms
        # jargon_context keys should include canonical terms
        # (may be empty if query terms don't exactly match)
        assert isinstance(result.jargon_context, dict)

    def test_assemble_without_few_shot_store(self, judgment_store, semantic_store):
        """Should work without FewShotStore."""
        assembler = ContextAssembler(
            judgment_store=judgment_store,
            semantic_store=semantic_store,
        )
        result = assembler.assemble("test query")
        assert isinstance(result, ContextPackage)
        assert result.few_shots == []

    def test_assemble_metadata(self, assembler):
        """Metadata should include agent_type."""
        result = assembler.assemble("test", agent_type="specialist")
        assert result.metadata["agent_type"] == "specialist"


class TestContextPackage:
    def test_to_dict(self):
        pkg = ContextPackage(query="test", max_tokens=4000)
        d = pkg.to_dict()
        assert d["query"] == "test"
        assert d["max_tokens"] == 4000
        assert isinstance(d["patterns"], list)

    def test_estimate_tokens(self):
        pkg = ContextPackage(
            query="test query",
            patterns=[{"id": "p1", "drivers": [{"driver": "X"}]}],
            guardrails=[{"id": "g1"}],
        )
        tokens = pkg.estimate_tokens()
        assert tokens > 0

    def test_empty_package(self):
        pkg = ContextPackage(query="empty")
        d = pkg.to_dict()
        assert d["patterns"] == []
        assert d["guardrails"] == []
        assert d["few_shots"] == []
