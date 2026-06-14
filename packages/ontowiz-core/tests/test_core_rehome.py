"""F1 #3 — re-home src/core -> ontowiz-core (Tier B).

Red-first: these import the governance API from ontowiz_core, which is a stub
until the move lands. Green when src/core is re-homed here.
"""

from __future__ import annotations


def test_governance_api_importable_from_ontowiz_core():
    from ontowiz_core import (  # noqa: F401
        ArtifactStatus,
        BlastRadius,
        Delta,
        DeltaStatus,
        DeltaStore,
        DeltaType,
        EvidenceStore,
        GraphStore,
        Guardrail,
        JudgmentPattern,
        JudgmentStore,
        SemanticStore,
    )


def test_judgment_pattern_defaults_draft():
    from ontowiz_core import ArtifactStatus, JudgmentPattern

    jp = JudgmentPattern()
    assert jp.status == ArtifactStatus.DRAFT
    assert jp.id  # uuid default


def test_stores_instantiate():
    from ontowiz_core import DeltaStore, EvidenceStore, GraphStore, SemanticStore

    assert DeltaStore() is not None
    assert GraphStore() is not None
    assert SemanticStore() is not None
    assert EvidenceStore() is not None


def test_delta_status_lifecycle_values():
    from ontowiz_core import DeltaStatus

    # the governed lifecycle the bridge (#4) will drive
    names = {s.name for s in DeltaStatus}
    assert {"PROPOSED", "APPROVED", "REJECTED"}.issubset(names)
