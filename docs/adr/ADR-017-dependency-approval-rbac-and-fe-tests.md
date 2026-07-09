# ADR-017: Dependency approval — RBAC (JWT/bcrypt) + frontend test gate

**Date:** 2026-06-15
**Status:** SETTLED
**Deciders:** Founder (Human, acting Lead) + Tech Lead
**Reversibility:** two-way door (deps can be removed if the surfaces are dropped)
**Source:** DEC-017; ADR-006 (No New Dependencies Without Lead Approval)
**Relates:** ADR-006 (the gate this satisfies), DEC-012 (prior dep exemption)

## Context

ADR-006 requires explicit Lead approval, recorded in `docs/Lead2Dev.md`, before any
new pip/npm package is added. The "port the catalog into Next.js + bind RBAC to a
real principal" unit needs capabilities the approved stack does not cover:

- **RBAC principal binding.** Today's authz is a trusted `X-OntoWiz-Role` header
  (roles.py) — no identity. Binding to a real principal needs token issue/verify
  and password hashing.
- **Frontend test gate.** ADR-006's approved frontend stack (Next/React/ReactFlow/
  Tailwind) has **no test runner**, yet ADR-015 makes TDD-red + ≥85% coverage on
  new code non-negotiable. React component testing has no stdlib equivalent.

A stdlib-only RBAC path (`hmac`+`hashlib`) was considered; the founder chose to
match `market_zero` exactly (pyjwt + bcrypt) for parity with the sister codebase.

## Decision

Approved new dependencies (ADR-006 exemption, this unit):

**Python (Tier A, `ontowiz-serve`):**
- `pyjwt` — HS256 token issue/verify (`ONTOWIZ_JWT_SECRET`).
- `bcrypt` — password hashing.

**npm (dev-only, `frontend/`):**
- `vitest`, `@vitejs/plugin-react`, `vite-tsconfig-paths` — test runner + JSX +
  `@/` path resolution.
- `@testing-library/react`, `@testing-library/jest-dom`, `jsdom` — component
  rendering + DOM assertions.

All are dev/server-side; none ship inside a compiled Domain Pack. `langchain`-class
heavyweights remain rejected (DEC-012 spirit). Recorded in `docs/Lead2Dev.md`
(Dependency Approvals) per ADR-006.

## Consequences

**Positive:** RBAC binds to a verifiable principal (closes the roles.py honesty
caveat); the frontend port gets a real TDD-red gate; sister-repo parity.
**Negative:** +2 Python and +6 npm packages of attack surface (SEN security-review
scope). bcrypt is a native build.
**Neutral:** the FE test deps are `devDependencies` — they do not affect
`next build` output or the shipped bundle.
