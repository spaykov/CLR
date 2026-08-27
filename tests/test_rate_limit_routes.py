import pytest
from fastapi.testclient import TestClient

import main
from clr.config import settings
from clr.core import advisor


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "")
    monkeypatch.setattr(settings, "login_password", "wrong-on-purpose")
    # process/batch calls advisor.suggest_reductions unconditionally, even for
    # an empty batch — stub it out so these tests don't need a live Ollama.
    monkeypatch.setattr(advisor, "suggest_reductions", lambda messages, score: [])
    return TestClient(main.app)


def test_login_is_rate_limited_by_ip(client):
    for _ in range(5):
        resp = client.post("/api/v1/auth/login", json={"password": "nope"})
        assert resp.status_code == 401

    resp = client.post("/api/v1/auth/login", json={"password": "nope"})
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers


def test_process_batch_has_a_tighter_limit_than_the_default(client, monkeypatch):
    monkeypatch.setattr(settings, "login_password", "")  # no auth needed for this one

    for _ in range(10):
        resp = client.post("/api/v1/process/batch", json={"messages": []})
        assert resp.status_code == 200

    resp = client.post("/api/v1/process/batch", json={"messages": []})
    assert resp.status_code == 429


def test_general_default_limit_applies_to_other_routes(client, monkeypatch):
    monkeypatch.setattr(settings, "login_password", "")

    for _ in range(60):
        resp = client.get("/api/v1/version")
        assert resp.status_code == 200

    resp = client.get("/api/v1/version")
    assert resp.status_code == 429


def test_different_sessions_get_independent_budgets_on_the_same_route(monkeypatch):
    monkeypatch.setattr(settings, "api_key", "")
    monkeypatch.setattr(settings, "login_password", "the-password")
    monkeypatch.setattr(advisor, "suggest_reductions", lambda messages, score: [])

    # Two separate browser sessions (two TestClients so cookies don't mix),
    # each logging in independently -> two distinct session-cookie identities.
    session_a = TestClient(main.app)
    session_b = TestClient(main.app)
    assert session_a.post("/api/v1/auth/login", json={"password": "the-password"}).status_code == 200
    assert session_b.post("/api/v1/auth/login", json={"password": "the-password"}).status_code == 200

    for _ in range(10):
        resp = session_a.post("/api/v1/process/batch", json={"messages": []})
        assert resp.status_code == 200
    exhausted = session_a.post("/api/v1/process/batch", json={"messages": []})
    assert exhausted.status_code == 429

    # Session B never made a /process/batch call — its budget is untouched.
    fresh = session_b.post("/api/v1/process/batch", json={"messages": []})
    assert fresh.status_code == 200
