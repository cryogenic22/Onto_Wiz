"""F0.10 — gated hydration: the hydratable set IS the advertised directory.

Red tests for `hydrate_sections` / `hydrate_for_pack`. The defect these encode:
`hydrate_by_name` (ontowiz-ctx) silently drops names it cannot match, so asking the
system for knowledge it deliberately gated returned an empty *success*. Every case
below asserts a fail-closed refusal instead.
"""

from __future__ import annotations

import pytest
from ontowiz_ctx.core.model import CTXDocument, Header, KeyValue, Layer, Section
from ontowiz_runtime import (
    HydrationPayload,
    SectionNotServableError,
    get_context,
    hydrate_sections,
    servable_sections,
)
from ontowiz_spec import EvalCase, Lifecycle, Tag, TagDimension

COMMERCIAL = [Tag(dimension=TagDimension.ANALYTICS_DOMAIN, value="commercial")]


def _doc() -> CTXDocument:
    """Three ID-bearing sections so the gate can actually include/exclude them."""
    return CTXDocument(
        header=Header(magic="§CTX", version="1.0", layer=Layer.L2),
        body=(
            Section(name="DH-KEEP", children=(
                KeyValue(key="ID", value="keep"),
                KeyValue(key="BODY", value="rebate pressure explains the share loss"),
            )),
            Section(name="DH-DROP", children=(
                KeyValue(key="ID", value="drop"),
                KeyValue(key="BODY", value="manufacturing yield drift"),
            )),
            Section(name="DH-DRAFT", children=(
                KeyValue(key="ID", value="unapproved"),
                KeyValue(key="BODY", value="ungoverned speculation"),
            )),
        ),
    )


def _artifact(id_: str, state: Lifecycle, domain: str = "commercial") -> EvalCase:
    ec = EvalCase(
        id=id_, name=id_, question="q",
        tags=[Tag(dimension=TagDimension.ANALYTICS_DOMAIN, value=domain)],
    )
    if state == Lifecycle.DRAFT:
        return ec
    delta = "d" if state in (Lifecycle.ACTIVE, Lifecycle.VERIFIED) else None
    return ec.transition(state, changed_by="c", delta_id=delta)


def _arts() -> list[EvalCase]:
    return [
        _artifact("keep", Lifecycle.ACTIVE, domain="commercial"),
        _artifact("drop", Lifecycle.ACTIVE, domain="manufacturing"),
        _artifact("unapproved", Lifecycle.DRAFT, domain="commercial"),
    ]


def _hydrate(sections: list[str], **kw):
    return hydrate_sections(
        "why did we lose share?",
        doc=_doc(),
        sections=sections,
        artifacts=_arts(),
        tags=COMMERCIAL,
        pack="commercial_analytics@0.1",
        **kw,
    )


# ── the happy path ───────────────────────────────────────────────────────────


def test_hydrate_returns_gated_section_body():
    payload = _hydrate(["DH-KEEP"])
    assert isinstance(payload, HydrationPayload)
    assert payload.sections_matched == 1
    # the governed content itself came back, not just the section header
    assert "rebate pressure explains the share loss" in payload.text


def test_section_names_are_case_insensitive():
    # matches hydrate_by_name's existing contract (index keyed on .upper())
    assert _hydrate(["dh-keep"]).sections_matched == 1


def test_servable_sections_matches_the_advertised_directory():
    res = get_context("q", doc=_doc(), artifacts=_arts(), tags=COMMERCIAL,
                      pack="commercial_analytics@0.1")
    names = servable_sections(res)
    assert "DH-KEEP" in names
    # the gated-out and ungoverned sections are in neither the directory nor the set
    assert "DH-DROP" not in names and "DH-DRAFT" not in names
    for name in names:
        assert name in res.system_prompt


# ── fail-closed refusals ─────────────────────────────────────────────────────


def test_hydrate_refuses_tag_gated_section():
    # DH-DROP exists in the document but the tag gate excluded it
    with pytest.raises(SectionNotServableError):
        _hydrate(["DH-DROP"])


def test_hydrate_refuses_non_servable_lifecycle():
    # DH-DRAFT's artifact is DRAFT — never servable, even though it is in-domain
    with pytest.raises(SectionNotServableError):
        _hydrate(["DH-DRAFT"])


def test_hydrate_refuses_unknown_section():
    with pytest.raises(SectionNotServableError):
        _hydrate(["DH-NEVER-EXISTED"])


def test_unknown_and_gated_sections_are_indistinguishable():
    """The refusal must not be an existence oracle for gated artifacts.

    If a gated-out section refused differently from a nonexistent one, any caller
    could enumerate the pack's DRAFT/REVIEW content by diffing error messages —
    exactly what the lifecycle gate exists to prevent.
    """
    with pytest.raises(SectionNotServableError) as gated:
        _hydrate(["DH-DROP"])
    with pytest.raises(SectionNotServableError) as unknown:
        _hydrate(["DH-DROP-XYZ"])

    gated_msg = str(gated.value).replace("DH-DROP", "<N>")
    unknown_msg = str(unknown.value).replace("DH-DROP-XYZ", "<N>")
    assert gated_msg == unknown_msg


def test_partial_batch_refuses_whole_request():
    # all-or-nothing: silently serving the good half is how the original defect read
    with pytest.raises(SectionNotServableError):
        _hydrate(["DH-KEEP", "DH-DROP"])


def test_empty_section_list_is_rejected():
    with pytest.raises(ValueError):
        _hydrate([])


def test_refusal_message_leaks_nothing():
    with pytest.raises(SectionNotServableError) as err:
        _hydrate(["DH-DROP"])
    msg = str(err.value)
    # names a gated *sibling* it was never asked about → an enumeration leak
    assert "DH-DRAFT" not in msg
    # no artifact ids of gated content, no filesystem paths, no traceback
    assert "unapproved" not in msg
    assert "\\" not in msg and "/" not in msg.replace("ctx/hydrate", "")
    # the servable set (which the caller already holds) may be echoed
    assert "DH-KEEP" in msg


# ── trust parity ─────────────────────────────────────────────────────────────


def test_hydrate_trust_matches_context_trust():
    """A hydrate response is as attributable as the context response that led to it."""
    res = get_context("why did we lose share?", doc=_doc(), artifacts=_arts(),
                      tags=COMMERCIAL, pack="commercial_analytics@0.1")
    payload = _hydrate(["DH-KEEP"])
    assert payload.trust == res.trust
    assert payload.trust.pack == "commercial_analytics@0.1"
    assert payload.trust.backing_deltas == ["d"]


def test_result_without_a_gated_doc_serves_nothing():
    """Fail closed by default: no gated projection means nothing is hydratable.

    A ContextResult that never went through the gate carries no `eligible_doc`.
    That must refuse, not fall back to some ungated document.
    """
    from ontowiz_runtime import ContextResult, hydrate_from_result

    bare = ContextResult(query="q", agent_type="general")
    assert servable_sections(bare) == []
    with pytest.raises(SectionNotServableError):
        hydrate_from_result(bare, ["DH-KEEP"])


def test_dev_mode_widens_the_servable_set_but_not_past_draft():
    res = get_context("q", doc=_doc(), artifacts=_arts(), tags=COMMERCIAL, dev_mode=True)
    # DRAFT is never servable, in any mode
    assert "DH-DRAFT" not in servable_sections(res)
    with pytest.raises(SectionNotServableError):
        _hydrate(["DH-DRAFT"], dev_mode=True)
