"""F-RB2 — RBAC bound to a real principal (login + Bearer-derived role).

The catalog's authz was a trusted ``X-OntoWiz-Role`` header (no identity). Now an
authenticated Bearer principal's role wins; the header survives only as a dev
fallback when no token is presented. The headline test proves a header cannot
escalate an authenticated principal.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from ontowiz_factory.seed import build_commercial_pack
from ontowiz_serve.api import create_app

COMMERCIAL_YAML = Path(__file__).resolve().parents[3] / "ontology" / "commercial.yaml"
REVIEW = "/v1/packs/commercial_analytics/0.1.0/artifacts/rule_formulary_exclusion/review"


def _client(tmp_path) -> TestClient:
    build_commercial_pack(COMMERCIAL_YAML, tmp_path)
    return TestClient(create_app(tmp_path))


def _login(c, role) -> str:
    r = c.post("/v1/auth/login", json={"email": f"{role}@ontowiz.ai", "password": "ontowiz-demo"})
    assert r.status_code == 200, r.text
    assert r.json()["role"] == role
    return r.json()["access_token"]


def test_login_and_me_roundtrip(tmp_path):
    c = _client(tmp_path)
    token = _login(c, "curator")
    me = c.get("/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["role"] == "curator"
    assert me.json()["email"] == "curator@ontowiz.ai"


def test_login_bad_credentials_401(tmp_path):
    c = _client(tmp_path)
    assert c.post("/v1/auth/login",
                  json={"email": "curator@ontowiz.ai", "password": "nope"}).status_code == 401


def test_me_requires_auth_401(tmp_path):
    assert _client(tmp_path).get("/v1/auth/me").status_code == 401
    # a malformed token is rejected, not ignored
    assert _client(tmp_path).get(
        "/v1/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_review_authorized_by_token_role(tmp_path):
    c = _client(tmp_path)
    token = _login(c, "curator")
    ok = c.post(REVIEW, json={"decision": "approve", "note": ""},
                headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200
    assert ok.json()["decision"] == "approve"


def test_token_role_cannot_be_escalated_by_header(tmp_path):
    c = _client(tmp_path)
    token = _login(c, "sme")  # SME lacks the 'review' capability
    # even presenting a curator header, the authenticated SME principal wins → 403
    r = c.post(REVIEW, json={"decision": "approve", "note": ""},
               headers={"Authorization": f"Bearer {token}", "X-OntoWiz-Role": "curator"})
    assert r.status_code == 403
