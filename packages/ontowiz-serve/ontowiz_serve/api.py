"""REST door (Tier A) — FastAPI over the runtime. No business logic here.

Endpoints:
  GET  /health
  GET  /v1/packs                      list pack manifests
  GET  /v1/packs/{name}/{version}     one pack manifest
  POST /v1/context                    governance-gated context for a query

Tier A: imports ontowiz_runtime / ontowiz_spec only — never the factory.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import HTMLResponse
from ontowiz_runtime import (
    CommentStore,
    ContextResult,
    LoadedPack,
    PackDetail,
    PackRegistry,
    UsageStore,
    artifact_view,
    catalog_index,
    catalog_search,
    catalog_stats,
    context_for_pack,
    explain_concept,
    pack_detail,
    pack_diff,
    pack_functions,
)
from ontowiz_spec import Tag, TagDimension
from pydantic import BaseModel, Field

from .auth import AuthError, decode_token, issue_token
from .catalog_page import catalog_html
from .roles import ROLE_CAPABILITIES, require_capability, require_role
from .users import UserStore


class TagIn(BaseModel):
    dimension: str
    value: str


class CommentIn(BaseModel):
    author: str = Field(max_length=120)
    text: str = Field(max_length=4000)


class ReviewIn(BaseModel):
    decision: str = Field(max_length=40)  # approve | request_changes | reject
    note: str = Field(default="", max_length=4000)


class LoginIn(BaseModel):
    email: str = Field(max_length=200)
    password: str = Field(max_length=200)


class UsageIn(BaseModel):
    pack: str = Field(max_length=200)
    version: str = Field(max_length=50)
    function: str | None = Field(default=None, max_length=80)
    hit: bool = True


class ContextRequest(BaseModel):
    query: str = Field(max_length=8000)
    pack_name: str = Field(max_length=200)
    pack_version: str = Field(max_length=50)
    agent_type: str = "general"
    tags: list[TagIn] = Field(default_factory=list)
    dev_mode: bool = False


def _to_tags(items: list[TagIn]) -> list[Tag]:
    try:
        return [Tag(dimension=TagDimension(t.dimension), value=t.value) for t in items]
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"invalid tag dimension: {e}") from e


def _detail_payload(d: PackDetail) -> dict:
    """Serialise a runtime PackDetail to the registry-detail response shape."""
    return {
        "name": d.name,
        "version": d.version,
        "description": d.description,
        "artifact_count": d.artifact_count,
        "artifact_kinds": d.artifact_kinds,
        "evals": d.evals,
        "coverage": d.coverage,
        "artifacts": [asdict(r) for r in d.artifacts],
        "gaps": d.gaps,
    }


def _context_payload(r: ContextResult) -> dict:
    """Serialise a ContextResult to the /v1/context response shape."""
    return {
        "query": r.query,
        "agent_type": r.agent_type,
        "system_prompt": r.system_prompt,
        "eligible": [a.id for a in r.eligible],
        "trust": {
            "pack": r.trust.pack,
            "confidence": r.trust.confidence,
            "lifecycle_floor": r.trust.lifecycle_floor,
            "artifacts_used": r.trust.artifacts_used,
            "backing_deltas": r.trust.backing_deltas,
        },
        "tokens_estimate": r.tokens_estimate,
    }


Loader = Callable[[str, str], LoadedPack]


def _make_loader(registry: PackRegistry) -> Loader:
    """A pack loader that maps a missing pack to a 404 (not a raw FileNotFoundError)."""
    def _load(name: str, version: str) -> LoadedPack:
        try:
            return registry.load(name, version)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=f"pack not found: {name}@{version}") from e
    return _load


def _require_artifact(load: Loader, name: str, version: str, artifact_id: str) -> None:
    """404 unless ``artifact_id`` exists in the pack — guards annotate/review writes."""
    try:
        artifact_view(load(name, version), artifact_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"artifact not found: {artifact_id}") from e


def _claims_from_bearer(authorization: str | None) -> dict | None:
    """Decode a ``Authorization: Bearer <jwt>`` header. None if no bearer present.

    A *present but invalid/expired* token is a 401 — it is not silently ignored.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    try:
        return decode_token(authorization.split(" ", 1)[1])
    except AuthError as e:
        raise HTTPException(status_code=401, detail="invalid or expired token") from e


