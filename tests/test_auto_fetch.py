from datetime import datetime, timedelta, timezone

import pytest

import main
from clr.core import email_fetcher, email_pipeline, storage


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test.db")


@pytest.mark.asyncio
async def test_skips_when_no_gmail_credentials(monkeypatch):
    monkeypatch.setattr(email_fetcher, "has_credentials", lambda: False)
    called = []
    monkeypatch.setattr(email_pipeline, "run_email_fetch", lambda hours: called.append(hours))

    await main.run_auto_fetch_once()

    assert called == []
    assert storage.get_last_auto_fetch_at() is None


@pytest.mark.asyncio
async def test_first_run_uses_configured_lookback_hours(monkeypatch):
    monkeypatch.setattr(email_fetcher, "has_credentials", lambda: True)
    monkeypatch.setattr(main.settings, "auto_fetch_lookback_hours", 24)
    called = []
    monkeypatch.setattr(
        email_pipeline, "run_email_fetch",
        lambda hours: called.append(hours) or {"processed": []},
    )

    await main.run_auto_fetch_once()

    assert called == [24]
    assert storage.get_last_auto_fetch_at() is not None


@pytest.mark.asyncio
async def test_later_run_covers_gap_since_last_watermark(monkeypatch):
    fixed_now = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)

    class _FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed_now

    monkeypatch.setattr(main, "datetime", _FixedDatetime)
    monkeypatch.setattr(email_fetcher, "has_credentials", lambda: True)
    storage.set_last_auto_fetch_at(fixed_now - timedelta(hours=3))
    called = []
    monkeypatch.setattr(
        email_pipeline, "run_email_fetch",
        lambda hours: called.append(hours) or {"processed": []},
    )

    await main.run_auto_fetch_once()

    assert called == [4]  # ceil(3) + 1 hour of slack


@pytest.mark.asyncio
async def test_updates_watermark_only_on_success(monkeypatch):
    monkeypatch.setattr(email_fetcher, "has_credentials", lambda: True)

    def _boom(hours):
        raise RuntimeError("IMAP exploded")

    monkeypatch.setattr(email_pipeline, "run_email_fetch", _boom)

    await main.run_auto_fetch_once()  # must not raise

    assert storage.get_last_auto_fetch_at() is None
