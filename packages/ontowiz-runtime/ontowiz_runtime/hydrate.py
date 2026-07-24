"""F0.10 — governed hydration: the hydratable set IS the advertised directory.

The L3 directory tells an agent to call ``ctx/hydrate(section=NAME)``. Until this
module existed, the only thing that could answer was CTX's own hydrate server,
which reads a ``.ctx`` **file path** — the ungated document — so the governance
gate was bypassed, and a request for a gated-out section returned an empty
*success* rather than a refusal (``hydrate_by_name`` drops names it cannot match).

Here, hydration reads only ``ContextResult.eligible_doc``: the same gated
projection the directory was built from. Eligibility is therefore computed once
and shared, not re-derived — the two cannot drift apart.

Tier rule: ontowiz_spec / ontowiz_ctx only (Tier A). Never Tier B.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ontowiz_ctx.core.hydrator import hydrate_by_name
from ontowiz_ctx.core.model import CTXDocument, Section
from ontowiz_ctx.core.serializer import serialize_section
from ontowiz_spec import ArtifactBase, Tag

from .context import ContextResult, TrustEnvelope, context_for_pack, get_context
from .registry import LoadedPack


class SectionNotServableError(LookupError):
    """A requested section is not in the gated directory for this request.

    Deliberately **one** error for three different causes — gated out by tag,
    gated out by lifecycle, or never existed. Distinguishing them would turn the
    hydrate door into an existence oracle for DRAFT/REVIEW content, which is
    precisely what the lifecycle gate withholds. The message repeats only the
    name the caller supplied and the sections it was already shown.
    """

    def __init__(self, section: str, servable: list[str]) -> None:
        self.section = section
        self.servable = list(servable)
        listed = ", ".join(self.servable) if self.servable else "(none)"
        super().__init__(f"section not servable: {section!r}. Servable sections: {listed}")


@dataclass
class HydrationPayload:
    """What a consumer gets back from a hydrate call."""

    text: str = ""
    sections: list[str] = field(default_factory=list)
    sections_matched: int = 0
    sections_available: int = 0
    trust: TrustEnvelope = field(default_factory=TrustEnvelope)
    tokens_estimate: int = 0


def servable_sections(result: ContextResult) -> list[str]:
    """The section names this result's agent may hydrate, in directory order."""
    doc = result.eligible_doc
    if doc is None:
        return []
    return [e.name for e in doc.body if isinstance(e, Section)]


def _clean(sections: list[str]) -> list[str]:
    names = [s.strip() for s in sections if s and s.strip()]
    if not names:
        raise ValueError("at least one section name is required")
    return names


def hydrate_from_result(result: ContextResult, sections: list[str]) -> HydrationPayload:
    """Hydrate from an already-gated ContextResult. Fail-closed, all-or-nothing.

    Every requested name is checked against the gated directory *before* anything
    is read. One non-servable name refuses the whole request: serving the good half
    of a batch is how the original silent-empty defect read to a caller.
    """
    names = _clean(sections)
    servable = servable_sections(result)
    index = {n.upper() for n in servable}
    for name in names:
        if name.upper() not in index:
            raise SectionNotServableError(name, servable)

    doc: CTXDocument = result.eligible_doc  # non-None: servable was non-empty
    hydrated = hydrate_by_name(doc, names, include_header=False)
    text = "\n".join("\n".join(serialize_section(s)) for s in hydrated.sections)
    return HydrationPayload(
        text=text,
        sections=[s.name for s in hydrated.sections],
        sections_matched=len(hydrated.sections),
        sections_available=hydrated.sections_available,
        trust=result.trust,
        tokens_estimate=hydrated.tokens_injected,
    )


def hydrate_sections(
    query: str,
    *,
    doc: CTXDocument,
    sections: list[str],
    agent_type: str = "general",
    artifacts: list[ArtifactBase] | None = None,
    tags: list[Tag] | None = None,
    pack: str = "",
    dev_mode: bool = False,
) -> HydrationPayload:
    """Gate, then hydrate — the document-level entry point (mirrors get_context)."""
    names = _clean(sections)
    result = get_context(
        query, doc=doc, agent_type=agent_type, artifacts=artifacts,
        tags=tags, pack=pack, dev_mode=dev_mode,
    )
    return hydrate_from_result(result, names)


def hydrate_for_pack(
    query: str,
    pack: LoadedPack,
    sections: list[str],
    *,
    agent_type: str = "general",
    tags: list[Tag] | None = None,
    dev_mode: bool = False,
) -> HydrationPayload:
    """Gate, then hydrate a loaded Domain Pack (mirrors context_for_pack).

    The entry point both serve doors wrap. The returned trust envelope is the
    *same* envelope the matching ``/v1/context`` call produced, so a hydrated
    answer is exactly as attributable as the directory that led to it.
    """
    names = _clean(sections)
    result = context_for_pack(
        query, pack, agent_type=agent_type, tags=tags, dev_mode=dev_mode
    )
    return hydrate_from_result(result, names)
