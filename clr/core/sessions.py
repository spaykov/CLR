import secrets
import time

# In-memory only: sessions are lost on process restart (including the
# uvicorn --reload worker restarting after a code change during dev).
# Acceptable for a single-process local/LAN tool; would need a shared store
# (e.g. the sqlite db in storage.py) to survive restarts or scale to
# multiple workers.
_SESSION_TTL_SECONDS = 12 * 60 * 60

_sessions: dict[str, float] = {}


def create_session() -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = time.time() + _SESSION_TTL_SECONDS
    return token


def is_valid(token: str) -> bool:
    expiry = _sessions.get(token)
    if expiry is None:
        return False
    if expiry < time.time():
        del _sessions[token]
        return False
    return True


def destroy(token: str) -> None:
    _sessions.pop(token, None)
