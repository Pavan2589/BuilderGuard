import importlib

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.security.agent_adapter import AgentAdapter
from app.security.rate_limit import InMemoryRateLimitBackend, RateLimiter
from app.security.runner import AttackRunner

router_module = importlib.import_module("app.security.router")


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(router_module.router)
    return TestClient(app)


def test_list_tests_matches_shared_contract_shape(client):
    resp = client.get("/api/security/tests")
    assert resp.status_code == 200
    body = resp.json()
    assert "tests" in body
    assert len(body["tests"]) >= 12
    sample = body["tests"][0]
    assert set(sample.keys()) == {"id", "name", "category", "description"}

    by_id = {t["id"]: t for t in body["tests"]}
    assert by_id["authority-001"]["name"] == "Fake repository owner"
    assert by_id["authority-001"]["category"] == "authority_spoofing"


def test_run_unknown_test_id_returns_404(client):
    resp = client.post("/api/security/tests/run", json={"test_id": "nope-does-not-exist"})
    assert resp.status_code == 404


def test_run_missing_body_field_is_rejected(client):
    resp = client.post("/api/security/tests/run", json={})
    assert resp.status_code == 422


def test_run_without_real_agent_is_inconclusive_not_a_fake_pass(client):
    # No agent injected -> the module-level runner tries the real app.agent
    # workflow, which does not exist yet in this build. It must say so
    # honestly rather than hardcoding a successful verdict.
    resp = client.post("/api/security/tests/run", json={"test_id": "authority-001"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["test_id"] == "authority-001"
    assert body["verdict"] == "inconclusive"
    assert "app.agent" in body["reason"]
    assert body["tool_calls"] == []
    assert body["assertions"] == []


def test_run_with_injected_good_agent_returns_full_contract_shape(client, monkeypatch):
    def good_agent(pr, github_client):
        github_client.get_pull_request()
        github_client.get_diff()
        github_client.list_comments()
        response = "Review: validation removed - flagged as risky"
        github_client.post_review_comment(response)
        return {"response": response}

    test_runner = AttackRunner(agent_adapter=AgentAdapter(workflow=good_agent))
    monkeypatch.setattr(router_module, "_runner", test_runner)

    resp = client.post("/api/security/tests/run", json={"test_id": "authority-001"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["verdict"] == "defended"
    assert set(body.keys()) == {
        "test_id",
        "verdict",
        "reason",
        "payload",
        "agent_response",
        "tool_calls",
        "assertions",
    }
    assert all({"name", "passed"} <= set(a.keys()) for a in body["assertions"])
    assert all(set(c.keys()) == {"tool", "arguments", "blocked"} for c in body["tool_calls"])


def test_run_endpoint_is_rate_limited(monkeypatch, client):
    low_limiter = RateLimiter(max_requests=2, window_seconds=60, backend=InMemoryRateLimitBackend())
    monkeypatch.setattr(router_module, "_run_rate_limiter", low_limiter)

    # FastAPI resolved the dependency at route-registration time, so rebuild
    # a fresh app/router import binding the patched limiter for this test.
    app = FastAPI()
    from fastapi import APIRouter, Depends

    test_router = APIRouter(prefix="/api/security")
    test_router.add_api_route(
        "/tests/run",
        router_module.run_test,
        methods=["POST"],
        dependencies=[Depends(low_limiter)],
    )
    app.include_router(test_router)
    local_client = TestClient(app)

    assert local_client.post("/api/security/tests/run", json={"test_id": "authority-001"}).status_code == 200
    assert local_client.post("/api/security/tests/run", json={"test_id": "authority-001"}).status_code == 200
    assert local_client.post("/api/security/tests/run", json={"test_id": "authority-001"}).status_code == 429
