"""The ported artifact library — SpecOmagic's 10 types + the 3 judgment types.

Each type subclasses ``ArtifactBase`` (this repo's governance/lifecycle base), so
it inherits lifecycle, tags, provenance and layering for free. Only the
type-specific fields and renderers are ported.

Provenance:
  * InstructionSet, Taxonomy, JargonMap, EntityRegistry, FewShotLibrary,
    OverrideRule, PromptTemplate, DecisionHeuristic, DataQuirk, ProcessPlaybook
    — ported from SpecOmagic (src/specomagic/models/{artifacts,sme_artifacts}.py).
    ``to_prompt_text`` renderers reused verbatim.
  * JudgmentPattern, Guardrail, ActionTemplate — the *servable data shapes* of
    Onto_Wiz's src/core/models.py judgment artifacts. The behavioural governance
    versions (match_score / is_violated / evaluate_drivers, with Governance /
    Scope / DecayConfig) stay in ontowiz-core (Tier B). Tier A carries only what
    an agent consumes.

Naming note: SpecOmagic's nested ``AntiPattern`` (inside DecisionHeuristic) is
ported here as ``HeuristicAntiPattern`` to avoid colliding with the first-class
``AntiPattern`` artifact in artifacts.py.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .artifacts import ARTIFACT_MODELS, ArtifactBase, ArtifactKind
from .tags import Tag

# ── Instruction Sets ────────────────────────────────────────────────────────


class Rule(BaseModel):
    """A single business/analytical rule within an instruction set."""

    id: str
    rule: str
    priority: int = Field(default=1, ge=1)  # 1 = highest
    condition: str | None = None
    source: str | None = None
    geography: str | None = None
    data_source: str | None = None
    applies_to: list[str] = Field(default_factory=list)


class InstructionSet(ArtifactBase):
    """A curated set of instructions for an agent to perform an analytical task."""

    kind: ArtifactKind = ArtifactKind.INSTRUCTION_SET
    scope: dict[str, str] = Field(default_factory=dict)
    context: str = ""
    rules: list[Rule] = Field(default_factory=list)
    output_format: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)

    def rules_by_priority(self) -> list[Rule]:
        return sorted(self.rules, key=lambda r: r.priority)

    def to_prompt_text(self) -> str:
        lines: list[str] = [f"## {self.name}"]
        if self.context:
            lines.append(f"\n{self.context}")
        if self.rules:
            lines.append("\n### Rules")
            for rule in self.rules_by_priority():
                condition = f" (when: {rule.condition})" if rule.condition else ""
                lines.append(f"- [P{rule.priority}] {rule.rule}{condition}")
        if self.output_format:
            lines.append("\n### Output Format")
            for key, val in self.output_format.items():
                lines.append(f"- {key}: {val}")
        if self.warnings:
            lines.append("\n### Warnings")
            lines.extend(f"- WARNING: {w}" for w in self.warnings)
        return "\n".join(lines)


# ── Taxonomies ──────────────────────────────────────────────────────────────


class TaxonomyNode(BaseModel):
    """A node in a taxonomy tree."""

    name: str
    children: list[TaxonomyNode] = Field(default_factory=list)

    def flatten(self, prefix: str = "") -> list[str]:
        path = f"{prefix} > {self.name}" if prefix else self.name
        result = [path]
        for child in self.children:
            result.extend(child.flatten(path))
        return result


TaxonomyNode.model_rebuild()


class Taxonomy(ArtifactBase):
    """Hierarchical classification system for consistent categorization."""

    kind: ArtifactKind = ArtifactKind.TAXONOMY
    tree: list[TaxonomyNode] = Field(default_factory=list)

    def all_paths(self) -> list[str]:
        paths: list[str] = []
        for node in self.tree:
            paths.extend(node.flatten())
        return paths

    def find_node(self, name: str) -> TaxonomyNode | None:
        queue = list(self.tree)
        while queue:
            node = queue.pop(0)
            if node.name == name:
                return node
            queue.extend(node.children)
        return None

    def to_prompt_text(self) -> str:
        lines = [f"## Taxonomy: {self.name}"]
        lines.extend(f"- {path}" for path in self.all_paths())
        return "\n".join(lines)


# ── Jargon Maps ─────────────────────────────────────────────────────────────


class JargonEntry(BaseModel):
    """A single jargon/synonym mapping."""

    canonical: str
    synonyms: list[str] = Field(default_factory=list)
    definition: str = ""
    not_to_be_confused_with: list[str] = Field(default_factory=list)


class JargonMap(ArtifactBase):
    """Maps synonyms and jargon to canonical terms."""

    kind: ArtifactKind = ArtifactKind.JARGON_MAP
    entries: list[JargonEntry] = Field(default_factory=list)

    def resolve(self, term: str) -> str | None:
        term_lower = term.lower()
        for entry in self.entries:
            if entry.canonical.lower() == term_lower:
                return entry.canonical
            if any(s.lower() == term_lower for s in entry.synonyms):
                return entry.canonical
        return None

    def lookup(self, term: str) -> JargonEntry | None:
        canonical = self.resolve(term)
        if canonical is None:
            return None
        for entry in self.entries:
            if entry.canonical == canonical:
                return entry
        return None

    def to_prompt_text(self) -> str:
        lines = ["## Terminology"]
        for entry in self.entries:
            synonyms = ", ".join(entry.synonyms) if entry.synonyms else "none"
            lines.append(f"- **{entry.canonical}**: {entry.definition}")
            lines.append(f"  Aliases: {synonyms}")
            if entry.not_to_be_confused_with:
                lines.append(f"  NOT to be confused with: {', '.join(entry.not_to_be_confused_with)}")
        return "\n".join(lines)


# ── Entity Registry ─────────────────────────────────────────────────────────


class EntityRecord(BaseModel):
    """A single entity in the registry."""

    id: str
    entity_type: str
    name: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    aliases: list[str] = Field(default_factory=list)
    relationships: list[dict[str, str]] = Field(default_factory=list)


class EntityRegistry(ArtifactBase):
    """Canonical registry of all domain entities."""

    kind: ArtifactKind = ArtifactKind.ENTITY_REGISTRY
    entities: list[EntityRecord] = Field(default_factory=list)

    def get_by_id(self, entity_id: str) -> EntityRecord | None:
        return next((e for e in self.entities if e.id == entity_id), None)

    def get_by_type(self, entity_type: str) -> list[EntityRecord]:
        return [e for e in self.entities if e.entity_type == entity_type]

    def resolve_name(self, name: str) -> EntityRecord | None:
        name_lower = name.lower()
        for entity in self.entities:
            if entity.name.lower() == name_lower:
                return entity
            if any(a.lower() == name_lower for a in entity.aliases):
                return entity
        return None

    def to_prompt_text(self) -> str:
        lines = ["## Domain Entities"]
        by_type: dict[str, list[EntityRecord]] = {}
        for e in self.entities:
            by_type.setdefault(e.entity_type, []).append(e)
        for etype, entities in by_type.items():
            lines.append(f"\n### {etype.replace('_', ' ').title()}")
            for e in entities:
                aliases = f" (aka {', '.join(e.aliases)})" if e.aliases else ""
                lines.append(f"- **{e.name}**{aliases}")
                lines.extend(f"  - {k}: {v}" for k, v in e.attributes.items())
        return "\n".join(lines)


# ── Few-Shot Libraries ──────────────────────────────────────────────────────


class FewShotExample(BaseModel):
    """A single input/output example for few-shot prompting."""

    input: str
    output: str


class FewShotLibrary(ArtifactBase):
    """Curated input/output examples organized by task type."""

    kind: ArtifactKind = ArtifactKind.FEWSHOT_LIBRARY
    task_type: str = ""
    examples: list[FewShotExample] = Field(default_factory=list)

    def to_prompt_text(self, max_examples: int = 2) -> str:
        lines = [f"## Examples ({self.name})"]
        for i, ex in enumerate(self.examples[:max_examples]):
            lines.append(f"\n### Example {i + 1}")
            lines.append(f"**Input:** {ex.input}")
            lines.append(f"**Output:** {ex.output}")
        return "\n".join(lines)


# ── Override Rules ──────────────────────────────────────────────────────────


class OverrideRule(ArtifactBase):
    """Hard constraint that always fires in a specific context (safety layer)."""

    kind: ArtifactKind = ArtifactKind.OVERRIDE_RULE
    trigger_tags: list[Tag] = Field(default_factory=list)
    rule: str = ""
    reason: str = ""

    def matches(self, context_tags: list[Tag]) -> bool:
        if not self.trigger_tags:
            return True  # no trigger = always fires
        context_set = {(t.dimension.value, t.value) for t in context_tags}
        return all((t.dimension.value, t.value) in context_set for t in self.trigger_tags)

    def to_prompt_text(self) -> str:
        lines = ["## Override Rules", f"- **MANDATORY:** {self.rule}"]
        if self.reason:
            lines.append(f"  Reason: {self.reason}")
        return "\n".join(lines)


# ── Prompt Templates ────────────────────────────────────────────────────────


class PromptTemplate(ArtifactBase):
    """Standardized query template with placeholders and defaults."""

    kind: ArtifactKind = ArtifactKind.PROMPT_TEMPLATE
    template: str = ""
    defaults: dict[str, str] = Field(default_factory=dict)
    placeholders: list[str] = Field(default_factory=list)

    def render(self, **kwargs: str) -> str:
        values = dict(self.defaults)
        values.update(kwargs)
        try:
            return self.template.format(**values)
        except KeyError as e:
            missing = str(e).strip("'")
            return f"[Missing placeholder: {missing}] " + self.template


# ── Decision Heuristics (SME) ───────────────────────────────────────────────


class TriggerCondition(BaseModel):
    """A signal condition that triggers a decision heuristic."""

    signal_name: str
    threshold: str
    data_source: str = ""


class HeuristicAntiPattern(BaseModel):
    """A wrong conclusion SMEs know to avoid (nested in DecisionHeuristic).

    Renamed from SpecOmagic's ``AntiPattern`` to avoid colliding with the
    first-class ``AntiPattern`` artifact.
    """

    wrong_conclusion: str
    why_wrong: str
    unless_evidence: str = ""


class DecisionHeuristic(ArtifactBase):
    """A codified decision rule derived from SME expertise."""

    kind: ArtifactKind = ArtifactKind.DECISION_HEURISTIC
    trigger_signals: list[TriggerCondition] = Field(default_factory=list)
    trigger_context: list[str] = Field(default_factory=list)
    decision_logic: str = ""
    # NOTE: narrows ArtifactBase.confidence (default 1.0) to a bounded SME-facing
    # confidence in the heuristic itself.
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    judgment_type: str = "empirical"  # empirical | causal_hypothesis | normative
    exceptions: list[str] = Field(default_factory=list)
    anti_patterns: list[HeuristicAntiPattern] = Field(default_factory=list)
    evidence_required: list[str] = Field(default_factory=list)
    typical_outcome: str = ""
    recommended_actions: list[str] = Field(default_factory=list)
    captured_from: str = ""
    sme_id: str = ""
    sme_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    scope: dict[str, str] = Field(default_factory=dict)
    valid_for_days: int = 180

    def to_prompt_text(self) -> str:
        lines: list[str] = [f"## Decision Heuristic: {self.name}"]
        if self.decision_logic:
            lines.append(f"\n**Decision Rule:** {self.decision_logic}")
        if self.trigger_signals:
            lines.append("\n### Trigger Signals")
            for sig in self.trigger_signals:
                source = f" (from {sig.data_source})" if sig.data_source else ""
                lines.append(f"- {sig.signal_name} {sig.threshold}{source}")
        if self.trigger_context:
            lines.append(f"\n**Context:** {', '.join(self.trigger_context)}")
        lines.append(f"\n**Judgment Type:** {self.judgment_type}")
        lines.append(f"**Confidence:** {self.confidence}")
        if self.exceptions:
            lines.append("\n### Exceptions")
            lines.extend(f"- {exc}" for exc in self.exceptions)
        if self.anti_patterns:
            lines.append("\n### Anti-Patterns (DO NOT conclude)")
            for ap in self.anti_patterns:
                lines.append(f"- WRONG: {ap.wrong_conclusion}")
                lines.append(f"  WHY: {ap.why_wrong}")
                if ap.unless_evidence:
                    lines.append(f"  UNLESS: {ap.unless_evidence}")
        if self.evidence_required:
            lines.append("\n### Required Evidence")
            lines.extend(f"- {ev}" for ev in self.evidence_required)
        if self.typical_outcome:
            lines.append(f"\n**Typical Outcome:** {self.typical_outcome}")
        if self.recommended_actions:
            lines.append("\n### Recommended Actions")
            lines.extend(f"- {action}" for action in self.recommended_actions)
        return "\n".join(lines)


# ── Data Quirks (SME) ───────────────────────────────────────────────────────


class DataQuirk(ArtifactBase):
    """A known data limitation or oddity that affects analytical results."""

    kind: ArtifactKind = ArtifactKind.DATA_QUIRK
    data_source: str = ""
    quirk_description: str = ""
    impact_severity: str = "medium"  # low | medium | high | critical
    affects_metrics: list[str] = Field(default_factory=list)
    affects_therapy_areas: list[str] = Field(default_factory=list)
    workaround: str = ""
    validation_query: str = ""
    cross_reference: str = ""
    known_since: str = ""
    expected_fix: str | None = None
    seasonal: bool = False
    seasonal_pattern: str = ""

    def to_prompt_text(self) -> str:
        lines: list[str] = [f"## Data Quirk: {self.name}"]
        if self.data_source:
            lines.append(f"\n**Data Source:** {self.data_source}")
        if self.quirk_description:
            lines.append(f"**Issue:** {self.quirk_description}")
        lines.append(f"**Severity:** {self.impact_severity.upper()}")
        if self.affects_metrics:
            lines.append(f"**Affects Metrics:** {', '.join(self.affects_metrics)}")
        if self.affects_therapy_areas:
            lines.append(f"**Affects Therapy Areas:** {', '.join(self.affects_therapy_areas)}")
        if self.workaround:
            lines.append(f"\n**Workaround:** {self.workaround}")
        if self.cross_reference:
            lines.append(f"**Cross-Reference:** {self.cross_reference}")
        if self.seasonal:
            lines.append(f"\n**Seasonal Pattern:** {self.seasonal_pattern}")
        if self.validation_query:
            lines.append(f"\n**Validation Query:** `{self.validation_query}`")
        return "\n".join(lines)


# ── Process Playbooks (SME) ─────────────────────────────────────────────────


class PlaybookStep(BaseModel):
    """A single step in an analytical playbook."""

    order: int
    action: str
    inputs: list[str] = Field(default_factory=list)
    outputs: list[str] = Field(default_factory=list)
    quality_check: str = ""
    decision_point: str = ""
    estimated_minutes: int = 0
    tools: list[str] = Field(default_factory=list)
    common_mistake: str = ""


class ProcessPlaybook(ArtifactBase):
    """A step-by-step analytical workflow codified from SME expertise."""

    kind: ArtifactKind = ArtifactKind.PROCESS_PLAYBOOK
    task_type: str = ""
    description: str = ""
    steps: list[PlaybookStep] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    required_data_sources: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    estimated_total_minutes: int = 0
    common_pitfalls: list[str] = Field(default_factory=list)
    quality_criteria: list[str] = Field(default_factory=list)
    scope: dict[str, str] = Field(default_factory=dict)

    def to_prompt_text(self) -> str:
        lines: list[str] = [f"## Process Playbook: {self.name}"]
        if self.description:
            lines.append(f"\n{self.description}")
        if self.task_type:
            lines.append(f"\n**Task Type:** {self.task_type}")
        if self.prerequisites:
            lines.append("\n### Prerequisites")
            lines.extend(f"- {p}" for p in self.prerequisites)
        if self.required_data_sources:
            lines.append(f"\n**Data Sources:** {', '.join(self.required_data_sources)}")
        if self.required_tools:
            lines.append(f"**Tools:** {', '.join(self.required_tools)}")
        if self.steps:
            lines.append("\n### Steps")
            for step in sorted(self.steps, key=lambda s: s.order):
                lines.append(f"\n**Step {step.order}: {step.action}**")
                if step.inputs:
                    lines.append(f"  Inputs: {', '.join(step.inputs)}")
                if step.outputs:
                    lines.append(f"  Outputs: {', '.join(step.outputs)}")
                if step.quality_check:
                    lines.append(f"  Quality Check: {step.quality_check}")
                if step.decision_point:
                    lines.append(f"  Decision: {step.decision_point}")
                if step.common_mistake:
                    lines.append(f"  WARNING: {step.common_mistake}")
                if step.tools:
                    lines.append(f"  Tools: {', '.join(step.tools)}")
                if step.estimated_minutes:
                    lines.append(f"  Est. Time: {step.estimated_minutes} min")
        if self.estimated_total_minutes:
            lines.append(f"\n**Total Estimated Time:** {self.estimated_total_minutes} min")
        if self.common_pitfalls:
            lines.append("\n### Common Pitfalls")
            lines.extend(f"- {p}" for p in self.common_pitfalls)
        if self.quality_criteria:
            lines.append("\n### Quality Criteria")
            lines.extend(f"- {c}" for c in self.quality_criteria)
        return "\n".join(lines)


# ── Judgment artifacts (servable shapes of src/core/models.py) ──────────────


class DriverAttribution(BaseModel):
    """A potential driver with prior confidence and the evidence it needs."""

    driver: str
    prior_confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence_required: list[str] = Field(default_factory=list)


class JudgmentPattern(ArtifactBase):
    """A reusable judgment abstraction — when these signals fire, these drivers."""

    kind: ArtifactKind = ArtifactKind.JUDGMENT_PATTERN
    applies_when_signals: list[str] = Field(default_factory=list)
    applies_when_context: list[str] = Field(default_factory=list)
    typical_drivers: list[DriverAttribution] = Field(default_factory=list)
    disallowed_drivers: list[str] = Field(default_factory=list)
    judgment_type: str = "causal_hypothesis"  # empirical | causal_hypothesis | normative

    def to_prompt_text(self) -> str:
        lines: list[str] = [f"## Judgment Pattern: {self.name}"]
        if self.applies_when_signals:
            lines.append(f"\n**Applies when signals:** {', '.join(self.applies_when_signals)}")
        if self.applies_when_context:
            lines.append(f"**Context:** {', '.join(self.applies_when_context)}")
        lines.append(f"**Judgment Type:** {self.judgment_type}")
        if self.typical_drivers:
            lines.append("\n### Typical Drivers")
            for d in self.typical_drivers:
                ev = f" (needs: {', '.join(d.evidence_required)})" if d.evidence_required else ""
                lines.append(f"- {d.driver} [prior {d.prior_confidence}]{ev}")
        if self.disallowed_drivers:
            lines.append(f"\n**Disallowed Drivers:** {', '.join(self.disallowed_drivers)}")
        return "\n".join(lines)


class Guardrail(ArtifactBase):
    """Explicit normative constraint: what NOT to do (always-included safety layer)."""

    kind: ArtifactKind = ArtifactKind.GUARDRAIL
    blocks_action_types: list[str] = Field(default_factory=list)
    blocks_drivers: list[str] = Field(default_factory=list)
    unless_evidence: list[str] = Field(default_factory=list)
    unless_approver_role: list[str] = Field(default_factory=list)
    applies_to_personas: list[str] = Field(default_factory=list)
    excludes_personas: list[str] = Field(default_factory=list)

    def to_prompt_text(self) -> str:
        lines: list[str] = [f"## Guardrail: {self.name}"]
        if self.blocks_drivers:
            lines.append(f"- **DO NOT conclude:** {', '.join(self.blocks_drivers)}")
        if self.blocks_action_types:
            lines.append(f"- **DO NOT take actions:** {', '.join(self.blocks_action_types)}")
        if self.unless_evidence:
            lines.append(f"  UNLESS evidence: {', '.join(self.unless_evidence)}")
        if self.unless_approver_role:
            lines.append(f"  UNLESS approved by: {', '.join(self.unless_approver_role)}")
        return "\n".join(lines)


class FunctionAction(BaseModel):
    """A specific action for a specific function."""

    action: str
    priority: str = "medium"  # low | medium | high
    conditions: list[str] = Field(default_factory=list)


class ActionTemplate(ArtifactBase):
    """Cross-functional action recommendations triggered by a judgment pattern."""

    kind: ArtifactKind = ArtifactKind.ACTION_TEMPLATE
    trigger_pattern_id: str = ""
    brand_actions: list[FunctionAction] = Field(default_factory=list)
    field_actions: list[FunctionAction] = Field(default_factory=list)
    access_actions: list[FunctionAction] = Field(default_factory=list)
    medical_actions: list[FunctionAction] = Field(default_factory=list)
    expected_impact_metric: str = ""
    expected_impact_timeframe: str = ""
    expected_impact_confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    def get_actions_for_function(self, function: str) -> list[FunctionAction]:
        mapping = {
            "brand": self.brand_actions,
            "field": self.field_actions,
            "access": self.access_actions,
            "medical": self.medical_actions,
        }
        return mapping.get(function.lower(), [])

    def to_prompt_text(self) -> str:
        lines: list[str] = [f"## Action Template: {self.name}"]
        for function in ("brand", "field", "access", "medical"):
            actions = self.get_actions_for_function(function)
            if actions:
                lines.append(f"\n### {function.title()}")
                for a in actions:
                    cond = f" (if {', '.join(a.conditions)})" if a.conditions else ""
                    lines.append(f"- [{a.priority}] {a.action}{cond}")
        if self.expected_impact_metric:
            lines.append(
                f"\n**Expected impact:** {self.expected_impact_metric} "
                f"({self.expected_impact_timeframe}, conf {self.expected_impact_confidence})"
            )
        return "\n".join(lines)


# ── Registry: complete the catalogue (the 6 new types are already registered) ─
ARTIFACT_MODELS.update(
    {
        ArtifactKind.INSTRUCTION_SET: InstructionSet,
        ArtifactKind.TAXONOMY: Taxonomy,
        ArtifactKind.JARGON_MAP: JargonMap,
        ArtifactKind.ENTITY_REGISTRY: EntityRegistry,
        ArtifactKind.FEWSHOT_LIBRARY: FewShotLibrary,
        ArtifactKind.OVERRIDE_RULE: OverrideRule,
        ArtifactKind.PROMPT_TEMPLATE: PromptTemplate,
        ArtifactKind.DECISION_HEURISTIC: DecisionHeuristic,
        ArtifactKind.DATA_QUIRK: DataQuirk,
        ArtifactKind.PROCESS_PLAYBOOK: ProcessPlaybook,
        ArtifactKind.JUDGMENT_PATTERN: JudgmentPattern,
        ArtifactKind.GUARDRAIL: Guardrail,
        ArtifactKind.ACTION_TEMPLATE: ActionTemplate,
    }
)
