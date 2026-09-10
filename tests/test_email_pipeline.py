from datetime import datetime, timezone

import pytest

from clr.config import settings
from clr.core import advisor, email_fetcher, email_pipeline, predictor, rewriter, storage, summarizer
from clr.core import filter as filter_mod
from clr.models.message import IncomingMessage, MessageCategory, Priority, ProcessedMessage


def _fake_email(id: str) -> IncomingMessage:
    return IncomingMessage(
        id=id,
        source="sender@example.com",
        content="Hello\n\nbody",
        category=MessageCategory.email,
        received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


@pytest.fixture(autouse=True)
def _stub_pipeline_stages(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setattr(
        filter_mod, "filter_message",
        lambda m: ProcessedMessage(original=m, priority=Priority.medium, cognitive_cost=3),
    )
    monkeypatch.setattr(summarizer, "summarize", lambda p: p)
    monkeypatch.setattr(rewriter, "rewrite", lambda p: p)
    monkeypatch.setattr(predictor, "predict_needs", lambda msgs, **kw: [])
    monkeypatch.setattr(advisor, "suggest_reductions", lambda msgs, score: [])


def test_run_email_fetch_processes_and_persists_messages(monkeypatch):
    monkeypatch.setattr(email_fetcher, "fetch_emails", lambda hours: [_fake_email("1")])

    result = email_pipeline.run_email_fetch(hours=24)

    assert result["fetched"] == 1
    assert len(result["processed"]) == 1
    assert {i["id"] for i in storage.get_history()} == {"1"}


def test_run_email_fetch_skips_previously_deleted_ids(monkeypatch):
    storage.save_processed(ProcessedMessage(original=_fake_email("1"), priority=Priority.medium))
    storage.delete_processed("1")
    monkeypatch.setattr(email_fetcher, "fetch_emails", lambda hours: [_fake_email("1")])

    result = email_pipeline.run_email_fetch(hours=24)

    assert result["fetched"] == 1
    assert result["skipped_deleted"] == 1
    assert result["processed"] == []


def test_run_email_fetch_returns_empty_bandwidth_when_nothing_to_process(monkeypatch):
    monkeypatch.setattr(email_fetcher, "fetch_emails", lambda hours: [])

    result = email_pipeline.run_email_fetch(hours=24)

    assert result["processed"] == []
    assert result["bandwidth"]["label"] == "clear"
