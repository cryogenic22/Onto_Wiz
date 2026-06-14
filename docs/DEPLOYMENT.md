# Deployment — Onto_Wiz on Railway

The platform deploys as **three Railway services** in one project:

```
┌─────────────────┐     ┌──────────────────────┐     ┌──────────────┐
│  frontend (Next)│ ──▶ │  api (ontowiz-serve) │ ──▶ │  Postgres    │
│  Node 22        │     │  Python, Tier A only │     │  (managed)   │
└─────────────────┘     └──────────────────────┘     └──────────────┘
```

## 1. API service — `ontowiz-serve` (Tier A only)

Config: root `railway.toml`. Builds with nixpacks.

- **Install:** `pip install -r requirements-deploy.txt` — installs Tier A only
  (`spec → ctx → runtime → serve`). **Tier B (`ontowiz-core`, `ontowiz-factory`)
  is deliberately excluded** — it builds packs, it never serves them (ADR-012).
  The serve image therefore contains no proprietary engine code.
- **Start:** `uvicorn ontowiz_serve.api:create_app --factory --host 0.0.0.0 --port $PORT`
  (factory → `packs_root="packs"`, `allow_dev_context=False`).
- **Health:** `GET /health` → `{"status":"ok"}`.
- **Serves:** `/v1/context`, `/v1/catalog`, `/v1/packs/...`, MCP, catalog page at `/`.

Required service variables:
| Var | Purpose | Notes |
|---|---|---|
| `ANTHROPIC_API_KEY` | only if the live consult/benchmark path is exercised | not needed for plain context serving |
| `ONTOWIZ_ALLOW_DEV_CONTEXT` | leave unset/false in prod | gates non-ACTIVE artifacts |
| `DATABASE_URL` | Postgres (Unit 6: comment/usage stores) | injected by Railway when Postgres is attached |
| `PORT` | injected by Railway | do not set manually |

Verified locally: the exact `requirements-deploy.txt` set boots the factory app
and `/health` returns 200 with `/v1/context` + `/v1/catalog` present (21 routes).

## 2. Postgres service

Managed Railway Postgres plugin. Exposes `DATABASE_URL` to the API service via a
reference variable. Until Unit 6 lands, the comment/usage stores remain JSON-on-disk
under `packs/.catalog/` (note: that path is ephemeral on Railway — Postgres replaces it).

## 3. Frontend service — `frontend/` (Next.js)

Root directory `frontend/`. Node 22. `npm ci && npm run build`, served by `npm run start`.
Points at the API service's public URL via a build/runtime env var (e.g. `NEXT_PUBLIC_API_URL`).

## First-time setup (operator runs interactively)

```bash
railway login                      # interactive
railway init                       # or: railway link  (existing project)
railway add --database postgres    # provision Postgres
# Set variables in the dashboard or:  railway variables --set ANTHROPIC_API_KEY=...
railway up                         # deploy
```

> ⚠️ Rotate the `ANTHROPIC_API_KEY` that was previously in the plaintext `.env`.
> It must only ever live in Railway service variables, never in the repo.
