"""Artifact lifecycle states and governance transition records.

These are the *shapes* of governance, shared by every package. The *logic* of
governance (who may transition, blast radius, HITL routing) lives in Tier B
(`ontowiz_core`). A Tier A consumer can read lifecycle state but never drive a
transition except through a governed Delta.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel


class Lifecycle(str, Enum):
    """The lifecycle of a knowledge artifact.

    Nothing reaches an agent below ACTIVE in production. The runtime context
    gate (Tier A) admits only ACTIVE (+ VERIFIED in strict mode).
    """

    DRAFT = "draft"          # freshly extracted candidate; never served
    REVIEW = "review"        # in an SME/curator queue
    VERIFIED = "verified"    # SME-confirmed, not yet promoted
    ACTIVE = "active"        # live; servable to agents
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


# States a production context assembly is allowed to serve.
SERVABLE_STATES: frozenset[Lifecycle] = frozenset({Lifecycle.ACTIVE})
# States a dev/preview context assembly may serve.
SERVABLE_STATES_DEV: frozenset[Lifecycle] = frozenset(
    {Lifecycle.ACTIVE, Lifecycle.VERIFIED, Lifecycle.REVIEW}
)


class LifecycleTransition(BaseModel):
    """One immutable entry in an artifact's audit trail."""

    from_state: Lifecycle | None = None
    to_state: Lifecycle
    changed_by: str
    reason: str = ""
    # The governed Delta that caused this transition, if any. Tier A reads it;
    # Tier B writes it. A transition with no delta_id is a system/seed event.
    delta_id: str | None = None
    at: str | None = None  # ISO-8601 timestamp, stamped by the writer
