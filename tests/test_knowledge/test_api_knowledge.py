"""Integration tests for Knowledge API endpoints."""

import pytest
from fastapi.testclient import TestClient

from src.api.server import app


@pytest.fixture
def client():
    return TestClient(app)


class TestKnowledgeContextEndpoint:
    def test_post_context(self, client):
        """POST /knowledge/context should return a ContextResponse."""
        resp = client.post(
            "/knowledge/context",
            json={"query": "NBRx drop in oncology", "agent_type": "general"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "NBRx drop in oncology"
        assert "patterns" in data
        assert "guardrails" in data
        assert "few_shots" in data
        assert "jargon_context" in data
        assert "token_estimate" in data
        assert data["token_estimate"] > 0

    def test_post_context_empty_query(self, client):
        """Empty query should return 422."""
        resp = client.post(
            "/knowledge/context",
            json={"query": ""},
        )
        assert resp.status_code == 422

    def test_post_context_low_tokens(self, client):
        """Token budget below 100 should return 422."""
        resp = client.post(
            "/knowledge/context",
            json={"query": "test", "max_tokens": 50},
        )
        assert resp.status_code == 422

    def test_post_context_custom_agent_type(self, client):
        resp = client.post(
            "/knowledge/context",
            json={"query": "test", "agent_type": "specialist", "max_tokens": 2000},
        )
        assert resp.status_code == 200
        assert resp.json()["metadata"]["agent_type"] == "specialist"


class TestKnowledgeArtifactsEndpoint:
    def test_list_all_artifacts(self, client):
        """GET /knowledge/artifacts should list artifacts."""
        resp = client.get("/knowledge/artifacts")
        assert resp.status_code == 200
        data = resp.json()
        assert "artifacts" in data
        assert "total" in data

    def test_list_artifacts_by_type(self, client):
        """Should filter by artifact type."""
        resp = client.get("/knowledge/artifacts?type=few_shot")
        assert resp.status_code == 200
        data = resp.json()
        assert data["artifact_type"] == "few_shot"
        for a in data["artifacts"]:
            assert a["artifact_type"] == "few_shot"

    def test_get_artifact_not_found(self, client):
        """Non-existent artifact should return 404."""
        resp = client.get("/knowledge/artifacts/nonexistent-id")
        assert resp.status_code == 404
