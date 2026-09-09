from fastapi import FastAPI

from dealhunter import __version__
from dealhunter.api.routes import router

app = FastAPI(title="DealHunter API", version=__version__)
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "dealhunter-api", "version": __version__}
