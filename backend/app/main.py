"""
FastAPI application entry point.
Configures middleware, routers, exception handlers, and lifespan events.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time

from app.config import get_settings
from app.utils.logger import setup_logging, get_logger
from app.routers import health, repository, generate, export, chat

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown events."""
    settings = get_settings()
    setup_logging(debug=settings.DEBUG, structured=not settings.DEBUG)
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Mock mode: {settings.MOCK_MODE}")

    # In-memory storage for processing state (replace with DB/Redis in production)
    app.state.repositories = {}
    app.state.generations = {}

    yield

    logger.info("Shutting down application")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description="GenAI-powered engineering assistant that analyzes repositories and generates software requirements and unit test cases",
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ─── CORS ───
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ─── Request timing middleware ───
    @app.middleware("http")
    async def add_timing_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{elapsed:.3f}s"
        return response

    # ─── Global exception handler ───
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An internal error occurred. Please try again.",
                "error_type": type(exc).__name__,
            },
        )

    # ─── Routers ───
    app.include_router(health.router, tags=["Health"])
    app.include_router(repository.router, prefix="/api", tags=["Repository"])
    app.include_router(generate.router, prefix="/api", tags=["Generation"])
    app.include_router(export.router, prefix="/api", tags=["Export"])
    app.include_router(chat.router, prefix="/api", tags=["Chat"])

    return app


app = create_app()
