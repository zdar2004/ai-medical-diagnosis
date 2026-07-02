import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import db_manager

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    logger.info("Starting %s v%s [%s]", settings.app_name, settings.app_version, settings.environment)
    await db_manager.connect()
    yield
    await db_manager.disconnect()
    logger.info("Application shut down cleanly.")


# ── App factory ───────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-Powered Medical Diagnosis & Clinical Decision Support System",
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url="/api/redoc" if not settings.is_production else None,
    openapi_url="/api/openapi.json" if not settings.is_production else None,
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request timing middleware ─────────────────────────────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{duration:.2f}"
    return response


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal server error occurred.",
            "detail": str(exc) if settings.is_development else "Contact support.",
        },
    )


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["System"], summary="Health check")
async def health_check():
    """
    Returns service status.
    Checks FastAPI and MongoDB connectivity.
    """
    db_status = "disconnected"
    try:
        await db_manager.client.admin.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "unreachable"

    overall = "healthy" if db_status == "connected" else "degraded"

    return {
        "success": True,
        "status": overall,
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "services": {
            "api": "online",
            "database": db_status,
        },
    }


@app.get("/api/ping", tags=["System"], summary="Liveness probe")
async def ping():
    """Minimal liveness endpoint — no DB check."""
    return {"success": True, "message": "pong"}


# ── Router registration (add here as features are built) ─────────────────────
from app.api.v1.routes import auth, users                          # Phase 2
from app.api.v1.routes import patients                             # Phase 5
from app.api.v1.routes import diagnoses                         # Phase 6+

app.include_router(auth.router,     prefix="/api/v1/auth",  tags=["Auth"])
app.include_router(users.router,    prefix="/api/v1/users", tags=["Users"])
app.include_router(patients.router, prefix="/api/v1/patients", tags=["Patients"])
app.include_router(diagnoses.router, prefix="/api/v1/diagnoses", tags=["Diagnoses"])