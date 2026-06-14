"""Seed importer — turn ontology/commercial.yaml into governed artifacts + a pack.

The first real Domain Pack: the existing commercial ontology (entities +
inference rules) becomes an EntityRegistry and a set of DecisionHeuristics,
activated as system seed events, then compiled into commercial_analytics.

Tier B (factory).
"""

from __future__ import annotations

from pathlib import Path

import yaml
from ontowiz_core.bridge import apply_delta, propose_transition
from ontowiz_core.models import DeltaStatus
from ontowiz_spec import (
    ArtifactBase,
    DecisionHeuristic,
    EntityRecord,
    EntityRegistry,
    HeuristicAntiPattern,
    Lifecycle,
    Tag,
    TagDimension,
    TriggerCondition,
)

from .compiler import CompiledPack, compile_pack, write_pack

_COMMERCIAL_TAG = Tag(dimension=TagDimension.ANALYTICS_DOMAIN, value="commercial")
# The entity registry is shared infrastructure — it belongs to the base function.
_BASE_FUNCTION_TAG = Tag(dimension=TagDimension.FUNCTION, value="base")

# Adjacency anti-patterns: several governed heuristics share conditions (e.g.
# pathway-exclusion and guideline-shift both key on Clinical:Guideline) and a
# consuming agent conflates them. We give each one an explicit "what this is NOT"
# so the pack discriminates the pair instead of leaving it to the model. Keyed by
# rule id; each entry seeds a HeuristicAntiPattern into the heuristic content.
_ANTI_PATTERNS: dict[str, HeuristicAntiPattern] = {
    "rule_pathway_exclusion": HeuristicAntiPattern(
        wrong_conclusion="An external clinical-guideline (NCCN/ESMO) shift",
        why_wrong="This is an INSTITUTIONAL pathway-committee deprioritization at "
        "specific centers — not a national guideline-body update. The governed "
        "label is pathway exclusion, not guideline shift.",
    ),
    "rule_guideline_driven_shift": HeuristicAntiPattern(
        wrong_conclusion="A single institution's pathway-committee decision",
        why_wrong="This is a national guideline body (NCCN/ESMO) changing standard "
        "of care across institutions at once — not one center's pathway exclusion.",
    ),
    "rule_competitor_lockout": HeuristicAntiPattern(
        wrong_conclusion="A genuine budget crisis",
        why_wrong="A pricing rumor plus a budget objection WITHOUT hard financial "
        "evidence is a competitor lockout; the budget claim is a secondary effect, "
        "not a real funding crisis.",
    ),
    "rule_genuine_budget_crisis": HeuristicAntiPattern(
        wrong_conclusion="A competitor lockout or a negotiation tactic",
        why_wrong="HARD financial evidence (audited distress) makes the budget "
        "constraint genuine — not a bargaining lever or a competitor lockout.",
    ),
    "rule_channel_shift": HeuristicAntiPattern(
        wrong_conclusion="A genuine loss of patient demand",
        why_wrong="A dispensing/channel migration is a measurement artifact in the "
        "tracked source — apparent volume loss, not true demand erosion.",
    ),
    "rule_demand_erosion": HeuristicAntiPattern(
        wrong_conclusion="A channel-shift measurement artifact or an access barrier",
        why_wrong="NBRx decline PLUS prescriber/KOL disengagement is a genuine loss "
        "of clinical preference — not a dispensing artifact and not coverage.",
    ),
    "rule_formulary_exclusion": HeuristicAntiPattern(
        wrong_conclusion="A field-execution or sales-force performance problem",
        why_wrong="Volume falling in lockstep across one payer's book after a tier/"
        "formulary action is payer-driven — not local rep execution.",
    ),
    "rule_field_execution_gap": HeuristicAntiPattern(
        wrong_conclusion="A payer/formulary access barrier or market-wide demand loss",
        why_wrong="Underperformance isolated to a territory with a rep vacancy / low "
        "coverage, while neighbors are fine, is a field-execution gap — not payer action.",
    ),
    "rule_safety_signal": HeuristicAntiPattern(
        wrong_conclusion="Competitive pressure or a pricing/commercial cause",
        why_wrong="A volume drop coinciding with clinical safety inquiries is most "
        "likely a SAFETY signal — clinical, not commercial.",
    ),
    "rule_supply_disruption": HeuristicAntiPattern(
        wrong_conclusion="A demand or access problem",
        why_wrong="A volume drop tied to a manufacturing/fill-finish interruption "
        "with no demand-signal change is supply-driven — not demand or access.",
    ),
}


