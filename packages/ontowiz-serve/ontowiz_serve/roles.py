"""Role / capability model (Tier A, RBAC-lite) for the catalog doors.

A header-based role (``X-OntoWiz-Role``) maps to a capability set. This is a
lightweight authorization layer — it gates *which actions* a caller may take
(govern, review, install…), not identity. There is no auth/identity provider
here yet (honest MVP): the role is asserted by the caller and trusted; a real
deployment would bind it to an authenticated principal.
"""

from __future__ import annotations

from fastapi import HTTPException

# role → the capabilities it is allowed to exercise
ROLE_CAPABILITIES: dict[str, list[str]] = {
    "sme": ["comment", "enrich"],
    "curator": ["comment", "review", "govern"],
    "builder": ["comment", "install"],
    "manager": ["comment", "review", "stats"],
}
KNOWN_ROLES = frozenset(ROLE_CAPABILITIES)


def require_role(role: str) -> str:
    """Validate a role header value. 403 if it is not a known role."""
    if role not in KNOWN_ROLES:
        raise HTTPException(status_code=403, detail=f"unknown role: {role!r}")
    return role


def require_capability(role: str, capability: str) -> str:
    """Ensure ``role`` may exercise ``capability``. 403 otherwise."""
    require_role(role)
    if capability not in ROLE_CAPABILITIES[role]:
        raise HTTPException(
            status_code=403,
            detail=f"role {role!r} lacks capability {capability!r}",
        )
    return role