def _resolve_principal(authorization: str | None, x_ontowiz_role: str) -> tuple[str, str]:
    """Return ``(role, who)``. An authenticated Bearer principal wins; the
    ``X-OntoWiz-Role`` header is honoured only as a dev fallback when no token is
    presented — so a header cannot escalate an authenticated caller's role.
    """
    claims = _claims_from_bearer(authorization)
    if claims is not None:
        role = require_role(claims.get("role", ""))
        return role, claims.get("email") or claims.get("sub") or role
    return require_role(x_ontowiz_role), ""


def _register_pages(app: FastAPI) -> None:
    @app.get("/", response_class=HTMLResponse)
    def catalog_page() -> str:
        return catalog_html()

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/v1/roles")
    def roles() -> dict:
        return ROLE_CAPABILITIES


def _register_catalog(app: FastAPI, registry: PackRegistry, usage: UsageStore) -> None:
    @app.get("/v1/catalog")
    def catalog() -> list[dict]:
        return [asdict(e) for e in catalog_index(registry)]

    @app.get("/v1/catalog/stats")
    def catalog_stats_route() -> list[dict]:
        return [asdict(p) for p in catalog_stats(usage)]

    @app.post("/v1/usage")
    def record_usage(body: UsageIn) -> dict:
        return asdict(usage.record(body.pack, body.version, function=body.function, hit=body.hit))

    @app.get("/v1/catalog/search")
    def catalog_search_route(
        q: str = "", function: str | None = None, domain: str | None = None
    ) -> list[dict]:
        return [asdict(h) for h in catalog_search(registry, q, function=function, domain=domain)]

    @app.get("/v1/packs")
    def list_packs() -> list[dict]:
        return [m.model_dump(mode="json") for m in registry.list_manifests()]


def _register_pack_views(app: FastAPI, load: Loader) -> None:
    # /diff declared before /{version} so "diff" is not parsed as a version
    @app.get("/v1/packs/{name}/diff")
    def pack_diff_route(
        name: str, from_version: str = Query(alias="from"), to_version: str = Query(alias="to"),
    ) -> dict:
        return asdict(pack_diff(load(name, from_version), load(name, to_version)))

    @app.get("/v1/packs/{name}/{version}")
    def get_pack(name: str, version: str) -> dict:
        return dict(load(name, version).manifest.model_dump(mode="json"))

    @app.get("/v1/packs/{name}/{version}/detail")
    def get_pack_detail(name: str, version: str) -> dict:
        return _detail_payload(pack_detail(load(name, version)))

    @app.get("/v1/packs/{name}/{version}/functions")
    def pack_functions_route(name: str, version: str) -> list[dict]:
        return [asdict(s) for s in pack_functions(load(name, version))]

    @app.get("/v1/packs/{name}/{version}/artifacts/{artifact_id}")
    def get_artifact(name: str, version: str, artifact_id: str) -> dict:
        try:
            return asdict(artifact_view(load(name, version), artifact_id))
        except KeyError as e:
            raise HTTPException(status_code=404, detail=f"artifact not found: {artifact_id}") from e

    @app.get("/v1/packs/{name}/{version}/explain")
    def explain_pack(name: str, version: str, concept: str) -> dict:
        return {"concept": concept,
                "lineage": [asdict(e) for e in explain_concept(load(name, version), concept)]}


