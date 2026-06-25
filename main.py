import getpass
import os
import pathlib
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from clr.api.routes import router
from clr.config import settings

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


@app.get("/", response_class=FileResponse, include_in_schema=False)
def index():
    return str(BASE_DIR / "ui" / "templates" / "index.html")


app.include_router(router)


if __name__ == "__main__":
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