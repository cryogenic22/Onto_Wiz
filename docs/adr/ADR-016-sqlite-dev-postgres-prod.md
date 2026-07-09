# ADR-016: SQLite for dev/test, Postgres for production (persistence engine)

**Date:** 2026-06-15
**Status:** SETTLED
**Deciders:** Founder (Human) + Tech Lead
**Reversibility:** two-way door (engine is DSN-selected behind a wrapper)
**Source:** DEC-016; sister repo `market_zero` (`db.py` thin-wrapper pattern)
**Amends:** ADR-013 (Persistence — Postgres for the machine) — *in part*

## Context

ADR-013 (founder's explicit call) chose **Postgres, not SQLite** for the
machine-side state (telemetry, Forge, eval history, comments). When productionising
the catalog stores (`CommentStore`, `UsageStore`) we hit a hard local constraint:

- Docker Desktop's daemon is not running (no `docker compose up` for the
  `pgvector/pgvector:pg17` service ADR-013/market_zero assume).
- A native PostgreSQL 17 server is reachable on `localhost:5434`, but no working
  credential for that cluster is available to the build, and we will not guess one.
- `verify-audit.sh` (ADR-015 completion gate) runs the package suite **offline**.
  Backing the stores with a server that must be live at verify-time would break the
  hermetic guarantee that makes "done" falsifiable in any environment.

The founder's rationale for Postgres (durable, multi-writer, pgvector for later
semantic alias search) is about the **production** deployment, not the dev/test
inner loop.

## Decision

Persistence engine is **selected by DSN behind a single thin `Database` wrapper**
(`ontowiz_runtime.db`, ported from `market_zero/db.py`, psycopg2→sqlite3):

- **Dev / test / `verify-audit`:** **SQLite** (`stdlib sqlite3`), file-backed at
  `<packs_root>/.catalog/catalog.db`. Zero services, hermetic, fast.
- **Production:** **Postgres** remains the target (ADR-013 honoured), selected by
  `ONTOWIZ_DB_DSN`. The wrapper exposes one interface; swapping the engine is a
  configuration change plus one driver-specific `Database` subclass — no call-site
  changes in `CommentStore`/`UsageStore`.

This **amends ADR-013**: its "Postgres, not SQLite" directive stands for the
shipped production machine; the local/test tier runs SQLite. ADR-013's Tier-A/YAML
product-persistence half is untouched.

## Consequences

**Positive:** `verify-audit` stays offline and green; the JSON-MVP honesty caveat
(C6/C10) is retired with a real, transactional store; production Postgres path is
preserved, not foreclosed.
**Negative:** two engines to keep behind one interface; the Postgres impl is
specified but not yet exercised by an automated test here (no local PG creds /
docker). Tracked as a follow-up: add a Postgres-backed contract test once a DSN is
available (gated `@pytest.mark.postgres`, skipped when absent).
**Neutral:** SQLite single-writer semantics are adequate for the single-process
serve app; concurrency parity with Postgres is a production concern, not a dev one.
