import pathlib
import sqlite3
from datetime import datetime, timezone

from clr.models.message import ProcessedMessage

DB_PATH = pathlib.Path(__file__).resolve().parent.parent.parent / "clr_data.db"

# Mirrors ProcessedMessage minus original.content and original.metadata: the raw
# email body is deliberately not persisted (PII, phishing payloads, tracking
# links) and is already re-fetchable from Gmail on demand.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS processed_messages (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    category TEXT NOT NULL,
    received_at TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    simplified TEXT NOT NULL DEFAULT '',
    priority TEXT NOT NULL,
    action_required INTEGER NOT NULL,
    suggested_action TEXT NOT NULL DEFAULT '',
    filtered_out INTEGER NOT NULL,
    filter_reason TEXT NOT NULL DEFAULT '',
    cognitive_cost INTEGER NOT NULL,
    processed_at TEXT NOT NULL
)
"""

# A user-initiated delete is a tombstone, not just a row removal: re-fetching
# the same email later (e.g. from Gmail, still within the lookback window)
# must not resurrect it. IDs here are permanent and outlive the row they
# once corresponded to in processed_messages.
_DELETED_SCHEMA = """
CREATE TABLE IF NOT EXISTS deleted_message_ids (
    id TEXT PRIMARY KEY,
    deleted_at TEXT NOT NULL
)
"""


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    conn.execute(_DELETED_SCHEMA)
    return conn


def save_processed(message: ProcessedMessage) -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO processed_messages
                (id, source, category, received_at, summary, simplified, priority,
                 action_required, suggested_action, filtered_out, filter_reason,
                 cognitive_cost, processed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message.original.id,
                message.original.source,
                message.original.category.value,
                message.original.received_at.isoformat(),
                message.summary,
                message.simplified,
                message.priority.value,
                int(message.action_required),
                message.suggested_action,
                int(message.filtered_out),
                message.filter_reason,
                message.cognitive_cost,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_history(limit: int = 50, offset: int = 0) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute(
            "SELECT * FROM processed_messages ORDER BY processed_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def delete_processed(message_id: str) -> bool:
    conn = _connect()
    try:
        cur = conn.execute("DELETE FROM processed_messages WHERE id = ?", (message_id,))
        deleted = cur.rowcount > 0
        if deleted:
            conn.execute(
                "INSERT OR REPLACE INTO deleted_message_ids (id, deleted_at) VALUES (?, ?)",
                (message_id, datetime.now(timezone.utc).isoformat()),
            )
        conn.commit()
        return deleted
    finally:
        conn.close()


def clear_history() -> int:
    conn = _connect()
    try:
        ids = [row["id"] for row in conn.execute("SELECT id FROM processed_messages")]
        now = datetime.now(timezone.utc).isoformat()
        conn.executemany(
            "INSERT OR REPLACE INTO deleted_message_ids (id, deleted_at) VALUES (?, ?)",
            [(i, now) for i in ids],
        )
        cur = conn.execute("DELETE FROM processed_messages")
        conn.commit()
        return cur.rowcount
    finally:
        conn.close()


def get_deleted_ids(ids: list[str]) -> set[str]:
    """Which of the given message ids have been tombstoned by a prior delete."""
    if not ids:
        return set()
    conn = _connect()
    try:
        placeholders = ",".join("?" * len(ids))
        rows = conn.execute(
            f"SELECT id FROM deleted_message_ids WHERE id IN ({placeholders})", ids
        ).fetchall()
        return {row["id"] for row in rows}
    finally:
        conn.close()