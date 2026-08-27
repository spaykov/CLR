from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

import main
from clr.config import settings
from clr.core import advisor, email_fetcher, predictor, rewriter, storage, summarizer
from clr.core import filter as filter_mod
from clr.models.message import IncomingMessage, MessageCategory, Priority, ProcessedMessage


def _fake_email(id: str, subject: str = "Hello") -> IncomingMessage:
    return IncomingMessage(
        id=id,
        source="sender@example.com",
        content=f"{subject}\n\nbody",
        category=MessageCategory.email,
        received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        metadata={"subject": subject, "from": "sender@example.com"},
    )


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(settings, "api_key", "")
    monkeypatch.setattr(settings, "login_password", "")
    # Stub out the LLM-calling pipeline stages so this test doesn't need Ollama.
    monkeypatch.setattr(
        filter_mod, "filter_message",
        lambda m: ProcessedMessage(original=m, priority=Priority.medium, cognitive_cost=3),
    )
    monkeypatch.setattr(summarizer, "summarize", lambda p: p)
    monkeypatch.setattr(rewriter, "rewrite", lambda p: p)
    monkeypatch.setattr(predictor, "predict_needs", lambda msgs, **kw: [])
    monkeypatch.setattr(advisor, "suggest_reductions", lambda msgs, score: [])
    return TestClient(main.app)


def test_refetching_same_email_after_delete_does_not_resurrect_it(client, monkeypatch):
    email = _fake_email("stable-id-1")
    monkeypatch.setattr(email_fetcher, "fetch_emails", lambda hours=24: [email])

    resp = client.post("/api/v1/email/fetch", json={"hours": 24})
    assert resp.status_code == 200
    assert resp.json()["fetched"] == 1
    assert {i["id"] for i in client.get("/api/v1/history").json()["items"]} == {"stable-id-1"}

    del_resp = client.delete("/api/v1/history/stable-id-1")
    assert del_resp.status_code == 200

    # Same underlying email fetched again (fetch_emails now returns the same
    # stable id, exactly like a real refetch would after the ids.py fix).
    resp2 = client.post("/api/v1/email/fetch", json={"hours": 24})
    assert resp2.status_code == 200
    body = resp2.json()
    assert body["fetched"] == 1
    assert body["skipped_deleted"] == 1
    assert body["processed"] == []
    assert client.get("/api/v1/history").json()["items"] == []


def test_a_different_email_still_gets_processed_after_an_unrelated_delete(client, monkeypatch):
    monkeypatch.setattr(email_fetcher, "fetch_emails", lambda hours=24: [_fake_email("id-1")])
    client.post("/api/v1/email/fetch", json={"hours": 24})
    client.delete("/api/v1/history/id-1")

    monkeypatch.setattr(email_fetcher, "fetch_emails", lambda hours=24: [_fake_email("id-2")])
    resp = client.post("/api/v1/email/fetch", json={"hours": 24})

    assert resp.json()["skipped_deleted"] == 0
    assert {i["id"] for i in client.get("/api/v1/history").json()["items"]} == {"id-2"}
