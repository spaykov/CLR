import getpass
import os
import pathlib
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from clr.api.auth import SESSION_COOKIE_NAME
from clr.api.routes import router, public_router
from clr.config import settings
from clr.core import sessions

BASE_DIR = pathlib.Path(__file__).parent

app = FastAPI(
    title="Cognitive Load Reducer",
    description="AI-powered cognitive firewall that reduces mental overhead.",
    version="0.1.0",
)

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "ui" / "static"),
    name="static",
)


@app.middleware("http")
async def no_cache_for_frontend(request, call_next):
    # Force revalidation on every load so browsers can't serve a stale HTML/JS/CSS
    # bundle after --reload picks up a backend or frontend change.
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def index(request: Request):
    if settings.login_password:
        token = request.cookies.get(SESSION_COOKIE_NAME)
        if not (token and sessions.is_valid(token)):
            return (BASE_DIR / "ui" / "templates" / "login.html").read_text(encoding="utf-8")
    return (BASE_DIR / "ui" / "templates" / "index.html").read_text(encoding="utf-8")


app.include_router(router)
app.include_router(public_router)


MIN_API_KEY_LENGTH = 20
MIN_LOGIN_PASSWORD_LENGTH = 12


def validate_startup_config(
    host: str, api_key: str, login_password: str, tls_available: bool = True
) -> None:
    """Fail fast on an insecure LAN-exposed config, before uvicorn ever binds.

    These checks only hard-fail once the server is actually reachable beyond
    your own machine — a short throwaway secret, or plain HTTP, for pure
    localhost dev isn't this function's business. `tls_available` defaults to
    True so callers that don't care about the TLS check (e.g. existing
    secrets-only tests) aren't forced to thread it through.
    """
    exposed_beyond_localhost = host not in ("127.0.0.1", "localhost")
    if not exposed_beyond_localhost:
        return

    if not (api_key or login_password):
        raise SystemExit(
            f"CLR_HOST={host} binds beyond localhost but neither "
            "CLR_API_KEY nor CLR_LOGIN_PASSWORD is set. Set at least one in "
            ".env before exposing the server, or set CLR_HOST back to "
            "127.0.0.1."
        )

    if api_key and len(api_key) < MIN_API_KEY_LENGTH:
        raise SystemExit(
            f"CLR_API_KEY is only {len(api_key)} characters, below the "
            f"{MIN_API_KEY_LENGTH}-character minimum for a LAN-exposed server. "
            "Generate a stronger one with `python scripts/rotate_secrets.py`."
        )

    if login_password and len(login_password) < MIN_LOGIN_PASSWORD_LENGTH:
        raise SystemExit(
            f"CLR_LOGIN_PASSWORD is only {len(login_password)} characters, "
            f"below the {MIN_LOGIN_PASSWORD_LENGTH}-character minimum for a "
            "LAN-exposed server. Generate a stronger one with "
            "`python scripts/rotate_secrets.py`."
        )

    if not tls_available:
        raise SystemExit(
            f"CLR_HOST={host} binds beyond localhost but no TLS certificate "
            "was found at the configured CLR_TLS_CERT_FILE/CLR_TLS_KEY_FILE "
            "paths. Plain HTTP on a LAN exposes your login password, session "
            "cookie, and any Gmail content in transit. Generate one with "
            "`python scripts/generate_tls_cert.py`, or set CLR_HOST back to "
            "127.0.0.1."
        )


if __name__ == "__main__":
    cert_path = pathlib.Path(settings.tls_cert_file)
    key_path = pathlib.Path(settings.tls_key_file)
    tls_available = cert_path.exists() and key_path.exists()

    validate_startup_config(
        settings.host, settings.api_key, settings.login_password, tls_available
    )

    if settings.gmail_address and not settings.gmail_app_password:
        password = getpass.getpass(
            f"Gmail app password for {settings.gmail_address} (leave blank to skip email features): "
        )
        if password:
            # Set in the environment (not just the settings object) so the
            # uvicorn --reload worker subprocess inherits it too.
            os.environ["CLR_GMAIL_APP_PASSWORD"] = password
            settings.gmail_app_password = password

    ssl_kwargs = {}
    if tls_available:
        ssl_kwargs = {"ssl_keyfile": str(key_path), "ssl_certfile": str(cert_path)}

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=True,
        **ssl_kwargs,
    )