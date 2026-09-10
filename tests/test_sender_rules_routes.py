import pytest
from fastapi.testclient import TestClient

import main
from clr.config import settings
from clr.core import storage


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(settings, "api_key", "")
    monkeypatch.setattr(settings, "login_password", "")
    return TestClient(main.app)


def test_add_and_list_sender_rules(client):
    resp = client.post("/api/v1/sender-rules", json={"pattern": "deeplearning.ai", "action": "digest"})
    assert resp.status_code == 200
    assert resp.json()["pattern"] == "deeplearning.ai"

    items = client.get("/api/v1/sender-rules").json()["items"]
    assert {i["pattern"] for i in items} == {"deeplearning.ai"}


def test_add_sender_rule_rejects_invalid_action(client):
    resp = client.post("/api/v1/sender-rules", json={"pattern": "example.com", "action": "block"})
    assert resp.status_code == 422


def test_delete_sender_rule(client):
    created = client.post("/api/v1/sender-rules", json={"pattern": "example.com", "action": "ignore"}).json()

    resp = client.delete(f"/api/v1/sender-rules/{created['id']}")
    assert resp.status_code == 200
    assert client.get("/api/v1/sender-rules").json()["items"] == []


def test_delete_sender_rule_missing_returns_404(client):
    resp = client.delete("/api/v1/sender-rules/999")
    assert resp.status_code == 404


def test_update_sender_rule(client):
    created = client.post("/api/v1/sender-rules", json={"pattern": "thebatch@deeplearning.ai", "action": "ignore"}).json()

    resp = client.put(f"/api/v1/sender-rules/{created['id']}", json={"pattern": "deeplearning.ai", "action": "digest"})
    assert resp.status_code == 200

    items = client.get("/api/v1/sender-rules").json()["items"]
    assert items == [{"id": created["id"], "pattern": "deeplearning.ai", "action": "digest", "created_at": created["created_at"]}]


def test_update_sender_rule_missing_returns_404(client):
    resp = client.put("/api/v1/sender-rules/999", json={"pattern": "example.com", "action": "digest"})
    assert resp.status_code == 404


def test_update_sender_rule_rejects_invalid_action(client):
    created = client.post("/api/v1/sender-rules", json={"pattern": "example.com", "action": "ignore"}).json()

    resp = client.put(f"/api/v1/sender-rules/{created['id']}", json={"pattern": "example.com", "action": "block"})
    assert resp.status_code == 422
