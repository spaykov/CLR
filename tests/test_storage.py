from datetime import datetime, timezone

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
    return ProcessedMessage(
        original=raw,
        summary="a summary",
        simplified="a simplified version",
        priority=priority,
        action_required=True,
        suggested_action="reply",
        filtered_out=False,
        filter_reason="",
        cognitive_cost=5,
    )


def test_save_and_get_history_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")

    storage.save_processed(_processed("1"))
    storage.save_processed(_processed("2", priority=Priority.high))

    items = storage.get_history()
    assert {item["id"] for item in items} == {"1", "2"}


def test_history_excludes_raw_content(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    storage.save_processed(_processed("1"))

    item = storage.get_history()[0]
    assert "content" not in item
    assert "original" not in item


def test_history_respects_limit_and_offset(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    for i in range(5):
        storage.save_processed(_processed(str(i)))

    page1 = storage.get_history(limit=2, offset=0)
    page2 = storage.get_history(limit=2, offset=2)
    assert len(page1) == 2
    assert len(page2) == 2
    assert {item["id"] for item in page1}.isdisjoint({item["id"] for item in page2})


def test_save_processed_is_idempotent_by_id(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    storage.save_processed(_processed("1", priority=Priority.low))
    storage.save_processed(_processed("1", priority=Priority.critical))

    items = storage.get_history()
    assert len(items) == 1
    assert items[0]["priority"] == "critical"


def test_delete_processed_removes_only_that_item(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    storage.save_processed(_processed("1"))
    storage.save_processed(_processed("2"))

    assert storage.delete_processed("1") is True
    items = storage.get_history()
    assert {item["id"] for item in items} == {"2"}


def test_delete_processed_missing_id_returns_false(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    assert storage.delete_processed("does-not-exist") is False


def test_clear_history_removes_everything_and_returns_count(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    for i in range(3):
        storage.save_processed(_processed(str(i)))

    assert storage.clear_history() == 3
    assert storage.get_history() == []