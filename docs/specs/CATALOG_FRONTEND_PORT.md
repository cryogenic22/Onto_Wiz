# Mini-spec — Catalog frontend port + DB + RBAC (Loops F1–F10)

> ADR-008 mini-spec. Goal: port the served Domain Intelligence Catalog
> (`ontowiz_serve.catalog_page` + the `/v1/catalog*` routes) into the production
> **Next.js `frontend/`** app, and — in the same coordinated unit, by the user's
> explicit call — close two backlog follow-ups: swap the JSON Comment/Usage MVP
> stores for a database, and bind RBAC to a real authenticated principal.
> Reuse-first: architecture/decisions adopted from the sister repo
> `C:/Users/kapil/Documents/market_zero` (see provenance notes per loop).
>
> Discipline per loop: mini-spec → reuse-first → TDD red → green → gates → record.
> Reversibility: additive (new wrapper/service/routes/components); the store and
> auth changes preserve existing call-site signatures. Tier rule held: Tier A
> imports Tier A only.

## Decisions feeding this unit (recorded as ADRs)

- **ADR-016** — persistence engine: **SQLite for dev/hermetic + verify-audit**,
  Postgres remains the production target via `ONTOWIZ_DB_DSN`. Supersedes
  ADR-013 *in part* (the founder's "Postgres, not SQLite" call holds for prod;
  the local/test tier runs SQLite so `verify-audit` stays offline). Chosen
  because docker is down and no local Postgres credential is available; the thin
  `Database` wrapper makes the engine a one-config swap.
- **ADR-017** — dependency approval (ADR-006 gate): `pyjwt`, `bcrypt` (Python,
  RBAC) and `vitest`, `@testing-library/react`, `@testing-library/jest-dom`,
  `jsdom`, `@vitejs/plugin-react`, `vite-tsconfig-paths` (npm, FE test gate).
  Recorded in `docs/Lead2Dev.md` and `DEC-016`/`DEC-017`.

## DB + RBAC loops (backend — covered by `verify-audit`)

| Loop | Title | Package (tier) | Success criteria (the red test) |
|---|---|---|---|
| **F-DB1** | SQLite `Database` wrapper | runtime (A) | `Database(path)` opens sqlite3, `execute`/`fetch_one`/`fetch_all`/`transaction()` round-trip; ported from market_zero `db.py` (psycopg2→sqlite3). DSN/path-driven so a Postgres impl is a swap. |
| **F-DB2** | `CommentStore` on SQLite | runtime (A) | Same constructor `CommentStore(root)` + `add`/`list`; backed by `root/catalog.db`. The existing `test_comments.py` (order, scoping, cross-instance persistence) stays green; add a table-schema test. |
| **F-DB3** | `UsageStore` on SQLite | runtime (A) | Same constructor + `record`/`all` + `catalog_stats`; backed by the same `catalog.db`. Existing `test_telemetry.py` stays green; add a schema test. |
| **F-RB1** | Auth service | serve (A) | `hash_password`/`verify_password` (bcrypt), `issue_token`/`decode_token` (pyjwt HS256, `ONTOWIZ_JWT_SECRET`), `ROLE_HIERARCHY` + `role_satisfies`. Ported from market_zero `services/auth.py`. |
| **F-RB2** | Principal binding | serve (A) | `get_current_user` resolves a Bearer JWT → principal+role; `require_capability` derives the role from the **token**, not the `X-OntoWiz-Role` header (header kept only as a dev fallback when no `Authorization` is present). `POST /v1/auth/login` issues a token from a seeded SQLite `UserStore`. `GET /v1/auth/me`. Existing api tests stay green. |

## Frontend port loops (Next.js — new Vitest gate)

| Loop | Title | Success criteria (the red test) |
|---|---|---|
| **F-FE0** | Vitest + RTL harness | `vitest.config.ts` (jsdom, globals, tsconfig paths) + setup; `npm test` runs a green smoke test; `npm run typecheck` clean. |
| **F-FE1** | Catalog types + API client | `src/types/catalog.ts` mirrors the runtime dataclasses; `src/services/catalog.ts` (catalog, search, functions, detail, artifact, comments GET/POST, roles, diff, stats, login/me) against `NEXT_PUBLIC_CATALOG_API_URL` (the serve app, default `:8080`). Tested with mocked `fetch`. |
| **F-FE2** | Catalog grid + search | `/catalog` route: grid of `CatalogEntry` cards (domain, version, function tags, artifact_count, lift, sealed); debounced search calls `/v1/catalog/search`. Component test renders cards + empty state. |
| **F-FE3** | Pack detail (slices + artifacts) | Pack view: function-slice chips (with slice-vs-full token note) + artifact rows (served/gated pill); slice filter narrows the list. Component test. |
| **F-FE4** | Artifact drawer | Drawer: verdict, anti-patterns ("Not → … because"), governance trail, raw YAML (escaped). Component test. |
| **F-FE5** | Comments + auth + review | Login (issues/stores a JWT) + role display from `/auth/me`; comment list + post (Bearer-authed); curator/manager-only review action (403 surfaced for others). Component test. |

## Close-out

`scripts/verify-audit.sh` → PASS (Python gates) **and** the new frontend gate
(`npm test` ≥85% on new code, `npm run typecheck`, `npm run build`). Evidence
recorded in `docs/PROJECT_STATUS.md`; resume pointer updated in
`docs/SESSION_HANDOFF.md`.

## Honest boundaries to preserve in the record

- SQLite is the dev/test engine; **Postgres is the production target** (ADR-016) —
  not yet exercised here (no local PG credential / docker down).
- The `UserStore` is **seeded** (no self-service signup / password reset / refresh
  tokens); JWT has no rotation. RBAC now binds to a real principal, but identity
  provisioning is out of scope for this unit.
- The frontend gate is **Vitest component/client tests**, not full e2e against a
  live backend; `verify-audit.sh` stays Python-only (the FE gate is run and
  recorded alongside it, not folded into it).
