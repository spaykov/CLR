from fastapi import HTTPException, Request

from clr.api.auth import SESSION_COOKIE_NAME
from clr.core import rate_limit


def _ip_key(request: Request) -> str:
    return f"ip:{request.client.host if request.client else 'unknown'}"


def _client_key(request: Request) -> str:
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"key:{api_key}"
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        return f"session:{token}"
    return _ip_key(request)


def rate_limited(limit: int, window_seconds: float, *, by_ip: bool = False):
    """FastAPI dependency: reject with 429 once `limit` calls land within
    `window_seconds` for the same client on this route.

    Keyed by API key or session cookie by default, so different users/
    devices get independent budgets. Pass `by_ip=True` for pre-auth
    endpoints (e.g. /auth/login) where no key/cookie exists yet — keying
    those by IP instead of by credential stops an attacker from resetting
    their own budget by simply omitting/varying the cookie.
    """
    key_fn = _ip_key if by_ip else _client_key

    def dependency(request: Request) -> None:
        # limit/window are part of the bucket key so that a route with both
        # the router-level default and its own tighter limit tracks each
        # independently, instead of two dependencies sharing (and doubly
        # consuming) one counter.
        bucket = f"{request.url.path}:{limit}:{window_seconds}:{key_fn(request)}"
        if not rate_limit.allow(bucket, limit, window_seconds):
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please wait a moment and try again.",
                headers={"Retry-After": str(int(window_seconds))},
            )

    return dependency
