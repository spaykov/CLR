import time
from collections import defaultdict, deque

_hits: dict[str, deque] = defaultdict(deque)


def allow(key: str, limit: int, window_seconds: float) -> bool:
    """Sliding-window rate check: True (and records the call) if fewer than
    `limit` calls have landed for `key` in the last `window_seconds`, else
    False.

    In-memory only — resets on process restart, same tradeoff already
    accepted for clr/core/sessions.py. Fine for a single-process local/LAN
    tool; would need a shared store (e.g. Redis) behind multiple workers.
    """
    now = time.monotonic()
    hits = _hits[key]
    while hits and now - hits[0] > window_seconds:
        hits.popleft()
    if len(hits) >= limit:
        return False
    hits.append(now)
    return True


def reset() -> None:
    """Test-only: clear all rate-limit state."""
    _hits.clear()
