import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.database import db_manager
from app.services.auth_service import AuthService

# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Application Lifespan
# ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown."""

    logger.info(
        "Starting %s v%s (%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )

    # Connect MongoDB
    await db_manager.connect()

    # Create required database indexes
    auth_service = AuthService(db_manager.get_db())
    await auth_service.create_indexes()

    logger.info("Database initialized successfully.")

    yield

    # Shutdown
    await db_manager.disconnect()

    logger.info("Application shut down successfully.")


# ──────────────────────────────────────────────────────────────
# FastAPI App
# ──────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-Powered Medical Diagnosis & Clinical Decision Support System",
    lifespan=lifespan,
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url="/api/redoc" if not settings.is_production else None,
    openapi_url="/api/openapi.json" if not settings.is_production else None,
)


# ──────────────────────────────────────────────────────────────
# CORS
# ──────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────
# Request Timing Middleware
# ──────────────────────────────────────────────────────────────

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    duration = (time.perf_counter() - start) * 1000

    response.headers["X-Process-Time-Ms"] = f"{duration:.2f}"

    return response


# ──────────────────────────────────────────────────────────────
# Global Exception Handler
# ──────────────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):

    logger.exception(
        "Unhandled exception on %s %s",
        request.method,
        request.url,
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal server error occurred.",
            "detail": str(exc)
            if settings.is_development
            else "Contact support.",
        },
    )


# ──────────────────────────────────────────────────────────────
# Health Endpoints
# ──────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["System"])
async def health_check():

    db_status = "disconnected"

    try:
        await db_manager.client.admin.command("ping")
        db_status = "connected"
    except Exception:
        db_status = "unreachable"

    return {
        "success": True,
        "status": "healthy" if db_status == "connected" else "degraded",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "services": {
            "api": "online",
            "database": db_status,
        },
    }


@app.get("/api/ping", tags=["System"])
async def ping():
    return {
        "success": True,
        "message": "pong",
    }


# ──────────────────────────────────────────────────────────────
# Routers
# ──────────────────────────────────────────────────────────────

from app.api.v1.routes import auth, users

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Auth"],
)

app.include_router(
    users.router,
    prefix="/api/v1/users",
    tags=["Users"],
)

# Future Phases
#
# from app.api.v1.routes import patients
# from app.api.v1.routes import diagnoses
#
# app.include_router(
#     patients.router,
#     prefix="/api/v1/patients",
#     tags=["Patients"],
# )
#
# app.include_router(
#     diagnoses.router,
#     prefix="/api/v1/diagnoses",
#     tags=["Diagnoses"],
# )