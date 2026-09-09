import logging

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from dealhunter import __version__
from dealhunter.api.routes import router
from dealhunter.api.v1.routes_phase2_10 import router as phase_router
from dealhunter.providers.errors import ProviderBlockedError, ProviderError

logger = logging.getLogger(__name__)

app = FastAPI(title="DealHunter API", version=__version__)
app.include_router(router)
app.include_router(phase_router)


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


@app.get("/", response_class=HTMLResponse)
def home():
    try:
        with open("src/dealhunter/ui/static/index.html", "r", encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return "<h1>DealHunter</h1><p>UI shell unavailable in this runtime.</p>"
