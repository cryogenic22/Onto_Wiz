"""Reference consumer — an agent using a Domain Pack, end to end (Tier B demo).

This is the *consumption* half of the living loop: an agent answers a query with
the pack wired in (via the faithful CTX router loop), the answer ships with its
trust envelope (provenance + confidence + backing deltas), and the interaction
emits a :class:`UsageEvent` — the telemetry that feeds the steward/feedback loops.

The "was the pack actually useful?" signal reuses the CTX router's own
low-confidence detector (``needs_rehydration``): an answer that signals missing
context is recorded as unhelpful, which is exactly the gap that surfaces a Forge
mission. A library/REST/MCP consumer would wrap this same call.
"""

from __future__ import annotations

from dataclasses import dataclass

from ontowiz_ctx.core.hydrator import needs_rehydration
from ontowiz_runtime.context import TrustEnvelope
from ontowiz_runtime.registry import LoadedPack

from .benchmark import ChatAgent, answer_with_pack
from .feedback import UsageEvent


@dataclass
class Consultation:
    """One agent turn over a pack: the answer, its provenance, and the usage signal."""

    query: str
    answer: str
    trust: TrustEnvelope
    usage: UsageEvent


def consult(
    query: str,
    pack: LoadedPack,
    agent: ChatAgent,
    *,
    agent_type: str = "commercial_analyst",
    correction: str = "",
) -> Consultation:
    """Answer a query with the pack, returning the answer + trust + a usage signal.

    ``helpful`` is inferred from the answer (a low-confidence / "not found" answer
    is unhelpful) unless the caller supplies a ``correction``, which always marks
    the turn unhelpful and carries the fix into the feedback loop. The usage event
    is attributed to the top-ranked eligible artifact (the one the router led with).
    """
    answer, ctx = answer_with_pack(query, pack, agent, agent_type=agent_type)
    artifact_id = ctx.eligible[0].id if ctx.eligible else ""
    helpful = bool(answer) and not needs_rehydration(answer) and not correction
    usage = UsageEvent(
        artifact_id=artifact_id, helpful=helpful, correction=correction, query=query
    )
    return Consultation(query=query, answer=answer, trust=ctx.trust, usage=usage)