def _seed_active(artifact: ArtifactBase) -> ArtifactBase:
    """Activate a seed artifact via a system-approved Delta (auditable provenance).

    Even bootstrap seeds go through the governance bridge, so every ACTIVE seed
    artifact carries a real ``delta_id`` in its audit trail — indistinguishable
    from an SME-governed promotion, and honouring the transition invariant.
    """
    delta = propose_transition(
        artifact, Lifecycle.ACTIVE, proposed_by="system:seed",
        reason="seed import from commercial.yaml",
    )
    delta.status = DeltaStatus.MERGED  # system bootstrap is auto-approved
    return apply_delta(artifact, delta)


def _relationships_by_source(meta: dict) -> dict[str, list[dict[str, str]]]:
    """Index the ontology relationships by (lowercased) source entity name.

    L5: these were dropped entirely; folding each onto its source entity ships the
    domain's relational structure in the registry.
    """
    out: dict[str, list[dict[str, str]]] = {}
    for r in meta.get("relationships", []):
        out.setdefault(str(r.get("source", "")).lower(), []).append(
            {
                "type": str(r.get("type", "")),
                "target": str(r.get("target", "")),
                "attributes": ", ".join(r.get("attributes", [])),
            }
        )
    return out


def _entity_registry(meta: dict) -> EntityRegistry | None:
    """Build the EntityRegistry (entities + their relationships) from the meta-model."""
    rels = _relationships_by_source(meta)
    entities = [
        EntityRecord(
            id=e["name"].lower(),
            entity_type="commercial",
            name=e["name"],
            attributes={"fields": e.get("attributes", [])},
            relationships=rels.get(e["name"].lower(), []),
        )
        for e in meta.get("entities", [])
    ]
    if not entities:
        return None
    return EntityRegistry(
        id="commercial-entities", name="Commercial Entities",
        entities=entities, tags=[_COMMERCIAL_TAG, _BASE_FUNCTION_TAG],
    )


def _rule_tags(rule: dict, default_function: str | None = None) -> list[Tag]:
    """Relevance tags for a heuristic: the domain, its FUNCTION, and any therapy overlay.

    ``function`` sub-divides the one licensable pack by ``TagDimension.FUNCTION``
    (the slice the runtime can serve in isolation); a module-level default applies
    when a rule does not name its own. ``therapy_area`` is an overlay (e.g.
    oncology), not a function — a rule carries both.
    """
    tags = [_COMMERCIAL_TAG]
    function = rule.get("function") or default_function
    if function:
        tags.append(Tag(dimension=TagDimension.FUNCTION, value=str(function)))
    therapy = rule.get("therapy_area")
    if therapy:
        tags.append(Tag(dimension=TagDimension.THERAPY_AREA, value=str(therapy)))
    return tags


def _heuristic_from_rule(rule: dict, default_function: str | None = None) -> DecisionHeuristic:
    """Map one inference rule to a DecisionHeuristic, preserving its disambiguating
    detail: description (L2), trigger conditions + priority (L4), anti-pattern (L3)."""
    verdict = rule.get("consequence", {}).get("verdict", "")
    logic = rule.get("logic", "")
    description = rule.get("description", "")
    anti = _ANTI_PATTERNS.get(rule["id"])
    signals = [
        TriggerCondition(
            signal_name=str(c.get("name", "")),
            threshold=" | ".join(c.get("args", [])),
            data_source=str(c.get("pattern", "")),
        )
        for c in rule.get("conditions", [])
    ]
    scope = {"priority": str(rule["priority"])} if rule.get("priority") is not None else {}
    return DecisionHeuristic(
        id=rule["id"],
        name=rule["id"].replace("rule_", "").replace("_", " ").title(),
        decision_logic=f"{logic} => {verdict}".strip(" =>"),
        typical_outcome=verdict,
        trigger_context=[description] if description else [],
        trigger_signals=signals,
        anti_patterns=[anti] if anti else [],
        scope=scope,
        confidence=0.8,
        tags=_rule_tags(rule, default_function),
    )


