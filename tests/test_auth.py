import pytest
from fastapi.testclient import TestClient

import main
from clr.api.auth import SESSION_COOKIE_NAME
from clr.config import settings
from clr.core import sessions


@pytest.fixture
def client():
    return TestClient(main.app)


@pytest.fixture(autouse=True)
def _clear_sessions():
    yield
    sessions._sessions.clear()


def test_no_secrets_configured_allows_unauthenticated_access(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "")
    monkeypatch.setattr(settings, "login_password", "")
    resp = client.get("/api/v1/version")
    assert resp.status_code == 200


def test_key_configured_rejects_missing_header(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "secret123")
    resp = client.get("/api/v1/version")
    assert resp.status_code == 401


def test_key_configured_rejects_wrong_key(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "secret123")
    resp = client.get("/api/v1/version", headers={"X-API-Key": "wrong"})
    assert resp.status_code == 401


def test_key_configured_accepts_correct_key(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "secret123")
    resp = client.get("/api/v1/version", headers={"X-API-Key": "secret123"})
    assert resp.status_code == 200


def test_health_is_exempt_even_when_key_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "secret123")
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200


def test_login_wrong_password_returns_401(client, monkeypatch):
    monkeypatch.setattr(settings, "login_password", "pw123")
    resp = client.post("/api/v1/auth/login", json={"password": "wrong"})
    assert resp.status_code == 401
    assert SESSION_COOKIE_NAME not in resp.cookies


def test_login_without_configured_password_returns_400(client, monkeypatch):
    monkeypatch.setattr(settings, "login_password", "")
    resp = client.post("/api/v1/auth/login", json={"password": "anything"})
    assert resp.status_code == 400


def test_api_key_does_not_work_as_login_password(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "script-secret")
    monkeypatch.setattr(settings, "login_password", "pw123")
    resp = client.post("/api/v1/auth/login", json={"password": "script-secret"})
    assert resp.status_code == 401


def test_login_correct_password_sets_cookie_that_authenticates(client, monkeypatch):
    # login_password only — proves session auth works without an api_key set.
    monkeypatch.setattr(settings, "login_password", "pw123")
    login_resp = client.post("/api/v1/auth/login", json={"password": "pw123"})
    assert login_resp.status_code == 200
    assert SESSION_COOKIE_NAME in login_resp.cookies

    resp = client.get("/api/v1/version")  # cookie carried automatically by the client
    assert resp.status_code == 200


def test_login_cookie_is_not_secure_over_plain_http(client, monkeypatch):
    monkeypatch.setattr(settings, "login_password", "pw123")
    resp = client.post("/api/v1/auth/login", json={"password": "pw123"})
    assert "Secure" not in resp.headers.get("set-cookie", "")


def test_login_cookie_is_secure_over_https(monkeypatch):
    monkeypatch.setattr(settings, "login_password", "pw123")
    https_client = TestClient(main.app, base_url="https://testserver")
    resp = https_client.post("/api/v1/auth/login", json={"password": "pw123"})
    assert "Secure" in resp.headers.get("set-cookie", "")


def test_logout_invalidates_session(client, monkeypatch):
    monkeypatch.setattr(settings, "login_password", "pw123")
    client.post("/api/v1/auth/login", json={"password": "pw123"})
    assert client.get("/api/v1/version").status_code == 200

    client.post("/api/v1/auth/logout")
    assert client.get("/api/v1/version").status_code == 401


def test_auth_status_reflects_login_state(client, monkeypatch):
    monkeypatch.setattr(settings, "login_password", "pw123")
    assert client.get("/api/v1/auth/status").json() == {"auth_required": True, "authenticated": False}

    client.post("/api/v1/auth/login", json={"password": "pw123"})
    assert client.get("/api/v1/auth/status").json() == {"auth_required": True, "authenticated": True}


def test_auth_status_not_required_when_only_api_key_set(client, monkeypatch):
    # api_key alone doesn't gate the browser login flow — it's script-only.
    monkeypatch.setattr(settings, "api_key", "script-secret")
    monkeypatch.setattr(settings, "login_password", "")
    assert client.get("/api/v1/auth/status").json() == {"auth_required": False, "authenticated": True}


def test_index_serves_login_page_when_unauthenticated(client, monkeypatch):
    monkeypatch.setattr(settings, "login_password", "pw123")
    resp = client.get("/")
    assert resp.status_code == 200
    assert "login-form" in resp.text


def test_index_serves_app_after_login(client, monkeypatch):
    monkeypatch.setattr(settings, "login_password", "pw123")
    client.post("/api/v1/auth/login", json={"password": "pw123"})
    resp = client.get("/")
    assert resp.status_code == 200
    assert "login-form" not in resp.text
    assert 'data-tab="bandwidth"' in resp.text


def test_index_serves_app_directly_when_only_api_key_set(client, monkeypatch):
    # api_key is script-only; it must not gate the browser SPA.
    monkeypatch.setattr(settings, "api_key", "script-secret")
    monkeypatch.setattr(settings, "login_password", "")
    resp = client.get("/")
    assert resp.status_code == 200
    assert "login-form" not in resp.text
    assert 'data-tab="bandwidth"' in resp.text
