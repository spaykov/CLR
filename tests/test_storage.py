import sqlite3
from datetime import datetime, timedelta, timezone

from clr.core import storage
from clr.models.message import IncomingMessage, MessageCategory, Priority, ProcessedMessage


def _processed(
    id: str,
    priority: Priority = Priority.medium,
    action_required: bool = True,
    filtered_out: bool = False,
    received_at: datetime = datetime(2026, 1, 1, tzinfo=timezone.utc),
) -> ProcessedMessage:
    raw = IncomingMessage(
        id=id,
        source="test@example.com",
        content="irrelevant raw body",
        category=MessageCategory.email,
        received_at=received_at,
    )
    return ProcessedMessage(
        original=raw,
        summary="a summary",
        simplified="a simplified version",
        priority=priority,
        action_required=action_required,
        suggested_action="reply",
        filtered_out=filtered_out,
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


def test_delete_processed_tombstones_the_id(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    storage.save_processed(_processed("1"))

    storage.delete_processed("1")

    assert storage.get_deleted_ids(["1"]) == {"1"}


def test_delete_processed_missing_id_does_not_tombstone(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")

    assert storage.delete_processed("does-not-exist") is False
    assert storage.get_deleted_ids(["does-not-exist"]) == set()


def test_clear_history_tombstones_all_cleared_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    for i in range(3):
        storage.save_processed(_processed(str(i)))

    storage.clear_history()

    assert storage.get_deleted_ids(["0", "1", "2"]) == {"0", "1", "2"}


def test_get_deleted_ids_only_matches_requested_ids(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    storage.save_processed(_processed("1"))
    storage.save_processed(_processed("2"))
    storage.delete_processed("1")
    storage.delete_processed("2")

    assert storage.get_deleted_ids(["1"]) == {"1"}
    assert storage.get_deleted_ids([]) == set()


def test_acknowledge_processed_marks_item(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    storage.save_processed(_processed("1"))

    assert storage.acknowledge_processed("1") is True
    items = storage.get_history()
    assert items[0]["acknowledged"] == 1


def test_acknowledge_processed_missing_id_returns_false(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    assert storage.acknowledge_processed("does-not-exist") is False


def test_get_priority_items_includes_high_critical_or_action_required(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    storage.save_processed(_processed("critical", priority=Priority.critical, action_required=False))
    storage.save_processed(_processed("high", priority=Priority.high, action_required=False))
    storage.save_processed(_processed("medium-actionable", priority=Priority.medium, action_required=True))
    storage.save_processed(_processed("medium-quiet", priority=Priority.medium, action_required=False))
    storage.save_processed(_processed("low", priority=Priority.low, action_required=False))

    ids = {item["id"] for item in storage.get_priority_items()}
    assert ids == {"critical", "high", "medium-actionable"}


def test_get_priority_items_excludes_filtered_out_and_acknowledged(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    storage.save_processed(_processed("filtered", priority=Priority.critical, filtered_out=True))
    storage.save_processed(_processed("acked", priority=Priority.critical))
    storage.acknowledge_processed("acked")
    storage.save_processed(_processed("visible", priority=Priority.critical))

    ids = {item["id"] for item in storage.get_priority_items()}
    assert ids == {"visible"}


def test_get_priority_items_orders_by_priority_then_recency(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    storage.save_processed(_processed("high-older", priority=Priority.high, received_at=base))
    storage.save_processed(_processed("critical", priority=Priority.critical, received_at=base))
    storage.save_processed(_processed("high-newer", priority=Priority.high, received_at=base + timedelta(hours=1)))

    ordered_ids = [item["id"] for item in storage.get_priority_items()]
    assert ordered_ids == ["critical", "high-newer", "high-older"]


def test_get_priority_items_respects_limit(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    for i in range(5):
        storage.save_processed(_processed(str(i), priority=Priority.critical))

    assert len(storage.get_priority_items(limit=2)) == 2


def test_auto_fetch_watermark_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    assert storage.get_last_auto_fetch_at() is None

    when = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)
    storage.set_last_auto_fetch_at(when)
    assert storage.get_last_auto_fetch_at() == when


def test_auto_fetch_watermark_can_be_updated(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    storage.set_last_auto_fetch_at(datetime(2026, 3, 1, tzinfo=timezone.utc))
    storage.set_last_auto_fetch_at(datetime(2026, 3, 2, tzinfo=timezone.utc))

    assert storage.get_last_auto_fetch_at() == datetime(2026, 3, 2, tzinfo=timezone.utc)


def test_acknowledged_column_migrates_onto_a_pre_existing_db(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(storage, "DB_PATH", db_path)

    # Simulate a DB created before the `acknowledged` column existed.
    old_schema = storage._SCHEMA.replace(",\n    acknowledged INTEGER NOT NULL DEFAULT 0\n)", "\n)")
    conn = sqlite3.connect(db_path)
    conn.execute(old_schema)
    conn.commit()
    conn.close()

    storage.save_processed(_processed("1"))
    items = storage.get_history()
    assert items[0]["acknowledged"] == 0


def test_tombstoned_id_can_be_saved_again_directly(tmp_path, monkeypatch):
    # storage.save_processed itself doesn't enforce tombstones — that's the
    # caller's job (see /email/fetch filtering deleted ids before processing).
    # This documents that save_processed is not where resurrection is blocked.
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")
    storage.save_processed(_processed("1"))
    storage.delete_processed("1")

    storage.save_processed(_processed("1"))

    assert {item["id"] for item in storage.get_history()} == {"1"}