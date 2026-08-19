"""The unified knowledge artifact model.

This is the single contract every Onto_Wiz package agrees on. It merges three
lineages into one registry:

  * SpecOmagic (10 types): InstructionSet, Taxonomy, JargonMap, EntityRegistry,
    FewShotLibrary, OverrideRule, PromptTemplate, DecisionHeuristic, DataQuirk,
    ProcessPlaybook
  * Onto_Wiz judgment layer: JudgmentPattern, Guardrail, ActionTemplate
  * New, first-class per the spec: EvalCase, MetricDefinition, SourceContract,
    QuestionPlaybook, AntiPattern, ExceptionRule

F0 establishes the shared base + governance fields + the kind registry, and
defines the *new* types in full (they have no upstream to port). The ported
types are filled in during F1, each subclassing ``ArtifactBase`` so they
inherit lifecycle, tags, provenance, and layering for free.
"""

from __future__ import annotations

import re
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

from .lifecycle import Lifecycle, LifecycleTransition
from .tags import Tag

# Artifact ids become section names and on-disk filenames — restrict to a safe,
# injective charset (no '.'/'/' so two ids cannot collapse to one section name
# or escape the pack directory).
_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")
# Windows reserved device names — would create a non-file on write_pack.
_RESERVED_IDS = frozenset(
    {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
)

# States that an agent can be served from / that assert verification — promotion
# into them must cite the governing Delta (enforced in ``transition``).
_GOVERNED_TARGETS = frozenset({Lifecycle.VERIFIED, Lifecycle.ACTIVE})


class UngovernedTransitionError(RuntimeError):
    """Raised when a promotion to a governed state omits its governing delta id.

    The Tier-A invariant behind "nothing reaches ACTIVE without a governed
    Delta": the low-level ``transition`` primitive itself refuses to advance into
    VERIFIED/ACTIVE unless a ``delta_id`` is supplied. The Tier-B bridge always
    supplies one; ad-hoc callers cannot silently promote knowledge.
    """


class ArtifactKind(str, Enum):
    """The closed catalogue of artifact types the system understands."""

    # — SpecOmagic lineage —
    INSTRUCTION_SET = "instruction_set"
    TAXONOMY = "taxonomy"
    JARGON_MAP = "jargon_map"
    ENTITY_REGISTRY = "entity_registry"
    FEWSHOT_LIBRARY = "fewshot_library"
    OVERRIDE_RULE = "override_rule"
    PROMPT_TEMPLATE = "prompt_template"
    DECISION_HEURISTIC = "decision_heuristic"
    DATA_QUIRK = "data_quirk"
    PROCESS_PLAYBOOK = "process_playbook"
    # — Onto_Wiz judgment lineage —
    JUDGMENT_PATTERN = "judgment_pattern"
    GUARDRAIL = "guardrail"
    ACTION_TEMPLATE = "action_template"
    # — New, first-class —
    EVAL_CASE = "eval_case"
    METRIC_DEFINITION = "metric_definition"
    SOURCE_CONTRACT = "source_contract"
    QUESTION_PLAYBOOK = "question_playbook"
    ANTI_PATTERN = "anti_pattern"
    EXCEPTION_RULE = "exception_rule"


# Artifact kinds that are safety/accuracy layers — the context gate is forbidden
# from budget-trimming these away. (Ported behaviour from SpecOmagic assembler.)
ALWAYS_INCLUDED_KINDS: frozenset[ArtifactKind] = frozenset(
    {ArtifactKind.OVERRIDE_RULE, ArtifactKind.GUARDRAIL, ArtifactKind.DATA_QUIRK}
)


class ArtifactBase(BaseModel):
    """Every artifact carries governance, provenance, tags and layering.

    Immutability discipline: ``transition`` returns a *new* instance rather than
    mutating, so the audit trail can never be silently rewritten. The actual
    decision to transition belongs to Tier B governance; this method only
    records a transition that governance has authorised.
    """

    id: str
    kind: ArtifactKind
    name: str
    version: int = 1

    # — governance / lifecycle —
    lifecycle: Lifecycle = Lifecycle.DRAFT
    lifecycle_history: list[LifecycleTransition] = Field(default_factory=list)
    created_by: str = "system"
    reviewed_by: str | None = None
    approved_at: str | None = None

    # — relevance / placement —
    tags: list[Tag] = Field(default_factory=list)
    layer: str = "base"  # base → therapy → function → client → engagement

    # — provenance —
    source_document_ids: list[str] = Field(default_factory=list)
    # Confidence in this artifact's correctness, [0, 1]. Drives steward signals
    # and is surfaced in the trust envelope.
    confidence: float = 1.0

    created_at: str | None = None
    updated_at: str | None = None

    model_config = {"use_enum_values": False}

    @field_validator("id")
    @classmethod
    def _id_is_safe(cls, v: str) -> str:
        if not _ID_RE.match(v):
            raise ValueError(
                f"artifact id {v!r} must match {_ID_RE.pattern} (no spaces, dots, "
                "or path separators — ids become section names and filenames)"
            )
        if v.lower() in _RESERVED_IDS:
            raise ValueError(f"artifact id {v!r} is a reserved device name")
        return v

    @model_validator(mode="after")
    def _governed_state_needs_delta(self) -> ArtifactBase:
        """A constructed/loaded artifact in a governed state must carry its delta.

        Closes the constructor and stale-YAML bypass of the transition invariant:
        a record can only *be* ACTIVE/VERIFIED if its last governed history entry
        cites a delta_id. (``transition`` builds such entries; ad-hoc construction
        and tampered pack YAML cannot.)
        """
        if self.lifecycle in _GOVERNED_TARGETS:
            governed = [h for h in self.lifecycle_history if h.to_state in _GOVERNED_TARGETS]
            if not governed or not (governed[-1].delta_id or "").strip():
                raise UngovernedTransitionError(
                    f"artifact {self.id!r} is {self.lifecycle.value} but no governing "
                    "delta_id is recorded in its lifecycle history"
                )
        return self

    def transition(
        self,
        to_state: Lifecycle,
        *,
        changed_by: str,
        reason: str = "",
        delta_id: str | None = None,
        at: str | None = None,
    ) -> ArtifactBase:
        """Return a copy advanced to ``to_state`` with the audit entry appended.

        Promotion into a governed state (VERIFIED/ACTIVE) requires a non-blank
        ``delta_id`` — the primitive-level half of the governance invariant.
        """
        if to_state in _GOVERNED_TARGETS and not (delta_id or "").strip():
            raise UngovernedTransitionError(
                f"transition to {to_state.value} requires a governing delta_id; "
                "promote via the Delta bridge, not a direct write"
            )
        entry = LifecycleTransition(
            from_state=self.lifecycle,
            to_state=to_state,
            changed_by=changed_by,
            reason=reason,
            delta_id=delta_id,
            at=at,
        )
        return self.model_copy(
            update={
                "lifecycle": to_state,
                "lifecycle_history": [*self.lifecycle_history, entry],
                "reviewed_by": changed_by if to_state == Lifecycle.VERIFIED else self.reviewed_by,
                "approved_at": at if to_state == Lifecycle.ACTIVE else self.approved_at,
                "updated_at": at or self.updated_at,
            }
        )

    def to_prompt_text(self) -> str:
        """Render this artifact as context text. Overridden per kind in F1."""
        return f"[{self.kind.value}] {self.name}"


# ──────────────────────────────────────────────────────────────────────────
# New first-class artifact types (no upstream — defined in full at F0)
# ──────────────────────────────────────────────────────────────────────────


class EvalCase(ArtifactBase):
    """A testable consequence of knowledge — the spec's non-negotiable.

    Every other artifact should be able to point at an EvalCase that proves it
    changes agent behaviour. The eval loop (Tier B) runs these; the Forge
    manufactures them as a by-product of SME rounds.
    """

    kind: ArtifactKind = ArtifactKind.EVAL_CASE
    question: str
    # What a *good* packed-agent answer must contain / must avoid.
    must_contain: list[str] = Field(default_factory=list)
    must_not_contain: list[str] = Field(default_factory=list)
    gold_answer: str = ""
    # The artifact id(s) this case exists to validate.
    validates: list[str] = Field(default_factory=list)
    # Optional rubric criteria (weight by name) for LLM-judge scoring.
    rubric: dict[str, float] = Field(default_factory=dict)


class MetricDefinition(ArtifactBase):
    """A canonical, governed definition of a measurable quantity."""

    kind: ArtifactKind = ArtifactKind.METRIC_DEFINITION
    formula: str = ""
    unit: str = ""
    grain: str = ""  # e.g. "weekly / brand / territory"
    synonyms: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    trusted_sources: list[str] = Field(default_factory=list)


class SourceContract(ArtifactBase):
    """What a data source can and cannot be trusted for."""

    kind: ArtifactKind = ArtifactKind.SOURCE_CONTRACT
    source: str
    trusted_for: list[str] = Field(default_factory=list)      # e.g. ["TRx", "NBRx"]
    not_trusted_for: list[str] = Field(default_factory=list)  # e.g. ["net price"]
    known_lag: str = ""                                       # e.g. "claims lag 6 weeks"
    reliability: str = "soft"                                 # hard | soft | rumor


class QuestionPlaybook(ArtifactBase):
    """How to answer a *class* of business question."""

    kind: ArtifactKind = ArtifactKind.QUESTION_PLAYBOOK
    question_pattern: str = ""           # e.g. "Why is share declining?"
    decomposition: list[str] = Field(default_factory=list)  # ordered analytical steps
    required_metrics: list[str] = Field(default_factory=list)
    required_sources: list[str] = Field(default_factory=list)
    common_traps: list[str] = Field(default_factory=list)


class AntiPattern(ArtifactBase):
    """A common wrong conclusion the agent must not reach."""

    kind: ArtifactKind = ArtifactKind.ANTI_PATTERN
    wrong_conclusion: str = ""           # e.g. "stocking effect read as demand"
    why_wrong: str = ""
    correct_instead: str = ""
    trigger_signals: list[str] = Field(default_factory=list)


class ExceptionRule(ArtifactBase):
    """When a rule, heuristic or definition does *not* apply."""

    kind: ArtifactKind = ArtifactKind.EXCEPTION_RULE
    applies_to_artifact_id: str = ""     # the rule this carves an exception in
    condition: str = ""                  # when the exception holds
    instead: str = ""                    # what to do under the exception
    reason: str = ""


# Registry of concrete model classes by kind. F1 extends this as ported types
# land. Consumers use ``ARTIFACT_MODELS[kind]`` to deserialise pack YAML.
ARTIFACT_MODELS: dict[ArtifactKind, type[ArtifactBase]] = {
    ArtifactKind.EVAL_CASE: EvalCase,
    ArtifactKind.METRIC_DEFINITION: MetricDefinition,
    ArtifactKind.SOURCE_CONTRACT: SourceContract,
    ArtifactKind.QUESTION_PLAYBOOK: QuestionPlaybook,
    ArtifactKind.ANTI_PATTERN: AntiPattern,
    ArtifactKind.EXCEPTION_RULE: ExceptionRule,
}
