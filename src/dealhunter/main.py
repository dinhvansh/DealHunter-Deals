import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from sqlalchemy.exc import SQLAlchemyError

from dealhunter import __version__
from dealhunter.api.routes import router
from dealhunter.api.setup_auth import router as setup_router
from dealhunter.api.v1.routes_phase2_10 import router as phase_router
from dealhunter.db.session import SessionLocal
from dealhunter.providers.errors import ProviderBlockedError, ProviderError
from dealhunter.services.security import SESSION_COOKIE, get_session_user, setup_complete

logger = logging.getLogger(__name__)

app = FastAPI(title="DealHunter API", version=__version__)
app.include_router(setup_router)
app.include_router(router)
app.include_router(phase_router)

PUBLIC_ALWAYS = {
    "/health",
    "/setup",
    "/login",
    "/api/v1/setup/status",
    "/api/v1/setup/complete",
    "/api/v1/auth/login",
}


def _wants_html(request: Request) -> bool:
    return "text/html" in request.headers.get("accept", "") or not request.url.path.startswith("/api/")


def _load_html(name: str) -> str:
    path = Path("src/dealhunter/ui/static") / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return "<h1>DealHunter</h1><p>UI unavailable in this runtime.</p>"


@app.middleware("http")
async def setup_and_auth_gate(request: Request, call_next):
    path = request.url.path
    if path == "/health" or path.startswith("/api/v1/go/"):
        return await call_next(request)

    try:
        with SessionLocal() as db:
            completed = setup_complete(db)
            if not completed:
                if path in PUBLIC_ALWAYS or path.startswith("/api/v1/setup/"):
                    return await call_next(request)
                if _wants_html(request):
                    return RedirectResponse("/setup", status_code=307)
                return JSONResponse(
                    status_code=428,
                    content={"detail": {"code": "setup_required", "message": "Complete /setup first."}},
                )

            if path == "/setup":
                return RedirectResponse("/", status_code=307)
            if path in {"/login", "/api/v1/auth/login", "/api/v1/setup/status"}:
                return await call_next(request)

            user = get_session_user(db, request.cookies.get(SESSION_COOKIE))
            if user is None:
                if _wants_html(request):
                    next_path = request.url.path
                    return RedirectResponse(f"/login?next={next_path}", status_code=307)
                return JSONResponse(
                    status_code=401,
                    content={"detail": {"code": "authentication_required", "message": "Log in first."}},
                )
            request.state.user = user
    except SQLAlchemyError:
        logger.exception("auth_gate_database_error path=%s", path)
        if _wants_html(request):
            return HTMLResponse(
                "<h1>DealHunter database is not migrated</h1><p>Run <code>alembic upgrade head</code> and reload.</p>",
                status_code=503,
            )
        return JSONResponse(
            status_code=503,
            content={
                "detail": {
                    "code": "database_not_ready",
                    "message": "Run `alembic upgrade head` before using DealHunter.",
                }
            },
        )
    return await call_next(request)


@app.exception_handler(ProviderBlockedError)
async def provider_blocked_handler(request: Request, exc: ProviderBlockedError):
    logger.warning("provider_blocked path=%s error=%s", request.url.path, exc)
    return JSONResponse(
        status_code=502,
        content={
            "detail": {
                "code": "provider_blocked",
                "message": str(exc),
                "hint": "Shopee challenged or rate-limited the collector. Check the Chrome session/IP and reduce request frequency.",
            }
        },
    )


@app.exception_handler(ProviderError)
async def provider_error_handler(request: Request, exc: ProviderError):
    logger.warning("provider_error path=%s error=%s", request.url.path, exc)
    return JSONResponse(
        status_code=502,
        content={
            "detail": {
                "code": "provider_error",
                "message": str(exc),
                "hint": "Check `docker compose logs --tail=200 api` and verify Google Chrome Stable can open Shopee.",
            }
        },
    )


@app.get("/health")
def health():
    return {"status": "ok", "service": "dealhunter-api", "version": __version__}


@app.get("/setup", response_class=HTMLResponse)
def setup_page():
    return _load_html("setup.html")


@app.get("/login", response_class=HTMLResponse)
def login_page():
    return _load_html("login.html")


@app.get("/settings", response_class=HTMLResponse)
def settings_page():
    return _load_html("settings.html")


@app.get("/", response_class=HTMLResponse)
def home():
    html = _load_html("index.html")
    marker = '<span class="top-pill">AI Deal Radar</span>'
    settings_link = marker + '<a class="top-pill" href="/settings">⚙ Settings</a>'
    return html.replace(marker, settings_link, 1)
