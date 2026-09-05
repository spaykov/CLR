from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import main
from clr.config import settings
from clr.core import storage
from clr.models.message import IncomingMessage, MessageCategory, Priority, ProcessedMessage


def _processed(id: str, priority: Priority = Priority.medium) -> ProcessedMessage:
    raw = IncomingMessage(
        id=id,
        source="test@example.com",
        content="irrelevant raw body",
        category=MessageCategory.email,
        received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    return ProcessedMessage(original=raw, priority=priority, cognitive_cost=3)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(settings, "api_key", "")
    monkeypatch.setattr(settings, "login_password", "")
    return TestClient(main.app)


def test_delete_history_item_removes_it(client):
    storage.save_processed(_processed("1"))
    storage.save_processed(_processed("2"))

    resp = client.delete("/api/v1/history/1")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}

    remaining = {item["id"] for item in client.get("/api/v1/history").json()["items"]}
    assert remaining == {"2"}


def test_delete_history_item_missing_returns_404(client):
    resp = client.delete("/api/v1/history/does-not-exist")
    assert resp.status_code == 404


def test_clear_all_history(client):
    storage.save_processed(_processed("1"))
    storage.save_processed(_processed("2"))

    resp = client.delete("/api/v1/history")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True, "deleted": 2}
    assert client.get("/api/v1/history").json()["items"] == []


def test_acknowledge_history_item(client):
    storage.save_processed(_processed("1", priority=Priority.critical))
    assert {i["id"] for i in client.get("/api/v1/priority-list").json()["items"]} == {"1"}

    resp = client.post("/api/v1/history/1/acknowledge")
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}

    items = client.get("/api/v1/priority-list").json()["items"]
    assert items == []


def test_acknowledge_history_item_missing_returns_404(client):
    resp = client.post("/api/v1/history/does-not-exist/acknowledge")
    assert resp.status_code == 404


def test_priority_list_returns_only_actionable_items(client):
    storage.save_processed(_processed("critical", priority=Priority.critical))
    storage.save_processed(_processed("low", priority=Priority.low))

    ids = {item["id"] for item in client.get("/api/v1/priority-list").json()["items"]}
    assert ids == {"critical"}


def test_delete_endpoints_require_auth_when_configured(client, monkeypatch):
    monkeypatch.setattr(settings, "api_key", "secret123")
    storage.save_processed(_processed("1"))

    resp = client.delete("/api/v1/history/1")
    assert resp.status_code == 401

    resp = client.delete("/api/v1/history", headers={"X-API-Key": "secret123"})
    assert resp.status_code == 200
