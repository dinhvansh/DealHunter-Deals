from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from dealhunter import __version__
from dealhunter.api.routes import router
from dealhunter.api.v1.routes_phase2_10 import router as phase_router

app = FastAPI(title="DealHunter API", version=__version__)
app.include_router(router)
app.include_router(phase_router)


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