def artifacts_from_commercial(ontology_path: str | Path) -> list[ArtifactBase]:
    """Map the commercial ontology YAML to typed knowledge artifacts."""
    data = yaml.safe_load(Path(ontology_path).read_text(encoding="utf-8"))["ontology"]
    meta = data.get("meta_model", {})
    arts: list[ArtifactBase] = []
    registry = _entity_registry(meta)
    if registry is not None:
        arts.append(registry)
    arts.extend(_heuristic_from_rule(rule) for rule in data.get("inference_rules", []))
    return arts


def _merged_registry(metas: list[dict]) -> EntityRegistry | None:
    """Fold the entities + relationships of several module meta-models into one.

    Entities are de-duplicated by (lowercased) name — the first wins — so modules
    can reference shared base entities without redefining them.
    """
    entities: list[dict] = []
    relationships: list[dict] = []
    seen: set[str] = set()
    for meta in metas:
        for e in meta.get("entities", []):
            key = str(e.get("name", "")).lower()
            if key and key not in seen:
                seen.add(key)
                entities.append(e)
        relationships.extend(meta.get("relationships", []))
    return _entity_registry({"entities": entities, "relationships": relationships})


def artifacts_from_commercial_modules(
    base_path: str | Path, modules_dir: str | Path
) -> list[ArtifactBase]:
    """Read the base ontology plus every ``*.yaml`` module and merge into one set.

    Each module declares its ``function`` once (the default for its rules); a rule
    may still override with its own ``function``. Entities across all files merge
    into a single registry. This is the drop-a-file expansion path.
    """
    base = yaml.safe_load(Path(base_path).read_text(encoding="utf-8"))["ontology"]
    datas: list[dict] = [base]
    defaults: list[str | None] = [None]
    for module_path in sorted(Path(modules_dir).glob("*.yaml")):
        data = yaml.safe_load(module_path.read_text(encoding="utf-8"))["ontology"]
        datas.append(data)
        defaults.append(data.get("function"))

    arts: list[ArtifactBase] = []
    registry = _merged_registry([d.get("meta_model", {}) for d in datas])
    if registry is not None:
        arts.append(registry)
    for data, default_function in zip(datas, defaults, strict=True):
        arts.extend(
            _heuristic_from_rule(rule, default_function)
            for rule in data.get("inference_rules", [])
        )
    return arts


def _read_commercial_artifacts(ontology_path: str | Path) -> list[ArtifactBase]:
    """Single-file or drop-a-file: include a sibling ``<base>/`` module dir if present."""
    base = Path(ontology_path)
    modules_dir = base.with_suffix("")  # ontology/commercial.yaml -> ontology/commercial/
    if modules_dir.is_dir():
        return artifacts_from_commercial_modules(base, modules_dir)
    return artifacts_from_commercial(base)


def build_commercial_pack(
    ontology_path: str | Path, dest_root: str | Path, *, version: str = "0.1.0"
) -> Path:
    """Compile and write the commercial_analytics pack from the ontology YAML.

    If a sibling ``<base>/`` directory exists (e.g. ``ontology/commercial/``), its
    function modules are merged in automatically (drop-a-file expansion).
    """
    active = [_seed_active(a) for a in _read_commercial_artifacts(ontology_path)]
    pack: CompiledPack = compile_pack(
        active,
        name="commercial_analytics",
        version=version,
        domain="commercial",
        description="Commercial pharma base pack, seeded from commercial.yaml",
    )
    return write_pack(pack, dest_root)
