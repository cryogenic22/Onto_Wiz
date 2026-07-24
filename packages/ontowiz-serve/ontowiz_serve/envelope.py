"""F0.10 — one response shaper, so the two doors cannot drift apart.

The MCP door hand-rolled its own trust block and quietly omitted ``artifacts_used``
and ``backing_deltas``, which the REST door emitted: the same governed answer was
less attributable depending on which door you came through. Both doors now call
these functions, and a parity test asserts the two shapes are byte-identical.

Tier A: ontowiz_runtime only.
"""

from __future__ import annotations

from ontowiz_runtime import ContextResult, HydrationPayload, TrustEnvelope


def trust_payload(trust: TrustEnvelope) -> dict:
    """Serialise the trust envelope. The one definition of "provenance shipped"."""
    return {
        "pack": trust.pack,
        "confidence": trust.confidence,
        "lifecycle_floor": trust.lifecycle_floor,
        "artifacts_used": trust.artifacts_used,
        "backing_deltas": trust.backing_deltas,
    }


def context_payload(r: ContextResult) -> dict:
    """Serialise a ContextResult to the context response shape (both doors)."""
    return {
        "query": r.query,
        "agent_type": r.agent_type,
        "system_prompt": r.system_prompt,
        "eligible": [a.id for a in r.eligible],
        "trust": trust_payload(r.trust),
        "tokens_estimate": r.tokens_estimate,
    }


def hydration_payload(p: HydrationPayload) -> dict:
    """Serialise a HydrationPayload to the hydrate response shape (both doors)."""
    return {
        "text": p.text,
        "sections": p.sections,
        "sections_matched": p.sections_matched,
        "sections_available": p.sections_available,
        "trust": trust_payload(p.trust),
        "tokens_estimate": p.tokens_estimate,
    }
