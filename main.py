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


if __name__ == "__main__":
    if settings.host not in ("127.0.0.1", "localhost") and not (
        settings.api_key or settings.login_password
    ):
        raise SystemExit(
            f"CLR_HOST={settings.host} binds beyond localhost but neither "
            "CLR_API_KEY nor CLR_LOGIN_PASSWORD is set. Set at least one in "
            ".env before exposing the server, or set CLR_HOST back to "
            "127.0.0.1."
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

    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level,
        reload=True,
    )