# Mini-spec — Catalog productionization (Loops C1–C10)

> ADR-008 mini-spec for the next 10 loops. Goal: turn the
> `DOMAIN_INTELLIGENCE_CATALOG.html` vision into a **real, served catalog** backed
> by the live pack registry — and close two honest-deferred backlog gaps
> (forecasting benchmark, telemetry persistence) on the way.
> Discipline per loop: mini-spec → reuse-first → TDD red → green → gates → record.
> Reversibility: all additive (new helpers/routes/stores); no breaking changes to
> existing endpoints. Tier rule held: Tier A imports Tier A only.

| Loop | Title | Package (tier) | Success criteria (the red test) |
|---|---|---|---|
| **C1** | Catalog index | runtime + serve (A) | `catalog_index(registry)` returns one entry per pack: domain, latest+all versions, artifact_count, **function slices with counts**, sealed flag, eval summary (cases/pass_rate/agent_lift), coverage. `GET /v1/catalog` serialises it. |
| **C2** | Function-slice surface | runtime + serve (A) | `pack_functions(loaded)` → per function: count, served_count, eval_count, full-vs-slice token estimate (reuse `context_for_function`). `GET /v1/packs/{n}/{v}/functions`. |
| **C3** | Catalog search | runtime + serve (A) | `catalog_search(registry, q, function?, domain?)` ranks packs by lexical overlap (reuse the `_rank_by_query` idea) + lists matching artifacts. `GET /v1/catalog/search`. |
| **C4** | Artifact detail surface | runtime + serve (A) | `artifact_view(loaded, id)` → verdict/body, anti-patterns, trigger signals, provenance (sources + delta history + governance steps), eval coverage, raw YAML. `GET /v1/packs/{n}/{v}/artifacts/{id}`; 404 on miss. |
| **C5** | Served catalog page | serve (A) | `GET /` returns a self-contained HTML shell (text/html) that fetches the live `/v1/catalog`. Route test asserts 200 + shell marker + JS fetch of `/v1/catalog`. |
| **C6** | Annotations / comments | runtime + serve (A) | `CommentStore` persists (pack, version, artifact_id) → {author, role, text, created_at} as JSON; `add`/`list`. `GET/POST /v1/packs/{n}/{v}/artifacts/{id}/comments`. |
| **C7** | Roles / RBAC-lite | serve (A) | role→capability map; `GET /v1/roles`; a curator-only `POST .../review` returns 403 for builder, 200 for curator (role via `X-OntoWiz-Role`, default sme). |
| **C8** | Forecasting eval suite | factory (B) | 4 forecasting `EvalCase`s authored; suite invariants enforced (must_contain term **is in the served heuristic body** and **not in its own question**); suite count grows 26→30. Live agent-lift stays honestly deferred. |
| **C9** | Version diff / evolution | runtime + serve (A) | `pack_diff(a, b)` → added/removed/changed artifact ids + per-function deltas. `GET /v1/packs/{n}/diff?from=&to=`. Proves `0.1.0 → 0.3.0` added the forecasting slice. |
| **C10** | Catalog telemetry | runtime + serve (A) | `UsageStore` persists consult records (pack, version, function?, hit); `catalog_stats(store)` → per-pack consult counts + hit-rate. `POST /v1/usage` + `GET /v1/catalog/stats`. |

Honest boundaries to preserve in the record: comment/usage stores are JSON-on-disk
MVPs (not a database); RBAC is header-based (no auth/identity provider); the C8
forecasting benchmark proves eval-case *well-formedness* offline — the live LLM
agent-lift number for `0.3.0` remains a separate, deferred measurement step.
