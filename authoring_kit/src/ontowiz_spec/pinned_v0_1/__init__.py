"""ontowiz-spec — shared data contracts (Tier A).

Zero logic, one heavy dependency (pydantic). Everything in the system imports
this; this imports nothing of ours. If a change here ripples everywhere, that
is the contract doing its job.
"""

from __future__ import annotations

from .artifacts import (
    ALWAYS_INCLUDED_KINDS,
    ARTIFACT_MODELS,
    AntiPattern,
    ArtifactBase,
    ArtifactKind,
    EvalCase,
    ExceptionRule,
    MetricDefinition,
    QuestionPlaybook,
    SourceContract,
    UngovernedTransitionError,
)
from .library import (
    ActionTemplate,
    DataQuirk,
    DecisionHeuristic,
    DriverAttribution,
    EntityRecord,
    EntityRegistry,
    FewShotExample,
    FewShotLibrary,
    FunctionAction,
    Guardrail,
    HeuristicAntiPattern,
    InstructionSet,
    JargonEntry,
    JargonMap,
    JudgmentPattern,
    OverrideRule,
    PlaybookStep,
    ProcessPlaybook,
    PromptTemplate,
    Rule,
    Taxonomy,
    TaxonomyNode,
    TriggerCondition,
)
from .lifecycle import (
    SERVABLE_STATES,
    SERVABLE_STATES_DEV,
    Lifecycle,
    LifecycleTransition,
)
from .pack_manifest import PackEvalSummary, PackLayer, PackManifest
from .tags import Tag, TagDimension, TagQuery

__version__ = "0.1.0"

__all__ = [
    "ArtifactBase",
    "UngovernedTransitionError",
    "ArtifactKind",
    "ARTIFACT_MODELS",
    "ALWAYS_INCLUDED_KINDS",
    "EvalCase",
    "MetricDefinition",
    "SourceContract",
    "QuestionPlaybook",
    "AntiPattern",
    "ExceptionRule",
    "Lifecycle",
    "LifecycleTransition",
    "SERVABLE_STATES",
    "SERVABLE_STATES_DEV",
    "Tag",
    "TagDimension",
    "TagQuery",
    "PackManifest",
    "PackLayer",
    "PackEvalSummary",
    # ported artifact library (SpecOmagic 10 + judgment 3)
    "InstructionSet",
    "Taxonomy",
    "JargonMap",
    "EntityRegistry",
    "FewShotLibrary",
    "OverrideRule",
    "PromptTemplate",
    "DecisionHeuristic",
    "DataQuirk",
    "ProcessPlaybook",
    "JudgmentPattern",
    "Guardrail",
    "ActionTemplate",
    # sub-models
    "Rule",
    "TaxonomyNode",
    "JargonEntry",
    "EntityRecord",
    "FewShotExample",
    "TriggerCondition",
    "HeuristicAntiPattern",
    "PlaybookStep",
    "DriverAttribution",
    "FunctionAction",
]
