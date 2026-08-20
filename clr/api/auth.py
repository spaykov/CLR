import secrets

from fastapi import Header, HTTPException, Request, status

from clr.config import settings
from clr.core import sessions

SESSION_COOKIE_NAME = "clr_session"


async def require_api_key(
    request: Request, x_api_key: str | None = Header(default=None)
) -> None:
    """Enforce auth on /api/v1/* when either secret is configured; no-op if neither is.

    Accepts an X-API-Key header matching CLR_API_KEY (scripts/curl) or a
    valid session cookie set by POST /auth/login with CLR_LOGIN_PASSWORD
    (browser UI). The two secrets are independent — either one being
    configured turns auth on for both entry points.
    """
    if not settings.api_key and not settings.login_password:
        return
    if settings.api_key and x_api_key and secrets.compare_digest(x_api_key, settings.api_key):
        return
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token and sessions.is_valid(token):
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid API key",
    )
