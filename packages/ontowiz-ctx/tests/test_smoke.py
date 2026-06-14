"""Smoke tests for the vendored CTX engine.

We do not hold vendored code to our coverage bar, but we DO lock that the engine
imports and that the round-trip + hydration paths we depend on still work after
the ctxpack -> ontowiz_ctx rename.
"""

from __future__ import annotations

from ontowiz_ctx.core.hydration_protocol import build_system_prompt
from ontowiz_ctx.core.hydrator import hydrate_by_name
from ontowiz_ctx.core.model import CTXDocument, Header, KeyValue, Layer, Section
from ontowiz_ctx.core.parser import parse
from ontowiz_ctx.core.serializer import serialize


def _doc() -> CTXDocument:
    return CTXDocument(
        header=Header(magic="§CTX", version="1.0", layer=Layer.L2),
        body=(
            Section(name="ENTITY-CUSTOMER",
                    children=(KeyValue(key="IDENTIFIER", value="C-1"),
                              KeyValue(key="TIER", value="gold"))),
        ),
    )


def test_serialize_parse_roundtrip():
    text = serialize(_doc())
    reparsed = parse(text, level=2)
    names = [s.name for s in reparsed.body if isinstance(s, Section)]
    assert "ENTITY-CUSTOMER" in names


def test_build_system_prompt_lists_entities_and_hydration():
    prompt = build_system_prompt(_doc())
    assert "ENTITY-CUSTOMER" in prompt
    assert "ctx/hydrate" in prompt


def test_hydrate_by_name_returns_section():
    result = hydrate_by_name(_doc(), ["ENTITY-CUSTOMER"])
    assert result.sections
    assert result.sections[0].name == "ENTITY-CUSTOMER"