def _register_collaboration(app: FastAPI, load: Loader, comments: CommentStore) -> None:
    @app.get("/v1/packs/{name}/{version}/artifacts/{artifact_id}/comments")
    def list_comments(name: str, version: str, artifact_id: str) -> list[dict]:
        return [asdict(c) for c in comments.list(name, version, artifact_id)]

    @app.post("/v1/packs/{name}/{version}/artifacts/{artifact_id}/comments")
    def add_comment(
        name: str, version: str, artifact_id: str, body: CommentIn,
        authorization: str | None = Header(default=None),
        x_ontowiz_role: str = Header(default="sme"),
    ) -> dict:
        _require_artifact(load, name, version, artifact_id)
        role, _who = _resolve_principal(authorization, x_ontowiz_role)
        return asdict(comments.add(name, version, artifact_id,
                                   author=body.author, role=role, text=body.text))

    @app.post("/v1/packs/{name}/{version}/artifacts/{artifact_id}/review")
    def review_artifact(
        name: str, version: str, artifact_id: str, body: ReviewIn,
        authorization: str | None = Header(default=None),
        x_ontowiz_role: str = Header(default="sme"),
    ) -> dict:
        # governance action — only an authenticated role with 'review' may decide;
        # the X-OntoWiz-Role header cannot escalate a Bearer principal.
        role, who = _resolve_principal(authorization, x_ontowiz_role)
        require_capability(role, "review")
        _require_artifact(load, name, version, artifact_id)
        comments.add(name, version, artifact_id, author=who or role, role=role,
                     text=f"[review:{body.decision}] {body.note}".strip())
        return {"artifact_id": artifact_id, "decision": body.decision, "by": who or role}


def _register_auth(app: FastAPI, users: UserStore) -> None:
    @app.post("/v1/auth/login")
    def login(body: LoginIn) -> dict:
        user = users.authenticate(body.email, body.password)
        if user is None:
            raise HTTPException(status_code=401, detail="invalid credentials")
        token = issue_token(user.id, user.role, email=user.email)
        return {"access_token": token, "token_type": "bearer",
                "role": user.role, "email": user.email}

    @app.get("/v1/auth/me")
    def me(authorization: str | None = Header(default=None)) -> dict:
        claims = _claims_from_bearer(authorization)
        if claims is None:
            raise HTTPException(status_code=401, detail="authentication required")
        return {"sub": claims.get("sub", ""), "role": claims.get("role", ""),
                "email": claims.get("email", "")}


def create_app(packs_root: str | Path = "packs", *, allow_dev_context: bool = False) -> FastAPI:
    """Build the REST app over a packs directory.

    ``allow_dev_context`` (default False, server-side only) gates whether a
    request's ``dev_mode`` can serve non-ACTIVE artifacts — so a client cannot
    pull ungoverned knowledge by flipping a request flag.
    """
    app = FastAPI(title="Onto_Wiz Domain Intelligence", version="0.1.0")
    registry = PackRegistry(packs_root)
    catalog_dir = Path(packs_root) / ".catalog"
    comments, usage = CommentStore(catalog_dir), UsageStore(catalog_dir)
    users = UserStore(catalog_dir)
    users.seed_default()
    load = _make_loader(registry)

    _register_pages(app)
    _register_catalog(app, registry, usage)
    _register_pack_views(app, load)
    _register_collaboration(app, load, comments)
    _register_auth(app, users)

    @app.post("/v1/context")
    def get_context_route(req: ContextRequest) -> dict:
        dev_mode = req.dev_mode and allow_dev_context  # server has the final say
        res = context_for_pack(
            req.query, load(req.pack_name, req.pack_version),
            agent_type=req.agent_type, tags=_to_tags(req.tags), dev_mode=dev_mode,
        )
        return _context_payload(res)

    return app


def main() -> None:  # pragma: no cover
    import os

    import uvicorn

    allow_dev = os.environ.get("ONTOWIZ_ALLOW_DEV_CONTEXT", "").lower() in {"1", "true", "yes"}
    uvicorn.run(create_app(allow_dev_context=allow_dev), host="0.0.0.0", port=8080)
