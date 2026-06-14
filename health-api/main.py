from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import reports, klaire, email, storage, jobs
from api.core.config import get_settings

app = FastAPI(title="Clearline HMO Health Screening API", version="0.1.0")

_settings = get_settings()
_cors_origins = (
    ["*"]
    if _settings.cors_origins.strip() == "*"
    else [o.strip() for o in _settings.cors_origins.split(",") if o.strip()]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=_settings.cors_origins.strip() != "*",
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
app.include_router(klaire.router, prefix="/api", tags=["klaire"])
app.include_router(email.router, prefix="/api/email", tags=["email"])
app.include_router(storage.router, prefix="/api/storage", tags=["storage"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok"}
