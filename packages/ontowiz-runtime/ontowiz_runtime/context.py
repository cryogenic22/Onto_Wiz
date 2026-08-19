"""The context pipeline — the one function every consumer ultimately calls.

This is the Tier A seam that fuses governance-gated relevance (deterministic)
with CTX's LLM-as-router hydration (cost-efficient). F0 wires the shape and the
dependencies end to end; the pack-loading and tag-scoring internals are filled
in at F2 when the compiler produces real packs.

    query + agent_type + pinned pack(s) + budget
        → ① governance + relevance gate   (here, deterministic)
        → ② CTX L3 directory              (ontowiz_ctx.hydration_protocol)
        → ③ LLM-as-router hydration       (ontowiz_ctx.hydrator — agent-driven)
        → ④ trust envelope                (here)

Tier rule: this module may import ontowiz_spec and ontowiz_ctx (Tier A) only.
It must never import ontowiz_core or ontowiz_factory (Tier B).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ontowiz_ctx.core.hydration_protocol import build_system_prompt

# Tier A dependencies only.
from ontowiz_ctx.core.model import CTXDocument, KeyValue, Section
from ontowiz_spec import (
    ALWAYS_INCLUDED_KINDS,
    SERVABLE_STATES,
    SERVABLE_STATES_DEV,
    ArtifactBase,
    Lifecycle,
    Tag,
    TagDimension,
)

from .registry import LoadedPack


@dataclass
class TrustEnvelope:
    """Provenance shipped with every context package (aura pattern)."""

    pack: str = ""               # "name@version"
    artifacts_used: list[str] = field(default_factory=list)
    confidence: float = 0.0
    backing_deltas: list[str] = field(default_factory=list)
    lifecycle_floor: str = Lifecycle.ACTIVE.value


@dataclass
class ContextResult:
    """What a consumer gets back from get_context()."""

    query: str
    agent_type: str
    # The ultra-lean L3 directory for the system prompt (CTX, ~<500 tokens).
    system_prompt: str = ""
    # The eligible artifacts after the governance + relevance gate.
    eligible: list[ArtifactBase] = field(default_factory=list)
    trust: TrustEnvelope = field(default_factory=TrustEnvelope)
    tokens_estimate: int = 0
    # The document the directory was built from — the gated projection, and the
    # only thing hydration is allowed to read. Carried so the hydrate door cannot
    # re-derive eligibility and drift from what was advertised.
    eligible_doc: CTXDocument | None = None


def gate(
    artifacts: list[ArtifactBase],
    *,
    tags: list[Tag] | None = None,
    dev_mode: bool = False,
) -> list[ArtifactBase]:
    """① The governance + relevance gate.

    Admits only servable-lifecycle artifacts, then narrows by tag relevance.
    Runs *before* anything is offered to the agent — a non-servable artifact is
    never even listed in the L3 directory, so governance cannot be bypassed
    downstream.

    Safety layers (``ALWAYS_INCLUDED_KINDS``) are exempt from the *tag* narrowing:
    a guardrail that disappears exactly when the caller asks for a narrower slice
    is the worst failure mode of slicing. They stay fully subject to the lifecycle
    filter — an unapproved guardrail is still not servable. The exemption is safe
    because ``gate`` only ever sees one loaded pack's artifacts; revisit it when
    multi-pack composition lands (E4-be).
    """
    servable = SERVABLE_STATES_DEV if dev_mode else SERVABLE_STATES
    eligible = [a for a in artifacts if a.lifecycle in servable]

    if tags:
        wanted = {t.key() for t in tags}
        scored: list[ArtifactBase] = []
        for a in eligible:
            if a.kind in ALWAYS_INCLUDED_KINDS:
                scored.append(a)
                continue
            have = {t.key() for t in a.tags}
            if not wanted or (have & wanted):
                scored.append(a)
        eligible = scored
    return eligible


def _rank_by_query(artifacts: list[ArtifactBase], query: str) -> list[ArtifactBase]:
    """Stable-sort eligible artifacts by query-term overlap (most relevant first).

    A light lexical signal so the directory is query-sensitive; the agent (the
    LLM-as-router) still decides what to actually hydrate. With no query terms the
    original gated order is preserved.
    """
    terms = {t for t in re.findall(r"\w+", query.lower()) if len(t) > 2}
    if not terms:
        return artifacts

    def score(a: ArtifactBase) -> int:
        text = f"{a.name} {a.to_prompt_text()}".lower()
        return sum(1 for t in terms if t in text)

    return sorted(artifacts, key=score, reverse=True)


def _section_id(section: Section) -> str | None:
    for child in section.children:
        if isinstance(child, KeyValue) and child.key.upper() == "ID":
            return str(child.value)
    return None


def _restrict_doc(doc: CTXDocument, eligible_ids: list[str]) -> CTXDocument:
    """Project the doc onto the gated set, in the gated (query-ranked) order.

    The directory the agent is shown is derived from the *same* set as the gate —
    a gated-out artifact is never listed — and artifact sections are emitted in
    the ranked order so the most query-relevant lead. Non-artifact / ID-less
    sections are preserved up front in their original order.
    """
    order = {sid: i for i, sid in enumerate(eligible_ids)}
    eligible_set = set(eligible_ids)
    others: list[object] = []
    sections: list[Section] = []
    for elem in doc.body:
        if not isinstance(elem, Section):
            others.append(elem)
            continue
        sid = _section_id(elem)
        if sid is None:
            others.append(elem)  # not a gated artifact — keep
        elif sid in eligible_set:
            sections.append(elem)
    sections.sort(key=lambda s: order.get(_section_id(s) or "", 0))
    return CTXDocument(header=doc.header, body=(*others, *sections), source_text=doc.source_text)


def _trust_for(eligible: list[ArtifactBase], pack: str, dev_mode: bool) -> TrustEnvelope:
    """Build the trust envelope from the gated artifacts (confidence + provenance)."""
    confidence = sum(a.confidence for a in eligible) / len(eligible) if eligible else 0.0
    backing = [
        a.lifecycle_history[-1].delta_id
        for a in eligible
        if a.lifecycle_history and a.lifecycle_history[-1].delta_id
    ]
    return TrustEnvelope(
        pack=pack,
        artifacts_used=[a.id for a in eligible],
        confidence=round(confidence, 3),
        backing_deltas=backing,
        lifecycle_floor=(Lifecycle.VERIFIED if dev_mode else Lifecycle.ACTIVE).value,
    )


def get_context(
    query: str,
    *,
    doc: CTXDocument,
    agent_type: str = "general",
    artifacts: list[ArtifactBase] | None = None,
    tags: list[Tag] | None = None,
    pack: str = "",
    dev_mode: bool = False,
) -> ContextResult:
    """Run the full context pipeline for a single query.

    Governance-gates the artifacts, ranks the eligible set by query relevance,
    builds the CTX L3 directory from that set, and returns it with a trust
    envelope. This signature is what the library, REST and MCP doors all wrap.
    """
    artifacts = artifacts or []
    # gate (governance + tag/lifecycle), then order by query relevance — the
    # LLM-as-router still makes the final hydration choice
    eligible = _rank_by_query(gate(artifacts, tags=tags, dev_mode=dev_mode), query)

    # the directory is built from the gated set only, so a non-eligible artifact
    # is never listed or hydratable downstream
    eligible_doc = _restrict_doc(doc, [a.id for a in eligible])
    system_prompt = build_system_prompt(eligible_doc)
    trust = _trust_for(eligible, pack, dev_mode)
    return ContextResult(
        query=query,
        agent_type=agent_type,
        system_prompt=system_prompt,
        eligible=eligible,
        trust=trust,
        tokens_estimate=len(system_prompt.split()),
        eligible_doc=eligible_doc,
    )


def context_for_pack(
    query: str,
    pack: LoadedPack,
    *,
    agent_type: str = "general",
    tags: list[Tag] | None = None,
    dev_mode: bool = False,
) -> ContextResult:
    """Run the context pipeline over a loaded Domain Pack.

    The end-to-end entry point an agent uses: pass a pack loaded from the
    registry and a query; get back the governance-gated CTX directory + trust
    envelope stamped with ``name@version``.
    """
    return get_context(
        query,
        doc=pack.l2_doc,
        agent_type=agent_type,
        artifacts=pack.artifacts,
        tags=tags,
        pack=f"{pack.manifest.name}@{pack.manifest.version}",
        dev_mode=dev_mode,
    )


def context_for_function(
    query: str,
    pack: LoadedPack,
    function: str,
    *,
    agent_type: str = "general",
    dev_mode: bool = False,
) -> ContextResult:
    """Serve a single ``TagDimension.FUNCTION`` slice of a loaded pack.

    The one licensable pack is sub-divided by function (market_access,
    brand_performance, …); this narrows serving to just that slice so a consult
    in one function never sees another's heuristics. Thin sugar over the tag gate
    in ``context_for_pack``.
    """
    return context_for_pack(
        query,
        pack,
        agent_type=agent_type,
        tags=[Tag(dimension=TagDimension.FUNCTION, value=function)],
        dev_mode=dev_mode,
    )
